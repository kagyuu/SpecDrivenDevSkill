-- 002-rooms.sql — rooms(Sprint 2)
-- 参照: docs/P002-frontend-spec.md 6.2(rooms)、docs/P003-backend-spec.md 3.4(uq_rooms_name_active)
-- 差分適用型マイグレーション(ADR-009)のため IF NOT EXISTS は付けない。001-init.sql は編集しない。

CREATE TABLE rooms (
  room_id     INTEGER PRIMARY KEY AUTOINCREMENT,
  name        TEXT    NOT NULL,
  capacity    INTEGER NOT NULL CHECK (capacity >= 1 AND capacity <= 500),
  equipment   TEXT    NOT NULL DEFAULT '',
  description TEXT    NOT NULL DEFAULT '',
  is_active   INTEGER NOT NULL DEFAULT 1,
  created_at  TEXT    NOT NULL,
  updated_at  TEXT    NOT NULL
);

-- 有効な行のなかでのみ一意(無効化した会議室と同名の再登録を許すため部分ユニークにする)
CREATE UNIQUE INDEX uq_rooms_name_active ON rooms(name) WHERE is_active = 1;
