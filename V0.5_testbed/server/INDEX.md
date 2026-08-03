# server/ INDEX

> P104(実装構造修正)で更新。会議室予約システムのバックエンド(全4スプリント U001〜U004実装済み)。CR-002対応(U006、会議室説明文)で追加更新。

## 技術スタックと deviation

* 言語/フレームワーク: Python 3.11 + **Starlette + Pydantic 2**(ADR-002はFastAPIを指定しているが、本サンドボックスはpypi.orgに接続できずfastapi/uv syncが利用不可のため代替。詳細は `docs/P101-impl-context.md`)。
* DB: SQLite(`sqlite3` 標準ライブラリ、`isolation_level=None` の自前トランザクション管理で `BEGIN IMMEDIATE` 排他制御を実現、ADR-006)。
* パスワードハッシュ: `hashlib.scrypt`(bcryptパッケージが利用不可のための代替、ADR-004実装詳細)。
* テスト: `unittest`(標準ライブラリ。pytestが利用不可のための代替)。`server/tests/` に134件、全PASS(CR-002対応で121件→134件)。
* ASGIサーバー: `uvicorn`(インストール済み)。

## ディレクトリ構成

* `app/main.py` — アプリケーション起点(`create_app(db_path=None)`)。全ルーター登録、共通例外ハンドラ登録、起動時 `init_db()`。`AccessLogMiddleware`(P202-F002修正)。`GET /api/health` はリポジトリルートの `VERSION` ファイルを読んで `{"status":"ok","version":"..."}` を返す(P302修正、起動時ログにもversionを出力)。
* `app/db/`
  * `connection.py` — SQLite接続取得(`get_connection`)・マイグレーション適用(`init_db`)。CR-002対応で、`ALTER TABLE ADD COLUMN`系マイグレーションが複数回実行されても冪等に成功するよう`duplicate column name`エラーを捕捉する処理を追加。
  * `migrations/0001_initial.sql` — USERS/ROOMS/RESERVATIONS/RESERVATION_PARTICIPANTS/SESSIONS 全5テーブルのCREATE TABLE文(`docs/P003-backend-spec.md` §6準拠)。
  * `migrations/0002_add_room_description.sql` — CR-002対応。`ROOMS.description`(TEXT、NULL可)を追加。
* `app/core/`
  * `exceptions.py` — 共通例外(`ValidationError`/`InvalidCredentialsError`/`AuthRequiredError`/`ForbiddenError`/`NotFoundError`/`OverlapError`)。`docs/P002-frontend-spec.md` §2のエラーコードに対応。
  * `password.py` — `hash_password`/`verify_password`(scrypt代替実装)。
  * `validators.py` — 社員ID/パスワード/会議室名/収容人数/氏名/権限/時間範囲/件名/備考の各バリデーション純粋関数。`validate_room_description`(CR-002対応で追加、任意・最大200文字)。
  * `datetime_utils.py` — `parse_date`/`parse_time`/`is_future_or_today`/`is_upcoming`。
  * `logging_utils.py` — `log_event(level, event, **fields)`(P202-F001修正で新設)。構造化ログ(JSON Lines)を標準出力に出す(`docs/P003-backend-spec.md` §8)。`app/main.py` の `AccessLogMiddleware` と `app/api/errors.py` から利用。
