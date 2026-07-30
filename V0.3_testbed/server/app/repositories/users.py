"""ユーザーRepository。docs/03-backend-spec.md 4章「ユーザー系」対応。"""
import sqlite3

from app.security import hash_password


def row_to_public_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "employee_id": row["employee_id"],
        "name": row["name"],
        "role": row["role"],
        "is_active": bool(row["is_active"]),
    }


def list_users(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
    return [row_to_public_dict(r) for r in rows]


def get_user(conn: sqlite3.Connection, user_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return row_to_public_dict(row) if row else None


def get_user_by_employee_id(conn: sqlite3.Connection, employee_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM users WHERE employee_id = ?", (employee_id,)).fetchone()


def employee_id_exists(conn: sqlite3.Connection, employee_id: str, exclude_id: int | None = None) -> bool:
    if exclude_id is None:
        row = conn.execute("SELECT 1 FROM users WHERE employee_id = ?", (employee_id,)).fetchone()
    else:
        row = conn.execute(
            "SELECT 1 FROM users WHERE employee_id = ? AND id != ?", (employee_id, exclude_id)
        ).fetchone()
    return row is not None


def create_user(conn: sqlite3.Connection, employee_id: str, name: str, role: str, password: str) -> dict:
    cur = conn.execute(
        "INSERT INTO users (employee_id, name, password_hash, role, is_active) VALUES (?, ?, ?, ?, 1)",
        (employee_id, name, hash_password(password), role),
    )
    conn.commit()
    return get_user(conn, cur.lastrowid)


def update_user(
    conn: sqlite3.Connection,
    user_id: int,
    name: str,
    role: str,
    is_active: bool,
    password: str | None,
) -> dict | None:
    if password:
        conn.execute(
            "UPDATE users SET name = ?, role = ?, is_active = ?, password_hash = ? WHERE id = ?",
            (name, role, int(is_active), hash_password(password), user_id),
        )
    else:
        conn.execute(
            "UPDATE users SET name = ?, role = ?, is_active = ? WHERE id = ?",
            (name, role, int(is_active), user_id),
        )
    conn.commit()
    return get_user(conn, user_id)


def deactivate_user(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
    conn.commit()
