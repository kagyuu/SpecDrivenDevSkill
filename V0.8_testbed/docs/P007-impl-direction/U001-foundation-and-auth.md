あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U001 — foundation-and-auth

## タスク一覧(OKF副目次)

* 状態は `[ ]`(未着手) / `[~]`(進行中) / `[x]`(完了) の3種類とする。1タスクの作業を開始したら `[~]` に、完了条件をすべて満たしたら `[x]` に更新する。
* このスプリントファイル自体の状態(`docs/P007-impl-direction.md` の該当行)は、全タスクが `[x]` になって初めて `[x]` にする。1件以上のタスクが `[~]`/`[x]` で残りが `[ ]` の場合は `[~]` とする。
* **中断からの再開**: セッションが中断した場合、再開担当はまずこの一覧を確認する。`[~]` のタスクがあれば、それが中断時点の作業対象である。ただし `[~]` の状態だけで「どこまで終わっているか」は分からないため、再開時は必ず該当タスクの【完了条件】(単体テスト実行など)を実際に再実行して現状を確認してから、続きを行うか最初からやり直すかを判断する。`[ ]` のまま存在するファイル(先行して部分的に作成された形跡があるもの)は、対応するタスクが `[~]`/`[x]` でない限り「未着手」として扱い、内容を鵜呑みにしない。
* **先行実装の禁止**: 現在 `[~]` のタスクを進める際、まだ `[ ]` の後続タスク(同一スプリント内・他スプリントとも)が対象とするファイルには着手しない。

