"""開発用初期データ投入。docs/06-impl-direction/U001-foundation.md U001-T1 参照。"""
import sqlite3

from app.security import hash_password


def seed(conn: sqlite3.Connection) -> None:
    existing = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    if existing > 0:
        return

    conn.execute(
        "INSERT INTO users (employee_id, name, password_hash, role, is_active) VALUES (?, ?, ?, ?, 1)",
        ("admin", "管理者", hash_password("admin12345"), "admin"),
    )
    conn.execute(
        "INSERT INTO users (employee_id, name, password_hash, role, is_active) VALUES (?, ?, ?, ?, 1)",
        ("u001", "山田太郎", hash_password("password1"), "general"),
    )
    conn.execute(
        "INSERT INTO users (employee_id, name, password_hash, role, is_active) VALUES (?, ?, ?, ?, 1)",
        ("u002", "鈴木花子", hash_password("password2"), "general"),
    )
    for name, capacity, equipment in [
        ("会議室A", 4, "プロジェクタ"),
        ("会議室B", 8, "プロジェクタ,ホワイトボード"),
        ("会議室C", 12, "ホワイトボード"),
    ]:
        conn.execute(
            "INSERT INTO rooms (name, capacity, equipment, is_active) VALUES (?, ?, ?, 1)",
            (name, capacity, equipment),
        )
    conn.commit()
