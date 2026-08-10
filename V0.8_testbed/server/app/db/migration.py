"""Migration runner (U001-T2, docs/P007-impl-direction/U001-foundation-and-auth.md).

Applies every *.sql file under server/migrations/, in filename order, that
is not yet recorded in the schema_migrations table. This is the concrete
mechanism behind ADR-004 (docs/ADR.md) and docs/P003-backend-spec.md 3章:
each migration file's statements and its schema_migrations bookkeeping row
are applied in a single transaction, so a mid-migration failure never
leaves the database "applied but not recorded" (or the reverse).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "migrations"


def _migration_files(migrations_dir: Path) -> list[Path]:
    return sorted(migrations_dir.glob("*.sql"), key=lambda p: p.name)


def _version_for(path: Path) -> str:
    return path.stem  # e.g. "001_initial_schema"


def _split_statements(sql: str) -> list[str]:
    """Split a migration file into individual SQL statements.

    Deliberately simple (strip '--' line comments, then split on ';')
    rather than a full SQL parser; sufficient for this project's own
    migrations/*.sql files, none of which contain a ';' inside a string
    literal or identifier.

    sqlite3.Connection.executescript() is intentionally NOT used here: it
    implicitly commits each statement as it runs, so a later statement's
    error does not roll back the earlier ones in the same script (verified
    empirically; see test_apply_pending_migrations_rolls_back_on_syntax_error
    in server/tests/test_migration.py). Executing statements one at a time
    inside an explicit BEGIN/COMMIT is what makes the "one transaction per
    migration file" guarantee in docs/P003-backend-spec.md 3章 actually hold
    for DDL, not just for INSERT/UPDATE/DELETE.
    """
    uncommented_lines = [raw_line.split("--", 1)[0] for raw_line in sql.splitlines()]
    joined = "\n".join(uncommented_lines)
    return [stmt.strip() for stmt in joined.split(";") if stmt.strip()]


def _ensure_schema_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version      TEXT PRIMARY KEY,
            applied_at   TEXT NOT NULL
        )
        """
    )


def applied_versions(conn: sqlite3.Connection) -> set[str]:
    _ensure_schema_migrations_table(conn)
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {row["version"] for row in rows}


def apply_pending_migrations(
    conn: sqlite3.Connection, migrations_dir: Path | None = None
) -> list[str]:
    """Apply every not-yet-applied migration file, in order.

    Returns the list of versions newly applied by this call. An empty list
    means everything was already up to date - this is what makes a second
    (or third, ...) call idempotent (docs/P003-backend-spec.md 3章,
    docs/P009-acceptance-direction/A009-restart-resilience.md).
    """
    directory = migrations_dir or MIGRATIONS_DIR
    _ensure_schema_migrations_table(conn)
    already_applied = applied_versions(conn)

    newly_applied: list[str] = []
    for path in _migration_files(directory):
        version = _version_for(path)
        if version in already_applied:
            continue

        statements = _split_statements(path.read_text(encoding="utf-8"))
        conn.execute("BEGIN")
        try:
            for statement in statements:
                conn.execute(statement)
            conn.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (version, datetime.now(timezone.utc).isoformat()),
            )
        except Exception:
            conn.rollback()
            raise
        else:
            conn.commit()
        newly_applied.append(version)
    return newly_applied
