-- 004-meeting-url.sql — reservations.meeting_url(オンライン会議URL)の追加
-- 起票: CR-001(docs/P901-cr-direction/CR-001.md)
-- 参照: docs/P002-frontend-spec.md 6.2(reservations のテーブル定義)、
--       docs/P003-backend-spec.md 3.5(マイグレーションの作法)、docs/ADR.md ADR-009 / ADR-011
-- 差分適用型マイグレーション(ADR-009)のため、適用済みの 001〜003 は編集しない。
-- SQLite の ALTER TABLE ... ADD COLUMN は IF NOT EXISTS を持たないが、schema_migrations に
-- 記録済みのファイルは再実行の対象にならないため、2回目以降の起動でも失敗しない。
-- NOT NULL を付けられるのは既定値を伴う場合のみ。DEFAULT '' により既存行にも適用できる(ADR-011)。

ALTER TABLE reservations ADD COLUMN meeting_url TEXT NOT NULL DEFAULT '';
