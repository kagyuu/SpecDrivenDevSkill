-- U001-T2 (docs/P007-impl-direction/U001-foundation-and-auth.md)
-- Seeds the initial administrator account used to log in before any other
-- user has been created via S07 (docs/P002-frontend-spec.md 3.7節).
--
-- password_hash below is a real hashlib.scrypt(n=2**14, r=8, p=1) digest of
-- the plaintext password "ChangeMe123!", in the "scrypt$<salt_hex>$<hash_hex>"
-- format defined in docs/P003-backend-spec.md 1.2節. It was computed once
-- with the project's own venv (see server/tests/test_migration.py for the
-- verification that login against this hash actually succeeds).
--
-- FIXME (carried over from docs/P007-impl-direction/U001-foundation-and-auth.md
-- U001-T2): this is a development/testbed-only credential. It must be
-- rotated (or a forced-change-on-first-login flow added, out of scope per
-- docs/P001-requirement.md) before any production deployment.

INSERT INTO users (user_id, name, password_hash, role, is_active, created_at, updated_at)
VALUES (
    'admin',
    'システム管理者',
    'scrypt$17ef7e0f2394bb640c887419f565530a$e56d27fa6aaf3f5b64d4ae277cc9dc2c03ae8e971fffe101df5a7fd36a6d5093111fb06e70d5a97c6faa5dd02949aebb8553f441aefe7a30c9755a74d76ed883',
    'admin',
    1,
    '2026-08-09T00:00:00',
    '2026-08-09T00:00:00'
);
