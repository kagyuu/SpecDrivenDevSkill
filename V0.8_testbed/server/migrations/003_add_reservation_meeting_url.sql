-- CR-001 (docs/P901-cr-direction/CR-001.md, docs/P903-cr-records/CR-001.md)
-- Adds an optional "オンライン会議URL" field to reservations.
-- NULL-able, no DEFAULT needed beyond SQLite's implicit NULL default, so
-- existing rows (created before this migration) simply get NULL and are
-- unaffected (docs/P003-backend-spec.md 2.2節).
--
-- Idempotency: this file is applied at most once by
-- server/app/db/migration.py's apply_pending_migrations(), which records
-- this file's version ("003_add_reservation_meeting_url") in the
-- schema_migrations table and skips already-applied versions on every
-- subsequent call - see docs/P003-backend-spec.md 3章 and the real
-- two-consecutive-run verification recorded in
-- docs/P903-cr-records/CR-001.md.

ALTER TABLE reservations ADD COLUMN meeting_url TEXT;
