# server/ INDEX

FastAPI + 標準ライブラリ`sqlite3`(ADR-002, ADR-003)によるバックエンド。CR-001対応(P903、`internal_memo`列追加)にて最新の実装内容で更新した。

- `pyproject.toml` — 依存関係定義(fastapi, uvicorn, bcrypt, httpx, pytest)。`[tool.uv] package = false`
- `migrations/` — マイグレーションSQL(差分適用方式、`docs/P003-backend-spec.md` §4)
  - `001_create_core_tables.sql` — users / rooms / sessions テーブル
  - `002_seed_initial_users.sql` — テストユーザー(admin001/user001/user002)シード
  - `003_create_reservations_tables.sql` — reservations / reservation_participants テーブル、複合インデックス
  - `004_add_reservation_internal_memo.sql` — reservations に `internal_memo`(TEXT、NULL可)列を追加(※CR-001により追加。所有者・管理者のみ閲覧可、マスキングは`routers/reservations.py`で実施)
- `app/main.py` — FastAPIアプリのエントリポイント。起動時マイグレーション実行(lifespan)、ルーター登録、共通エラーハンドラ、構造化ログ出力ミドルウェア(P202 F005で、エラー時のログに`error_code`を含めるよう修正済み)
- `app/db/` — データベース接続・マイグレーション基盤
  - `connection.py` — `DATABASE_PATH` 環境変数からのsqlite3接続取得。`check_same_thread=False` を指定(P202 F003対応: 実サーバーの複数ワーカースレッド下で発生していた`sqlite3.ProgrammingError`を修正済み。理由はファイル内コメント参照)
  - `migrate.py` — 差分適用・冪等なマイグレーションランナー
- `app/security/password.py` — bcryptによるパスワードハッシュ(ADR-004)
- `app/validation/` — DBアクセスを持たない純粋なバリデーション関数
  - `auth.py` — ログイン入力チェック
  - `reservation.py` — 時間範囲・重複判定(半開区間)・収容人数判定
- `app/repositories/` — データアクセス層(sqlite3直接使用、現在時刻を内部で取得しない方針を徹底)
  - `users.py` — users CRUD
  - `sessions.py` — sessions CRUD、有効期限判定
  - `rooms.py` — rooms CRUD(`get_room_by_id` はU002-T4で追加、理由はファイル冒頭コメント参照)
  - `reservations.py` — reservations CRUD、重複判定クエリ、期間別一覧。`internal_memo`は常に実値を返す(マスキングはRouter層の責務、※CR-001により追加)
- `app/services/` — 業務ロジック層(バリデーション順序、権限チェック)
  - `auth.py` — ログインフロー
  - `rooms.py` — 会議室CRUDフロー、`include_inactive`の管理者限定処理
  - `reservations.py` — 予約CRUDフロー(バリデーション順序、権限チェック)
  - `users.py` — ユーザーCRUDフロー(社員ID重複変換、自己無効化禁止)
- `app/schemas/` — Pydantic v2 リクエスト/レスポンススキーマ(auth, room, reservation, user)
- `app/api/` — APIハンドラ層
  - `deps.py` — DB接続取得・認証ミドルウェア(`get_current_user`/`require_admin`)
  - `errors.py` — 共通APIエラー(`ApiError`)
  - `routers/auth.py` — `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/me`
  - `routers/rooms.py` — `GET/POST/PUT/DELETE /api/rooms`
  - `routers/reservations.py` — `GET/POST/PUT/DELETE /api/reservations`, `GET /api/reservations/mine`, `GET /api/reservations/{id}`。`_to_response(reservation, viewer)`が`internal_memo`のマスキング(所有者・管理者以外はnull)を行う(※CR-001により追加)
  - `routers/users.py` — `GET/POST/PUT/DELETE /api/users`
- `tests/` — 単体テスト・結合テスト・受け入れ結合テスト(pytest、121件PASS。`docs/P007-impl-direction/U00N-*.md`・`docs/P008-test-direction/T002-*.md`・`docs/P009-acceptance-direction/A003・A005・A008・A009-*.md` 対応分。CR-001対応で`internal_memo`関連テストを追加)
  - `db/`, `security/`, `validation/`, `repositories/`, `schemas/`, `api/`, `integration/`, `acceptance/` の各ディレクトリにテスト対象別に配置
  - `acceptance/server_process_helper.py` — A005・A009向け、実サーバー(uvicorn)をサブプロセスとして起動・停止する共通ヘルパー
- `data/` — SQLiteデータファイル格納先(`.gitignore` 対象、リポジトリには含めない)
