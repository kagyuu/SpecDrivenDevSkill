# 成果物まとめ

> 本書は `spec-driven-dev` Skill フェーズP302(納品物作成)の成果物です。
> インプット: `docs/P001-requirement.md` 〜 `docs/P009-acceptance-direction.md`(各子ドキュメントを含む)、`docs/test-records/*.md`、`docs/P201-review-report.md`、`docs/P202-fix-plan.md` と `docs/P202-fix-plan/`、`docs/P204-impact-analysis.md`、`docs/ADR.md`、`docs/ArchitectureHandbook.md`、`./INDEX.md`、`server/INDEX.md`、`client/INDEX.md`、およびソースツリーと配布資産。
> 本書は人間がリリース判断を行うための最終資料である。改善要望が出た場合は Refactor(P901〜)の起点として `docs/P901-cr-direction/CR-NNN.md` に起票する。
> **改訂(CR-001 / P903 2026-08-05)**: CR-001(予約にオンライン会議URL)の対応にともない、第1章・1.3・4.4・4.8・5章・**7.5(既存環境のアップグレード手順)**・9.1.1・10.1 を更新しました。バージョンは 1.0.0 → **1.1.0**。

## 1. 概要

| 項目 | 内容 |
| --- | --- |
| システム名 | 会議室予約システム |
| バージョン | **1.1.0**(`./VERSION`。※CR-001 で 1.0.0 → 1.1.0) |
| アプリケーション種別 | **サービス提供型システム**(フロントエンド + バックエンド + SQLite。詳細は3章) |
| 配布方式 | Docker Compose(単一アプリケーションサービス + 任意のTLS終端リバースプロキシ) |
| 規模 | 7画面(S01〜S07)/ 17API(API-01〜API-17)/ 要求ID **49件**(※CR-001 で REQ-ITEM-008 を追加) |
| テスト結果 | ※CR-001 反映後: 単体**372件**(バックエンド234 + フロントエンド146。※内訳は実行単位で重複しない件数)・結合(T001〜**T019**)**19件**・受け入れ結合(A001〜A012)12件 = **すべてPASS**(本フェーズで再実行して確認。9.1.1) |
| 未解決障害 | **0件**(`docs/P202-fix-plan/P202-fix-unresolved.md`)。CR-001 の対応でもFAIL・BLOCKEDは発生していない |
| **リリース判定** | **保留**(根拠は11章。テスト・仕様面の欠陥ではなく、**Docker Composeのビルド・起動を実機確認できていない**ことが理由) |

### 1.1 実行前チェックの結果(`SKILL-P302-deliver.md`「実行前チェック」)

| # | 確認項目 | 結果 |
| --- | --- | --- |
| 1 | `docs/P002-frontend-spec.md` / `docs/P003-backend-spec.md` の存在 | **あり**(両方) |
| 2 | `docs/P006-test-plan.md` の存在 | **あり** |
| 3 | `docs/test-records/*.md` の存在 | **あり**(4件: 20260805-1152 / -1226 / -1603 / -1620) |
| 4 | `docs/P202-fix-plan/P202-fix-resolved.md` / `P202-fix-unresolved.md` の存在 | **両方あり**(解決2件 / 未解決0件) |
| 5 | ソースツリーからのアプリケーション種別の推定 | **可能**(サービス提供型システム。3章) |
| 6 | `docs/P302-deliver.md` が既に存在するか | **なし**(本書が初版。既存内容の引き継ぎは不要) |
| 7 | フロント/バックの接続前提と実際の配布トポロジーの一致 | **一致させた**(下記1.2。**不一致となる構成を採らない**判断を行い、その根拠を明記した) |
| 8 | 停止・再起動しても正常に起動するか(初期化処理の冪等性) | **実測で確認済み**(同一DBファイルに対し3回連続で起動・停止し、3回すべて正常起動。下記1.3および9章) |

### 1.2 実行前チェック#7 の詳細 — 配布トポロジーの決定

**結論: フロントエンドとバックエンドを別サービス・別オリジンに分けない。1コンテナ・1プロセスで両方を配信する。**

実際のコードを確認した結果、フロントエンドは**同一オリジンを前提としたルート相対パス**でAPIを呼んでいる。

| 確認箇所 | 実際の記述 | 意味 |
| --- | --- | --- |
| `client/src/lib/api.js` 56〜64行 | `runtime.fetch(path, options)` に渡す `path` は呼び出し側の文字列そのまま。オリジンを付与する処理が**存在しない** | ベースURLの概念がない |
| `client/src/views/*.js` / `client/src/components/header.js` の全27箇所 | `api.get('/api/rooms')` `api.post('/api/auth/login', ...)` など、**すべて `/api/...` のルート相対パス** | 画面を配信したオリジンにAPIがある前提 |
| `client/src/lib/api.js` 59行 | `credentials: 'same-origin'` | **クロスオリジンではCookieを送出しない**。別オリジンにすると認証が成立しない |
| `client/index.html` | `<link href="/src/styles.css">` / `<script src="/src/main.js">` | 画面を配信したオリジンが `/src/*` も配信する前提 |
| `client/src/` 全体の grep | `http://` / `https://` / `BASE_URL` / `API_BASE` などの**外部設定は1件も存在しない** | 環境変数等でAPIの宛先を差し替える手段がない |
| `server/src/meeting_room/main.py` 123〜130行 | 同一アプリが `/api/*` と `/`・`/src/*`・`/assets/*`・フォールバックを配信する | サーバー側も同一オリジン配信を前提に実装済み |
| `server/src/meeting_room/main.py` 18行 | `CLIENT_DIR = Path(__file__).resolve().parents[3] / "client"` | **`server/` と `client/` が同じ親ディレクトリに並んでいること**がコンテナ内でも必要 |

この前提は設計判断として明文化されている(`docs/ADR.md` ADR-010「単一プロセスでAPIと静的ファイルの双方を配信し、TLS終端・ログ集約はプロセスの外側に委ねる」)。

**実測による裏づけ**(本フェーズで実行):

* 単一プロセス(`python3 -m uvicorn meeting_room.main:app`)に対して、`GET /` = **200**、`GET /src/main.js` = **200**、`POST /api/auth/login` = **200**。1つのオリジンで画面・静的ファイル・APIのすべてが成立することを確認した。
* 逆に、`client/` だけを別オリジン(`python3 -m http.server` の別ポート)で配信した場合、`GET /` = 200・`GET /src/main.js` = 200 だが **`GET /api/me` = 404** となる。`client/` と `server/` を別コンテナ・別オリジンに分けた docker-compose を組むと、画面は表示されるがすべてのAPI呼び出しが404になり、システムは動作しない。

したがって `docker-compose.yml` は **`app` の1サービス構成**とし、`Dockerfile` で `server/` と `client/` を同一イメージの `/app/server` `/app/client` に並べて配置した。TLS終端リバースプロキシ(`tls` プロファイルの `proxy`)を使う場合も、**パスで upstream を分けず全パスを `app` に渡す**ことで同一オリジンを維持している(`deploy/nginx.conf.example`)。

* この判定に至った経緯として、`docs/P009-acceptance-direction.md` の受け入れ結合テストは**バックエンドに実HTTPクライアントで直接接続する方式**(`server/tests/acceptance/support.py`)、および**画面モジュールの描画関数を実サーバーに接続する方式**(`client/tests/acceptance/support.js`)で実行されており、いずれも「ブラウザが `index.html` を取得したオリジンから相対パスでAPIを呼ぶ」という経路そのものは検証していない。つまり**テストが全件PASSしていても、配布トポロジーの取り違えは検出されない**。本フェーズでコードを直接確認して topology を決定したのは、この検出漏れを埋めるためである。

### 1.3 実行前チェック#8 の詳細 — 再起動時の起動可否(初期化処理の冪等性)

**結論: 同一DBファイルに対して3回連続で起動・停止し、3回すべて正常に起動してリクエストを処理できた。冪等化のための修正は不要。**

実行内容(`DB_PATH` を固定した1つのSQLiteファイルに対して、起動 → HTTP確認 → `SIGTERM` 停止 を3回繰り返した):

| 回 | `GET /` | `GET /src/main.js` | `POST /api/auth/login`(初期管理者) | `schema_migrations` の行 | `users` 件数 | 起動時エラー |
| --- | --- | --- | --- | --- | --- | --- |
| 1回目(DBファイルなしから) | 200 | 200 | 200 | `001-init.sql` / `002-rooms.sql` / `003-reservations.sql`(3行) | 1 | なし |
| 2回目(同一ファイル) | 200 | 200 | 200 | 同じ3行(**増えていない**) | 1(**増えていない**) | なし |
| 3回目(同一ファイル) | 200 | 200 | 200 | 同じ3行 | 1 | なし |

* 差分適用マイグレーション(`server/src/meeting_room/db.py` の `apply_migrations`)が `schema_migrations` に未記録のファイルのみを適用するため(ADR-009)、2回目以降は適用対象が0件になる。
* 初期管理者シード(`seed_initial_admin`)は「有効な管理者が0人のときだけINSERT」であるため、2回目以降は何もしない。`users` が1件のままであることで確認した。
* 停止後に `app.db-wal` / `app.db-shm` は残っていない(SQLiteが最終接続クローズ時にWALを削除するため)。WALが残った状態からの起動可否は `docs/P009-acceptance-direction/A007-restart-resilience.md`(A007 手順8)で別途PASSしている。
* この観点は `docs/P006-test-plan.md` 3.3 の V-O-01 / V-O-02 に対応し、A007 が**同一DBファイルで4回起動**する形で既にPASSしている。本フェーズの確認は、**配布物としての起動コマンド(`python3 -m uvicorn meeting_room.main:app`)で同じことが成り立つか**を独立に確かめたものである。
* **※CR-001(2026-08-05T17:22Z)による再確認**: CR-001 でマイグレーション `004-meeting-url.sql`(`ALTER TABLE reservations ADD COLUMN meeting_url TEXT NOT NULL DEFAULT ''`)を追加したため、同じ確認をやり直した。**同一DBファイルに対して3回連続で起動・停止し、3回すべて `GET /` = 200 で正常起動**。`schema_migrations` は **4行**(`001`〜`004`)のまま増えず、`users` も1件のままで、`duplicate column name: meeting_url` は発生しなかった。`apply_migrations()` を直接2回呼ぶ確認(1回目=4件適用 / 2回目=0件適用)も別途成功している。記録は `docs/test-records/20260805-1723-test-record.md`。
  * この再確認は、SQLiteに `ADD COLUMN IF NOT EXISTS` が無いため**差分適用方式でなければ2回目の起動が必ず失敗する**箇所であり、ADR-009 の判断が実際に効いていることを示す最初の実例である。
