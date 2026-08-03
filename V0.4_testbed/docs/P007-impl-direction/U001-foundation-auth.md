あなたはExecutor(実装担当)です。このスプリント(U001: foundation-auth)には6個のタスク(U001-1〜U001-6)があります。**1回に1タスクだけ**実施し、完了条件を満たしたら報告し、次タスクの指示を待ってください。自己判断で次タスクに進まないでください。

参照する仕様書: `docs/P002-frontend-spec.md`、`docs/P003-backend-spec.md`、`docs/P005-impl-plan.md` §3.1、`docs/P006-test-plan.md`。

---

# 【タスクID】U001-1

## 【目的】

* `client/`(React 18 + TypeScript + Vite)と `server/`(Python + FastAPI)の2つのアプリケーションディレクトリを初期化し、SQLiteの全テーブル(USERS/ROOMS/RESERVATIONS/RESERVATION_PARTICIPANTS/SESSIONS)のスキーマ・マイグレーションを作成する。

## 【作成・編集対象ファイル】

* `client/`(`npm create vite@latest client -- --template react-ts` 相当で新規作成)
* `server/`(`uv init server` 相当で新規作成。`server/pyproject.toml`、`server/app/__init__.py`)
* `server/app/db/migrations/0001_initial.sql`(全テーブルのCREATE TABLE文)
* `server/app/db/connection.py`(SQLite接続・マイグレーション実行ヘルパー)

## 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §6(データモデル、ER図・テーブル定義書)

## 【実装内容】

* `server/app/db/migrations/0001_initial.sql` に、`docs/P003-backend-spec.md` §6.1〜§6.3のとおり USERS(password_hash/created_at/updated_at含む)、ROOMS、RESERVATIONS、RESERVATION_PARTICIPANTS、SESSIONS の5テーブルをCREATE TABLE文で定義する。
* `RESERVATIONS.room_id` → `ROOMS.id`、`RESERVATIONS.created_by` → `USERS.id`、`RESERVATION_PARTICIPANTS.reservation_id`/`user_id` → 各PK への外部キー制約を定義する。`RESERVATION_PARTICIPANTS` は `ON DELETE CASCADE` を設定する(`docs/P003-backend-spec.md` §9参照)。
* `RESERVATIONS(room_id, date)` に複合インデックスを作成する(`docs/P003-backend-spec.md` §8性能対応)。
* `server/app/db/connection.py` に、SQLiteファイルパスを環境変数(`DATABASE_PATH`、既定値 `server/data/app.db`)から読み込み、起動時に未適用のマイグレーションを適用する関数 `init_db()` を実装する。
* `server/app/main.py` にFastAPIアプリの起点を作成し、起動時に `init_db()` を呼び出す(ルーティングは空でよい。後続タスクで追加)。

## 【実装してはいけないこと】

* USERS/ROOMS/RESERVATIONS以外のテーブル追加、および `docs/P003-backend-spec.md` にないカラムの追加。
* 認証・API・フロントエンドの実装(本タスクの範囲外、U001-3以降で行う)。

## 【Unit Test内容】

* テスト対象: `init_db()`(マイグレーション適用処理)
* 正常系テスト: 空のSQLiteファイルに対し `init_db()` を実行し、5テーブルすべてが作成されることを `sqlite_master` を参照して確認する。
* 主要な異常系テスト: 既にマイグレーション適用済みのDBに対して再度 `init_db()` を実行してもエラーにならない(冪等)ことを確認する。
* 実行するテストコマンド: `cd server && uv run pytest tests/test_db_init.py -v`
* 合格条件: 上記2ケースがいずれもPASSすること。

## 【実行コマンド】

* `cd client && npm install && npm run build`(ビルドが通ることを確認)
* `cd server && uv sync && uv run pytest tests/test_db_init.py -v`

## 【完了条件】

* `client/` `server/` のビルドが両方成功する。
* `tests/test_db_init.py` の全テストがPASSする。

## 【次タスクに進む前の停止条件】

* `client/` または `server/` のビルドが3回試行しても成功しない場合は、この時点で停止し内容を記録する(SKILL.md Executorの停止条件: P102で3回自己修正しても単体テストを合格にできない場合)。

