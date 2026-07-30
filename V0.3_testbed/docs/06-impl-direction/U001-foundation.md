# U001: foundation — DBスキーマ・認証基盤・ログイン画面

対象スプリント位置づけ: `docs/04-impl-plan.md` スプリント1。全スプリントの土台。

参照仕様: `docs/02-frontend-spec.md`(S01, API外部仕様のうち認証系), `docs/03-backend-spec.md`(2章セッション, 3章認証・認可, 4章認証系API内部仕様)

コード格納先: `server/`(Python, uv), `client/`(静的HTML/JS)

---

## タスク U001-T1: DBスキーマ・初期データ

【タスクID】U001-T1
【目的】SQLiteスキーマ(`users`, `rooms`, `reservations`, `reservation_participants`, `sessions`)を作成し、開発用初期データ(管理者1名・一般ユーザー2名・会議室3室)を投入できるようにする。
【作成・編集対象ファイル】`server/pyproject.toml`, `server/app/__init__.py`, `server/app/db.py`, `server/app/seed.py`
【参照すべき仕様箇所】`docs/03-backend-spec.md` 2章・4章のテーブル定義
【実装内容】`db.py` に `sqlite3` でのスキーマDDL(`CREATE TABLE IF NOT EXISTS`、外部キー制約 `PRAGMA foreign_keys = ON`)と接続取得関数を実装する。`seed.py` は初回起動時のみ(`users`テーブルが空の場合)、管理者(`admin`/初期パスワード`admin12345`)・一般ユーザー(`u001`,`u002`)・会議室3室(会議室A/B/C)を投入する。
【実装してはいけないこと】`docs/03-backend-spec.md` にないテーブル・カラムの追加。
【Unit Test内容】`server/tests/test_db.py`: スキーマ作成後に5テーブルが存在すること、seed実行後に管理者ユーザーが1件存在すること、再度seedを呼んでも重複投入されないこと。
【実行コマンド】`cd server && python3 -m unittest tests.test_db -v`
【完了条件】上記テストが全てPASSすること。
【次タスクに進む前の停止条件】テストが1件でもFAILした場合は先に進まない。

## タスク U001-T2: パスワードハッシュ・セッション管理(純粋関数/ロジック層)

【タスクID】U001-T2
【目的】パスワードのハッシュ化・照合、セッションの発行・検証・失効ロジックを実装する。
【作成・編集対象ファイル】`server/app/security.py`
【参照すべき仕様箇所】`docs/03-backend-spec.md` 3章
【実装内容】`hash_password(password) -> str`、`verify_password(password, hashed) -> bool`(PBKDF2-HMAC-SHA256、salt付き)。`create_session(conn, user_id) -> session_id`(8時間有効)、`get_session_user(conn, session_id) -> user_row|None`(期限切れなら削除してNone)、`delete_session(conn, session_id)`。
【実装してはいけないこと】平文パスワードの保存・ログ出力。
【Unit Test内容】`server/tests/test_security.py`: 正しいパスワードでverify成功、誤りで失敗、同一パスワードでも salt により hash が毎回異なること、セッション発行直後は有効、期限切れセッション(expires_atを過去に書き換え)はNoneを返すこと。
【実行コマンド】`cd server && python3 -m unittest tests.test_security -v`
【完了条件】全テストPASS。
【次タスクに進む前の停止条件】FAIL時は先に進まない。

## タスク U001-T3: 認証API(login/logout/me、型・スキーマ層含む)

【タスクID】U001-T3
【目的】`POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/me` をStarlette上のASGIアプリとして実装する(`docs/06-impl-direction.md`記載のFastAPI代替方針に従いStarlette+Pydanticを使用)。Pydanticスキーマ定義もここに含める(型・スキーマ層と認証API層の関連が強いためタスクをまとめる)。
【作成・編集対象ファイル】`server/app/main.py`, `server/app/routers/auth.py`, `server/app/schemas.py`
【参照すべき仕様箇所】`docs/02-frontend-spec.md` 2章(認証系API)、`docs/03-backend-spec.md` 3章
【実装内容】Cookie `session_id`(HttpOnly, SameSite=Lax)の発行・検証。`require_login`依存関数。共通エラー形式 `{"error": {"code","message"}}`。共通例外ハンドラ(未捕捉例外→500、Pydanticバリデーションエラー→400)。`GET /health`(バージョン確認用、`docs/09-deliver.md`で使用)。
【実装してはいけないこと】仕様にない認証方式(JWT等)への変更。
【Unit Test内容】`server/tests/test_auth_api.py`: Starletteの`TestClient`を用い、正しい認証情報でログイン成功しCookieが返る/誤った認証情報で401/無効化ユーザーで401/ログアウト後は`/api/me`が401/未ログインで`/api/me`が401。
【実行コマンド】`cd server && python3 -m unittest tests.test_auth_api -v`
【完了条件】全テストPASS。
【次タスクに進む前の停止条件】FAIL時は先に進まない。

## タスク U001-T4: フロントエンド土台 + S01ログイン画面

【タスクID】U001-T4
【目的】ビルド不要の静的フロントエンド一式の土台と、S01ログイン画面を実装する。
【作成・編集対象ファイル】`client/index.html`, `client/style.css`, `client/app.js`, `client/api.js`
【参照すべき仕様箇所】`docs/02-frontend-spec.md` 1章(S01バリデーション), 2章(login API)
【実装内容】`api.js` に `fetch`ベースの共通APIクライアント(Cookie送信 `credentials: "include"`)。`app.js` に簡易ハッシュルーター(`#/login`, `#/calendar` 等)。S01: 社員ID・パスワード入力、ログイン失敗時のエラーメッセージ表示、成功時は `#/calendar` へ遷移(スプリント2まではプレースホルダ表示)。
【実装してはいけないこと】仕様にない入力項目の追加。
【Unit Test内容】フロントエンドは軽量な素のJSのため、UIコンポーネント単体の自動テストは実施せず、`docs/05-test-plan.md`記載のとおりAPIシナリオスクリプトで代替する(本タスクではAPI連携確認は次タスクで実施)。
【実行コマンド】(該当なし。次タスクの結合確認で検証する)
【完了条件】`client/index.html` を目視確認し、次タスクの結合確認で担保する。
【次タスクに進む前の停止条件】なし。

## タスク U001-T5(結合確認用の薄いタスク): ログイン結合確認

【タスクID】U001-T5
【目的】サーバーを実起動し、ログイン→`/api/me`→ログアウトの一連がHTTP経由で仕様通り動くことを確認する(スプリント1に閉じた結合テスト)。
【作成・編集対象ファイル】`server/tests/integration/test_u001_login_flow.py`
【参照すべき仕様箇所】`docs/02-frontend-spec.md` 4.1 シーケンス図
【実装内容】`uvicorn`でサーバーをバックグラウンド起動し、`urllib`でHTTPリクエストを送って login→me→logout→me(401)を確認する。
【実装してはいけないこと】アプリケーションコードの修正(テストのみ追加)。
【Unit Test内容】(結合テストのため対象外)。正常系: admin/admin12345でログイン成功、`/api/me`でadminのroleが返る、logoutで204、logout後`/api/me`が401。
【実行コマンド】`cd server && python3 -m unittest tests.integration.test_u001_login_flow -v`
【完了条件】全テストPASS。
【次タスクに進む前の停止条件】FAIL時はU002へ進まない。

---

このスプリントの実装(全タスクのUnit Test・結合確認を含む)が完了したら、`docs/06-impl-direction.md` のU001行のチェックボックスを `[x]` に更新する。

## 実施結果

* U001-T1〜T5: 全実施・全PASS。詳細件数は `docs/06-impl-direction.md` 実施結果サマリおよび `docs/07-test-direction.md` を参照。