* **未確認事項**: 上記は Docker コンテナではなくホスト上のプロセスで確認した。`docker compose restart` / `restart: unless-stopped` による再起動そのものは実機確認できていない(9章)。ただし冪等性はアプリケーションコード側の性質であり、実行媒体には依存しない。

## 2. 参照した成果物

### 2.1 存在を確認して参照した文書

| 文書 | 参照した内容 |
| --- | --- |
| `docs/P001-requirement.md` | 要求48件の出発点、非機能要件 |
| `docs/P002-frontend-spec.md` | 画面S01〜S07、入力ルール、**API契約(第5章。単一の正)** |
| `docs/P003-backend-spec.md` | 層構成、データモデル、重複チェック、**非機能要件の担当フェーズと委譲先(第8章)** |
| `docs/P004-traceability-matrix.md` | 要求ID48件の一覧と状態、技術要求の逸脱2件、過剰実装6件 |
| `docs/P005-impl-plan.md` | Sprint 1〜4の分割、**インフラ専用スプリントを設けない判断(第4章)** |
| `docs/P006-test-plan.md` | テスト観点 V-F-01〜15 / V-N-01〜08 / V-O-01〜02、基準データセット、合否条件 |
| `docs/P007-impl-direction.md` + `U001`〜`U004` | 実装単位と単体テスト観点 |
| `docs/P008-test-direction.md` + `T001`〜`T018` | 結合テスト18件(全行 `[x]`) |
| `docs/P009-acceptance-direction.md` + `A001`〜`A012` | 受け入れ結合テスト12件(全行 `[x]`)、**A011 手順7 の本書への申し送り** |
| `docs/test-records/20260805-1152 / -1226 / -1603 / -1620-test-record.md` | 全テストの実行記録 |
| `docs/P201-review-report.md` | 最終結果一覧(30件PASS)、合否に含めない申し送り事項6件(第5章) |
| `docs/P202-fix-plan.md` / `fixed/F001` / `fixed/F002` / `P202-fix-resolved.md` / `P202-fix-unresolved.md` | 修正2件の内容と、未解決0件・人間確認事項5件 |
| `docs/P204-impact-analysis.md` | 修正が他機能を壊していないことの確認 |
| `docs/ADR.md`(ADR-001〜010)/ `docs/ArchitectureHandbook.md` | 技術判断の根拠。特に**ADR-010(実行トポロジ)** |
| `./INDEX.md` / `server/INDEX.md` / `client/INDEX.md` | リポジトリ・ソースツリーの目次 |
| ソースツリー | `server/src/meeting_room/**`、`client/src/**`、`server/migrations/*.sql`、`server/tests/**`、`client/tests/**` |
| 配布資産(既存) | `server/pyproject.toml`、`server/.python-version`、`server/.gitignore`、`server/README.md`(**空だった**)、`client/package.json` |

### 2.2 存在しなかったもの(推測で補わず、存在しないことを記録する)

| 期待される所在 | 状態 | 本フェーズでの扱い |
| --- | --- | --- |
| `Dockerfile` | 本フェーズ開始時点で**存在しなかった** | 新規作成した(6章)。**ビルドは未実行**(9章) |
| `docker-compose.yml` / `compose.yml` | 同上 | 新規作成した(6章)。**起動は未実行**(9章) |
| `.env.example` | 同上 | 新規作成した |
| `VERSION` | 同上 | 新規作成した(5章) |
| `BUILD_HISTORY.md` / `CHANGELOG.md` | 同上 | `BUILD_HISTORY.md` を新規作成した(5章)。`CHANGELOG.md` は**作成していない**(リリース履歴が1件も存在せず、書ける実績がないため) |
| リポジトリ直下の `README.md` | 同上 | 新規作成した |
| `server/README.md` | ファイルは存在したが**中身が空**だった(`server/INDEX.md` に「内容はP302で整備する」と記載あり) | 内容を記述した |
| `docs/CR.md` / `docs/P901-cr-direction/` / `docs/P903-cr-records/` | **存在しない**(変更要求がまだ起票されていない) | 正常。Refactor未実施のため |
| Gitリポジトリ | **存在しない**(`git status` → `fatal: not a git repository`) | ビルド履歴の `Commit` 列はすべて `未取得`(5章) |
| `docs/P012` 専用文書 | 存在しない | `SKILL.md` の定義どおり(P012は該当文書を直接更新する) |
| `docs/P103`/`P205` 専用文書 | 存在しない | `docs/test-records/*.md` が該当(定義どおり) |

## 3. アプリケーション種別と配布方針

### 3.1 種別の判定

**分類1: サービス提供型システム**(Webアプリケーション + APIサーバー + データストアの常駐プロセス)。

判定根拠:

* `docs/P001-requirement.md` が7つのブラウザ画面と17本のREST APIを要求しており、常駐してHTTPを待ち受ける形態である。
* `server/src/meeting_room/main.py` がASGIアプリ(`create_app`)を提供し、`python3 -m uvicorn meeting_room.main:app` で起動する(結合テスト・受け入れテストが実際にこの方法で起動している)。
* CLIのエントリポイント(`bin/` `cmd/` `console_scripts`)、バッチスクリプト、ライブラリとしての公開APIは**いずれも存在しない**。したがって分類2〜4ではない。

### 3.2 配布方針

| 項目 | 方針 | 根拠 |
| --- | --- | --- |
| 配布形態 | Docker Compose | サービス提供型システムであるため(`SKILL-P302-deliver.md`「配布資産の整備方針」) |
| サービス数 | **1(`app`)**+ 任意の `proxy`(TLS終端) | **フロントエンドは同一オリジン前提のルート相対パスfetch**(1.2参照)。分割すると動作しない |
| DBミドルウェア | **なし**(SQLite単一ファイル) | ADR-004。別プロセスのDBを起動しないため `db` サービスを持たない |
| データ永続 | 名前付きボリューム `app-data` を `/app/data` にマウント | SQLiteファイルの喪失=全データ喪失 |
| プロセス数 | uvicorn `--workers 1` | ADR-010「単一プロセス・単一SQLiteファイル」。接続上限は uvicorn 既定のまま(A009で30スレッド同時の参照90本・更新30本で5xxが0件であることを実測済み) |
| TLS | プロセスの外側で終端(`proxy` サービス、または実行環境のロードバランサ) | ADR-010。アプリはHTTPで待ち受け、`X-Forwarded-Proto` を参照しない |
| ログ | 標準出力へJSON1行。compose では `json-file` ドライバでローテーション上限のみ設定 | ADR-010。転送先・監視設定はアプリの責務外(10章の人間確認事項) |
| 自動再起動 | `restart: unless-stopped` + `HEALTHCHECK` | REQ-NFR-002(可用性)の委譲を受けた設定。起動処理が冪等であることは1.3で実測確認済み |

## 4. 仕様・テスト・テスト実装の対応表

`docs/P004-traceability-matrix.md` が全48件の要求IDを確定しているため、それをそのまま仕様IDとして用いる(一時IDは付けない)。
表記: 「テスト実装/実行コマンド」の相対パスは、`server/...` は `cd server`、`client/...` は `cd client` を起点とする。

### 4.1 システムの前提(REQ-PRE)

| 仕様ID/項目 | 仕様内容 | 対応するテスト計画 | 対応するテスト指示 | 対応するテスト実装/実行コマンド | 最新結果 | 証跡 | 状態 |
|---|---|---|---|---|---|---|---|
| REQ-PRE-001 | 従業員300名・会議室10室規模 | P006 3.2 V-N-01 / V-N-02 | P009 A008 / A009 | `server/tests/acceptance/test_a008_calendar_performance.py`、`test_a009_concurrent_load.py`、`client/tests/acceptance/test_a008_calendar_render.js` | PASS | docs/test-records/20260805-1603, -1620 | OK |
| REQ-PRE-002 | クラウド環境へのデプロイ | (P003 8章によりP302へ委譲) | P009 A012(運用者受入の一部) | `server/tests/acceptance/test_a012_operator_acceptance.py` / `docker compose build && docker compose up -d` | A012 は PASS / **compose は未実行** | docs/test-records/20260805-1603 / 本書9章 | **BLOCKED**(Dockerデーモンが無く、配布トポロジーの実機確認ができていない) |
| REQ-PRE-003 | ID/パスワードによるログイン必須 | P006 3.1 V-F-04 | P008 T001 / T002、P009 A006 | `server/tests/integration/test_t001_login_session.py`、`test_t002_auth_failure.py`、`server/tests/acceptance/test_a006_session_lifecycle.py`、`client/tests/acceptance/test_a006_session_ui.js` | PASS | docs/test-records/20260805-1226, -1603, -1620 | OK |
| REQ-PRE-004 | 既存システム連携なし・外部カレンダー連携は対象外 | (なし) | (なし) | (なし) | - | docs/P004 2.1(P002 8章・P003 10章のスコープ確認) | **NO_TEST_PLAN**(検証対象となる振る舞いを持たない「〜しない」要求。設計書のスコープ確認で充足を確認しているが、テストは存在しない。10章に記載) |

### 4.2 採用技術(REQ-TECH)

