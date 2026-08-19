-- 002_seed_initial_users.sql
-- docs/P006-test-plan.md §5 のテストユーザーをシードする。
-- パスワードは全ユーザー共通で "TestPassw0rd!" (bcryptハッシュ済み)。

INSERT OR IGNORE INTO users (employee_id, name, password_hash, role, is_active, created_at, updated_at)
VALUES
    ('admin001', '管理者太郎', '$2b$12$7qTddFNjw4mfBuwrTIInUOMn/MkqrFzSPD87UjKsuvScWZRM5BLZq', 'admin', 1, '2026-08-11T00:00:00+00:00', '2026-08-11T00:00:00+00:00'),
    ('user001', '一般花子', '$2b$12$7qTddFNjw4mfBuwrTIInUOMn/MkqrFzSPD87UjKsuvScWZRM5BLZq', 'general', 1, '2026-08-11T00:00:00+00:00', '2026-08-11T00:00:00+00:00'),
    ('user002', '一般次郎', '$2b$12$7qTddFNjw4mfBuwrTIInUOMn/MkqrFzSPD87UjKsuvScWZRM5BLZq', 'general', 1, '2026-08-11T00:00:00+00:00', '2026-08-11T00:00:00+00:00');
