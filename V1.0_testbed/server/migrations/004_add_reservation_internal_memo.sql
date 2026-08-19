-- 004_add_reservation_internal_memo.sql
-- ※CR-001により追加。docs/P901-cr-direction/CR-001.md、docs/P903-cr-records/CR-001.md参照。
-- 予約の「備考(社内向けメモ)」欄。所有者・管理者のみ閲覧可(マスキングはAPI層で行う、
-- docs/P003-backend-spec.md §5.9参照)。

ALTER TABLE reservations ADD COLUMN internal_memo TEXT;
