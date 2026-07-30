"""会議室Repository。docs/03-backend-spec.md 4章「会議室系」対応。"""
import sqlite3


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "capacity": row["capacity"],
        "equipment": row["equipment"],
        "is_active": bool(row["is_active"]),
    }


def list_rooms(conn: sqlite3.Connection, include_inactive: bool = False) -> list[dict]:
    if include_inactive:
        rows = conn.execute("SELECT * FROM rooms ORDER BY id").fetchall()
    else:
        rows = conn.execute("SELECT * FROM rooms WHERE is_active = 1 ORDER BY id").fetchall()
    return [_row_to_dict(r) for r in rows]


def get_room(conn: sqlite3.Connection, room_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()
    return _row_to_dict(row) if row else None


def name_exists(conn: sqlite3.Connection, name: str, exclude_id: int | None = None) -> bool:
    if exclude_id is None:
        row = conn.execute(
            "SELECT 1 FROM rooms WHERE name = ? AND is_active = 1", (name,)
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT 1 FROM rooms WHERE name = ? AND is_active = 1 AND id != ?",
            (name, exclude_id),
        ).fetchone()
    return row is not None


def create_room(conn: sqlite3.Connection, name: str, capacity: int, equipment: str | None) -> dict:
    cur = conn.execute(
        "INSERT INTO rooms (name, capacity, equipment, is_active) VALUES (?, ?, ?, 1)",
        (name, capacity, equipment),
    )
    conn.commit()
    return get_room(conn, cur.lastrowid)


def update_room(
    conn: sqlite3.Connection, room_id: int, name: str, capacity: int, equipment: str | None, is_active: bool
) -> dict | None:
    conn.execute(
        "UPDATE rooms SET name = ?, capacity = ?, equipment = ?, is_active = ? WHERE id = ?",
        (name, capacity, equipment, int(is_active), room_id),
    )
    conn.commit()
    return get_room(conn, room_id)


def deactivate_room(conn: sqlite3.Connection, room_id: int) -> None:
    conn.execute("UPDATE rooms SET is_active = 0 WHERE id = ?", (room_id,))
    conn.commit()
