-- U001-T2 (docs/P007-impl-direction/U001-foundation-and-auth.md)
-- Full initial schema, transcribed verbatim from docs/P003-backend-spec.md 2.2節.

CREATE TABLE IF NOT EXISTS users (
    user_id        TEXT PRIMARY KEY,
    name           TEXT NOT NULL,
    password_hash  TEXT NOT NULL,
    role           TEXT NOT NULL CHECK (role IN ('general', 'admin')),
    is_active      INTEGER NOT NULL DEFAULT 1,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rooms (
    room_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    capacity       INTEGER NOT NULL CHECK (capacity >= 1),
    equipment      TEXT NOT NULL DEFAULT '[]',   -- JSON配列文字列
    description    TEXT,
    is_active      INTEGER NOT NULL DEFAULT 1,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reservations (
    reservation_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id            INTEGER NOT NULL REFERENCES rooms(room_id),
    organizer_user_id  TEXT NOT NULL REFERENCES users(user_id),
    title              TEXT NOT NULL,
    start_datetime     TEXT NOT NULL,  -- ISO8601 'YYYY-MM-DDTHH:MM:SS'
    end_datetime       TEXT NOT NULL,
    attendee_count     INTEGER,
    notes              TEXT,
    created_at         TEXT NOT NULL,
    updated_at         TEXT NOT NULL,
    CHECK (end_datetime > start_datetime)
);
CREATE INDEX IF NOT EXISTS idx_reservations_room_time
    ON reservations (room_id, start_datetime, end_datetime);
CREATE INDEX IF NOT EXISTS idx_reservations_organizer
    ON reservations (organizer_user_id);

CREATE TABLE IF NOT EXISTS reservation_participants (
    reservation_id  INTEGER NOT NULL REFERENCES reservations(reservation_id),
    user_id         TEXT NOT NULL REFERENCES users(user_id),
    PRIMARY KEY (reservation_id, user_id)
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id  TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES users(user_id),
    expires_at  TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions (user_id);

CREATE TABLE IF NOT EXISTS schema_migrations (
    version      TEXT PRIMARY KEY,
    applied_at   TEXT NOT NULL
);
