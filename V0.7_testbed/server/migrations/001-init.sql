-- 001-init.sql — users / sessions(Sprint 1)
-- 参照: docs/P002-frontend-spec.md 6.2(users)、docs/P003-backend-spec.md 3.2(sessions)
-- 差分適用型マイグレーション(ADR-009)のため IF NOT EXISTS は付けない。

CREATE TABLE users (
  user_id       TEXT    PRIMARY KEY,
  name          TEXT    NOT NULL,
  password_hash TEXT    NOT NULL,
  role          TEXT    NOT NULL CHECK (role IN ('general', 'admin')),
  is_active     INTEGER NOT NULL DEFAULT 1,
  created_at    TEXT    NOT NULL,
  updated_at    TEXT    NOT NULL
);

CREATE TABLE sessions (
  session_id       TEXT PRIMARY KEY,
  user_id          TEXT NOT NULL REFERENCES users(user_id),
  created_at       TEXT NOT NULL,
  last_accessed_at TEXT NOT NULL,
  expires_at       TEXT NOT NULL
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
