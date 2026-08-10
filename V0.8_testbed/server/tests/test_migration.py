"""Unit tests for U001-T2 (docs/P007-impl-direction/U001-foundation-and-auth.md).

Target: app/db/migration.py apply_pending_migrations()

Positive case: applying the project's real migrations/ to an empty DB
creates schema_migrations rows and the seeded admin user.
Positive case (idempotency): applying a second time is a no-op.
Negative case: a migration file with a syntax error rolls back cleanly and
is not recorded as applied.
"""

from __future__ import annotations

import hashlib
import hmac
import sqlite3
from pathlib import Path

import pytest

from app.db.migration import apply_pending_migrations, applied_versions


def _fresh_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def test_apply_pending_migrations_creates_schema_and_seed_admin():
    conn = _fresh_connection()

    applied = apply_pending_migrations(conn)

    # CR-001 (docs/P903-cr-records/CR-001.md) added
    # migrations/003_add_reservation_meeting_url.sql; the list/set below were
    # updated to include it so this assertion keeps matching the real
    # contents of migrations/ instead of a stale hardcoded snapshot.
    assert applied == [
        "001_initial_schema",
        "002_seed_admin",
        "003_add_reservation_meeting_url",
    ]
    assert applied_versions(conn) == {
        "001_initial_schema",
        "002_seed_admin",
        "003_add_reservation_meeting_url",
    }

    admin_row = conn.execute(
        "SELECT user_id, role, is_active, password_hash FROM users WHERE user_id = ?",
        ("admin",),
    ).fetchone()
    assert admin_row is not None
    assert admin_row["role"] == "admin"
    assert admin_row["is_active"] == 1

    # Verify the seeded hash really is a valid scrypt hash of "ChangeMe123!"
    # using the exact scheme from docs/P003-backend-spec.md 1.2節, without
    # importing app.security.password (that module is owned by U001-T3,
    # which has not started at this point in the sprint - U001-T2 must not
    # depend on it).
    algo, salt_hex, hash_hex = admin_row["password_hash"].split("$")
    assert algo == "scrypt"
    recomputed = hashlib.scrypt(
        b"ChangeMe123!", salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1
    )
    assert hmac.compare_digest(recomputed, bytes.fromhex(hash_hex))


def test_apply_pending_migrations_is_idempotent():
    conn = _fresh_connection()

    first = apply_pending_migrations(conn)
    # CR-001: see comment in test_apply_pending_migrations_creates_schema_and_seed_admin.
    assert first == [
        "001_initial_schema",
        "002_seed_admin",
        "003_add_reservation_meeting_url",
    ]

    # Re-running (simulating a second application start) must not error and
    # must not re-apply or re-insert anything.
    second = apply_pending_migrations(conn)
    assert second == []

    migration_count = conn.execute(
        "SELECT COUNT(*) AS n FROM schema_migrations"
    ).fetchone()["n"]
    assert migration_count == 3

    admin_count = conn.execute(
        "SELECT COUNT(*) AS n FROM users WHERE user_id = ?", ("admin",)
    ).fetchone()["n"]
    assert admin_count == 1

    # A third run, for good measure (mirrors the "restart twice" check in
    # docs/P009-acceptance-direction/A009-restart-resilience.md).
    third = apply_pending_migrations(conn)
    assert third == []


def test_apply_pending_migrations_rolls_back_on_syntax_error(tmp_path: Path):
    bad_dir = tmp_path / "migrations"
    bad_dir.mkdir()
    (bad_dir / "001_broken.sql").write_text(
        "CREATE TABLE broken_table (id INTEGER PRIMARY KEY);\n"
        "INSERT INTO broken_table (id) VALUES (1);\n"
        "THIS IS NOT VALID SQL;\n",
        encoding="utf-8",
    )

    conn = _fresh_connection()

    with pytest.raises(sqlite3.OperationalError):
        apply_pending_migrations(conn, migrations_dir=bad_dir)

    # Nothing from the failed migration file may be recorded as applied...
    assert applied_versions(conn) == set()
    # ...and the DDL/DML it did manage to run before failing must have been
    # rolled back too (this is the specific atomicity gap that ruled out
    # sqlite3.Connection.executescript(), see app/db/migration.py).
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    assert "broken_table" not in tables