---

# 【タスクID】U001-2

## 【目的】

* パスワードハッシュ化・検証、および社員ID/パスワード形式のバリデーションを行う純粋関数を実装する。

## 【作成・編集対象ファイル】

* `server/app/core/password.py`(`hash_password(plain: str) -> str`、`verify_password(plain: str, hashed: str) -> bool`)
* `server/app/core/validators.py`(`validate_employee_id(value: str) -> bool`、`validate_password_policy(value: str) -> bool`)

## 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §3(パスワードのハッシュ方式、bcrypt cost factor 12)
* `docs/P002-frontend-spec.md` §3 S01(社員ID: 半角英数字1〜20文字)、§3 S07(初期パスワード: 8文字以上、英字・数字を各1文字以上含む)

## 【実装内容】

* `hash_password` は `bcrypt`(cost factor 12)でハッシュ化する。`verify_password` は平文とハッシュを比較しbool を返す。
* `validate_employee_id` は正規表現 `^[A-Za-z0-9]{1,20}$` に一致するかを判定する。
* `validate_password_policy` は8文字以上、かつ英字・数字をそれぞれ1文字以上含むかを判定する。

## 【実装してはいけないこと】

* パスワードを平文でログ出力・保存する処理。
* DB・APIへのアクセス(本タスクは純粋関数のみ)。

## 【Unit Test内容】

* テスト対象: `hash_password`/`verify_password`/`validate_employee_id`/`validate_password_policy`
* 正常系テスト: 正しいパスワードでハッシュ化後に `verify_password` がTrueを返す。仕様を満たす社員ID・パスワードでバリデーション関数がTrueを返す。
* 主要な異常系テスト: 誤ったパスワードで `verify_password` がFalseを返す。21文字の社員ID、記号を含む社員ID、7文字以下のパスワード、数字のみ/英字のみのパスワードでバリデーション関数がFalseを返す。
* 実行するテストコマンド: `cd server && uv run pytest tests/test_password.py tests/test_validators.py -v`
* 合格条件: 全テストPASS。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_password.py tests/test_validators.py -v`

## 【完了条件】

* 上記テストが全てPASSする。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

---

# 【タスクID】U001-3

## 【目的】

* ユーザー・セッションのRepository層、およびログイン/ログアウト/セッション検証を行うAuthServiceを実装する。

## 【作成・編集対象ファイル】

* `server/app/repositories/user_repository.py`(`find_by_employee_id`、`find_by_id`)
* `server/app/repositories/session_repository.py`(`create`、`find_valid`、`delete`)
* `server/app/services/auth_service.py`(`login`、`logout`、`resolve_current_user`)

## 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §2(認証・セッション内部設計、ログイン処理順序、Cookie有効期限8時間、遅延失効方式)

## 【実装内容】

* `session_repository.create(user_id)` は `secrets.token_urlsafe(32)` でセッションIDを生成し、`expires_at` を現在時刻+8時間としてINSERTし、セッションIDを返す。
* `session_repository.find_valid(session_id)` は `expires_at` が現在時刻より後のレコードのみ返す(期限切れはNone扱い)。
* `auth_service.login(employee_id, password)` は `docs/P003-backend-spec.md` §2の手順(1〜4)のとおり実装し、成功時 `(user, session_id)` を、失敗時は専用の例外 `InvalidCredentialsError` を送出する。
* `auth_service.resolve_current_user(session_id)` は `session_repository.find_valid` → `user_repository.find_by_id` の順に解決し、`users.is_active=false` の場合は該当セッションを削除したうえで `None` を返す(遅延失効)。
* `auth_service.logout(session_id)` は該当セッションを削除する(存在しなくても例外にしない)。

## 【実装してはいけないこと】

* HTTPリクエスト/レスポンス・Cookieの読み書き(本タスクはService/Repository層のみ。Handler層はU001-4で実装)。
* `docs/P003-backend-spec.md` にない追加の認証方式(例: JWT発行)。

## 【Unit Test内容】

* テスト対象: `auth_service.login`/`logout`/`resolve_current_user`
* 正常系テスト: 有効なID/パスワードでログイン成功しセッションが作成される。作成したセッションで `resolve_current_user` がユーザーを返す。
* 主要な異常系テスト: 誤ったパスワードで `InvalidCredentialsError`。存在しない社員IDで `InvalidCredentialsError`。無効化済みユーザーで `InvalidCredentialsError`。期限切れセッションで `resolve_current_user` がNoneを返す。無効化されたユーザーのセッションで `resolve_current_user` がNoneを返しセッションが削除される。
* 実行するテストコマンド: `cd server && uv run pytest tests/test_auth_service.py -v`
* 合格条件: 全テストPASS。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_auth_service.py -v`