| 仕様ID/項目 | 仕様内容 | 対応するテスト計画 | 対応するテスト指示 | 対応するテスト実装/実行コマンド | 最新結果 | 証跡 | 状態 |
|---|---|---|---|---|---|---|---|
| REQ-TECH-001 | フロントエンド: React 18 + TypeScript + Vite | (なし。ADR-001により代替) | (なし) | (なし) | - | docs/ADR.md ADR-001、docs/P004 3章(逸脱#1) | **NO_TEST_PLAN**(要求そのものが ADR-001 で意図的に代替されており、代替後の構成に対するテストは存在するが、要求どおりの構成に対するテストは存在しない。★FIXME★ 人間の確認対象。10章に記載) |
| REQ-TECH-002 | バックエンド: Python + FastAPI | (なし。ADR-002により代替) | (なし) | (なし) | - | docs/ADR.md ADR-002、docs/P004 3章(逸脱#2) | **NO_TEST_PLAN**(同上。★FIXME★ 人間の確認対象。10章に記載) |
| REQ-TECH-003 | データストア: SQLite | P006 4.1(`db.py`・`repositories/*`) | P008 T004、P009 A007 | `server/tests/test_db_migration.py`、`server/tests/integration/test_t004_restart_migration.py`、`server/tests/acceptance/test_a007_restart_resilience.py` | PASS | docs/test-records/20260805-1152, -1603, -1620 | OK |

### 4.3 画面と画面遷移(REQ-SCREEN / REQ-TRANS)

| 仕様ID/項目 | 仕様内容 | 対応するテスト計画 | 対応するテスト指示 | 対応するテスト実装/実行コマンド | 最新結果 | 証跡 | 状態 |
|---|---|---|---|---|---|---|---|
| REQ-SCREEN-001 | S01 ログイン画面 | P006 3.1 V-F-10 / 4.1 | P008 T003、P009 A001 | `client/tests/test_s01_login.js`、`client/tests/integration/test_t003_s01_login_api.js` | PASS | docs/test-records/20260805-1152, -1620 | OK |
| REQ-SCREEN-002 | S02 予約カレンダー画面(トップ) | P006 3.1 V-F-10 / 3.2 V-N-01 | P008 T015 / T016、P009 A001 / A005 / A008 | `client/tests/test_s02_calendar.js`、`test_grid.js`、`client/tests/integration/test_t015_calendar_grid_api.js`、`client/tests/acceptance/test_a008_calendar_render.js` | PASS | docs/test-records/20260805-1226, -1603, -1620 | OK |
| REQ-SCREEN-003 | S03 予約作成画面 | P006 3.1 V-F-10 / V-F-14 | P008 T016、P009 A001 / A004 | `client/tests/test_s03_reservation_new.js`、`test_reservation_form.js`、`client/tests/integration/test_t016_create_flow.js` | PASS(T016 は F001 で期待値修正後PASS) | docs/test-records/20260805-1620 | OK |
| REQ-SCREEN-004 | S04 予約詳細・編集画面 | P006 3.1 V-F-10 | P008 T017、P009 A001 | `client/tests/test_s04_reservation_detail.js`、`client/tests/integration/test_t017_detail_edit_cancel.js` | PASS | docs/test-records/20260805-1226, -1620 | OK |
| REQ-SCREEN-005 | S05 マイ予約一覧画面 | P006 3.1 V-F-10 | P008 T018、P009 A005 | `client/tests/test_s05_my_reservations.js`、`client/tests/integration/test_t018_my_reservations_filter.js`、`client/tests/acceptance/test_a005_consistency.js` | PASS | docs/test-records/20260805-1226, -1603, -1620 | OK |
| REQ-SCREEN-006 | S06 会議室管理画面(管理者用) | P006 3.1 V-F-10 / 3.2 V-N-05 | P008 T010、P009 A003 / A004 | `client/tests/test_s06_room_admin.js`、`client/tests/integration/test_t010_master_screens_api.js`、`client/tests/acceptance/test_a003_role_separation_ui.js` | PASS | docs/test-records/20260805-1152, -1603, -1620 | OK |
| REQ-SCREEN-007 | S07 ユーザー管理画面(管理者用) | P006 3.1 V-F-10 | P008 T010、P009 A003 | `client/tests/test_s07_user_admin.js`、`client/tests/integration/test_t010_master_screens_api.js` | PASS | 同上 | OK |
| REQ-TRANS-001 | 画面遷移図のとおりに遷移すること | P006 3.1 V-F-11 | P008 T016、P009 A001 / A006 / A011 | `client/tests/test_router.js`、`client/tests/integration/test_t016_create_flow.js`、`client/tests/acceptance/test_a001_business_flow.js`、`test_a006_session_ui.js` | PASS | docs/test-records/20260805-1620 | OK |

### 4.4 各画面の入出力項目(REQ-ITEM)

| 仕様ID/項目 | 仕様内容 | 対応するテスト計画 | 対応するテスト指示 | 対応するテスト実装/実行コマンド | 最新結果 | 証跡 | 状態 |
|---|---|---|---|---|---|---|---|
| REQ-ITEM-001 | S01: ユーザーID・パスワード・エラーメッセージ | P006 3.1 V-F-01 / 4.1 | P008 T003 | `client/tests/test_validation.js`、`client/tests/test_s01_login.js`、`server/tests/test_auth_handlers.py` | PASS | docs/test-records/20260805-1152, -1620 | OK |
| REQ-ITEM-002 | S02: 表示週・会議室フィルタ・グリッド・予約サマリ(参加予定人数は非表示) | P006 3.1 V-F-10 / 4.1 | P008 T015 | `client/tests/test_grid.js`、`test_s02_calendar.js`、`client/tests/integration/test_t015_calendar_grid_api.js` | PASS | docs/test-records/20260805-1226, -1620 | OK |
| REQ-ITEM-003 | S03: 会議室・日付・時刻・終日・件名・参加者・参加予定人数・備考・各エラー領域 | P006 3.1 V-F-01 / V-F-09 / V-F-14 | P008 T009 / T013 / T016 | `client/tests/test_reservation_form.js`、`test_s03_reservation_new.js`、`server/tests/integration/test_t009_attendee_candidates_scope.py`、`test_t013_capacity_and_authz.py` | PASS | docs/test-records/20260805-1152, -1226, -1620 | OK |
| REQ-ITEM-004 | S04: 予約内容表示・編集項目・取消ボタン(本人/管理者のみ) | P006 3.1 V-F-05 / V-F-10 | P008 T017、P009 A003 | `client/tests/test_s04_reservation_detail.js`、`client/tests/integration/test_t017_detail_edit_cancel.js`、`server/tests/acceptance/test_a003_role_separation.py` | PASS | docs/test-records/20260805-1226, -1603, -1620 | OK |
| REQ-ITEM-005 | S05: 期間フィルタ・予約一覧(日付/会議室/時間帯/件名) | P006 3.1 V-F-10 | P008 T018、P009 A005 | `client/tests/test_s05_my_reservations.js`、`client/tests/integration/test_t018_my_reservations_filter.js` | PASS | docs/test-records/20260805-1226, -1620 | OK |
| REQ-ITEM-006 | S06: 会議室一覧(説明文含む)・入力項目・論理削除 | P006 3.1 V-F-01 / V-F-13 | P008 T005 / T006 / T010 / T014 | `client/tests/test_s06_room_admin.js`、`server/tests/integration/test_t005_room_crud.py`、`test_t006_room_name_uniqueness.py`、`test_t014_room_deactivate_blocked.py` | PASS | docs/test-records/20260805-1152, -1226, -1620 | OK |
| REQ-ITEM-007 | S07: ユーザー一覧・入力項目(パスワード欄含む)・論理削除 | P006 3.1 V-F-01 / V-F-13 | P008 T008 / T010 | `client/tests/test_s07_user_admin.js`、`server/tests/integration/test_t008_user_crud_last_admin.py` | PASS | docs/test-records/20260805-1152, -1620 | OK |
| REQ-ITEM-008 ※CR-001 | 予約のオンライン会議URL(S03/S04で任意入力・500文字以内・`http(s)://` 始まり・S04でリンク表示・S02では非表示) | P006 3.1 **V-F-16** | P008 **T019** / T016 / T017、P009 A001 | `server/tests/test_reservation_write_handlers.py`(MeetingUrlApiTest)、`server/tests/test_reservation_read_handlers.py`、`server/tests/test_reservations_repo.py`、`server/tests/test_db_migration.py`、`server/tests/integration/test_t019_meeting_url.py`、`client/tests/test_validation.js`、`test_reservation_form.js`、`test_s03_reservation_new.js`、`test_s04_reservation_detail.js`、`client/tests/integration/test_t016_create_flow.js`、`test_t017_detail_edit_cancel.js`、`client/tests/acceptance/test_a001_business_flow.js` | PASS | docs/test-records/20260805-1723, -1731 | OK |

### 4.5 バックエンドAPI(REQ-API)

| 仕様ID/項目 | 仕様内容 | 対応するテスト計画 | 対応するテスト指示 | 対応するテスト実装/実行コマンド | 最新結果 | 証跡 | 状態 |
|---|---|---|---|---|---|---|---|
| REQ-API-001 | POST `/api/auth/login` | P006 3.1 V-F-02 / 3.2 V-N-04 | P008 T001 / T002 / T003 | `server/tests/test_auth_handlers.py`、`server/tests/integration/test_t001_login_session.py` | PASS | docs/test-records/20260805-1152, -1620 | OK |
| REQ-API-002 | POST `/api/auth/logout` | P006 3.1 V-F-04 | P008 T001、P009 A006 | `server/tests/test_auth_handlers.py`、`server/tests/acceptance/test_a006_session_lifecycle.py` | PASS | docs/test-records/20260805-1152, -1603, -1620 | OK |
| REQ-API-003 | GET `/api/me` | P006 3.1 V-F-02 / V-F-04 | P008 T001 / T002 | `server/tests/test_auth_handlers.py`、`server/tests/integration/test_t001_login_session.py` | PASS | 同上 | OK |
| REQ-API-004 | GET `/api/rooms` | P006 3.1 V-F-02 / V-F-13 | P008 T005 / T015 | `server/tests/test_room_handlers.py`、`server/tests/integration/test_t005_room_crud.py` | PASS | docs/test-records/20260805-1152, -1620 | OK |
| REQ-API-005 | POST `/api/rooms`(管理者のみ) | P006 3.1 V-F-02 / V-F-05 / V-F-08 | P008 T005 / T006 / T007 | `server/tests/test_room_handlers.py`、`test_room_service.py`、`server/tests/integration/test_t006_room_name_uniqueness.py`、`test_t007_admin_authz.py` | PASS | 同上 | OK |
| REQ-API-006 | PUT `/api/rooms/{room_id}`(管理者のみ) | 同上 | P008 T005 / T007、P009 A004 | `server/tests/test_room_handlers.py`、`server/tests/acceptance/test_a004_room_master_impact.py` | PASS | docs/test-records/20260805-1152, -1603, -1620 | OK |
| REQ-API-007 | DELETE `/api/rooms/{room_id}`(論理削除・管理者のみ) | P006 3.1 V-F-08 / V-F-13 | P008 T005 / T007 / T014、P009 A004 | `server/tests/integration/test_t014_room_deactivate_blocked.py`、`server/tests/acceptance/test_a004_room_master_impact.py` | PASS | 同上 | OK |
| REQ-API-008 | GET `/api/reservations`(期間・会議室指定) | P006 3.1 V-F-02 / 3.2 V-N-01 | P008 T011 / T015、P009 A008 | `server/tests/test_reservation_read_handlers.py`、`client/tests/integration/test_t015_calendar_grid_api.js`、`server/tests/acceptance/test_a008_calendar_performance.py` | PASS | docs/test-records/20260805-1226, -1603, -1620 | OK |
| REQ-API-009 | GET `/api/reservations/mine` | P006 3.1 V-F-02 | P008 T011 / T018、P009 A005 | `server/tests/test_reservation_read_handlers.py`、`client/tests/integration/test_t018_my_reservations_filter.js` | PASS | 同上 | OK |
| REQ-API-010 | GET `/api/reservations/{reservation_id}` | P006 3.1 V-F-02 / V-F-06 | P008 T011 / T017 | `server/tests/test_reservation_read_handlers.py`、`client/tests/integration/test_t017_detail_edit_cancel.js` | PASS | 同上 | OK |
| REQ-API-011 | POST `/api/reservations`(重複チェックあり) | P006 3.1 V-F-07 / V-F-09 / 4.1(重点) | P008 T011 / T012 / T013 / T016、P009 A002 | `server/tests/test_reservation_service.py`(境界値+2スレッド同時)、`server/tests/integration/test_t012_reservation_conflict.py`、`server/tests/acceptance/test_a002_double_booking.py` | PASS | docs/test-records/20260805-1226, -1603, -1620 | OK |
| REQ-API-012 | PUT `/api/reservations/{reservation_id}`(重複チェックあり) | 同上 | P008 T011 / T012 / T017、P009 A002 | `server/tests/test_reservation_write_handlers.py`、`server/tests/integration/test_t011_reservation_lifecycle.py` | PASS | 同上 | OK |
| REQ-API-013 | DELETE `/api/reservations/{reservation_id}` | P006 3.1 V-F-05 | P008 T011 / T017、P009 A001 / A003 | `server/tests/test_reservation_write_handlers.py`、`client/tests/acceptance/test_a001_business_flow.js` | PASS | 同上 | OK |
| REQ-API-014 | GET `/api/users`(管理者のみ / `scope=attendee_candidates`) | P006 3.1 V-F-05 | P008 T007 / T009 / T010 | `server/tests/test_user_handlers.py`、`server/tests/integration/test_t009_attendee_candidates_scope.py` | PASS | docs/test-records/20260805-1152, -1620 | OK |
| REQ-API-015 | POST `/api/users`(管理者のみ) | P006 3.1 V-F-01 / V-F-05 | P008 T007 / T008 / T010 | `server/tests/test_user_handlers.py`、`test_user_service.py`、`server/tests/integration/test_t008_user_crud_last_admin.py` | PASS | 同上 | OK |
| REQ-API-016 | PUT `/api/users/{user_id}`(管理者のみ) | P006 3.1 V-F-05 / V-F-08 | P008 T008 / T010、P009 A006 | `server/tests/test_user_service.py`、`server/tests/acceptance/test_a006_session_lifecycle.py` | PASS | docs/test-records/20260805-1152, -1603, -1620 | OK |
| REQ-API-017 | DELETE `/api/users/{user_id}`(論理削除・管理者のみ) | P006 3.1 V-F-08 / V-F-13 | P008 T008、P009 A006 | `server/tests/test_user_service.py`、`server/tests/integration/test_t008_user_crud_last_admin.py` | PASS | 同上 | OK |

### 4.6 非機能要件(REQ-NFR)

| 仕様ID/項目 | 仕様内容 | 対応するテスト計画 | 対応するテスト指示 | 対応するテスト実装/実行コマンド | 最新結果 | 証跡 | 状態 |
|---|---|---|---|---|---|---|---|
| REQ-NFR-001 | 性能: カレンダー表示3秒以内 | P006 3.2 V-N-01 | P009 A008 | `server/tests/acceptance/test_a008_calendar_performance.py`、`client/tests/acceptance/test_a008_calendar_render.js` | PASS | docs/test-records/20260805-1603, -1620 | OK |
| REQ-NFR-002 (a) | 可用性の前提: 停止・再起動しても正常起動しデータが残ること | P006 3.2 V-N-08 / 3.3 V-O-01 / V-O-02 | P008 T004、P009 A007 | `server/tests/integration/test_t004_restart_migration.py`、`server/tests/acceptance/test_a007_restart_resilience.py`、および本フェーズの3回連続起動確認(1.3) | PASS | docs/test-records/20260805-1603, -1620 / 本書1.3 | OK |
| REQ-NFR-002 (b) | 可用性: 平日日中99%以上 | (P003 8章によりP302へ委譲) | (なし) | `docker-compose.yml` の `restart: unless-stopped` + `HEALTHCHECK` | **未実行** | 本書3.2・9章 | **BLOCKED**(自動再起動・ヘルスチェックの設定は整備したが、Dockerデーモンが無く動作確認できていない。可用性の実測は運用監視の領域) |
| REQ-NFR-003 (a) | セキュリティ: パスワードのハッシュ化・管理者機能の権限チェック | P006 3.2 V-N-03 / V-N-05 / V-N-06 | P009 A003 / A010 | `server/tests/test_security.py`、`server/tests/acceptance/test_a010_security.py`、`test_a003_role_separation.py` | PASS | docs/test-records/20260805-1603, -1620 | OK |
| REQ-NFR-003 (b) | セキュリティ: 通信は全てHTTPS | (P003 8章によりP302へ委譲) | P009 A010(Cookie `Secure` 属性の確認まで) | `server/tests/acceptance/test_a010_security.py`(`Secure` 属性はPASS)/ TLS終端は `deploy/nginx.conf.example` + `docker compose --profile tls up` | Cookie属性は PASS / **TLS終端は未実行** | docs/test-records/20260805-1603 / 本書9章 | **BLOCKED**(リバースプロキシ資産は整備したが未検証。証明書の入手・更新手順は人間確認事項。10章) |
| REQ-NFR-004 | スケーラビリティ: 単一サーバー構成で十分 | P006 3.2 V-N-02 | P009 A009 | `server/tests/acceptance/test_a009_concurrent_load.py`、`docker-compose.yml`(`app` 単一サービス・`--workers 1`) | PASS | docs/test-records/20260805-1603, -1620 | OK |
| REQ-NFR-005 | 想定同時利用者数: 同時30接続 | P006 3.2 V-N-02 | P009 A009 | `server/tests/acceptance/test_a009_concurrent_load.py`(30スレッド同時: 参照90本・更新30本で5xxと `DB_LOCK_TIMEOUT` が0件) | PASS | 同上 | OK |
| REQ-NFR-006 (a) | ログ出力: 標準出力に1リクエスト1行のJSON | P006 3.2 V-N-07 | P009 A012 | `server/tests/test_errors.py`、`server/tests/acceptance/test_a012_operator_acceptance.py` | PASS | docs/test-records/20260805-1603, -1620 | OK |
| REQ-NFR-006 (b) | ログの監視方法(集約先・アラート) | (P003 8章によりP302へ委譲) | (なし) | `docker-compose.yml` の `logging` 設定(ローテーション上限のみ) | **未実行** | 本書10章 | **NO_TEST_PLAN**(転送先・監視基盤が実行環境側で未確定。10章の人間確認事項) |

### 4.7 テスト方針(REQ-TEST)

| 仕様ID/項目 | 仕様内容 | 対応するテスト計画 | 対応するテスト指示 | 対応するテスト実装/実行コマンド | 最新結果 | 証跡 | 状態 |
|---|---|---|---|---|---|---|---|
| REQ-TEST-001 | 単体テストは重複チェックを重点的にカバー | P006 4.1(境界値: 完全一致/部分重複/内包/被内包/境界接触/別室/別日) | P007 U003-T1 / U003-T2 | `server/tests/test_reservation_service.py`、`test_reservations_repo.py` | PASS | 本書9章(240件OK) | OK |
| REQ-TEST-002 | 結合テストで全画面の主要操作をシナリオ検証 | P006 4.2 | P008 T003 / T010 / T015〜T018 | `client/tests/integration/*.js`(41件) | PASS | 本書9章 | OK |
| REQ-TEST-003 | 権限まわりを結合テストで必ず確認 | P006 3.1 V-F-05 / 4.2 | P008 T007 / T013 / T017、P009 A003 | `server/tests/integration/test_t007_admin_authz.py`、`server/tests/acceptance/test_a003_role_separation.py`、`client/tests/acceptance/test_a003_role_separation_ui.js` | PASS | docs/test-records/20260805-1603, -1620 | OK |

### 4.8 対応表の集計

| 状態 | 件数 | 内訳 |
| --- | --- | --- |
| OK | **45**(※CR-001 で REQ-ITEM-008 を追加) | 機能要求はすべてOK |
| BLOCKED | **3** | REQ-PRE-002(クラウドデプロイ)/ REQ-NFR-002(b)(可用性)/ REQ-NFR-003(b)(HTTPS)。いずれも**Dockerデーモンが無く配布資産の実機確認ができていない**ことが原因 |
| NO_TEST_PLAN | **4** | REQ-PRE-004(検証対象の振る舞いを持たない)/ REQ-TECH-001・002(ADRによる意図的な代替)/ REQ-NFR-006(b)(監視基盤が実行環境側で未確定) |
| NO_TEST_CASE / NO_TEST_IMPL / NOT_RUN / FAILED / SPEC_CONFLICT / UNKNOWN | **0** | - |

* 行数は52行(※CR-001 で REQ-ITEM-008 を追加。REQ-NFR-002・003・006 を前提の異なる (a)/(b) に分けたため、要求ID49件より3行多い)。
* **FAILED は0件**である。BLOCKED / NO_TEST_PLAN は隠さず上表に残した。
* 状態区分についての注記: `SKILL-P302-deliver.md` の状態区分には「要求が意図的に別方式へ代替されている(ADRで決定済み)」を表す区分がないため、REQ-TECH-001・002 は `NO_TEST_PLAN` とした。同じ問題は `docs/P004-traceability-matrix.md` 3章でも報告されている(P004の `OK`/`PARTIAL`/`MISSING` にも該当区分がない)。★FIXME★ この分類の妥当性は人間が確認すること。

## 5. バージョン情報とビルド履歴

### 5.1 バージョン情報の所在

| 所在 | 値 | 位置づけ |
| --- | --- | --- |
| `./VERSION` | **1.1.0**(※CR-001 で 1.0.0 → 1.1.0) | **配布単位のバージョン(正)**。本フェーズで新規作成し、CR-001(機能追加)で minor を上げた |
| `client/package.json` の `version` | 1.1.0 | `VERSION` と一致 |
| `server/pyproject.toml` の `version` | **0.1.0** | **`VERSION` と不一致**(10章の人間確認事項) |
| `docker-compose.yml` の `image` | `meeting-room:1.1.0` | `VERSION` に合わせた |
| `Dockerfile` | `COPY VERSION ./VERSION` でイメージ内 `/app/VERSION` に同梱 | コンテナ内から確認できる |

* ※CR-001 によるバージョンの扱い: CR-001 は**後方互換の機能追加**(任意項目の追加。既存APIの必須項目・既存データの意味を変えない)であるため、セマンティックバージョニングに従って minor を上げ `1.1.0` とした。★FIXME★ **バージョンを上げる基準(CR対応のたびに上げるのか、どの桁を上げるのか)は本SKILLに規定がない**ため、Agentの判断でセマンティックバージョニングを適用した。運用の方針は人間が確定すること(10章にも記載)。
* 優先順位の適用: 言語標準のバージョン定義(`package.json` / `pyproject.toml`)は既に存在するが**両者の値が食い違っている**ため、リポジトリ全体=配布単位のバージョンを表す `VERSION` を新規作成し、これを正とした。既存の値は書き換えていない(バージョンの捏造・独断の付け替えを避けるため)。方針の確定は10章の人間確認事項とする。

### 5.2 実行モジュールからのバージョン確認

| 手段 | 可否 | 備考 |
| --- | --- | --- |
| `GET /version` | **不可** | エンドポイントが存在しない |
| `GET /health` | **不可** | エンドポイントが存在しない(コンテナの `HEALTHCHECK` は認証不要の `GET /` = 200 で代替した) |
| アプリ起動ログ | **不可** | 起動時にバージョンを出力していない |
| 画面フッター | **不可** | `client/index.html` にバージョン表示がない |
| `docker compose exec app cat /app/VERSION` | **可** | イメージに `VERSION` を同梱しているため |
| `docker image inspect meeting-room:1.1.0` | **可** | イメージタグから確認できる |

* API・画面からのバージョン確認手段は**未実装**である。`GET /version` の追加は `docs/P002-frontend-spec.md` 第5章(API契約の単一の正)に新しいエンドポイントを追加することになり、**仕様変更に該当する**ため本フェーズでは実装しない(`SKILL-P302-deliver.md`「このフェーズでは仕様変更を行わない」)。**CRの起票候補**として10章に記載する。

### 5.3 ビルド履歴

* `./BUILD_HISTORY.md` を新規作成した。B-0001〜B-0006 として、実際に実行したビルド・テストとその結果のみを記録している。
* `Commit` 列はすべて `未取得`(本リポジトリはGit管理下にない。`git status` → `fatal: not a git repository`)。
* `docker compose build` / `docker compose up` の行は **`未実行`** と明記している。

## 6. 配布資産一覧

### 6.1 本フェーズで新規作成した資産

| パス | 内容 | 実機検証 |
| --- | --- | --- |
| `Dockerfile` | 単一イメージ。`python:3.11-slim` に `server/requirements.txt` を入れ、`/app/server` と `/app/client` を**並べて**配置し、`uvicorn ... --workers 1` で起動。`HEALTHCHECK` は `GET /`(認証不要) | **未実施**(9章) |
| `docker-compose.yml` | `app` 1サービス + 名前付きボリューム `app-data` + `restart: unless-stopped` + `logging` ローテーション。`tls` プロファイルに TLS終端 `proxy`(nginx) | **未実施** |
| `.env.example` | `DB_PATH` / `SESSION_IDLE_SECONDS` / `SESSION_ABSOLUTE_SECONDS` / `INITIAL_ADMIN_ID` / `INITIAL_ADMIN_PASSWORD` / `APP_PORT` | - |
| `deploy/nginx.conf.example` | TLS終端 + HTTP→HTTPSリダイレクト。**upstreamをパスで分けず全パスを `app` に渡し同一オリジンを維持** | **未実施** |
| `.dockerignore` | `__pycache__` / `*.db` / `docs/` / `.env` / 証明書などを除外 | - |
| `VERSION` | `1.1.0`(※CR-001) | - |
| `BUILD_HISTORY.md` | ビルド・テスト履歴(B-0001〜B-0006 + docker行は未実行) | - |
| `README.md`(リポジトリ直下) | 最短の起動手順、Docker未検証の注意、`INDEX.md` / 本書への入口 | - |
| `server/requirements.txt` | `starlette==1.0.0` / `pydantic==2.13.3` / `uvicorn==0.46.0`(検証環境の実インストール版) | - |

### 6.2 本フェーズで更新した既存資産

| パス | 変更内容 | 理由 |
| --- | --- | --- |
| `server/pyproject.toml` | `dependencies = []` → `starlette` / `pydantic` / `uvicorn` を宣言。`description` を実態に合わせた | **実態と食い違っていた。** `main.py`・`handlers/*` は starlette を、`schemas.py` は pydantic を import しており、外部依存が0件ではない。この宣言がないとコンテナイメージに依存パッケージが入らず起動できない。バージョン変更は行っていない |
| `server/README.md` | 空ファイルだったため内容を記述(依存・起動・環境変数・テスト・運用注意) | `server/INDEX.md` に「内容はP302で整備する」と明記されていた |
| `client/package.json` | `"test": "node --test tests"` → `"node --test 'tests/*.js'"`。`test:integration` / `test:acceptance` を追加 | **既存の値は実行できない。** ディレクトリを渡す形はモジュール解決エラーになり、Nodeの既定パターンは `test_*.js` に一致しない(`docs/P201-review-report.md` 3章の★FIXME★、`docs/P007-impl-direction.md` 5章 #6)。`npm test` が126件PASSすることを実測確認した |
| `./INDEX.md` | 「2. 配布・実行資産」節を本フェーズの成果物に合わせて確定 | P301作成時点では本フェーズの資産が未作成だった |
| `docs/.inprogress` | `P301` → `P302` → **削除**(本フェーズ完了時) | `SKILL.md`「最後のフェーズ(P302)が完了した場合は、`docs/.inprogress` を削除する」 |

### 6.3 既存の配布資産(変更していないもの)

`server/.python-version`(3.11)、`server/.gitignore`、`server/migrations/*.sql`(3件)、`client/index.html`、`server/INDEX.md`、`client/INDEX.md`。

### 6.4 整備対象チェック

| 確認・整備対象 | 状態 |
| --- | --- |
| `Dockerfile` | 作成済み(未ビルド) |
| `docker-compose.yml` | 作成済み(未起動) |
| `.env.example` | 作成済み |
| 起動手順 | 本書7章 + `README.md` |
| 初期化スクリプト | **不要**(アプリ起動時にマイグレーション + 初期管理者シードを自動実行する。冪等性は1.3で実測確認済み) |
| DBマイグレーション手順 | 起動時自動。手動実行の手順は7章に記載 |
| ヘルスチェック | `HEALTHCHECK`(`GET /`)+ compose の `depends_on: service_healthy` |
| ログ出力先 | 標準出力(JSON1行)。compose の `json-file` ドライバでローテーション上限のみ設定。**転送先は未確定(10章)** |
| 永続ボリューム | 名前付きボリューム `app-data` → `/app/data` |
| ネットワーク設定 | compose の既定ネットワーク。`proxy` は同一ネットワーク内で `app:8000` に接続 |

## 7. 起動・実行手順

### 7.1 Docker Compose 起動手順(推奨)

> ⚠️ **以下の手順は実機で検証できていない**(検証環境にDockerデーモンが無い。9章)。初回実行時は各手順の結果を確認しながら進めること。

1. **前提ソフトウェアを確認する**
   ```bash
   docker --version          # 検証環境では 29.4.3 を確認
   docker compose version    # 検証環境では v5.1.3 を確認
   docker info               # ★デーモンが起動していること★(検証環境ではここで失敗した)
   ```
2. **`.env` を用意する**
   ```bash
   cp .env.example .env
   ```
3. **環境変数を設定する** — `.env` の `INITIAL_ADMIN_PASSWORD` を必ず変更する(既定値のままでは `docker compose` が起動を拒否するよう `?` 付きで定義してある)。必要なら `APP_PORT` も変更する。
4. **イメージをビルドする**
   ```bash
   docker compose build
   ```
5. **起動する**
   ```bash
   docker compose up -d
   ```
6. **ヘルスチェックを確認する**
   ```bash
   docker compose ps                     # app の STATUS が healthy になること
   docker compose logs -f app            # 起動ログとアクセスログ(JSON1行)を確認
   curl -i http://localhost:8000/        # 200 / Content-Type: text/html; charset=utf-8
   curl -i http://localhost:8000/src/main.js  # 200 / Content-Type: text/javascript
   ```
7. **初期データ・マイグレーションを確認する** — **手動実行は不要**。起動時に `migrations/*.sql` の未適用分の適用と、有効な管理者が0人の場合の初期管理者作成が自動で行われる。確認する場合:
   ```bash
   docker compose exec app python3 -c "import sqlite3,os;c=sqlite3.connect(os.environ['DB_PATH']);print([r[0] for r in c.execute('select version from schema_migrations')])"
   # → ['001-init.sql', '002-rooms.sql', '003-reservations.sql']
   ```
8. **ブラウザ・APIで動作確認する**
   ```bash
   curl -i -X POST http://localhost:8000/api/auth/login \
     -H 'Content-Type: application/json' \
     -d '{"user_id":"admin001","password":"<.env で設定した値>"}'
   # → 200 / Set-Cookie: sid=...; HttpOnly; SameSite=Lax; Secure; Path=/
   ```
   ブラウザで `http://localhost:8000/` を開き、初期管理者でログインする → S02カレンダーが表示される。
   **その後、S07ユーザー管理画面で初期管理者のパスワードを変更する。**

### 7.2 TLS(HTTPS)で公開する場合

**セッションCookieには `Secure` 属性が付く**(ADR-005 / `docs/P002-frontend-spec.md` 5.4)。ブラウザは `localhost` を例外的に安全なオリジンとして扱うため `http://localhost:8000/` ではログインできるが、**`localhost` 以外のホストに平文HTTPでアクセスするとCookieが保存・送出されず、ログインできない**(この性質は `server/tests/acceptance/support.py` の冒頭コメントにも記録されている)。本番相当の環境では必ずTLSを終端する。

1. 証明書と秘密鍵を `deploy/certs/server.crt` / `deploy/certs/server.key` に配置する(**取得・更新手順は未確定。10章**)。
2. `docker-compose.yml` の `app.ports` の公開をやめる(プロキシ経由のみに絞る)。
3. 起動する。
   ```bash
   docker compose --profile tls up -d
   curl -ik https://<ホスト名>/            # 200
   curl -i  http://<ホスト名>/             # 301 → https
   ```
* 実行環境のロードバランサ(ALB等)でTLSを終端する場合は、`proxy` サービスを使わず `app` の8000番をロードバランサの背後に置く。**その場合も、画面とAPIを同じホスト名・同じオリジンで公開すること**(1.2)。

### 7.3 Docker を使わない起動(開発・検証用。**この手順は実機で確認済み**)

```bash
pip install -r server/requirements.txt
cd server
PYTHONPATH=src DB_PATH=./data/app.db python3 -m uvicorn meeting_room.main:app --host 0.0.0.0 --port 8000
```

* `client/` が `server/` と同じ親ディレクトリに並んでいる必要がある(`main.py` の `CLIENT_DIR`)。
* 停止は `Ctrl-C`(または `SIGTERM`)。同じ `DB_PATH` に対して何度でも再起動できる(1.3で3回連続確認済み)。

### 7.4 バックアップ・リストア

* バックアップ対象は `app-data` ボリューム内の `app.db`(および同時に存在する `-wal` / `-shm`)。
  ```bash
  docker compose exec app python3 -c "import sqlite3,os;src=sqlite3.connect(os.environ['DB_PATH']);dst=sqlite3.connect('/app/data/backup.db');src.backup(dst);dst.close()"
  ```
* SQLiteのオンラインバックアップAPIを使う(ファイルの単純コピーはWALと不整合になりうる)。★FIXME★ バックアップの保管先・世代管理・リストア訓練の手順は運用要件として未確定であり、人間が確定すること(10章)。

### 7.5 既存環境のアップグレード手順(※CR-001。バージョン 1.0.0 → 1.1.0)

既に 1.0.0 で稼働している環境を 1.1.0 に上げる場合の手順。**スキーマ変更(`reservations.meeting_url` の追加)を含むため、手順1のバックアップを省略しないこと。**

1. **バックアップを取る**(第7.4節の手順)。SQLiteファイルの世代を1つ残す。
2. 新しいイメージをビルドする(`docker compose build`)。`docker-compose.yml` の `image` は `meeting-room:1.1.0`。
3. `docker compose up -d` で起動する。**マイグレーションはアプリケーション起動時に自動適用される**(ADR-009。`server/migrations/004-meeting-url.sql` が未適用のときだけ適用される)。手動でSQLを流す必要はない。
4. 起動ログにエラーが無いことを確認し、`GET /` が 200 を返すことを確認する。
5. 適用結果を確認する(任意):
   ```bash
   docker compose exec app python3 -c "import sqlite3,os;c=sqlite3.connect(os.environ['DB_PATH']);print([r[0] for r in c.execute('SELECT version FROM schema_migrations ORDER BY version')]);print([r[1] for r in c.execute('PRAGMA table_info(reservations)')])"
   ```
   `schema_migrations` に `004-meeting-url.sql` が含まれ、`reservations` に `meeting_url` 列があれば適用済み。
* **既存データへの影響**: `ALTER TABLE ... ADD COLUMN meeting_url TEXT NOT NULL DEFAULT ''` であるため、**既存の予約行は自動的に `meeting_url = ''`(未登録)になる**。データ移行スクリプトは不要で、既存予約の他の項目は変更されない。
* **切り戻し(ロールバック)**: ADR-009 のとおりダウンマイグレーションは持たない(★ACCEPTED★ 済みの制約)。1.0.0 に戻す必要が生じた場合は、**手順1のバックアップからDBファイルを復元**してから旧イメージを起動する。1.1.0 のDB(`meeting_url` 列あり)に対して 1.0.0 のアプリを起動した場合、列が増えているだけで `SELECT` は列名指定のため動作するが、**この組み合わせは検証していない**。★FIXME★ 旧バージョンへの切り戻しを保証する必要があるかは運用要件として未確定であり、人間が確定すること。
* 停止時間: マイグレーションは1文の `ALTER TABLE ADD COLUMN` のみで、SQLiteでは既存行の書き換えを伴わないため、通常は起動時間に含まれる程度である(予約件数に比例しない)。

## 8. テスト実行手順

| レベル | コマンド | 件数 | 合格条件 |
| --- | --- | --- | --- |
| バックエンド 単体+結合+受け入れ(一括) | `cd server && python3 -m unittest discover -s tests -t .` | **262**(※CR-001 で +22) | `OK`(FAIL・ERROR が0) |
| バックエンド 結合のみ | `cd server && python3 -m unittest discover -s tests/integration -t .` | **14**(※CR-001 で T019 を追加) | 同上 |
| バックエンド 受け入れのみ | `cd server && python3 -m unittest discover -s tests/acceptance -t .` | 14 | 同上 |
| フロントエンド 単体 | `cd client && npm test`(= `node --test 'tests/*.js'`) | **146**(※CR-001 で +20) | `fail 0` |
| フロントエンド 結合 | `cd client && npm run test:integration` | **46**(※CR-001 で +5) | `fail 0` |
| フロントエンド 受け入れ | `cd client && npm run test:acceptance` | **32**(※CR-001 で +1) | `fail 0` |
| ビルド(構文)確認 | `cd server && python3 -m compileall -q src` / `cd client && node --check <src配下の全16ファイル>` | - | 終了コード0 |

* **注意**: `node --test tests` のようにディレクトリを渡す形は動作しない(モジュール解決エラー)。また Node の既定パターンは既存の `test_*.js` という命名に一致しない。必ず上記のグロブ指定(= `package.json` の scripts)を使う。
* テスト結果の格納先: `docs/test-records/YYYYMMDD-HHMM-test-record.md`。形式は `TEMPLATE-test-record.md`。
* 合格条件(`docs/P006-test-plan.md` 7章): 単体テストは全件PASS。結合・システム・受け入れテストも全件PASS。
* テストはホスト上で実行する(uvicornを別プロセスで起動する受け入れテストがあるため)。コンテナ内でのテスト実行は想定していない。
* 実サーバーを起動するテスト(結合・受け入れ)は空きポートを自動で確保し、DBは一時ディレクトリに作る。既存の `server/data/app.db` を壊さない。

## 9. 最終確認結果

### 9.1 本フェーズが実際に実行した確認(2026-08-05T16:33Z〜16:38Z)

| # | 実行した内容 | 結果 |
| --- | --- | --- |
| 1 | `cd server && python3 -m unittest discover -s tests -t .` | **Ran 240 tests / OK** |
| 2 | `cd client && node --test 'tests/*.js'` | **126 pass / 0 fail** |
| 3 | `cd client && node --test 'tests/integration/*.js'` | **41 pass / 0 fail** |
| 4 | `cd client && node --test 'tests/acceptance/test_*.js'` | **31 pass / 0 fail** |
| 5 | `cd server && python3 -m compileall -q src` | 終了コード **0** |
| 6 | `cd client && node --check`(`src` 配下の全16ファイル) | すべて終了コード **0** |
| 7 | `cd client && npm test`(`package.json` 修正後の再確認) | **126 pass / 0 fail** |
| 8 | **同一DBファイルに対する3回連続の起動・停止**(実行前チェック#8) | 3回すべて正常起動。`GET /` = 200 / `GET /src/main.js` = 200 / `POST /api/auth/login` = 200。`schema_migrations` 3行のまま・`users` 1件のまま(1.3) |
| 9 | **同一オリジン配信の確認**(実行前チェック#7) | 単一プロセスで `/`・`/src/main.js`・`/api/auth/login` のすべてが200。`client/` のみを別オリジンで配信すると `/api/me` が404になることも確認(1.2) |
| 10 | `docker compose config`(**デーモン不要の構文・変数展開の検証**) | 成功。`app` 1サービス + `app-data` ボリュームに展開されることを確認。`--profile tls` を付けると `app` / `proxy` の2サービスになることも確認 |
| 11 | `INITIAL_ADMIN_PASSWORD` 未設定時のガード | 期待どおり起動前に失敗する(`required variable INITIAL_ADMIN_PASSWORD is missing a value: INITIAL_ADMIN_PASSWORD を .env に設定してください`) |

* 合計 438件(バックエンド240 + フロントエンド126+41+31)のテストが**すべてPASS**。FAIL・ERROR・SKIP は0件。
* テスト結果は `docs/P201-review-report.md` 3章の記録と一致した(退行なし)。

#### 9.1.1 ※CR-001 反映後の再確認(2026-08-05T17:22Z〜17:32Z)

| # | 実行した内容 | 結果 |
| --- | --- | --- |
| 1 | `cd server && python3 -m unittest discover -s tests -t .` | **Ran 262 tests / OK** |
| 2 | `cd client && node --test 'tests/*.js'` | **146 pass / 0 fail** |
| 3 | `cd client && node --test 'tests/integration/*.js'` | **46 pass / 0 fail** |
| 4 | `cd client && node --test 'tests/acceptance/test_*.js'` | **32 pass / 0 fail** |
| 5 | `cd server && python3 -m compileall -q src` | 終了コード **0** |
| 6 | `cd client && node --check`(`src` 配下の全ファイル) | すべて終了コード **0** |
| 7 | **同一DBファイルに対する3回連続の起動・停止**(`004-meeting-url.sql` 追加後の再確認) | 3回すべて正常起動。`GET /` = 200。`schema_migrations` は **4行**のまま・`users` 1件のまま。`duplicate column name` なし(1.3) |
| 8 | `apply_migrations()` の2回連続実行(同一DBファイル) | 1回目 = 4件適用 / 2回目 = 0件適用。例外なし |

* 合計 **486件**(バックエンド262 + フロントエンド146+46+32)のテストが**すべてPASS**。FAIL・ERROR・SKIP は0件。
* テスト結果は `docs/P201-review-report.md` 8章(第3回)の記録と一致した(退行なし)。
* Docker に関する未確認事項(9.2)は CR-001 でも解消していない(検証環境にDockerデーモンが無い)。第7.5節のアップグレード手順も、**Docker を使わない実プロセスでの起動確認までは実施済み**だが、`docker compose` 経由では未確認である。

### 9.2 実機確認できていないこと(**「整備済み」と「動作確認済み」を区別する**)

| 項目 | 状態 | 理由 |
| --- | --- | --- |
| `docker compose build` | **未実行** | 検証環境にDockerデーモンが存在しない。`docker info` → `failed to connect to the docker API at unix:///var/run/docker.sock: dial unix /var/run/docker.sock: connect: no such file or directory`(Docker CLI 29.4.3 / Compose v5.1.3 は存在する) |
| `docker compose up -d` / `HEALTHCHECK` / `restart: unless-stopped` / ボリューム永続 | **未実行** | 同上 |
| `docker compose --profile tls up -d`(nginx TLS終端・HTTP→HTTPSリダイレクト) | **未実行** | 同上。加えて証明書が存在しない |
| `pip install -r server/requirements.txt` によるイメージ内の依存解決 | **未実行** | 検証環境は外部パッケージレジストリ(pypi.org)に到達できない(ADR-001 / ADR-002)。バージョン指定は**検証環境に実際にインストールされていた版**に合わせてあるが、`pip install` 自体が成功するかは未確認 |
| 実ブラウザでの目視確認(レイアウト、実クリック、エラーメッセージの表示位置) | **未実行**(A011 手順7 = NOT RUN) | ブラウザ自動化ツールを取得できない環境。★ACCEPTED★ ADR-001 / `docs/P006-test-plan.md` 1.1 で検討済みの受け入れ済み制約(10章) |
| 実ブラウザからの相対パスfetch経路(`index.html` を取得したオリジンに対する `/api/*` 呼び出し) | **未実行** | 上と同じ理由。ただし同一オリジンで両方が200を返すことはHTTPレベルで確認済み(1.2) |

**これらは「資産は整備したが動作確認していない」状態である。整備済み=動作確認済みではない。**

## 10. 未整備事項・人間による確認事項

### 10.1 リリース判定に影響する事項(最優先)

| # | 内容 | 種別 | 対応 |
| --- | --- | --- | --- |
| 1 | **Docker Compose のビルド・起動が実機未検証**(`docker compose build` / `up` / `HEALTHCHECK` / ボリューム永続 / `restart` ポリシー)。Dockerデーモンのある環境で1度通す必要がある | 実行手順の未確認 | Dockerデーモンが使える環境で7.1を実行し、結果を `BUILD_HISTORY.md` の `(docker)` 行に記入する |
| 2 | **イメージ内の依存パッケージ解決が未検証**。`server/requirements.txt` のピン(`starlette==1.0.0` / `pydantic==2.13.3` / `uvicorn==0.46.0`)は検証環境の実インストール版に合わせたが、`pip install` の成功は未確認 | 実行手順の未確認 | #1 と同時に確認する |
| 3 | **TLS終端の実体と証明書の入手・更新手順が未確定**。`deploy/nginx.conf.example` と `tls` プロファイルは用意したが、証明書は存在せず未検証。ADR-010 にも同じ★FIXME★がある(「TLS終端を外側に置く前提そのもの(リバースプロキシの実体、証明書の入手・更新手順)はP001に記載がなく、P302で人間の確認を得て確定する必要がある」) | 本番環境固有の値・ADRの前提が本環境で未実現 | 実行環境(ALB / nginx / 他)と証明書の運用主体を人間が確定する。**`localhost` 以外の平文HTTPではログインできない**(7.2)ため、TLSなしでの本番公開は不可 |

* ※CR-001 による追加(#1〜#3 に変化はない): 第7.5節の**既存環境のアップグレード手順(1.0.0 → 1.1.0)**は、実プロセス(ホスト上のuvicorn)での自動マイグレーション適用までは実測で確認済みだが、`docker compose` 経由の適用は #1 と同じ理由で未検証である。あわせて、**旧バージョン(1.0.0)への切り戻しを保証する必要があるか**は運用要件として未確定(★FIXME★ 7.5)。

### 10.2 ADRの決定は正しいがその前提が本実行環境で実現されていないもの

| # | 内容 | 根拠 |
| --- | --- | --- |
| 4 | **TLS終端コンポーネントが本検証環境に存在しない。** ADR-010 は「TLS終端はプロセスの外側」と決定しており決定自体は正しいが、前提となるリバースプロキシ/ロードバランサが検証環境にない。したがって Cookie の `Secure` 属性が実際に機能する経路を通した確認ができていない | ADR-010、`docs/P003-backend-spec.md` 8章、`docs/P201-review-report.md` 5章、`docs/P202-fix-plan/P202-fix-unresolved.md` 参考#3 |
| 5 | **プロセス監視・自動再起動の実体がない。** `restart: unless-stopped` と `HEALTHCHECK` を整備したが、Dockerデーモンが無いため機能確認ができていない。可用性99%(REQ-NFR-002)の測定手段も実行環境側にない | `docs/P003-backend-spec.md` 8章、`docs/P005-impl-plan.md` 4章 |
| 6 | **ログ集約先が未確定。** 標準出力へのJSON出力(V-N-07)はPASSしているが、CloudWatch Logs等への転送、エラーログのアラート条件・通知先は未確定。compose では `json-file` ドライバのローテーション上限(10MB×5)のみ設定した | ADR-010、`docs/P003-backend-spec.md` 8章 |

### 10.3 対応するテストがない仕様 / テストの制約

| # | 内容 | 状態 |
| --- | --- | --- |
| 7 | REQ-PRE-004(既存システム連携なし・外部カレンダー連携は対象外)に対応するテストがない | 検証対象となる振る舞いを持たない「〜しない」要求であり、P002 8章・P003 10章のスコープ確認で充足を確認している。テストの追加は不要と判断するが、判断の妥当性は人間が確認すること |
| 8 | REQ-TECH-001 / REQ-TECH-002(React 18 + TS + Vite / FastAPI)は ADR-001 / ADR-002 により意図的に代替されており、要求どおりの構成に対するテストは存在しない | ★FIXME★ 人間は「(a) 代替構成のまま進める」「(b) 外部レジストリに到達できる環境を用意し、指定技術で作り直す」のいずれかを確定すること(ADR-002 の★FIXME★と同一の論点)。(b) を選ぶ場合はCRを起票して Refactor に入る |
| 9 | **実ブラウザでのレイアウト崩れ・実クリックの反応・エラーメッセージの物理的な表示位置が未確認**(A011 手順7 = NOT RUN)。`docs/P009-acceptance-direction.md` 5章から本書への申し送り事項 | ★ACCEPTED★ ブラウザ自動化ツールを取得できない環境であり、ヘッドレスブラウザによるE2Eも検討したうえで導入不能と結論している(ADR-001、`docs/P006-test-plan.md` 1.1)。残る制約は実ブラウザ固有挙動の自動検証ができないことであり、**A011の合否判定基準(手順1〜6の完了でPASS)により A011 自体は PASS**。**未対処の不備ではないため、リリース判定を `NG` にする理由としては扱わない。**代わりに、リリース前に**人間が1度ブラウザで7画面を目視確認する**ことを推奨する(A011 手順7の手順書はそのまま使える) |
| 10 | 受け入れ結合テストは、ブラウザが `index.html` を取得したオリジンから相対パスでAPIを呼ぶ経路そのものを検証していない(HTTP直叩き、または画面モジュール+実サーバーの組み合わせで実行している) | #9 の目視確認と同時に、ブラウザの開発者ツールで `/api/*` が同一オリジンに飛んでいることを確認すると、1.2の判断を実経路でも裏づけられる |

### 10.4 仕様の未明示・所見(CR起票候補)

| # | 内容 | 起票候補 |
| --- | --- | --- |
| 11 | **実行モジュールからバージョンを確認する手段がない**(`GET /version` / `GET /health` / 起動ログ / 画面フッターのいずれも未実装)。現在は `docker compose exec app cat /app/VERSION` でのみ確認できる | **CR起票候補**。`GET /version`(または `GET /health`)の追加は `docs/P002-frontend-spec.md` 第5章のAPI契約への追加=仕様変更のため、本フェーズでは実装しない |
| 12 | **バージョン付けの方針が未確定。** `./VERSION` = 1.1.0 / `client/package.json` = 1.1.0 に対し `server/pyproject.toml` = **0.1.0** で食い違っている(※CR-001 で `VERSION` を 1.1.0 に上げた際も `pyproject.toml` は据え置いた)。あわせて **「CR対応のたびにどの桁を上げるか」という基準そのものが本SKILLに規定されていない**(P903/P302のいずれにも記載がない) | 人間が「リポジトリ単一バージョンに揃える」か「コンポーネント別に持つ」かを決める。前者なら `pyproject.toml` を `VERSION` と揃える(本フェーズでは推測でのバージョン付け替えを避けて据え置いた)。バージョン採番の基準も明文化すること |
| 13 | 会議室の収容人数を減らした後、既存予約(参加予定人数が新収容人数を超える)の**件名だけを変更する `PUT`** も 400 `CAPACITY_EXCEEDED` になる。この挙動は仕様に明示がない(A004 手順4の実測) | **CR起票候補**(仕様判断)。`docs/P009-acceptance-direction/A004-room-master-impact.md` の★FIXME★、`docs/P202-fix-plan/P202-fix-unresolved.md` 参考#1 |
| 14 | 401時に `api.js` は画面遷移とメッセージ設定の後に例外を再送出するため、呼び出し側が捕捉していない経路(S02の週送りなど)では未処理のPromise拒否が残る。`docs/P002-frontend-spec.md` 2.4 は遷移とメッセージのみを規定しており仕様違反ではない | **CR起票候補**(所見)。`docs/P202-fix-plan/P202-fix-unresolved.md` 参考#4 |
| 15 | テスト指示の記述の細部に読み替えが必要な箇所がある(A003 手順7 の「会議室1件」/ A007 手順8 の「WALファイルが残っている状態」)。実施時に読み替えて実行し、読み替え内容はテスト記録に明記済み(重大度「低」) | 文書整備。必要ならCR。`docs/P201-review-report.md` 5章、`docs/P202-fix-plan/P202-fix-unresolved.md` 参考#5 |
| 16 | `docs/P004-traceability-matrix.md` 5章の**過剰実装6件**(P001に対応要求のない仕様)のうち5件が「要求書に追加すべき」と判定されている(セッション切れ時の強制遷移、S07のパスワード欄、`scope=attendee_candidates`、予約が残る会議室の無効化拒否、最後の管理者の保護) | **CR起票候補**(要件定義への追記)。実装・テストは既にあり、不足しているのは `docs/P001-requirement.md` 側の記載である |
| 22 ※CR-001 | オンライン会議URLの仕様で、Agentの想定で補った未確定点が3つ残っている。(a)**大文字スキーム(`HTTP://`)を許容しない**(P007 U003-T5 の★FIXME★)、(b)**S04のリンクを別タブで開く**(`target="_blank"` / `rel="noopener noreferrer"`。P002 3.4 の★FIXME★)、(c)**未登録時の表示は「-」**(CR-001 の★FIXME★)。いずれも CR-001 に指定がなかったため、既存項目の規約に合わせて決めた | 人間が (a)〜(c) を確認する。変更が必要なら新しいCRとして起票する(ADR-011 の備考にも同じ★FIXME★を記載済み) |

### 10.5 運用・環境固有の未確定事項

| # | 内容 |
| --- | --- |
| 17 | **初期管理者パスワード。** `.env.example` は `CHANGE_ME_BEFORE_DEPLOY` としており、`docker-compose.yml` は未設定時に起動を拒否する。実際の値の決定と初回ログイン後の変更は人間が行う |
| 18 | **バックアップ・リストアの運用手順が未確定**(保管先・世代管理・リストア訓練)。7.4にコマンド例のみ記載した★FIXME★ |
| 19 | **コンテナをroot以外のユーザーで実行するかが未確定。** 現在の `Dockerfile` は既定(root)で実行する。非rootに変更するにはボリュームの所有者調整が必要で、Docker未検証の環境で入れると起動失敗の原因になりうるため本フェーズでは変更しなかった。セキュリティ強化として人間が判断すること |
| 20 | **uvicornの接続上限**を明示設定していない(既定のまま)。同時30接続(REQ-NFR-005)に対しては A009(30スレッド同時)で5xxが0件であることを実測しているため既定で足りると判断した。想定を超える負荷をかける場合は `--limit-concurrency` の設定を人間が判断すること |
| 21 | **Gitリポジトリになっていない。** ビルド履歴のコミット追跡ができない(`BUILD_HISTORY.md` の `Commit` 列がすべて `未取得`)。納品前にVCS管理下に置くことを推奨する |
| 22 | `server/INDEX.md` の一部の記述が Reviewer Loop 以前の状態のまま残っている(`tests/integration/test_t016_create_flow.js` を「**手順7がFAIL**」と記述、など)。実際には F001 で解消済みでT016はPASS。`{ソースツリー}/INDEX.md` を更新するフェーズ(P104)は Reviewer Loop(P201〜P205)より前に実行されるため、ループ内での修正がINDEXに反映されない。P301は「ソースツリー自体は操作しない」と定められているため本フェーズでも書き換えていない。**INDEXの記述が古いだけで実装・テストには影響しない**が、次に Refactor(P903)でP104を再実行する際に更新されることを確認すること |

## 11. リリース判定

### 11.1 判定

**保留**

### 11.2 根拠

`保留` の定義は「軽微な未整備事項があるが、人間判断でリリース可否を決められる」である。次の理由により `OK` ではなく `保留` とした。

1. **`SKILL-P302-deliver.md` の明示規定に該当する。** 「実行環境にDocker CLIはあるがデーモンが起動していない場合(…)この場合、リリース判定は原則として `保留` とする」。本環境はまさにこの状態である(Docker CLI 29.4.3 / Compose v5.1.3 は存在するが `/var/run/docker.sock` が無い)。Dockerfile / docker-compose.yml / nginx設定例は通常どおり整備したが、**ビルド・起動を1度も実行していない**。
2. 配布トポロジー(1.2)・起動処理の冪等性(1.3。※CR-001 の `004-meeting-url.sql` 追加後も再確認済み)・全**486**件のテスト(9.1.1)は**実測で確認済み**であり、`NG` の要件(テスト失敗・仕様矛盾・配布不能)には該当しない。
   * ※CR-001 反映後: 結合テスト**19件**・受け入れ結合テスト12件・単体すべてPASS(合計486件。9.1.1)。FAIL 0件。
   * 未解決障害 0件(`docs/P202-fix-plan/P202-fix-unresolved.md` = ALL_RESOLVED)。
   * 仕様とテストの対応表(4章)に `FAILED` / `SPEC_CONFLICT` / `NOT_RUN` は0件。
3. 対応表の `BLOCKED` 3件(REQ-PRE-002 / REQ-NFR-002(b) / REQ-NFR-003(b))は、いずれも**同一原因=Dockerデーモン不在による配布資産の未検証**であり、アプリケーションの欠陥ではない。10.1 の #1〜#3 を解消すれば `OK` に転じる。
4. **A011 手順7(実ブラウザ目視確認)の NOT RUN は、`保留` の理由に数えていない。** これは ADR-001・`docs/P006-test-plan.md` 1.1 で★ACCEPTED★として検討済み・判断済みの制約であり(ヘッドレスブラウザも代替案として検討のうえ導入不能と結論)、A011 自身の合否判定基準が「手順1〜6の完了でPASS」と定めているため、テストIDとしての A011 は PASS である。未対処の不備として再度リリースブロッカーに数えることはしない(`SKILL.md`「★ACCEPTED★ が付いた内容は、既知であり、かつ既に判断済みである。…再度指摘しなくてよい」)。ただし人間の目視確認は10.3 #9のとおり推奨する。
5. 同様に、REQ-TECH-001 / 002 の技術要求の逸脱(ADR-001 / ADR-002)も `NG` の理由には数えていない。★FIXME★ 付きで人間の確認対象として明示されており(10.3 #8)、判断は人間に委ねる。

### 11.3 `OK` にするために必要なこと(受け入れ条件)

| # | 必要な作業 | 完了の判定 |
| --- | --- | --- |
| 1 | Dockerデーモンのある環境で 7.1 の手順1〜8を実行する | `docker compose ps` で `app` が `healthy`、`curl http://<host>:8000/` が200、初期管理者でログインできる |
| 2 | `docker compose restart` 後も正常に起動することを確認する | 再起動後も `healthy` になり、既存の予約・ユーザーが参照できる(1.3のホスト上での結果と一致すること) |
| 3 | TLS終端の実体と証明書の運用を確定し、HTTPSでログインできることを確認する | `https://<host>/` でログイン成功、`http://<host>/` が301 |
| 4 | 結果を `BUILD_HISTORY.md` の `(docker)` 行に記入する | `未実行` が実測値に置き換わる |
| 5 | (推奨)人間がブラウザで7画面を目視確認する(A011 手順7の手順書を使う) | レイアウト崩れ・クリック不能箇所がない |

* 上記1〜4が完了すれば、4章の `BLOCKED` 3件は解消し、リリース判定は `OK` に更新できる。
* 10.4 のCR起票候補(#11〜#16)は、リリースを止める性質のものではない。納品後に `docs/P901-cr-direction/CR-NNN.md` として起票し、Refactor(P901〜P905)で扱う。