* `app/schemas/reservation.py` — 予約関連Pydanticモデル(`ReservationCreateRequest`等)。
* `app/repositories/` — SQLite CRUD層。`user_repository.py`/`session_repository.py`/`room_repository.py`/`reservation_repository.py`(重複チェック `has_overlap`、`BEGIN IMMEDIATE` によるINSERT/UPDATE `insert_with_participants`/`update_with_participants`を含む)。
* `app/services/` — 業務ロジック層。`auth_service.py`(ログイン/ログアウト/セッション解決)、`room_service.py`、`user_service.py`(自己無効化禁止含む)、`reservation_service.py`(会議室/参加者存在確認、権限チェック`check_editable`を含む)。
* `app/api/` — Starletteルーター(FastAPI Handler層の代替)。
  * `deps.py` — `get_conn`/`require_auth`/`require_admin`(FastAPIの `Depends` 相当をプレーン関数で代替)。
  * `errors.py` — 共通エラーレスポンス変換(`AppError` → JSON `{"error": {...}}`)。P202-F002修正でエラー発生時の構造化ログ出力(`log_event`)を追加。
  * `auth.py` — `POST /api/auth/login`、`POST /api/auth/logout`、`GET /api/me`。P202-F001修正でセッションCookieの`Secure`属性を環境変数`SESSION_COOKIE_SECURE`で切り替え可能にした。
  * `rooms.py` — `GET/POST /api/rooms`、`PUT/DELETE /api/rooms/{room_id}`。CR-002対応でレスポンス・リクエストに`description`を追加。
  * `users.py` — `GET/POST /api/users`、`PUT/DELETE /api/users/{user_id}`。
  * `reservations.py` — `GET/POST /api/reservations`、`GET /api/reservations/mine`、`GET/PUT/DELETE /api/reservations/{reservation_id}`。全17エンドポイント実装済み。
* `tests/` — `unittest`ベースの単体・API結合テスト。`helpers.py`(共通テストDBセットアップ・シード関数)。ファイル名は対象モジュールに対応(`test_db_init.py`/`test_password.py`/`test_validators.py`/`test_auth_service.py`/`test_room_repository.py`/`test_user_repository.py`/`test_room_service.py`/`test_user_service.py`/`test_api_auth.py`/`test_api_rooms.py`/`test_api_users.py`/`test_datetime_utils.py`/`test_reservation_repository.py`/`test_reservation_service.py`/`test_api_reservations.py`)。
* `data/` — SQLiteファイル格納先(既定 `server/data/app.db`、`DATABASE_PATH`環境変数で変更可)。
* `pyproject.toml` — 依存関係の記述(参考。本サンドボックスでは `uv sync` を実行できないため、実行はシステムにインストール済みのstarlette/uvicorn/pydanticを直接利用している)。

## 実行方法

* 単体テスト全件: `cd server && python3 -m unittest discover -s tests -v`(134件PASS)。
* 開発サーバー起動(本番相当、TLS終端の前段プロキシがある前提): `cd server && DATABASE_PATH=server/data/app.db python3 -m uvicorn app.main:app --reload`。
* 開発サーバー起動(TLSなしのローカル動作確認・受け入れテスト用、★P202-F001修正★): `cd server && DATABASE_PATH=server/data/app.db SESSION_COOKIE_SECURE=false python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000`。`SESSION_COOKIE_SECURE=false` を指定しない場合、セッションCookieに `Secure` 属性が付くため、プレーンHTTPでは実ブラウザ・実HTTPクライアントがログイン後のCookieを送信できず認証が維持できない(詳細: `docs/ADR.md` ADR-004備考、`docs/test-records/20260803-1900-test-record.md` 根本原因1)。

## 参照

* `docs/ArchitectureHandbook.md` §4(ディレクトリ構成の方針)
* `docs/P101-impl-context.md`(サンドボックス制約とdeviationの詳細)
* `docs/P003-backend-spec.md` §1(レイヤー構成)、§8(ロギング)
* `docs/test-records/20260803-1830-test-record.md`(結合テスト実行記録)
* `docs/test-records/20260803-1900-test-record.md`(P201受け入れ結合テスト実行記録・第1回)
* `docs/ADR.md` ADR-004備考(セッションCookieの`Secure`属性とTLS前提について)
* `docs/test-records/20260803-2010-cr002-test-record.md`・`docs/test-records/20260803-2050-cr002-retest-record.md`(CR-002、T021〜T023の実行記録)
* `docs/P202-fix-plan/fixed/F004-room-update-drops-description.md`(CR-002処理中に検出した`room_service.update()`のdescription渡し忘れの修正記録)