- [x] U001-T1 [プロジェクト基盤構築](#u001-t1-プロジェクト基盤構築) — client/server両ディレクトリの初期化とビルド確認
- [x] U001-T2 [データモデル・マイグレーション実装](#u001-t2-データモデルマイグレーション実装) — 全6テーブルのDDLとマイグレーション実行機構
- [x] U001-T3 [認証Repository/Service層実装](#u001-t3-認証repositoryservice層実装) — パスワードハッシュ・セッション管理のロジック
- [x] U001-T4 [認証APIハンドラ実装](#u001-t4-認証apiハンドラ実装) — login/logout/meエンドポイント
- [x] U001-T5 [S01ログイン画面実装](#u001-t5-s01ログイン画面実装) — ログインフォームとAPI接続

---

## U001-T1: プロジェクト基盤構築

### 【目的】

* `client/`(React+TS+Vite)と `server/`(Python+FastAPI)のプロジェクト雛形を作成し、後続タスクがその上にコードを追加できる状態にする。

### 【作成・編集対象ファイル】

* `server/pyproject.toml`, `server/app/__init__.py`, `server/app/main.py`(FastAPIインスタンス生成、`/health` エンドポイントのみ持つ最小構成), `server/tests/__init__.py`
* `client/package.json`, `client/vite.config.ts`, `client/tsconfig.json`, `client/src/main.tsx`, `client/src/App.tsx`(「Meeting Room Reservation」とだけ表示する最小構成), `client/index.html`

### 【参照すべき仕様箇所】

* `docs/P005-impl-plan.md` 3章(U001の基盤作業の記述)
* `docs/P003-backend-spec.md` 0章(依存ライブラリの想定: fastapi, uvicorn, pydantic v2)

### 【実装内容】

* `server/`: `uv init` 相当の構成でPythonプロジェクトを初期化し、`fastapi`, `uvicorn[standard]`, `pydantic>=2` を依存に追加する。`app/main.py` に `GET /health` (`{"status": "ok"}` を返すだけ)を実装し、起動確認に使う。
* `client/`: `npm create vite@latest` 相当の構成(React + TypeScript テンプレート)でプロジェクトを初期化する。ルーティングライブラリとして `react-router-dom` を依存に追加する(後続タスクで画面遷移に使うため)。
* テストフレームワークの依存追加: `server/` に `pytest`、`client/` に `@testing-library/react` + `jsdom` + `tsx`(★P010初回レビューで追加。`.tsx`テストファイルをNode.js標準テストランナーで実行するためのローダー。`node --import tsx --test` の形で使う。`docs/P006-test-plan.md` 5章参照)。

### 【実装してはいけないこと】

* 認証・会議室・予約に関するロジックはこのタスクでは実装しない(後続タスクの範囲)。
* `docs/P002-frontend-spec.md`・`docs/P003-backend-spec.md` にない画面・APIを追加しない。

### 【Unit Test内容】

* テスト対象: `GET /health`
* 正常系: `GET /health` が200と `{"status": "ok"}` を返すこと
* 異常系: なし(このエンドポイントに異常系は無い)
* 実行するテストコマンド: `cd server && python -m pytest tests/ -v`
* 合格条件: 上記テストが1件PASSすること

### 【実行コマンド】

* `cd server && uvicorn app.main:app --reload`(起動確認。手動確認後にCtrl-Cで停止してよい)
* `cd client && npm install && npm run build`(ビルドが成功することを確認)

### 【完了条件】

* `server/` が `uvicorn app.main:app` で起動し、`GET /health` が200を返す
* `client/` が `npm run build` でエラーなくビルドできる
* 上記Unit Testが1件PASSする

### 【次タスクに進む前の停止条件】

* `npm install` がネットワークエラーで失敗する場合(パッケージレジストリに到達できない場合)は、3回リトライしても解消しなければ作業を停止し、その旨を記録して人間に報告する(`docs/P002-frontend-spec.md` 0章に記載のとおりレジストリ到達は事前確認済みだが、実行時点で状況が変わっている可能性に備える)。

---

## U001-T2: データモデル・マイグレーション実装

### 【目的】

* `docs/P003-backend-spec.md` 2.2節・3章にもとづき、全6テーブルのDDLとマイグレーション実行機構(起動時に未適用の `migrations/*.sql` を適用する仕組み)を実装する。

### 【作成・編集対象ファイル】

* `server/migrations/001_initial_schema.sql`(全6テーブルのDDL)
* `server/migrations/002_seed_admin.sql`(初期管理者アカウントのシードデータ)
* `server/app/db/migration.py`(マイグレーション適用ロジック: `schema_migrations` テーブルを確認し未適用ファイルのみ適用)
* `server/app/db/connection.py`(SQLite接続の取得。`PRAGMA foreign_keys = ON` を設定すること)
* `server/tests/test_migration.py`

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` 2.2節(DDL全文)、3章(マイグレーション方式)
* `docs/P005-impl-plan.md` U001節(シードデータの方針)

### 【実装内容】

* `001_initial_schema.sql` に `docs/P003-backend-spec.md` 2.2節のDDLをそのまま記載する(`users`, `rooms`, `reservations`, `reservation_participants`, `sessions`, `schema_migrations` の6テーブル、およびインデックス2件)。
* `002_seed_admin.sql` で、`user_id='admin'`, `name='システム管理者'`, `role='admin'`, `is_active=1` の行を1件INSERTする。`password_hash` は初期パスワード `ChangeMe123!` を1.2節(`docs/P003-backend-spec.md`)のscrypt方式でハッシュ化した固定値を計算して埋め込む(実装時にPythonスクリプトで一度だけ計算し、その結果の文字列をSQLに直接書く)。★FIXME★ この初期パスワードは開発・テスト用の仮値であり、本番投入前に変更または初回ログイン時の強制変更フローの追加が必要(強制変更フロー自体はP001に要求が無くスコープ外。`docs/P302-deliver.md` の配布手順書に、初期パスワードを本番投入前に変更する旨の注意書きを残すことをここで申し送る)。
* `migration.py`: 起動時に `schema_migrations` テーブルが無ければ作成し、`migrations/` 配下のファイルをファイル名の番号順にソート、`schema_migrations` に `version`(ファイル名から拡張子を除いたもの)が無いものだけをトランザクション内で `executescript` し、成功したら同一トランザクションで `schema_migrations` にINSERTする。
* `connection.py`: SQLiteファイルパスを環境変数 `DATABASE_PATH`(既定値 `server/data/app.db`)から取得する関数を実装する。

### 【実装してはいけないこと】

* `IF NOT EXISTS` の有無だけに冪等性を依存させない(`docs/P003-backend-spec.md` 3章の注意点のとおり、`schema_migrations` による管理を正とする)。
* 認証・会議室・予約のAPIロジックはこのタスクでは実装しない。

### 【Unit Test内容】

* テスト対象: `app/db/migration.py` の適用ロジック
* 正常系: 一時ディレクトリに `migrations/` を用意し、空のDBに対して2ファイル適用すると `schema_migrations` に2行記録され、`users` テーブルに `admin` 行が1件存在すること
* 正常系(冪等性): 同じマイグレーション適用処理を2回連続で実行しても例外が発生せず、`schema_migrations` の行数が2のまま増えないこと(2回目は「適用済みなのでスキップ」の分岐を通ることを確認)
* 主要な異常系: マイグレーションSQLが構文エラーの場合、例外が送出され `schema_migrations` に記録が残らないこと(ロールバックの確認)
* 実行するテストコマンド: `cd server && python -m pytest tests/test_migration.py -v`
* 合格条件: 上記3件すべてPASSすること

### 【実行コマンド】

* `cd server && python -m pytest tests/test_migration.py -v`

### 【完了条件】

* 上記Unit Test 3件がPASSする
* `uvicorn app.main:app` 起動時にマイグレーションが自動適用され、`admin` ユーザーが作成されることを手動確認する

### 【次タスクに進む前の停止条件】

* 冪等性テストが3回自己修正しても通らない場合は停止し、人間に報告する(このロジックはU003以降の重複チェックと並ぶ本アプリの信頼性上の要である)。

---

## U001-T3: 認証Repository/Service層実装

### 【目的】

* パスワードハッシュの生成・検証、セッションの発行・検証・削除を行うRepository層・Service層を実装する。APIハンドラ層(U001-T4)からはこの層のみを呼び出す。

### 【作成・編集対象ファイル】

* `server/app/repositories/user_repository.py`(`find_by_id`, `find_active_by_id` 等)
* `server/app/repositories/session_repository.py`(`create`, `find_valid`, `delete`, `delete_by_user_id`)
* `server/app/services/auth_service.py`(`login(employee_id, password) -> Session`, `logout(session_id)`, `get_current_user(session_id) -> User`)
* `server/app/security/password.py`(`hash_password(plain) -> str`, `verify_password(plain, hashed) -> bool`。scrypt実装)
* `server/tests/test_auth_service.py`, `server/tests/test_password.py`

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` 1.2節(パスワードハッシュ方式・パラメータ、セッションストア方式)
* `docs/P003-backend-spec.md` 4.1〜4.3節(内部仕様)

### 【実装内容】

* `password.py`: `hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)` でハッシュ化し、`scrypt$<salt_hex>$<hash_hex>` 形式で文字列化する。検証時は `hmac.compare_digest` で比較する(`docs/P003-backend-spec.md` 1.2節のとおり)。
* `auth_service.login`: `user_repository.find_active_by_id` でユーザー取得 → 存在しない/無効なら `InvalidCredentialsError` → `verify_password` で検証 → 不一致なら `InvalidCredentialsError` → `session_repository.create` でセッション発行(`session_id` は `secrets.token_urlsafe(32)`、`expires_at = now + 8時間`)。
* `auth_service.get_current_user`: `session_repository.find_valid`(`expires_at > now` のもののみ)でセッション取得 → 無ければ `UnauthorizedError` → 対応する `user_repository.find_active_by_id` を返す(ユーザーが後から無効化されているケースも401扱いにする)。
* `auth_service.logout`: `session_repository.delete` を呼ぶ。対象が無くても例外を出さない(冪等、`docs/P003-backend-spec.md` 4.2節)。

### 【実装してはいけないこと】

* APIのルーティング・HTTPステータスコードのマッピングはこのタスクに含めない(U001-T4の範囲)。Service層はHTTP例外(`fastapi.HTTPException`)を直接送出せず、独自例外クラス(`InvalidCredentialsError`, `UnauthorizedError`)を送出する。

### 【Unit Test内容】

* テスト対象: `password.py`, `auth_service.py`
* 正常系: 正しいパスワードでの `verify_password` がTrue、`login` が有効なセッションを返す
* 主要な異常系: 誤ったパスワードでの `verify_password` がFalse、存在しない社員IDでの `login` が `InvalidCredentialsError`、無効化されたユーザーでの `login` が `InvalidCredentialsError`、期限切れセッションでの `get_current_user` が `UnauthorizedError`
* 実行するテストコマンド: `cd server && python -m pytest tests/test_password.py tests/test_auth_service.py -v`
* 合格条件: 全件PASSすること(一時DBを使用、U001-T2のマイグレーション機構を流用してテスト用DBをセットアップする)

### 【実行コマンド】

* `cd server && python -m pytest tests/test_password.py tests/test_auth_service.py -v`

### 【完了条件】

* 上記Unit Testがすべて PASS する

### 【次タスクに進む前の停止条件】

* 3回自己修正してもテストが通らない場合は停止し、人間に報告する

---

## U001-T4: 認証APIハンドラ実装

### 【目的】

* U001-T3のService層を使い、`POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/me` を実装する。

### 【作成・編集対象ファイル】

* `server/app/routers/auth.py`
* `server/app/schemas/auth.py`(Pydanticモデル: `LoginRequest`, `LoginResponse`, `MeResponse`)
* `server/app/dependencies.py`(`get_current_user` 依存性、Cookieから `session_id` を取り出す)
* `server/app/errors.py`(共通エラーレスポンス形式への変換。`docs/P002-frontend-spec.md` 4章のエラー形式)
* `server/app/main.py`(ルーター登録)
* `server/tests/test_auth_api.py`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 4.1〜4.3節(外部仕様)
* `docs/P003-backend-spec.md` 4.1〜4.3節(内部仕様、Cookie属性)

### 【実装内容】

* `POST /api/auth/login`: リクエストボディを `LoginRequest` でパース → `auth_service.login` 呼び出し → 成功時201ではなく200(`docs/P002-frontend-spec.md` 4.1節のとおり200)でユーザー情報を返し、レスポンスに `Set-Cookie: session_id=...; HttpOnly; SameSite=Lax; Max-Age=28800`(+ 環境変数 `COOKIE_SECURE=true` のとき `Secure` を付与)を設定する → `InvalidCredentialsError` を401 `{"error": {"code": "INVALID_CREDENTIALS", ...}}` にマッピングする。
* `POST /api/auth/logout`: Cookieの `session_id` を取り出し `auth_service.logout` を呼び、`Set-Cookie: session_id=; Max-Age=0` でCookieを削除し200 `{}` を返す。
* `GET /api/me`: `Depends(get_current_user)` を使い、認証済みユーザー情報を200で返す。未認証は `dependencies.py` 側で401にマッピングする(`docs/P002-frontend-spec.md` 4章冒頭の共通仕様)。
* `errors.py`: `InvalidCredentialsError`→401、`UnauthorizedError`→401、`ValidationError`(Pydantic)→400+`fields`、を共通で変換する例外ハンドラをFastAPIの `exception_handler` として登録する。以降のスプリントの全APIがこのハンドラを共用する。

### 【実装してはいけないこと】

* 会議室・予約・ユーザー管理のエンドポイントはこのタスクに含めない。

### 【Unit Test内容】

* テスト対象: `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/me`(FastAPIの `TestClient` を使用)
* 正常系: 正しい認証情報でログイン→Set-Cookieヘッダーが含まれる→そのCookieで `GET /api/me` が200
* 主要な異常系: 誤った認証情報で401、Cookie無しで `GET /api/me` が401、ログアウト後に同じCookieで `GET /api/me` が401
* 実行するテストコマンド: `cd server && python -m pytest tests/test_auth_api.py -v`
* 合格条件: 全件PASS

### 【実行コマンド】

* `cd server && python -m pytest tests/test_auth_api.py -v`

### 【完了条件】

* 上記Unit TestがすべてPASSする

### 【次タスクに進む前の停止条件】

* 3回自己修正しても通らない場合は停止し、人間に報告する

---

## U001-T5: S01ログイン画面実装

### 【目的】

* `docs/P002-frontend-spec.md` 3.1節にもとづきログイン画面を実装し、U001-T4のAPIに接続する。

### 【作成・編集対象ファイル】

* `client/src/pages/LoginPage.tsx`
* `client/src/api/authApi.ts`(`login(employeeId, password)`, `logout()`, `getMe()` のfetchラッパー)
* `client/src/App.tsx`(ルーティングに `/login` を追加。認証状態に応じたリダイレクトの土台。カレンダー画面(S02)自体はU003で実装するため、ここでは `/`(ルート)に「ログイン後トップ」というプレースホルダを置く)
* `client/tests/LoginPage.test.tsx`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 3.1節(バリデーションルール、動作)、4.1節(API仕様)

### 【実装内容】

* 社員ID・パスワード入力欄、ログインボタンを持つフォームコンポーネントを実装する。
* クライアント側バリデーション: 未入力時にそれぞれ「社員IDを入力してください」「パスワードを入力してください」を表示する。
* 送信時 `authApi.login` を呼び出し、成功時はルート(`/`)へ遷移、401時は「社員IDまたはパスワードが正しくありません」を表示する(3.1節のとおり)。
* fetchは `credentials: 'include'` を指定し、Cookieが送受信されるようにする。

### 【実装してはいけないこと】

* S02(カレンダー画面)の本実装はこのタスクに含めない(U003の範囲)。ここでは遷移先として最小限のプレースホルダのみを置く。

### 【Unit Test内容】

* テスト対象: `LoginPage` コンポーネント
* 正常系: 社員ID・パスワードを入力してログインボタンを押すと `authApi.login` が正しい引数で呼ばれること(APIはモックする)
* 主要な異常系: 未入力でログインボタンを押すとバリデーションメッセージが表示されAPIが呼ばれないこと、APIが401を返した場合にエラーメッセージが表示されること
* 実行するテストコマンド: `cd client && node --import tsx --test tests/LoginPage.test.tsx`
* 合格条件: 全件PASS

### 【実行コマンド】

* `cd client && node --import tsx --test tests/LoginPage.test.tsx`
* このコマンドを実装時に実際に実行し、意図したテストが実行される(0件スキップにならない)ことを確認してから本タスクを完了とすること(`SKILL.md` 各フェーズ共通指示)。

### 【完了条件】

* 上記Unit TestがすべてPASSする
* 手動確認: `server/` と `client/` を同時起動し、ブラウザ(または手動fetch)でログイン→Cookie発行→`/api/me`成功、を確認する

### 【次タスクに進む前の停止条件】

* 3回自己修正しても単体テストが通らない場合は停止し、人間に報告する

---

## 重要

* 各タスクの範囲外のファイルは編集しないでください。
* タスクの実装後、実行したテストコマンドと結果を報告してください。
* タスクが完了したら、上記「タスク一覧」の該当行を `[x]` に更新してください。
* 全タスクが完了したら、`docs/P007-impl-direction.md` の本スプリント行を `[x]` に更新してください。
* Executor Stepの停止条件(`SKILL.md` 参照。例: 単体テストが3回自己修正しても合格しない)に該当しない限り、次のタスクに自動的に進んでください。1タスクごとに人間の指示を待つ必要はありません。