## 【完了条件】

* 上記テストが全てPASSする。テストDBは都度初期化しU001-1のマイグレーションを利用する。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

---

# 【タスクID】U001-4

## 【目的】

* 認証API(`POST /api/auth/login`、`POST /api/auth/logout`、`GET /api/me`)のHandler層、および認証・認可ミドルウェア(`require_auth`、`require_admin`)を実装する。

## 【作成・編集対象ファイル】

* `server/app/api/auth.py`(3エンドポイント)
* `server/app/api/deps.py`(`require_auth`、`require_admin` のFastAPI依存関数)
* `server/app/api/errors.py`(共通エラーレスポンス形式の例外ハンドラ)
* `server/app/main.py`(ルーター登録、例外ハンドラ登録)

## 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §1(認証方式)、§2(共通エラーレスポンス形式)、§4.1〜§4.3

## 【実装内容】

* `require_auth` はCookieの `session_id` を読み、`auth_service.resolve_current_user` を呼ぶ。解決できなければ `401 AUTH_REQUIRED`(`docs/P002-frontend-spec.md` §2の形式)を送出する。解決できれば `request.state.user` 相当としてユーザーを返す(依存関数の戻り値として後続ハンドラに渡す)。
* `require_admin` は `require_auth` の結果に対し `role == "admin"` を確認し、そうでなければ `403 FORBIDDEN` を送出する。
* `POST /api/auth/login` はリクエストボディをパースし(欠落時 `400 VALIDATION_ERROR`)、`auth_service.login` を呼び、成功時Cookie(`HttpOnly; Secure; SameSite=Lax; Max-Age=28800`)を設定し `{"user": {...}}` を返す。失敗時 `401 AUTH_INVALID_CREDENTIALS`。
* `POST /api/auth/logout` は `require_auth` を課さず(未ログインでも200を返す冪等設計、`docs/P003-backend-spec.md` §7.2)、Cookieがあれば `auth_service.logout` を呼び、Cookieを失効させて `{"message": "logged out"}` を返す。
* `GET /api/me` は `require_auth` を課し、解決済みユーザーをそのまま返す。
* `server/app/api/errors.py` に共通エラー形式(`{"error": {"code", "message", "details"}}`)の例外クラスと、FastAPIの例外ハンドラを実装する。

## 【実装してはいけないこと】

* `docs/P002-frontend-spec.md` にないレスポンスフィールドの追加。
* パスワードやセッションIDをレスポンスボディに含めること。

## 【Unit Test内容】

