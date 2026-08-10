# server/ INDEX

Python + FastAPI + 標準ライブラリ`sqlite3`(`docs/ADR.md` ADR-002)。仮想環境は `.venv/`(既存)。

- `pyproject.toml` — 依存関係定義(fastapi, uvicorn, pydantic / dev: pytest, httpx)
- `app/main.py` — FastAPIアプリのエントリポイント。起動時マイグレーション適用(lifespan)、全ルーター登録、共通エラーハンドラ登録、`GET /health`
- `app/db/` — DB接続・マイグレーション
  - `connection.py` — SQLite接続の取得(`DATABASE_PATH`環境変数)。`check_same_thread=False`を指定(P202 F001。並行リクエスト時に`sqlite3.ProgrammingError`が発生していた不具合を修正済み。`docs/P202-fix-plan/fixed/F001-sqlite-thread-safety.md`参照)
  - `migration.py` — 起動時マイグレーション適用ロジック(`migrations/*.sql`を`schema_migrations`テーブルで管理、冪等)
- `app/dependencies.py` — 共通FastAPI依存性: `get_db`(DB接続)、`get_current_user`(Cookie認証)、`require_admin`(管理者権限チェック)
- `app/exceptions.py` — ドメイン例外クラス群(ValidationError/NotFoundError/ForbiddenError/ReservationConflictError/SelfDeactivationForbiddenError/LastAdminProtectedError)。`code`/`message`/`fields`を自己記述
- `app/errors.py` — 例外→HTTPレスポンスの共通変換(`docs/P002-frontend-spec.md`4章冒頭のエラー形式に統一)。未処理例外(500)時は`app/logging_utils.py`で構造化ログを出力
- `app/logging_utils.py` — 構造化JSON Linesログ出力ヘルパー(`docs/P003-backend-spec.md`6章)
- `app/security/password.py` — パスワードハッシュ化・検証(scrypt)
- `app/repositories/` — データアクセス層(SQL文を閉じ込める)
  - `user_repository.py` — ユーザーCRUD、ディレクトリ検索、管理者数カウント
  - `session_repository.py` — セッションCRUD
  - `room_repository.py` — 会議室CRUD(論理削除)
  - `reservation_repository.py` — 予約CRUD、重複判定、排他制御(`begin_immediate_transaction`)、マイ予約検索
- `app/services/` — 業務ロジック層(Repository層のみに依存)
  - `auth_service.py` — ログイン/ログアウト/認証状態確認
  - `room_service.py` — 会議室のバリデーション・CRUD
  - `reservation_service.py` — 予約のバリデーション・重複チェック・CRUD・マイ予約一覧
  - `user_service.py` — ユーザーのバリデーション・CRUD・自己無効化禁止・最後の管理者保護
- `app/schemas/` — Pydanticリクエスト/レスポンスモデル
  - `auth.py`, `room.py`, `reservation.py`, `user.py`
- `app/routers/` — APIハンドラ層(Router→Service→Repositoryの一方向依存)
  - `auth.py` — `/api/auth/login`, `/api/auth/logout`, `/api/me`
  - `rooms.py` — `/api/rooms` CRUD(管理者専用の書き込み)
  - `reservations.py` — `/api/reservations` CRUD、`/api/reservations/mine`
  - `users.py` — `/api/users/directory`(ログイン済みなら誰でも)、`/api/users` CRUD(管理者専用)
- `migrations/` — DDL・シードデータ(`schema_migrations`テーブルで適用管理)
  - `001_initial_schema.sql` — 全6テーブル定義
  - `002_seed_admin.sql` — 初期管理者アカウント(`admin` / `ChangeMe123!`、要本番変更)
  - `003_add_reservation_meeting_url.sql` — CR-001対応。`reservations.meeting_url`(NULL許容TEXT)カラム追加(`docs/P903-cr-records/CR-001.md`参照)
- `tests/` — Unit Test + P103結合テスト(pytest、`python -m pytest tests/ -v`で計153件。CR-001対応でmeeting_url関連25件追加、`test_migration.py`の既存2件を新マイグレーション件数に合わせて更新)
  - `integration/` — P103結合テスト4件(`test_*.py`、実DB=一時SQLiteファイル)。他はUnit Test(149件)
- `data/` — SQLiteデータファイル格納先(`DATABASE_PATH`既定値、実行時生成、Git管理対象外)
