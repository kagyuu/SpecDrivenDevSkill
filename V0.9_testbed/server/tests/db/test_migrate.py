import sqlite3
from pathlib import Path

import pytest

from app.db.migrate import run_migrations

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return {row[0] for row in rows}


def test_run_migrations_creates_core_tables():
    # ※U002-T1にもとづき更新: 003マイグレーション追加により適用件数が2→3件に変わったため、
    # このアサーションを更新した(docs/P007-impl-direction/U002-reservation-core.md U002-T1が
    # 想定する「後続スプリントでの構造的な既存テスト無効化」に該当する、範囲外編集ではない更新)。
    # ※さらにCR-001(U002-T7)にもとづき更新: 004マイグレーション追加により適用件数が3→4件に
    # 変わったため、このアサーションを更新した(範囲外編集ではない、CR-001対応に伴う更新)。
    conn = sqlite3.connect(":memory:")
    applied = run_migrations(conn, MIGRATIONS_DIR, applied_at="2026-08-11T00:00:00+00:00")

    assert applied == [1, 2, 3, 4]
    tables = _table_names(conn)
    assert {
        "users",
        "rooms",
        "sessions",
        "schema_migrations",
        "reservations",
        "reservation_participants",
    }.issubset(tables)

    row_count = conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
    assert row_count == 4

    columns = {row[1] for row in conn.execute("PRAGMA table_info(reservations)").fetchall()}
    assert "internal_memo" in columns  # ※CR-001により追加


def test_run_migrations_is_idempotent_on_second_run():
    conn = sqlite3.connect(":memory:")
    run_migrations(conn, MIGRATIONS_DIR, applied_at="2026-08-11T00:00:00+00:00")

    # 2回目の実行(冪等性の直接確認): 例外が発生せず、行数も変わらない。
    second_applied = run_migrations(conn, MIGRATIONS_DIR, applied_at="2026-08-11T00:05:00+00:00")

    assert second_applied == []
    row_count = conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
    assert row_count == 4


def test_run_migrations_applies_004_as_a_pure_diff_on_top_of_001_002_003(tmp_path):
    # CR-001(U002-T7): 既に001〜003が適用済みのDBに、後から004(internal_memo列追加)を
    # 追加した場合でも、004のみが差分適用され、2回連続実行しても例外が発生しないことを確認する
    # (docs/P903-cr-records/CR-001.md「マイグレーション方式の確認」で約束した冪等性検証)。
    import shutil

    partial_dir = tmp_path / "migrations_partial"
    partial_dir.mkdir()
    for name in ("001_create_core_tables.sql", "002_seed_initial_users.sql", "003_create_reservations_tables.sql"):
        shutil.copy(MIGRATIONS_DIR / name, partial_dir / name)

    conn = sqlite3.connect(":memory:")
    first_applied = run_migrations(conn, partial_dir, applied_at="2026-08-11T00:00:00+00:00")
    assert first_applied == [1, 2, 3]
    columns_before = {row[1] for row in conn.execute("PRAGMA table_info(reservations)").fetchall()}
    assert "internal_memo" not in columns_before

    # 004を後から追加(=フルのmigrationsディレクトリを指す)して1回目の再実行。
    second_applied = run_migrations(conn, MIGRATIONS_DIR, applied_at="2026-08-11T01:00:00+00:00")
    assert second_applied == [4]
    columns_after = {row[1] for row in conn.execute("PRAGMA table_info(reservations)").fetchall()}
    assert "internal_memo" in columns_after

    # さらにもう一度(2回連続)実行しても例外が発生せず、何も再適用されないこと。
    third_applied = run_migrations(conn, MIGRATIONS_DIR, applied_at="2026-08-11T02:00:00+00:00")
    assert third_applied == []


def test_run_migrations_applies_003_as_a_pure_diff_on_top_of_001_002(tmp_path):
    # U002-T1: 既に001〜002が適用済みのDBに、後から003を追加した場合でも
    # 003のみが差分適用されること(既存の001/002は再実行されないこと)を確認する。
    # ※CR-001(U002-T7)にもとづき更新: 004マイグレーション追加により、フルの
    # migrationsディレクトリを指す2回目の実行では003に加えて004も差分適用されるため、
    # このテストの対象を「001・002のみ適用済みディレクトリ」から「001〜003のみ適用済み
    # ディレクトリ」に絞り、003単体の差分適用であることを検証する形に更新した
    # (範囲外編集ではない、CR-001対応に伴う既存テストの構造的な更新)。
    import shutil

    partial_dir = tmp_path / "migrations_partial"
    partial_dir.mkdir()
    for name in ("001_create_core_tables.sql", "002_seed_initial_users.sql"):
        shutil.copy(MIGRATIONS_DIR / name, partial_dir / name)

    conn = sqlite3.connect(":memory:")
    first_applied = run_migrations(conn, partial_dir, applied_at="2026-08-11T00:00:00+00:00")
    assert first_applied == [1, 2]
    assert "reservations" not in _table_names(conn)

    # 003のみを後から追加して再実行する(004はまだ追加しない)。
    full_through_003_dir = tmp_path / "migrations_through_003"
    full_through_003_dir.mkdir()
    for name in ("001_create_core_tables.sql", "002_seed_initial_users.sql", "003_create_reservations_tables.sql"):
        shutil.copy(MIGRATIONS_DIR / name, full_through_003_dir / name)
    second_applied = run_migrations(conn, full_through_003_dir, applied_at="2026-08-11T01:00:00+00:00")
    assert second_applied == [3]

    users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    assert users_count == 3  # 003適用によって既存データが失われていないこと
    assert {"reservations", "reservation_participants"}.issubset(_table_names(conn))


def test_run_migrations_raises_for_missing_directory():
    conn = sqlite3.connect(":memory:")
    with pytest.raises(FileNotFoundError):
        run_migrations(conn, "no/such/directory", applied_at="2026-08-11T00:00:00+00:00")
