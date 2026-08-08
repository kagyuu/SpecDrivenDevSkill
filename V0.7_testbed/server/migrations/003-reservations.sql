-- 003-reservations.sql — reservations / reservation_attendees(Sprint 3)
-- 参照: docs/P002-frontend-spec.md 6.2(reservations / reservation_attendees)、
--       docs/P003-backend-spec.md 3.4(インデックス)、3.5(マイグレーションの作法)
-- 差分適用型マイグレーション(ADR-009)のため IF NOT EXISTS は付けない。001/002 は編集しない。

CREATE TABLE reservations (
  reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
  room_id        INTEGER NOT NULL REFERENCES rooms(room_id),
  user_id        TEXT    NOT NULL REFERENCES users(user_id),
  reserved_date  TEXT    NOT NULL,
  start_time     TEXT    NOT NULL,
  end_time       TEXT    NOT NULL CHECK (end_time > start_time),
  title          TEXT    NOT NULL,
  attendee_count INTEGER NULL CHECK (attendee_count IS NULL OR (attendee_count BETWEEN 1 AND 9999)),
  note           TEXT    NOT NULL DEFAULT '',
  created_at     TEXT    NOT NULL,
  updated_at     TEXT    NOT NULL
);

CREATE TABLE reservation_attendees (
  reservation_id INTEGER NOT NULL REFERENCES reservations(reservation_id) ON DELETE CASCADE,
  user_id        TEXT    NOT NULL REFERENCES users(user_id),
  PRIMARY KEY (reservation_id, user_id)
);

-- 重複チェック・カレンダー描画の主経路(P003 3.4)
CREATE INDEX idx_reservations_room_date ON reservations(room_id, reserved_date);
-- 期間指定の一覧取得(API-12)
CREATE INDEX idx_reservations_date ON reservations(reserved_date);
-- マイ予約一覧(API-13)
CREATE INDEX idx_reservations_user_date ON reservations(user_id, reserved_date);
