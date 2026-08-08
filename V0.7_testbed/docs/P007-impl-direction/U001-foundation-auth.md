あなたはExecutor(実装担当)です。以下は Sprint 1 `foundation-auth` の作業範囲と完了条件を、タスク単位に分けて定義したものです。各タスクを記載順に実施し、実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P007-impl-direction.md` のWBSに従って自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# スプリント U001 — foundation-auth(基盤・認証)

* 位置づけ: 以降の全スプリントが依存する土台。`docs/P005-impl-plan.md` 2.1 を参照。
* 実装対象: `users` / `sessions` / `schema_migrations`、API-01〜API-03、S01ログイン画面、サーバー・クライアント双方の共通基盤。
* 参照する主要仕様: `docs/P002-frontend-spec.md`(以下P002)1.2 / 2.2 / 2.3 / 2.4 / 3.1 / 5.1〜5.4 / 6.2、`docs/P003-backend-spec.md`(以下P003)1.1 / 2 / 3 / 4 / 7、`docs/P006-test-plan.md`(以下P006)4.1。
* このスプリント全体の共通の禁止事項: P002・P003にない画面・API・DB項目・業務ルールを追加しないこと。会議室・予約に関するテーブルやAPIは**このスプリントでは一切作らない**(Sprint 2・3の担当)。

---

# 【タスクID】U001-T1 — 設定・DB接続・マイグレーション基盤

## 【目的】

* SQLiteへの接続方法と、スキーマの差分適用(マイグレーション)を、以降の全タスクが使える形で用意する。冪等性(2回目以降の起動でも失敗しないこと)をこの時点で確立する。

## 【作成・編集対象ファイル】

* `server/src/meeting_room/config.py`(新規)
* `server/src/meeting_room/db.py`(新規)
* `server/migrations/001-init.sql`(新規)
* `server/tests/test_db_migration.py`(新規)

## 【参照すべき仕様箇所】

* P003 2.1(ディレクトリ構成)、2.2(状態の保持)、3.2(`sessions`)、3.3(`schema_migrations`)、3.5(**マイグレーション方式**)、4.5(トランザクションとPRAGMA)
* P002 6.2(`users` のテーブル定義)

## 【実装内容】

* `config.py`: 環境変数から次を読む。`DB_PATH`(既定 `./data/app.db`)、`SESSION_IDLE_SECONDS`(既定 28800)、`SESSION_ABSOLUTE_SECONDS`(既定 86400)、`INITIAL_ADMIN_ID`(既定 `admin001`)、`INITIAL_ADMIN_PASSWORD`(既定 `Passw0rd!23`)。値はモジュール読み込み時に1回だけ解決する。
* `db.py`:
  * `connect()`: `sqlite3.connect(DB_PATH, timeout=5.0, isolation_level=None)` を返す。接続直後に `PRAGMA foreign_keys = ON` を実行する。`row_factory` を `sqlite3.Row` にする。
  * `init_wal()`: 起動時に1回 `PRAGMA journal_mode = WAL` を実行する。
  * `transaction(conn)`: `BEGIN IMMEDIATE` で開始し、正常終了で `COMMIT`、例外で `ROLLBACK` するコンテキストマネージャ。
  * `apply_migrations()`: P003 3.5 の手順1〜4を**そのとおりに**実装する。
    1. `CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)`。
    2. 適用済み `version` の集合を取得する。
    3. `server/migrations/*.sql` をファイル名昇順に並べ、**未適用のものだけ**を対象にする。
    4. ファイルごとに1トランザクションで、ファイル内の全SQLを**文単位で**実行し、最後に `schema_migrations` へ INSERT してコミットする。失敗時はロールバックして例外を送出する。
  * SQL文の分割は `;` を区切りとし、空文は読み飛ばす。`executescript()` は**使わない**(暗黙コミットでトランザクション境界が壊れるため)。
* `001-init.sql`: `users` テーブル(P002 6.2)、`sessions` テーブル(P003 3.2)、`idx_sessions_user_id` を作成する。`CREATE TABLE`(`IF NOT EXISTS` は付けない。差分適用のため不要)、CHECK制約(`role IN ('general','admin')`)、`is_active` の DEFAULT 1 を含める。

## 【実装してはいけないこと】

* 「全件再実行」方式のマイグレーション(P003 3.5 が明確に否定している)。
* `rooms` / `reservations` / `reservation_attendees` の作成(Sprint 2・3の担当)。
* ORM・マイグレーションツールの導入(標準ライブラリの `sqlite3` のみを使う)。

## 【Unit Test内容】

* テスト対象: `db.apply_migrations()`
* 正常系:
  * 空の一時DBに適用 → `users` / `sessions` / `schema_migrations` が存在する。`schema_migrations` に `001-init.sql` の行がある。
  * **同じDBに対して2回目を適用 → 例外が発生せず、`schema_migrations` の行数が増えないこと**(冪等性。P006 3.3 V-O-02 に対応)。
  * 一時ディレクトリに追加のマイグレーションファイル(`999-test.sql`: `ALTER TABLE users ADD COLUMN memo TEXT`)を置いて適用 → その1件だけが適用され、`memo` 列が増えること。さらにもう一度適用しても失敗しないこと。
* 異常系: 不正なSQLを含むマイグレーションファイル → 例外が送出され、`schema_migrations` にその version が記録されていないこと(ロールバック確認)。
* 実行コマンド: `cd server && python3 -m unittest discover -s tests -t .`
* 合格条件: 上記5ケースすべてPASS。

## 【実行コマンド】

* `cd server && python3 -m unittest discover -s tests -t .`

## 【完了条件】

* 上記の単体テストが全件PASSすること。
* `server/migrations/001-init.sql` が `users` と `sessions` の定義を含むこと。

## 【次タスクに進む前の停止条件】

* 単体テストが3回自己修正しても合格しない場合は、処理を停止して人間に報告する。

---

# 【タスクID】U001-T2 — ASGIアプリ骨格・エラー処理・ログ・静的配信

## 【目的】

* 全エンドポイントが共通で使うエラー変換とログ出力を用意し、フロントエンドを配信できるASGIアプリを起動可能にする。

## 【作成・編集対象ファイル】

* `server/src/meeting_room/errors.py`(新規)
* `server/src/meeting_room/main.py`(新規)
* `server/src/meeting_room/logging_middleware.py`(新規)
* `server/tests/test_errors.py`(新規)

## 【参照すべき仕様箇所】

* P002 5.1(共通事項)、5.2(**エラーレスポンス共通形式とエラーコード一覧**)
* P003 4.1(リクエスト処理の流れ)、4.4(エラーハンドリングとログ出力)、7(静的ファイル配信)

## 【実装内容】

* `errors.py`: `ApiError(status: int, code: str, message: str, details: list | None = None, extra: dict | None = None)` 例外クラスと、`to_response(err) -> JSONResponse` を実装する。出力形式はP002 5.2のとおり(`details` は `VALIDATION_ERROR` のときのみ含める。`extra` の内容は `error` オブジェクト直下にマージする(例: `conflicts`))。
* `logging_middleware.py`: 標準 `logging` を使い、1リクエスト1行のJSONを標準出力に出す。項目は P003 4.4 のとおり(`ts` `level` `method` `path` `status` `duration_ms` `user_id` `error_code` `message`)。**`sid`・パスワード・セッションIDは絶対に出力しない。** 5xxのときのみ `stack` を含める。
* `main.py`: Starletteの `Starlette` アプリを生成する。
  * 起動時に `db.init_wal()` → `db.apply_migrations()` を実行する(リクエスト受付前)。失敗したら例外を送出してプロセスを終了させる。
  * 例外ハンドラを登録し、`ApiError` はその内容で、未捕捉例外は 500 `INTERNAL_ERROR` に変換する。**500の本文にスタックトレース・SQL文・ファイルパスを含めない。**
  * 静的配信: `/` および `/api/` 以外の未知パスは `client/index.html`、`/src/*` `/assets/*` は `client/` 配下の実ファイルを返す。MIME型は `.js` → `text/javascript`、`.css` → `text/css`、`.html` → `text/html; charset=utf-8` を明示する。`client/` の外へ出るパス(`..` を含む)は 404 とする。
  * ルーティングの定義箇所を用意する(このタスクでは `/api/*` のルートは空でよい)。

## 【実装してはいけないこと】

* CORS設定(同一オリジン配信のため不要。P003 7章)。
* 認証・認可の実装(U001-T4の担当)。

## 【Unit Test内容】

* テスト対象: `errors.to_response`、ログ出力の項目
* 正常系: `ApiError(400, "VALIDATION_ERROR", ..., details=[...])` → ステータス400、本文が `{"error":{"code":..., "message":..., "details":[...]}}` になる。`ApiError(409, "RESERVATION_CONFLICT", ..., extra={"conflicts":[...]})` → `error.conflicts` が含まれる。
* 異常系: `details` を渡さない場合に `details` キーが出力されないこと。
* ログ: 生成したログ行がJSONとしてパースでき、必須項目が揃っており、`sid` という文字列を含まないこと。
* 実行コマンド: `cd server && python3 -m unittest discover -s tests -t .`
* 合格条件: 上記すべてPASS。

## 【実行コマンド】

* `cd server && python3 -m unittest discover -s tests -t .`
* 起動確認: `cd server && DB_PATH=./data/app.db python3 -m uvicorn meeting_room.main:app --port 8000`(★FIXME★ ASGIサーバーの起動コマンドは、実行環境で利用可能なASGIサーバー実装に合わせて読み替えること。利用できるものが無い場合は、標準ライブラリの `wsgiref` ではASGIを扱えないため、`main.py` に簡易的な起動関数を用意してよい。この点は `docs/P302-deliver.md` で確定する)

## 【完了条件】

* 単体テストが全件PASSすること。
* アプリが起動し、`/` にアクセスして `client/index.html`(この時点では空でもよい)が返ること。
* **アプリを一度停止して再度起動しても、エラーなく起動すること**(P006 3.3 V-O-01)。

## 【次タスクに進む前の停止条件】

* 単体テストが3回自己修正しても合格しない場合は、処理を停止して人間に報告する。

---

# 【タスクID】U001-T3 — パスワードハッシュ・ユーザーRepository・初期管理者シード

## 【目的】

* パスワードを安全に保存・検証する仕組みと、`users` テーブルへのデータアクセスを用意する。管理者が0人の状態を作らないため、初期管理者を冪等に投入する。

## 【作成・編集対象ファイル】

* `server/src/meeting_room/security.py`(新規)
* `server/src/meeting_room/repositories/users_repo.py`(新規。`repositories/__init__.py` も作成)
* `server/src/meeting_room/db.py`(編集: 初期管理者シード関数の呼び出しを追加)
* `server/tests/test_security.py`(新規)
* `server/tests/test_users_repo.py`(新規)

## 【参照すべき仕様箇所】

* P003 1.1(ハッシュ方式の代替理由)、3.6(初期データ)、4.3(**パスワードハッシュの具体的パラメータと格納形式**)
* P002 6.2(`users`)、5.3(レスポンスに `password_hash` を含めない)

## 【実装内容】

* `security.py`:
  * `hash_password(password: str) -> str`: 16バイトのソルトを `secrets.token_bytes(16)` で生成し、`hashlib.scrypt(password.encode('utf-8'), salt=salt, n=2**14, r=8, p=1, dklen=32)` を計算する。戻り値は `scrypt$16384$8$1$<base64(salt)>$<base64(dk)>`。
  * `verify_password(password: str, stored: str) -> bool`: 格納文字列からパラメータとソルトを復元して再計算し、`hmac.compare_digest` で比較する。形式が不正なら `False` を返す(例外を投げない)。
  * `new_session_id() -> str`: `secrets.token_urlsafe(32)`。
  * `now_utc() -> str` / `today_local() -> str`: **時刻取得はこの2関数に集約する**(P006 6章。他のモジュールで `datetime.now()` を直書きしない)。
* `users_repo.py`: `find_by_id` / `list_users(include_inactive)` / `list_active_id_and_name` / `insert` / `update` / `set_active` / `count_active_admins`。**SELECT句に `password_hash` を含めるのは `find_by_id_with_hash` のみ**とし、他は含めない。
* `db.py` に `seed_initial_admin()` を追加し、`apply_migrations()` の直後に呼ぶ。**有効な管理者が1人も存在しない場合にのみ**、`config` の `INITIAL_ADMIN_ID` / `INITIAL_ADMIN_PASSWORD` でユーザーを1件INSERTする(氏名は「初期管理者」)。既に存在する場合は何もしない(冪等)。

## 【実装してはいけないこと】

* bcrypt / argon2 等の外部ライブラリの利用(取得できない)。
* パスワードのログ出力、平文保存。
* `users` 以外のテーブルへのアクセス。

## 【Unit Test内容】

* テスト対象: `security`、`users_repo`、`seed_initial_admin`
* 正常系: 正しいパスワードで `verify_password` が真。同じパスワードを2回ハッシュ化すると異なる文字列になる(ソルト差)。`insert` → `find_by_id` で同じ行が返る。`set_active(False)` 後に `list_users(include_inactive=False)` に現れない。`count_active_admins` が期待値を返す。`list_active_id_and_name` が `user_id` と `name` **だけ**を返す。
* 異常系: 誤ったパスワードで偽。壊れた格納文字列(`"garbage"`)で偽かつ例外を投げない。存在しない `user_id` の `find_by_id` が `None`。
* シード: 空DBに1回呼ぶと管理者が1人。**2回呼んでも1人のまま**(冪等)。既に別の管理者がいる場合は追加しない。
* 実行コマンド: `cd server && python3 -m unittest discover -s tests -t .`
* 合格条件: 上記すべてPASS。

## 【実行コマンド】

* `cd server && python3 -m unittest discover -s tests -t .`

## 【完了条件】

* 単体テストが全件PASS。
* 一時DBに対して `apply_migrations()` → `seed_initial_admin()` を2回連続で実行しても、管理者が1人のままであること。

## 【次タスクに進む前の停止条件】

* 単体テストが3回自己修正しても合格しない場合は、処理を停止して人間に報告する。

---

# 【タスクID】U001-T4 — セッション管理・認証/認可・認証API3本

## 【目的】

* API-01〜API-03(ログイン・ログアウト・自分の情報取得)を完成させ、以降の全APIが使う認証・認可の共通処理を確立する。

## 【作成・編集対象ファイル】

* `server/src/meeting_room/schemas.py`(新規)
* `server/src/meeting_room/repositories/sessions_repo.py`(新規)
* `server/src/meeting_room/auth.py`(新規)
* `server/src/meeting_room/services/auth_service.py`(新規。`services/__init__.py` も作成)
* `server/src/meeting_room/handlers/auth_handlers.py`(新規。`handlers/__init__.py` も作成)
* `server/src/meeting_room/main.py`(編集: `/api/auth/login` `/api/auth/logout` `/api/me` のルート登録)
* `server/tests/test_auth_service.py` / `server/tests/test_auth_handlers.py`(新規)

## 【参照すべき仕様箇所】

* P002 3.1(S01の入力ルールとエラーメッセージ)、5.1・5.2、**5.4(API-01〜03の外部契約とCookie属性)**
* P003 2.2(セッションのスコープと有効期限)、4.2(バリデーション)、4.3(認証・認可)、6.1(API-01〜03の内部処理)

## 【実装内容】

* `schemas.py`: Pydantic v2 の `LoginRequest`(`user_id`: `^[A-Za-z0-9]{4,20}$`、`password`: 8〜64文字)。**エラーメッセージはP002 3.1の日本語文言を使う**(Pydanticの既定英語メッセージを返さない)。`UserResponse`(`user_id` / `name` / `role`)も定義する。
* `sessions_repo.py`: `create` / `find` / `touch`(`last_accessed_at` 更新) / `delete` / `delete_by_user` / `delete_expired`。
* `auth_service.py`:
  * `login(user_id, password)`: 期限切れセッションを削除 → ユーザー検索 → **行が無い場合もダミーのscrypt検証を1回実行**して応答時間差を減らす → 不一致・`is_active=0`・行なしのいずれも `ApiError(401, "AUTH_FAILED", "ユーザーIDまたはパスワードが正しくありません。")` → セッションを作成して `session_id` と `UserResponse` を返す。
  * `logout(session_id)`、`resolve_session(session_id)`(有効性判定: `expires_at > now` かつ `last_accessed_at + SESSION_IDLE_SECONDS > now` かつ所有ユーザーが有効。不成立なら該当行を削除して `None` を返す)。
* `auth.py`: `require_login(request)` → 401 `UNAUTHENTICATED`、`require_admin(request)` → 403 `FORBIDDEN`、`require_owner_or_admin(request, owner_user_id)` → 403。`require_login` は成功時に `request.state.user` を設定し、セッションを `touch` する。
* `auth_handlers.py`: 3本のハンドラ。ログイン成功時に `Set-Cookie: sid=<id>; HttpOnly; SameSite=Lax; Secure; Path=/`。ログアウトは `sid=; Max-Age=0` を返して 204。`GET /api/me` は `request.state.user` をそのまま返し追加のDBアクセスをしない。
* `main.py`: 上記3ルートを登録する。`/api/auth/login` 以外は `require_login` を通す。

## 【実装してはいけないこと】

* JWT・自前の署名トークン(P002 5.4 はセッションCookieと定めている)。
* セッションのメモリ保持(P003 2.2 が明確に否定している)。
* ログイン失敗の理由を区別したメッセージ。

## 【Unit Test内容】

* テスト対象: `schemas.LoginRequest`、`auth_service`、`auth.require_*`、`auth_handlers`
* 正常系: 正しい資格情報でログイン → セッション行が作られ、`Set-Cookie` に `HttpOnly` `SameSite=Lax` `Secure` `Path=/` が含まれる。`GET /api/me` が `user_id`/`name`/`role` を返す。ログアウト後に同じCookieでアクセスすると401。
* 異常系:
  * `user_id` が3文字 / 21文字 / 記号入り → 400 `VALIDATION_ERROR`、`details[0].field == "user_id"`、メッセージが日本語。
  * パスワード7文字 / 65文字 → 400。
  * 存在しないID・誤ったパスワード・`is_active=0` のユーザー → いずれも 401 `AUTH_FAILED` で**同一の `message`**。
  * Cookieなしで `/api/me` → 401 `UNAUTHENTICATED`。
  * `last_accessed_at` を9時間前にしたセッション → 401 かつ該当行が削除される。
  * `expires_at` を過去にしたセッション → 401。
  * 一般ユーザーのセッションで `require_admin` → 403 `FORBIDDEN`。
* 実行コマンド: `cd server && python3 -m unittest discover -s tests -t .`
* 合格条件: 上記すべてPASS。

## 【実行コマンド】

* `cd server && python3 -m unittest discover -s tests -t .`

## 【完了条件】

* 単体テストが全件PASS。
* API-01〜API-03がP002 5.4の契約どおりに応答すること。

## 【次タスクに進む前の停止条件】

* 単体テストが3回自己修正しても合格しない場合は、処理を停止して人間に報告する。

---

# 【タスクID】U001-T5 — フロントエンド共通基盤

## 【目的】

* 画面モジュールが共通で使う、ルーティング・APIクライアント・共通レイアウト・エラー表示・バリデーションを用意する。

## 【作成・編集対象ファイル】

* `client/index.html`(新規)
* `client/src/main.js`(新規: ルーター起動)
* `client/src/lib/router.js` / `api.js` / `validation.js` / `dom.js` / `datetime.js`(新規)
* `client/src/components/header.js`(新規)
* `client/src/styles.css`(新規)
* `client/tests/test_validation.js` / `test_api.js` / `test_datetime.js`(新規)

## 【参照すべき仕様箇所】

* P002 1.2(実装技術)、2.2(ルーティング表)、2.3(認証ガードと権限による表示制御)、2.4(**共通のエラー表示規則**)、3章(各画面のバリデーションルール)
* P003 7(静的配信のMIME型・パス)

## 【実装内容】

* `index.html`: `<script type="module" src="/src/main.js">` を読み込むだけの最小のシェル。`<div id="app">` と `<div id="header">` を持つ。
* `router.js`: `location.hash` を監視し、P002 2.2 のルート表に従って対応する描画関数を呼ぶ。未知のハッシュは `#/calendar` にリダイレクトする。ルート定義は「パス → モジュールの描画関数」の登録テーブルとし、画面追加時にテーブルへ1行足すだけで済む構造にする。
* `api.js`: `get/post/put/del(path, body)` を実装する。`credentials: 'same-origin'`、`Content-Type: application/json`。応答が2xxならJSON(204なら `null`)を返し、それ以外は `{status, code, message, details, extra}` を持つエラーオブジェクトを**throw**する。401を受けたら `#/login` へ遷移し、セッション切れメッセージを表示する(P002 2.4)。
* `validation.js`: P002 3章の各入力ルールを純粋関数として実装する(`validateUserId` / `validatePassword` / `validateTitle` / `validateTimeRange` / `validateAttendeeCount(count, capacity)` / `validateRoomName` / `validateCapacity` / `validateNote` など)。戻り値は `null`(OK)またはエラーメッセージ文字列。**メッセージ文言はP002の表と一字一句一致させる。**
* `dom.js`: 要素生成ヘルパ、フィールド単位のエラー表示 / 画面上部のメッセージ表示(P002 2.4 の対応表を1つの関数 `showApiError(err)` にまとめる)、送信中のボタン非活性化。
* `datetime.js`: 週の開始日(月曜)算出、日付の加減算、`YYYY-MM-DD` / `HH:MM` の整形、30分刻みの時刻リスト生成(08:00〜20:00)。
* `header.js`: 共通ヘッダー。`GET /api/me` の結果を受け取り、管理者のときのみ「会議室管理」「ユーザー管理」リンクを描画する。ログアウトボタンは `POST /api/auth/logout` 後に `#/login` へ。

## 【実装してはいけないこと】

* 外部パッケージのインストール・CDNからの読み込み(オフライン環境で動作しなくなる)。
* 画面固有のロジック(S01〜S07の中身はT6以降および他スプリントの担当)。

## 【Unit Test内容】

* テスト対象: `validation.js`、`api.js`、`datetime.js`
* 正常系: 各バリデーション関数が境界値で正しく判定する(`user_id` 4文字OK/3文字NG/20文字OK/21文字NG、件名100文字OK/101文字NG、備考500文字OK/501文字NG、開始<終了OK/同一NG、参加予定人数が収容人数と等しいときOK/+1でNG)。`datetime` の週開始日が月曜になる(週の各曜日で確認)。時刻リストが `08:00` 開始 `20:00` 終了で25要素。
* 異常系: `api.js` が 400/401/403/404/409/500 それぞれで期待どおりのエラーオブジェクトをthrowすること(`fetch` を差し替えて検証する)。
* 実行コマンド: `cd client && node --test tests`
* 合格条件: 上記すべてPASS。

## 【実行コマンド】

* `cd client && node --test tests`

## 【完了条件】

* 単体テストが全件PASS。
* サーバーを起動してブラウザ相当のリクエストで `/` を取得したとき、`index.html` と `/src/main.js` が正しいMIME型で返ること。

## 【次タスクに進む前の停止条件】

* 単体テストが3回自己修正しても合格しない場合は、処理を停止して人間に報告する。

---

# 【タスクID】U001-T6 — S01 ログイン画面

## 【目的】

* S01ログイン画面を実装し、ログイン成功でS02のルートへ遷移する導線を通す。

## 【作成・編集対象ファイル】

* `client/src/views/s01-login.js`(新規)
* `client/src/views/s02-calendar.js`(新規・**枠のみ**: 見出しと共通ヘッダーのみを描画するプレースホルダ。中身はSprint 4で実装する)
* `client/tests/test_s01_login.js`(新規)

## 【参照すべき仕様箇所】

* P002 3.1(S01の項目・バリデーション・エラー文言)、2.3(認証ガード)、2.4(エラー表示)、4(画面遷移図)

## 【実装内容】

* `s01-login.js`: ユーザーID・パスワードの入力欄、ログインボタン、エラーメッセージ領域を描画する。
  * 送信前にクライアント側バリデーション(`validation.js`)を実行し、違反があればフィールド直下にメッセージを出してAPIを呼ばない。
  * `POST /api/auth/login` が成功したら `#/calendar` へ遷移する。
  * 401 `AUTH_FAILED` のときは「ユーザーIDまたはパスワードが正しくありません。」をエラー領域に表示する。
  * 送信中はログインボタンを非活性にする。
  * S01では共通ヘッダーを描画しない。
* `s02-calendar.js`(枠のみ): `GET /api/me` を呼び、成功したら共通ヘッダーと「予約カレンダー」の見出しだけを描画する。401なら `api.js` の共通処理でS01へ戻る。**グリッド描画はここでは実装しない**(Sprint 4)。

## 【実装してはいけないこと】

* パスワードのローカルストレージ保存、Cookieのスクリプトからの読み取り(`sid` は HttpOnly)。
* S02のグリッド・フィルタ・予約表示(Sprint 4の担当)。

## 【Unit Test内容】

* テスト対象: `s01-login.js` の描画関数と送信ハンドラ
* 正常系: 描画結果にユーザーID入力・パスワード入力(type=password)・ログインボタン・エラー領域が含まれる。正しい入力でAPIクライアントが1回呼ばれ、成功後に遷移関数が `#/calendar` で呼ばれる。
* 異常系: 空入力で送信 → APIが呼ばれず、両フィールドにエラーメッセージが出る。401応答 → エラー領域に所定の文言が表示される。送信中はボタンが非活性。
* 実行コマンド: `cd client && node --test tests`
* 合格条件: 上記すべてPASS。

## 【実行コマンド】

* `cd client && node --test tests`
* `cd server && python3 -m unittest discover -s tests -t .`(退行がないことの確認)

## 【完了条件】

* クライアント・サーバー双方の単体テストが全件PASS。
* Sprint 1 の全タスク(T1〜T6)が完了したら、`docs/P007-impl-direction.md` の `U001` 行のチェックボックスを `[x]` に更新する。

## 【次タスクに進む前の停止条件】

* 単体テストが3回自己修正しても合格しない場合は、処理を停止して人間に報告する。

---

## 重要

* このスプリントの範囲外のファイルは編集しないでください。
* 実装後、実行したテストコマンドと結果を報告してください。
* このスプリントが完了したら、Executor Stepの停止条件(`SKILL.md` 参照。例: 単体テストが3回自己修正しても合格しない)に該当しない限り、次のスプリント(`U002-master-management.md`)に自動的に進んでください。1タスクごとに人間の指示を待つ必要はありません。
