-- 0001_initial.sql
-- 会議室予約システム 初期スキーマ (docs/P003-backend-spec.md §6 準拠)

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS USERS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ROOMS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    capacity INTEGER NOT NULL,
    equipment TEXT,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS RESERVATIONS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    title TEXT NOT NULL,
    notes TEXT,
    created_by INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (room_id) REFERENCES ROOMS(id),
    FOREIGN KEY (created_by) REFERENCES USERS(id)
);

CREATE INDEX IF NOT EXISTS idx_reservations_room_date ON RESERVATIONS(room_id, date);

CREATE TABLE IF NOT EXISTS RESERVATION_PARTICIPANTS (
    reservation_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (reservation_id, user_id),
    FOREIGN KEY (reservation_id) REFERENCES RESERVATIONS(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES USERS(id)
);

CREATE TABLE IF NOT EXISTS SESSIONS (
    session_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES USERS(id)
);