* テスト対象: `POST /api/auth/login`、`POST /api/auth/logout`、`GET /api/me`(FastAPIの `TestClient` を用いたAPIハンドラ単位のテスト)
* 正常系テスト: 正しいID/パスワードでログインし200・Set-Cookieが返る。ログイン後のCookieで `GET /api/me` が200・正しいuserを返す。ログアウトで200が返る。
* 主要な異常系テスト: 誤ったパスワードで401。必須項目欠落で400。Cookie無しで `GET /api/me` が401。未ログインで `POST /api/auth/logout` を呼んでも200。
* 実行するテストコマンド: `cd server && uv run pytest tests/test_api_auth.py -v`
* 合格条件: 全テストPASS。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_api_auth.py -v`
* `cd server && uv run uvicorn app.main:app --reload`(手動確認用、必須ではない)

## 【完了条件】

* 上記テストが全てPASSする。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

---

# 【タスクID】U001-5

## 【目的】

* S01ログイン画面のフロントエンドコンポーネントを実装し、`POST /api/auth/login` と接続する。

## 【作成・編集対象ファイル】

* `client/src/pages/LoginPage.tsx`
* `client/src/api/authApi.ts`(`login(employeeId, password)`、`logout()`、`getMe()` のfetchラッパー、`credentials: "include"` を指定してCookieを送受信する)
* `client/src/App.tsx`(ルーティングの起点。ログイン画面のみでよい。他画面はU002以降で追加)

## 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S01、§4.1、§6.1(ログインのシーケンス図)

## 【実装内容】

* `LoginPage.tsx` は社員ID・パスワードの入力欄(パスワードは `type=password`)、送信ボタン、エラーメッセージ表示領域を持つ。
* 送信時に `authApi.login` を呼び、成功時は(暫定的に)コンソールログでユーザー情報を出力する(S02が未実装のため画面遷移は行わない。実際の画面遷移接続はU003-6で行う)。
* 失敗時(401)は「社員IDまたはパスワードが正しくありません」を表示する。

## 【実装してはいけないこと】

* S02以降の画面の実装(このタスクの範囲外)。
* レスポンスボディからのトークン取り出し(Cookie方式のため不要)。

## 【Unit Test内容】

* テスト対象: `LoginPage` コンポーネントの表示・イベント処理(`authApi` はモック化する)
* 正常系テスト: 入力後に送信すると `authApi.login` が正しい引数で呼ばれる。
* 主要な異常系テスト: `authApi.login` が401相当のエラーを返すモックのとき、画面にエラーメッセージが表示される。未入力で送信した場合はフロントエンド側で送信をブロックする(必須バリデーション)。
* 実行するテストコマンド: `cd client && npm run test -- LoginPage`
* 合格条件: 全テストPASS。

## 【実行コマンド】

* `cd client && npm run test -- LoginPage`
* `cd client && npm run build`

## 【完了条件】

* 上記テストがPASSし、ビルドが成功する。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

---

# 【タスクID】U001-6(結合確認用の薄いタスク)

## 【目的】

* U001-1〜U001-5で実装したクライアント・サーバを実際に起動し、ログイン→`GET /api/me` が仕様通りに動作することを手動レベルで確認する(スプリント内の最終疎通確認。詳細な結合テストは `docs/P008-test-direction.md` 側で別途実施するため、本タスクでは起動確認のみに留める)。

## 【作成・編集対象ファイル】

* なし(コード変更は行わない。確認結果を `docs/test-records/` には残さず、本タスクの完了報告として記載するのみでよい。正式な結合テスト記録はP103で作成する)

## 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §6.1

## 【実装内容】

* `server` を起動し、`curl` 等で `POST /api/auth/login` → `Set-Cookie` を受け取り → 同一Cookieで `GET /api/me` を呼び、登録済みテストユーザーの情報が返ることを確認する。
* `client` を `npm run dev` で起動し、ブラウザ(またはヘッドレス環境)でログインフォームが表示されることを確認する(APIとの実接続確認まででよい。画面遷移は未実装)。

## 【実装してはいけないこと】

* 新規のプロダクションコードの追加(確認のみ)。

## 【Unit Test内容】

* テスト対象: なし(本タスクは手動疎通確認であり自動テストは対象外。U001-1〜U001-5で自動テストは実施済み)
* 実行するテストコマンド: なし
* 合格条件: 上記の疎通確認が成功すること。

## 【実行コマンド】

* `cd server && uv run uvicorn app.main:app --reload`
* `cd client && npm run dev`

## 【完了条件】

* ログイン→`GET /api/me` の疎通が確認できる。

## 【次タスクに進む前の停止条件】

* 疎通確認が3回試行しても成功しない場合は停止し内容を記録する。

## 重要

* 各タスクの範囲外のファイルは編集しないでください。
* 各タスク完了後、実行したテストコマンドと結果を報告してください。
* 次のタスクには自己判断で進まないでください(本ファイル内の次タスクへは、都度の指示を待って進めてください)。
