あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U001 — foundation-and-auth

## タスク一覧(OKF副目次)

* 状態は `[ ]`(未着手) / `[~]`(進行中) / `[x]`(完了) の3種類とする。1タスクの作業を開始したら `[~]` に、完了条件をすべて満たしたら `[x]` に更新する。
* このスプリントファイル自体の状態(`docs/P007-impl-direction.md` の該当行)は、全タスクが `[x]` になって初めて `[x]` にする。1件以上のタスクが `[~]`/`[x]` で残りが `[ ]` の場合は `[~]` とする。
* **中断からの再開**: セッションが中断した場合、再開担当はまずこの一覧を確認する。`[~]` のタスクがあれば、それが中断時点の作業対象である。ただし `[~]` の状態だけで「どこまで終わっているか」は分からないため、再開時は必ず該当タスクの【完了条件】(単体テスト実行など)を実際に再実行して現状を確認してから、続きを行うか最初からやり直すかを判断する。`[ ]` のまま存在するファイル(先行して部分的に作成された形跡があるもの)は、対応するタスクが `[~]`/`[x]` でない限り「未着手」として扱い、内容を鵜呑みにしない。
* **先行実装の禁止**: 現在 `[~]` のタスクを進める際、まだ `[ ]` の後続タスク(同一スプリント内・他スプリントとも)が対象とするファイルには着手しない。

