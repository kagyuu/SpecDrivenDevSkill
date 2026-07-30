"""SQLite接続とスキーマ定義。docs/03-backend-spec.md 2章・4章のテーブル定義に対応。"""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('general', 'admin')),
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    equipment TEXT,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL REFERENCES rooms(id),
    date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    subject TEXT NOT NULL,
    notes TEXT,
    created_by INTEGER NOT NULL REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS reservation_participants (
    reservation_id INTEGER NOT NULL REFERENCES reservations(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    PRIMARY KEY (reservation_id, user_id)
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
"""


def get_connection(path: str) -> sqlite3.Connection:
    """DB接続を取得しスキーマを初期化する。path=':memory:' はテスト用。"""
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn
