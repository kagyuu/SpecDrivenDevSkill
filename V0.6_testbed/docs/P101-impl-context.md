# P101 — 実装コンテキスト (Executor向け要約)

> このファイルはExecutor Step(P101〜P104)の実行のたびに更新する。直近の対象スプリントの情報を先頭に置く。

## 現在の対象スプリント

* **U004: reservation-detail-mine**(`docs/P007-impl-direction/U004-reservation-detail-mine.md`) — P007目次で `[ ]` の先頭(U001〜U003は完了済み)。
* 前提: U001〜U003完了。予約の閲覧・作成(GET/POST /api/reservations)が利用可能。

## ソースツリーの状態(INDEX.md要約、U002完了時点)

* `server/app/`: db(SQLite接続・マイグレーション)、core(password/validators/exceptions)、repositories(user/session/room)、services(auth/room/user)、api(auth/rooms/users/deps/errors)、main.py。`server/tests/` にunittestベースの単体テスト75件(全PASS)。
* `client/js/`: api(authApi/roomApi/userApi)、pages(loginPage/roomManagementPage/userManagementPage)、app.js(簡易ハッシュルータ)。`client/tests/` にnode:testベースの単体テスト19件(全PASS)。
* 予約関連(reservation_repository/reservation_service/api/reservations.py、CalendarPage/ReservationCreatePage等)は未着手。

### (参考)U001時点の記録

* U001着手時は `client/` `server/` とも未作成(P020時点で空INDEX)だった。

## 遵守すべき技術的決定(ADR.md一覧)

| ADR | タイトル | 状態 |
| --- | --- | --- |
| ADR-001 | フロントエンドにReact 18 + TypeScript + Vite | 採用 |
| ADR-002 | バックエンドにPython + FastAPI(レイヤードアーキテクチャ) | 採用 |
| ADR-003 | データストアにSQLite | 採用 |
| ADR-004 | Cookieベースのサーバーサイドセッション認証(JWT不採用) | 採用 |
| ADR-005 | セッション永続化はSQLite `sessions` テーブル(インメモリ不採用) | 採用 |
| ADR-006 | 予約重複チェックは `BEGIN IMMEDIATE` トランザクション | 採用 |
| ADR-007 | 予約は物理削除、会議室・ユーザーは論理削除 | 採用 |

> ★実行環境の制約★ 本セッションのサンドボックスは `pypi.org`・`registry.npmjs.org` への外向きネットワークアクセスが許可されていない(`Host not in allowlist` エラー)。このため `fastapi`・`bcrypt`・`pytest` を pip でインストールできず、`npm create vite` / `npm install react` 等も実行できない。ADR-001/ADR-002の意図(型安全・OpenAPI・コンポーネント化)を最大限尊重しつつ、以下の代替を採用する(Executor全スプリント共通の前提として、逐次のU00N指示書より優先してこのコンテキストの内容に従う)。
>   * バックエンド: `FastAPI` の代わりに、そのベースであるASGIフレームワーク `Starlette`(インストール済み)+ `Pydantic 2`(インストール済みでFastAPIと同じ検証ライブラリ)を直接使用する。レイヤー構成(Handler→Service→Repository)はP003の設計をそのまま踏襲する。
>   * パスワードハッシュ: `bcrypt` パッケージが無いため、Python標準ライブラリ `hashlib.scrypt`(N=2^14, r=8, p=1)を用いた同等のコスト付きハッシュ方式で代替する。ADR-004の実装詳細(P003 §3)の代替措置。
>   * フロントエンド: React+TS+Viteの代わりに、ビルド不要のプレーンHTML/CSS/JavaScript(ES Modules)で実装する。npmレジストリに接続できないため。
>   * 単体テストランナー: `pytest` が無いため、Python標準ライブラリ `unittest` を用いる。ただしP007/P008の指示書にある `uv run pytest tests/xxx.py::test_yyy -v` のテストID(関数名)は、`unittest.TestCase` のメソッド名としてそのまま踏襲し、`python3 -m unittest tests.xxx.ClassName.test_yyy -v` で個別実行できるようにする。フロントエンドの単体テストは、Node.js 22に標準搭載の `node --test` を使用する(npmパッケージ不要)。DOM操作を伴う画面コンポーネントは、テスト可能な純粋関数(フォームバリデーション・グリッド生成・フィルタ処理等)に分離し、そのロジック部分を単体テスト対象とする。

## これから着手するスプリント(P007目次の次の未完了項目)

* U004 reservation-detail-mine: 予約詳細・編集画面・マイ予約一覧画面、reservations の参照・更新・削除API(6タスク: U004-1〜U004-6)。

## 詳細仕様の参照先(迷ったとき)

* 認証・セッション内部設計: `docs/P003-backend-spec.md` §2
* パスワードハッシュ方式: `docs/P003-backend-spec.md` §3(★上記の代替措置を適用)
* データモデル: `docs/P003-backend-spec.md` §6(ER図・テーブル定義)、`docs/P002-frontend-spec.md` §5
* 共通エラーレスポンス形式: `docs/P002-frontend-spec.md` §2
* 予約重複チェック・排他制御: `docs/P003-backend-spec.md` §5(ADR-006)
* 予約編集権限(本人/管理者): `docs/P003-backend-spec.md` §4
* S04予約詳細・編集画面/S05マイ予約一覧画面: `docs/P002-frontend-spec.md` §3 S04/S05