- [x] U001-T1 [DBスキーマ・マイグレーション基盤](#u001-t1-dbスキーママイグレーション基盤) — schema_migrations方式のマイグレーションランナーと初期テーブル群
- [x] U001-T2 [パスワードハッシュ・入力バリデーション純粋関数](#u001-t2-パスワードハッシュ入力バリデーション純粋関数) — bcryptラッパーと社員ID/パスワード形式チェック
- [x] U001-T3 [Repository層(users/sessions/rooms読み取り)](#u001-t3-repository層userssessionsrooms読み取り) — sqlite3ベースのデータアクセス関数
- [x] U001-T4 [認証Service層・APIハンドラ + 会議室読み取りAPI](#u001-t4-認証service層apiハンドラ--会議室読み取りapi) — login/logout/me/rooms一覧
- [x] U001-T5 [フロントエンド基盤 + S01ログイン画面](#u001-t5-フロントエンド基盤--s01ログイン画面) — Vite初期化、ルーティング、ログイン画面
- [x] U001-T6 [結合確認用の薄いタスク: ログイン〜ルーム一覧の通し確認](#u001-t6-結合確認用の薄いタスク-ログインルーム一覧の通し確認) — TestClientでの一連の呼び出し確認

---

## U001-T1: DBスキーマ・マイグレーション基盤

### 【目的】

* `docs/P003-backend-spec.md` §4のマイグレーション方式(差分適用・冪等)を実装し、`users`/`rooms`/`sessions`/`schema_migrations` テーブルを作成する。

### 【作成・編集対象ファイル】

* `server/pyproject.toml`(新規、`uv init` で初期化)
* `server/migrations/001_create_core_tables.sql`(新規)
* `server/migrations/002_seed_initial_users.sql`(新規)
* `server/app/db/migrate.py`(新規、マイグレーションランナー)
* `server/app/db/connection.py`(新規、`DATABASE_PATH` 環境変数からのsqlite3接続取得)
* `server/tests/db/test_migrate.py`(新規)

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §3.2(テーブル定義)、§4(マイグレーション方式)

### 【実装内容】

* `uv init server` 相当の構成で `server/` を初期化する(`pyproject.toml`、`app/` パッケージ、`tests/`)。
* `server/app/db/migrate.py` に `run_migrations(conn: sqlite3.Connection, migrations_dir: str) -> list[int]`(適用したバージョン番号のリストを返す)を実装する。
  * 起動時、まず `CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)` を実行する。
  * `migrations_dir` 配下の `NNN_*.sql` をファイル名の数値プレフィックス順にソートし、`schema_migrations` に存在しないバージョンのみを1トランザクションずつ実行し、成功したら `schema_migrations` に記録する。
* `001_create_core_tables.sql` に `users`/`rooms`/`sessions`/`schema_migrations`(既に作成済みなら`IF NOT EXISTS`で無害)を、`docs/P003-backend-spec.md` §3.2のカラム定義どおりに作成するDDLを書く。
* `002_seed_initial_users.sql` に、`docs/P006-test-plan.md` §5 で定めたテストユーザー(`admin001`=管理者、`user001`/`user002`=一般ユーザー、パスワードはすべて `TestPassw0rd!` のbcryptハッシュ)を `INSERT` する。bcryptハッシュ値は、U001-T2で作成するハッシュ関数を使い、このタスク内で一度だけ算出してSQLに埋め込んでよい(マイグレーションSQL自体は静的な値を持つ)。

### 【実装してはいけないこと】

* `reservations`/`reservation_participants` テーブルの作成(U002の対象)。
* 全件再実行方式(`docs/P003-backend-spec.md` §4で明示的に不採用とした方式)。

### 【Unit Test内容】

* テスト対象: `run_migrations`
* 正常系: 空の一時DBに対して初回実行し、4テーブル(`users`/`rooms`/`sessions`/`schema_migrations`)が作成され、`schema_migrations` に2行(version=1,2)記録されることを確認する。
* 正常系: 同じ一時DBに対してもう一度 `run_migrations` を実行し、例外が発生せず、かつ `schema_migrations` の行数が変わらないこと(冪等性の直接確認)を確認する。
* 異常系: 存在しないディレクトリを渡した場合に分かりやすい例外を送出すること。
* 実行コマンド: `cd server && uv run python -m pytest tests/db/test_migrate.py -v`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/db/test_migrate.py -v`

### 【完了条件】

* 上記Unit Testがすべて成功する。
* `server/data/`(DB格納用ディレクトリ)は `.gitignore` 対象とする。

### 【次タスクに進む前の停止条件】

* Unit Testが3回の自己修正を経ても成功しない場合、`SKILL.md` のExecutor Step停止条件に従い処理を停止し人間に報告する。

---

## U001-T2: パスワードハッシュ・入力バリデーション純粋関数

### 【目的】

* `docs/P003-backend-spec.md` §2.2のbcryptハッシュ化と、`docs/P002-frontend-spec.md` §3のS01入力バリデーションを、Repository/APIから独立した純粋関数として実装する。

### 【作成・編集対象ファイル】

* `server/app/security/password.py`(新規)
* `server/app/validation/auth.py`(新規)
* `server/tests/security/test_password.py`(新規)
* `server/tests/validation/test_auth.py`(新規)

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §2.2
* `docs/P002-frontend-spec.md` §3 S01

### 【実装内容】

* `password.py`: `hash_password(raw: str) -> str`(`bcrypt.hashpw`)、`verify_password(raw: str, hashed: str) -> bool`(`bcrypt.checkpw`)。
* `auth.py`: `validate_login_input(employee_id: str, password: str) -> list[str]`(エラーメッセージのリストを返す。空リストなら妥当)。空文字/未指定の場合それぞれ「社員IDを入力してください」「パスワードを入力してください」を返す(`docs/P002-frontend-spec.md` §3 S01のとおり)。

### 【実装してはいけないこと】

* DBアクセス(このタスクは純粋関数のみ)。
* パスワードの平文ログ出力。

### 【Unit Test内容】

* テスト対象: `hash_password`/`verify_password`/`validate_login_input`
* 正常系: `verify_password(raw, hash_password(raw))` が真になること。異なる平文では偽になること。
* 正常系: 2回 `hash_password` を呼ぶと異なるハッシュ文字列になること(ソルトがランダムであることの確認)。
* 異常系: `validate_login_input("", "")` が2件のエラーメッセージを返すこと。`validate_login_input("u001", "pw")` が空リストを返すこと。
* 実行コマンド: `cd server && uv run python -m pytest tests/security/test_password.py tests/validation/test_auth.py -v`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/security/test_password.py tests/validation/test_auth.py -v`

### 【完了条件】

* 上記Unit Testがすべて成功する。

### 【次タスクに進む前の停止条件】

* Unit Testが3回の自己修正を経ても成功しない場合、処理を停止し人間に報告する。

---

## U001-T3: Repository層(users/sessions/rooms読み取り)

### 【目的】

* `docs/P003-backend-spec.md` §5.1〜§5.4の内部処理が必要とするデータアクセス関数を実装する。

### 【作成・編集対象ファイル】

* `server/app/repositories/users.py`(新規)
* `server/app/repositories/sessions.py`(新規)
* `server/app/repositories/rooms.py`(新規、読み取り関数のみ。書き込みはU003で追加)
* `server/tests/repositories/test_users_repo.py`(新規)
* `server/tests/repositories/test_sessions_repo.py`(新規)
* `server/tests/repositories/test_rooms_repo.py`(新規)

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §3.2、§5.1〜§5.4、§6(Repository層の時刻引数ルール)

### 【実装内容】

* `users.py`: `get_user_by_employee_id(conn, employee_id: str) -> User | None`(`is_active=1` のみ対象)、`get_user_by_id(conn, user_id: int) -> User | None`。
* `sessions.py`: `create_session(conn, token: str, user_id: int, created_at: str, expires_at: str) -> None`、`get_session(conn, token: str) -> Session | None`、`delete_session(conn, token: str) -> None`、`is_session_valid(session: Session, now: datetime) -> bool`。**`now` は呼び出し元(Service層)が計算して渡す明示的な引数とし、この関数・モジュール内で `datetime.now()` 等のシステム時計を呼び出してはならない**(`docs/P003-backend-spec.md` §6のRepository層時刻引数ルールに従う)。
* `rooms.py`: `list_active_rooms(conn) -> list[Room]`(`is_active=1` のみ)。

### 【実装してはいけないこと】

* Service層が担うべき業務判定(有効期限切れの理由づけ、認可判定)をRepository層に書かないこと。
* `sessions.py`・`users.py`・`rooms.py` のいずれの関数内でも `datetime.now()` / `date.today()` を直接呼び出さないこと。

### 【Unit Test内容】

* テスト対象: 上記各Repository関数
* 正常系: シードした一時DBに対し、`get_user_by_employee_id("admin001", ...)` が正しいロールで取得できること。
* 正常系: `create_session` → `get_session` で同一トークンのセッションが取得できること。`delete_session` 後は `get_session` が `None` を返すこと。
* 正常系: `is_session_valid` に、`expires_at` より前の `now` を渡すと真、後の `now` を渡すと偽になることを確認する(時刻を固定したテストで検証できることが本タスクの目的)。
* 正常系: `list_active_rooms` が `is_active=0` の会議室を含まないこと。
* 実行コマンド: `cd server && uv run python -m pytest tests/repositories/ -v`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/repositories/ -v`

### 【完了条件】

* 上記Unit Testがすべて成功する。

### 【次タスクに進む前の停止条件】

* Unit Testが3回の自己修正を経ても成功しない場合、処理を停止し人間に報告する。

---

## U001-T4: 認証Service層・APIハンドラ + 会議室読み取りAPI

### 【目的】

* `POST /api/auth/login`、`POST /api/auth/logout`、`GET /api/me`、`GET /api/rooms` を実装し、以降の全APIで使う認証ミドルウェア(FastAPIの依存性注入)を用意する。

### 【作成・編集対象ファイル】

* `server/app/services/auth.py`(新規)
* `server/app/api/deps.py`(新規、認証ミドルウェア `get_current_user`)
* `server/app/api/routers/auth.py`(新規)
* `server/app/api/routers/rooms.py`(新規、GET/api/roomsのみ)
* `server/app/schemas/auth.py`(新規、Pydanticリクエスト/レスポンススキーマ)
* `server/app/schemas/room.py`(新規)
* `server/app/main.py`(新規、FastAPIアプリ、lifespanでU001-T1のマイグレーションを実行、ルーター登録)
* `server/tests/api/test_auth_api.py`(新規)
* `server/tests/api/test_rooms_api.py`(新規)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §1、§2、§3 S01、§9
* `docs/P003-backend-spec.md` §5.1〜§5.4

### 【実装内容】

* `auth.py`(Service層): `login(conn, employee_id, password, now) -> tuple[User, str /*token*/, str /*expires_at*/]`。バリデーション→ユーザー検索→パスワード照合→トークン生成(`secrets.token_hex(32)`)→`create_session`呼び出し、の順で行う。失敗時は`AuthError`例外(理由を区別しない統一メッセージ)を送出する。
* `deps.py`: リクエストCookieから `session_id` を取得し、`get_session`→`is_session_valid(now=現在時刻)`→有効なら `get_user_by_id` を返す。無効/欠落なら401 `UNAUTHENTICATED` を送出するFastAPI依存関数 `get_current_user`。管理者専用ルート向けに `require_admin(user=Depends(get_current_user))`(role≠adminなら403 `FORBIDDEN`)も用意する。
* `routers/auth.py`: `POST /api/auth/login`(成功時`Set-Cookie`付き200、失敗時401 `AUTH_FAILED`)、`POST /api/auth/logout`(`get_current_user`必須、セッション削除後204)、`GET /api/me`(`get_current_user`必須、200)。
* `routers/rooms.py`: `GET /api/rooms`(`get_current_user`必須、`list_active_rooms`を呼びJSON配列で返す)。
* `main.py`: `lifespan` で `connection.py` からコネクションを取得し `run_migrations` を実行してからルーターを登録する。

### 【実装してはいけないこと】

* `POST/PUT/DELETE /api/rooms`(U003の対象)。
* JWTなど、`docs/P003-backend-spec.md` §2.1で不採用と整理したセッション方式の実装。

### 【Unit Test内容】

* テスト対象: `POST /api/auth/login`、`POST /api/auth/logout`、`GET /api/me`、`GET /api/rooms`(FastAPI `TestClient` を使用)
* 正常系: 正しい社員ID/パスワードでログイン→200・Cookie発行→`GET /api/me`で自分の情報が取れる。
* 異常系: 誤ったパスワードで401 `AUTH_FAILED`、メッセージが「社員IDまたはパスワードが正しくありません」であること。
* 異常系: Cookie無しで`GET /api/me`を呼ぶと401 `UNAUTHENTICATED`。
* 正常系: ログイン後 `GET /api/rooms` がシードデータの会議室一覧を返す(本タスク時点では会議室シードデータが無いため空配列で可。U003で会議室作成APIが実装され次第、結合テスト側でデータ有りのケースを追加する旨をコメントに残す)。
* 実行コマンド: `cd server && uv run python -m pytest tests/api/test_auth_api.py tests/api/test_rooms_api.py -v`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/api/test_auth_api.py tests/api/test_rooms_api.py -v`
* `cd server && uv run uvicorn app.main:app --reload`(手動起動確認用、Unit Testの合否には含めない)

### 【完了条件】

* 上記Unit Testがすべて成功する。

### 【次タスクに進む前の停止条件】

* Unit Testが3回の自己修正を経ても成功しない場合、処理を停止し人間に報告する。

---

## U001-T5: フロントエンド基盤 + S01ログイン画面

### 【目的】

* `client/` を初期化し、`docs/P002-frontend-spec.md` §3 S01のログイン画面を実装する。

### 【作成・編集対象ファイル】

* `client/package.json`(新規、`npm create vite@latest client -- --template react-ts` 相当で初期化)
* `client/src/api/client.ts`(新規、`fetch` ラッパー。`credentials: "include"` を既定にする)
* `client/src/pages/LoginPage.tsx`(新規)
* `client/src/router.tsx`(新規、React Router定義。この時点ではS01のみ実ルートとし、他画面は仮のプレースホルダで可)
* `client/src/tests/LoginPage.test.tsx`(新規)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S01、§1

### 【実装内容】

* `client.ts` に `apiFetch(path, options)` を実装し、非2xxレスポンス時は `{error_code, message}` を含む例外を投げる共通処理にする。
* `LoginPage.tsx`: 社員ID/パスワード入力欄(パスワードは`type=password`)、送信ボタン、エラーメッセージ表示領域。クライアント側で未入力チェックを行い、`docs/P002-frontend-spec.md` §3 S01のメッセージをそのまま表示する。送信中はボタンを無効化する。成功時は `POST /api/auth/login` の後にトップ(仮のプレースホルダルート)へ遷移する。

### 【実装してはいけないこと】

* S02以降の画面の実装(後続スプリントの対象)。
* パスワードのブラウザ保存(`autocomplete="current-password"` は可だが独自の永続化はしない)。

### 【Unit Test内容】

* テスト対象: `LoginPage` コンポーネント(Vitest + React Testing Library)
* 正常系: 社員ID・パスワードを入力して送信すると `apiFetch` が正しいエンドポイント・ボディで呼ばれること(モック使用)。
* 異常系: 未入力のまま送信すると「社員IDを入力してください」がAPI呼び出し無しで表示されること。
* 異常系: APIが401を返すモックを設定した場合、「社員IDまたはパスワードが正しくありません」が表示されること。
* 実行コマンド: `cd client && npm run test -- src/tests/LoginPage.test.tsx`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd client && npm install`
* `cd client && npm run test -- src/tests/LoginPage.test.tsx`
* `cd client && npm run build`(ビルドが通ることも完了条件に含める)

### 【完了条件】

* 上記Unit Testがすべて成功し、`npm run build` が成功する。

### 【次タスクに進む前の停止条件】

* Unit Testが3回の自己修正を経ても成功しない場合、処理を停止し人間に報告する。

---

## U001-T6: 結合確認用の薄いタスク: ログイン〜ルーム一覧の通し確認

### 【目的】

* U001-T1〜T4で実装したバックエンドの一連の流れ(マイグレーション適用済みDB起動→ログイン→me取得→ルーム一覧取得)が、モジュール単体テストの粒度を超えて実際に繋がって動作することを、Executor自身が最終確認する。本タスクはスプリント内結合テスト(`docs/P008-test-direction.md`)の代替ではなく、それに先立つ最小限の疎通確認である。

### 【作成・編集対象ファイル】

* `server/tests/api/test_smoke_u001.py`(新規)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §7.1(ログイン〜カレンダー初期表示シーケンス図のうち、本スプリント範囲であるログイン〜ルーム一覧取得の部分)

### 【実装内容】

* 一時DBファイルに対し `run_migrations` を実行し、`TestClient` で `POST /api/auth/login`→`GET /api/me`→`GET /api/rooms` を順に呼び、各レスポンスのステータスコードと主要フィールドを確認する1本のテスト関数を書く。

### 【実装してはいけないこと】

* 新しい業務ロジックの追加(既存実装の呼び出し確認のみ)。

### 【Unit Test内容】

* テスト対象: 上記の一連の呼び出し
* 正常系: 3リクエストすべてが期待どおりのステータスコードを返すこと。
* 実行コマンド: `cd server && uv run python -m pytest tests/api/test_smoke_u001.py -v`
* 合格条件: PASS。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/api/test_smoke_u001.py -v`

### 【完了条件】

* 上記テストがPASSする。

### 【次タスクに進む前の停止条件】

* 該当なし(本スプリントの最終タスク)。全タスク完了後、`docs/P007-impl-direction.md` のU001行を `[x]` に更新する。

## 重要

* 各タスクの範囲外のファイルは編集しないでください。
* タスクの実装後、実行したテストコマンドと結果を報告してください。
* タスクが完了したら、上記「タスク一覧」の該当行を `[x]` に更新してください。
* 全タスクが完了したら、`docs/P007-impl-direction.md` の本スプリント行を `[x]` に更新してください。
* Executor Stepの停止条件(`SKILL.md` 参照。例: 単体テストが3回自己修正しても合格しない)に該当しない限り、次のタスクに自動的に進んでください。1タスクごとに人間の指示を待つ必要はありません。
