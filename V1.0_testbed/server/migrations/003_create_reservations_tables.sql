-- 003_create_reservations_tables.sql
-- docs/P003-backend-spec.md §3.2 の reservations / reservation_participants に対応する。

CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL REFERENCES rooms(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL CHECK(end_time > start_time),
    title TEXT NOT NULL,
    expected_attendees INTEGER,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reservations_room_date ON reservations(room_id, date);

CREATE TABLE IF NOT EXISTS reservation_participants (
    reservation_id INTEGER NOT NULL REFERENCES reservations(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    PRIMARY KEY (reservation_id, user_id)
);
