-- 0003_add_reservation_attendee_count.sql
-- CR-003: 予約に参加予定人数(attendee_count)を追加する (docs/P003-backend-spec.md §6.3 参照)
-- 既存行は attendee_count = NULL (未設定) として扱う。
-- 値域(1以上の整数)および会議室の収容人数(ROOMS.capacity)との比較は
-- アプリケーション層(validators.py / reservation_service.py)で検証する。
-- 適用方式(SCHEMA_MIGRATIONSによる差分適用)は docs/P003-backend-spec.md §6.4 を参照。

ALTER TABLE RESERVATIONS ADD COLUMN attendee_count INTEGER;
