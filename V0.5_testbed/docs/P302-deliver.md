# 成果物まとめ

> 本書は `spec-driven-dev` Skill フェーズP302の成果物です。

## 1. 概要

会議室予約システム(社内向けWebアプリケーション)の設計〜実装〜テスト〜修正の全成果物を確認し、配布・実行手順を含めてまとめたものである。P201(実装横断レビュー)は2回の実行(第1回: FAIL/BLOCKED10件、P202〜P205の1ラウンド修正を経て第2回: 全件PASS)で収束した。本サンドボックスの制約(pypi.org / registry.npmjs.orgへの接続不可、Dockerデーモン未起動)により、技術スタックの一部代替(`docs/P101-impl-context.md`参照)と、Docker Compose資産の実機能確認未了という限界がある。詳細は本書§10「未整備事項」を参照。

## 2. 参照した成果物

* `docs/P001-requirement.md` 〜 `docs/P010-design-review.md`(Plan Loop Step全成果物)
* `docs/P007-impl-direction.md` および `docs/P007-impl-direction/U001〜U004-*.md`
* `docs/P008-test-direction.md` および `docs/P008-test-direction/T001〜T020-*.md`
* `docs/P009-acceptance-direction.md` および `docs/P009-acceptance-direction/A001〜A010-*.md`(A008はP202-F003でドキュメント修正済み)
* `docs/test-records/20260803-1830-test-record.md`(P103)、`docs/test-records/20260803-1900-test-record.md`(P201第1回)、`docs/test-records/20260803-1930-test-record.md`(P205)
* `docs/P201-review-report.md`(第1回・第2回)
* `docs/P202-fix-plan.md`、`docs/P202-fix-plan/fixed/F001〜F003-*.md`、`docs/P202-fix-plan/P202-fix-resolved.md`、`docs/P202-fix-plan/P202-fix-unresolved.md`
* `docs/P204-impact-analysis.md`
* `docs/ArchitectureHandbook.md`、`docs/ADR.md`
* `./INDEX.md`、`server/INDEX.md`、`client/INDEX.md`
* `docs/P101-impl-context.md`(サンドボックス制約とdeviation一覧)
* ソースツリー: `server/`(`pyproject.toml`含む)、`client/`(npm系ファイルなし、ビルド不要のプレーンJS)
* 配布資産の確認(存在有無):
  * `server/pyproject.toml` — 存在(依存関係のみ、バージョン `0.1.0`)
  * `Dockerfile`(server/client)・`docker-compose.yml`・`nginx.conf`・`.env.example` — 本フェーズ(P302)で新規作成(§6・§10参照、いずれも本サンドボックスでは実行未検証)
  * `README.md`・`Makefile`・`.env`(実ファイル) — 存在しない
  * `VERSION`・`BUILD_HISTORY.md` — 本フェーズで新規作成(§5参照)

## 3. アプリケーション種別と配布方針

**分類: 1. サービス提供型システム**(フロントエンド`client/` + バックエンドAPI`server/` + SQLite の構成。`docs/ArchitectureHandbook.md`・`docs/P003-backend-spec.md` §1参照)。

* バックエンド: Python 3.11 + Starlette + Pydantic 2(ADR-002はFastAPIを指定しているが、本サンドボックスの制約によりStarletteで代替。`docs/P101-impl-context.md`参照)。`uvicorn`で起動。
* フロントエンド: ビルド不要のプレーンHTML/CSS/JavaScript(ADR-001はReact 18 + TypeScript + Viteを指定しているが、同様の制約により代替)。静的ファイルサーバーで配信。
* データストア: SQLite(単一ファイル、`server/data/app.db`)。
* → Docker Composeで起動できる資産一式を本フェーズで整備した(§6・§7参照)。ただし本サンドボックスにDockerデーモンが存在しないため、実際の `docker build`/`docker compose up` による動作確認はできていない(§10参照、作り話・捏造ではなく明示的な制約として記録する)。

## 4. 仕様・テスト・テスト実装の対応表

要求IDは `docs/P004-traceability-matrix.md` のものをそのまま使用する。

| 仕様ID | 仕様内容 | 対応するテスト計画 | 対応するテスト指示 | 対応するテスト実装/実行コマンド | 最新結果 | 証跡 | 状態 |
|---|---|---|---|---|---|---|---|
| REQ-SCREEN-001 | S01 ログイン画面 | P006 §2.1 S01 | P007 U001単体、P008 T001〜T004、P009 A010 | `python3 -m unittest tests.test_api_auth -v` 等 | PASS | test-records 20260803-1830/1930 | OK |
| REQ-SCREEN-002 | S02 予約カレンダー画面 | P006 §2.1 S02 | P008 T011、P009 A001・A002・A006 | 同上 | PASS | 同上 | OK |
| REQ-SCREEN-003 | S03 予約作成画面 | P006 §2.1 S03 | P008 T011〜T014、P009 A002・A007 | 同上 | PASS | 同上 | OK |
| REQ-SCREEN-004 | S04 予約詳細・編集画面 | P006 §2.1 S04 | P008 T015〜T018、P009 A003 | 同上 | PASS | 同上 | OK |
| REQ-SCREEN-005 | S05 マイ予約一覧画面 | P006 §2.1 S05 | P008 T019、P009 A002 | 同上 | PASS | 同上 | OK |
| REQ-SCREEN-006 | S06 会議室管理画面 | P006 §2.1 S06 | P008 T005〜T007、P009 A001 | 同上 | PASS | 同上 | OK |
| REQ-SCREEN-007 | S07 ユーザー管理画面 | P006 §2.1 S07 | P008 T008〜T010、P009 A005 | 同上 | PASS | 同上 | OK |
| REQ-API-001 | POST /api/auth/login | P006 §1, §2.2 | P008 T001〜T003 | `test_api_auth.py` | PASS | test-records 20260803-1830 | OK |
| REQ-API-002 | POST /api/auth/logout | P006 §2.2 | P008 T004 | `test_api_auth.py` | PASS | test-records 20260803-1830 | OK |
| REQ-API-003 | GET /api/me | P006 §2.2 | P008 T004、P009 A005 | `test_api_auth.py` | PASS | test-records 20260803-1830/1930 | OK |
| REQ-API-004 | GET /api/rooms | P006 §2.2 | P008 T005、P009 A001・A006 | `test_api_rooms.py` | PASS | 同上 | OK |
| REQ-API-005 | POST /api/rooms(管理者のみ) | P006 §2.2 | P008 T005・T006・T007 | `test_api_rooms.py` | PASS | test-records 20260803-1830 | OK |
| REQ-API-006 | PUT /api/rooms/{room_id}(管理者のみ) | P006 §2.2 | 単体テストのみ(`test_room_service.py`)、P008個別タスクIDなし | `python3 -m unittest tests.test_room_service -v` | PASS(単体) | server/tests | OK(★結合レベルの専用テストIDが割り当てられていない。単体テストではカバー済みだが、P008の目次自体にPUT /api/roomsを名指しした項目がない) |
| REQ-API-007 | DELETE /api/rooms/{room_id}(論理削除、管理者のみ) | P006 §2.2 | P009 A001手順1 | `run_a001.py`相当 | PASS | test-records 20260803-1930 | OK |
| REQ-API-008 | GET /api/reservations | P006 §2.2、§3(性能) | P008 T011、P009 A002・A006 | `test_api_reservations.py` | PASS | 同上 | OK |
| REQ-API-009 | GET /api/reservations/mine | P006 §2.2 | P008 T019、P009 A002 | `test_api_reservations.py` | PASS | 同上 | OK |
| REQ-API-010 | GET /api/reservations/{reservation_id} | P006 §2.2 | P008 T015、P009 A003 | `test_api_reservations.py` | PASS | 同上 | OK |
| REQ-API-011 | POST /api/reservations(重複チェックあり) | P006 §2.2、§3(同時実行) | P008 T011〜T014、P009 A002・A007 | `test_api_reservations.py` | PASS | 同上 | OK |
| REQ-API-012 | PUT /api/reservations/{reservation_id} | P006 §2.2 | P008 T016・T017・T020、P009 A002・A003 | `test_api_reservations.py` | PASS | 同上 | OK |
| REQ-API-013 | DELETE /api/reservations/{reservation_id} | P006 §2.2 | P008 T018、P009 A002・A003 | `test_api_reservations.py` | PASS | 同上 | OK |
| REQ-API-014 | GET /api/users(管理者のみ) | P006 §2.2、§3(セキュリティ) | P009 A008手順1 | `run_a003_a005_a008_a009.py`相当 | PASS | test-records 20260803-1930 | OK |
| REQ-API-015 | POST /api/users(管理者のみ) | P006 §2.2 | P008 T008・T009 | `test_api_users.py` | PASS | test-records 20260803-1830 | OK |
| REQ-API-016 | PUT /api/users/{user_id}(管理者のみ) | P006 §2.2 | 単体テストのみ(`test_user_service.py`)、P008個別タスクIDなし | `python3 -m unittest tests.test_user_service -v` | PASS(単体) | server/tests | OK(REQ-API-006と同様の注記) |
| REQ-API-017 | DELETE /api/users/{user_id}(論理削除、管理者のみ) | P006 §2.2 | P008 T010、P009 A005 | `test_api_users.py` | PASS | test-records 20260803-1830/1930 | OK |
| REQ-NFR-001 | 性能(カレンダー表示3秒以内) | P006 §3 | P009 A006 | `run_a006.py`相当 | PASS | test-records 20260803-1930 | OK(API単体で平均1秒未満、A006指示書の独自基準に基づく。E2E描画込みの3秒判定は未実施、A006指示書の★FIXME★参照) |
| REQ-NFR-002 | 可用性(平日日中99%以上) | P006(記載なし、`docs/P003-backend-spec.md` §8でインフラ観点として対象外) | なし | なし | NOT_RUN | — | NO_TEST_CASE(単一サーバー構成の可用性はインフラ構成に依存し、本サンドボックスで検証可能なテストが定義されていない。§10参照) |
| REQ-NFR-003 | セキュリティ(HTTPS、パスワードハッシュ化、権限チェック) | P006 §3 | P009 A004・A008 | `run_a00x.py`/`run_a003_a005_a008_a009.py`相当 | PASS(権限・ハッシュ化の範囲) | test-records 20260803-1930 | OK(★注: 「HTTPS」自体、すなわちTLS終端の実機能確認は本デリバラブルに含まれていない。P202-F001でSecure Cookieの前提を明確化したが、TLS終端コンポーネント自体は未整備。§10参照) |
| REQ-NFR-004 | スケーラビリティ(将来のスケールアウト検討) | P006(記載なし、ADR-006で将来検討として整理) | なし | なし | NOT_RUN | — | NO_TEST_CASE(単一サーバー・単一SQLiteファイルの現構成が前提であり、スケールアウトの実機能テストは定義・実施されていない) |
| REQ-NFR-005 | 想定同時利用者数(排他制御) | P006 §3 | P009 A007 | `run_rest.py`相当 | PASS | test-records 20260803-1930 | OK |
| REQ-NFR-006 | ログ出力先(標準出力・構造化ログ) | P006 §3 | P009 A009 | `run_a003_a005_a008_a009.py`相当 | PASS | test-records 20260803-1930 | OK(標準出力へのJSON Lines出力を確認。クラウドのログ収集基盤への転送自体はデプロイ環境側の責務であり本デリバラブルの対象外、`docs/P003-backend-spec.md` §8参照) |

## 5. バージョン情報とビルド履歴

* 優先順位に従い、`server/pyproject.toml` の `version = "0.1.0"` を正とし、リポジトリルートに `VERSION`(`0.1.0`)を新規作成した(P302時点、client側にはnpm等のバージョン定義機構がないため、アプリケーション全体の代表バージョンとして`VERSION`を使用する)。
* 実行モジュールからのバージョン確認: `GET /api/health` が `{"status":"ok","version":"0.1.0"}` を返すよう `server/app/main.py` を修正した(P302で追加、`VERSION`ファイルを読む)。起動時ログにも `{"level":"info","event":"startup","version":"0.1.0"}` を出力する。動作確認済み(§9参照)。
* ビルド履歴: リポジトリルートに `BUILD_HISTORY.md` を新規作成した(B001〜B004、テスト実行の節目を記録)。本プロジェクトはGit管理されていないため、Commit列はすべて「未取得」である。

## 6. 配布資産一覧

| 資産 | 状態 | 備考 |
|---|---|---|
| `server/Dockerfile` | P302で新規作成 | `python:3.11-slim`ベース、`pip install starlette uvicorn "pydantic>=2"`。本サンドボックスはpypi.org非接続のためビルド未検証。 |
| `client/Dockerfile` | P302で新規作成 | `python:3.11-slim`ベース、`python3 -m http.server`で静的配信。ビルド未検証。 |
| `docker-compose.yml` | P302で新規作成 | `server`・`client`・`nginx`(リバースプロキシ)の3サービス構成。`docker compose up`未検証(Dockerデーモン未起動、§10参照)。 |
| `nginx.conf` | P302で新規作成 | `client`(静的配信)・`server`(API)を単一オリジンに統合するリバースプロキシ設定。理由: `client/js/api/*.js` が `BASE_URL=""` の相対パス(`/api/...`)でfetchしているため、別オリジンのままでは動作しない(本フェーズで判明、§10参照)。 |
| `.env.example` | P302で新規作成 | `DATABASE_PATH`・`SESSION_COOKIE_SECURE` のひな形。 |
| `VERSION` | P302で新規作成 | `0.1.0`。 |
| `BUILD_HISTORY.md` | P302で新規作成 | B001〜B004。 |
| `README.md` | 存在しない | §10参照。起動・実行手順は本書§7・§8、および `server/INDEX.md`・`client/INDEX.md` に記載済みのため、`README.md`としての独立整備は未着手のまま申し送る。 |

## 7. 起動・実行手順

### Docker Compose 起動手順(未検証、手順のみ整備)

1. 前提ソフトウェア(Docker Engine、Docker Compose plugin)を確認する。
2. `.env.example` を参考に環境変数を確認する(現状の`docker-compose.yml`は値を直接埋め込んでいるため、変更する場合は`docker-compose.yml`を編集する)。
3. `docker compose build` でイメージをビルドする。★本サンドボックスでは未実行★
4. `docker compose up -d` で起動する。★本サンドボックスでは未実行★
5. `curl http://localhost:8080/api/health` でヘルスチェック・バージョン(`{"status":"ok","version":"0.1.0"}`)を確認する。
6. ブラウザで `http://localhost:8080/` を開き、S01ログイン画面が表示されることを確認する。初期管理者アカウントは自動投入されないため、次項の「初期データ投入」を先に行う必要がある(★未整備事項、§10参照★)。

### ローカル動作確認手順(本サンドボックスで実際に実行・検証済み)

1. `cd server && python3 -m unittest discover -s tests -v` で単体テスト121件がPASSすることを確認する。
2. `cd server && DATABASE_PATH=<任意のパス> python3 -c "..."` で管理者・会議室等の初期データを投入する(現状、初期管理者を作成するAPI/CLIが存在しないため、直接`app.repositories.user_repository.insert`等を呼ぶ簡易スクリプトで代用した。★未整備事項、§10参照★)。
3. `cd server && DATABASE_PATH=<同上> SESSION_COOKIE_SECURE=false python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8811` でサーバーを起動する(TLSなしのローカル確認時は`SESSION_COOKIE_SECURE=false`が必須、`docs/ADR.md` ADR-004備考参照)。
4. 別ターミナルで `cd client && python3 -m http.server 8080` を起動し、`http://127.0.0.1:8080/` を開く(この場合、client・serverが別オリジンになるため、実ブラウザでの動作にはCORS設定または`nginx.conf`相当のリバースプロキシが必要になる。本サンドボックスの受け入れテストではAPIを直接`requests`ライブラリで呼び出す方式で代替したため、この別オリジン構成での実ブラウザ動作は未検証。§10参照)。
5. `curl http://127.0.0.1:8811/api/health` でヘルスチェックを確認する。

## 8. テスト実行手順

* Unit Test(バックエンド): `cd server && python3 -m unittest discover -s tests -v`(121件、合格条件: 全件PASS)。
* Unit Test(フロントエンド): `cd client && node --test tests/*.test.mjs`(35件、合格条件: 全件PASS)。
* 結合テスト(P008、スプリント内): `docs/P008-test-direction.md` のT001〜T020を個別テストIDで実行(`python3 -m unittest tests.test_api_xxx.ClassName.test_yyy -v`)。合格条件: 全件PASS。結果格納先: `docs/test-records/20260803-1830-test-record.md`。
* 受け入れ結合テスト(P009): `docs/P009-acceptance-direction.md` のA001〜A010。本サンドボックスの制約により`pytest`/Playwright等の指定ツールではなく、実際に起動した`uvicorn`サーバーに対し`requests`ライブラリで実行した(詳細は各テスト記録の冒頭deviation注記を参照)。合格条件: 全件PASS。結果格納先: `docs/test-records/20260803-1900-test-record.md`(第1回)・`docs/test-records/20260803-1930-test-record.md`(P205再実行、最終)。
* 全テスト合格条件: 単体156件・結合20件・受け入れ結合10件、合計186件すべてPASS。

## 9. 最終確認結果

* バックエンド単体テスト: **121/121 PASS**
* フロントエンド単体テスト: **35/35 PASS**
* P008結合テスト(T001〜T020): **20/20 PASS**
* P009受け入れ結合テスト(A001〜A010): **10/10 PASS**(P201第1回は10/10がPASS以外、P202〜P205の1ラウンドの修正で全件PASSに到達。詳細は `docs/P201-review-report.md` 第2回参照)
* 上記のとおり、単体・結合・受け入れ結合を合わせた186件すべてがPASSしている状態でP302を作成した。

## 10. 未整備事項・人間による確認事項

* **Docker Compose資産が未検証**: `server/Dockerfile`・`client/Dockerfile`・`docker-compose.yml`・`nginx.conf` はP302で新規作成したが、本サンドボックスにDockerデーモンが存在しない(`docker info`がソケット接続エラー)ため、`docker build`/`docker compose up`による実際の起動確認ができていない。人間が実行環境で最初にビルド・起動確認を行うこと。
* **TLS終端コンポーネントが未整備**: ADR-004はセッションCookieに`Secure`属性を要求しており、本番相当のデプロイではTLS終端(リバースプロキシによるHTTPS化、証明書)が前提になる。本デリバラブルにはTLS終端の実装・証明書取得手順が含まれていない。人間が実行環境に応じて用意すること(自己署名証明書によるnginx-TLS化、クラウドのマネージドロードバランサ利用等)。
* **フロントエンドの相対URLと配布トポロジーの整合性**: `client/js/api/*.js` は `BASE_URL=""` で `/api/...` への相対パスでfetchしており、client・serverを単純に別オリジン(別ポート)のコンテナとして起動しただけでは動作しない。本フェーズで`nginx.conf`により単一オリジンに統合したが、この構成自体は未検証(上記Docker Compose未検証と同じ制約)。
* **初期管理者アカウントを作成する手段が存在しない**: `POST /api/users` は管理者権限が必須(`require_admin`)だが、初回起動時に管理者が1人も存在しない状態から管理者を作成するAPI・CLI・シードスクリプトが実装されていない(`docs/P007-impl-direction.md`のいずれのスプリントにも記載がない)。本受け入れテストでは`user_repository.insert`を直接呼ぶ簡易スクリプトで代用したが、これは配布物としての正式な初期化手順ではない。CR起票候補。
* **REQ-NFR-002(可用性)・REQ-NFR-004(スケーラビリティ)は実行可能なテストが定義されておらず、NOT_RUN**: いずれもインフラ構成(サーバー冗長化、負荷分散)に依存する要求であり、`docs/P003-backend-spec.md` §8がP005/P302で具体化する方針としていたが、単一サーバー構成の本デリバラブルでは実機能テストの対象外のまま据え置いた。
* **REQ-API-006・REQ-API-016(PUT /api/rooms、PUT /api/users)にP008の個別結合テストタスクIDが割り当てられていない**: 単体テスト(`test_room_service.py`・`test_user_service.py`)ではカバーされているが、P008目次にはこの2エンドポイントを名指しした結合テスト項目がない(P006 §2.2には異常系として一般的に言及されているのみ)。機能的な欠陥ではないが、テスト計画の粒度としての抜けであり、CR起票候補。
* **README.mdが存在しない**: 起動・実行手順は本書§7・§8および`server/INDEX.md`・`client/INDEX.md`に分散して記載されている。プロジェクトルート直下の単一エントリポイントとしての`README.md`は未整備。
* **P202-F001で判明したSecure Cookie問題の教訓**: `server/tests/test_api_auth.py`等の単体テストが`TestClient(app, base_url="https://testserver")`でHTTPS相当の疑似環境を使っていたため、実際のプレーンHTTP環境で起きる不具合(Secure Cookieが送信されない)を単体テスト・結合テスト(P008)では検出できず、P009(受け入れ結合テスト、P201)で初めて発覚した。今後同様の「テスト用クライアントの簡略化が本番相当の挙動を隠してしまう」パターンがないか、他のテストコードも人間によるレビューを推奨する。

## 11. リリース判定

**判定: 保留**

根拠:

* 単体・結合・受け入れ結合テスト186件すべてがPASSしており、機能面・セキュリティ面(パスワードハッシュ化、SQLインジェクション対策、権限チェック、排他制御)・性能面の受け入れ基準はすべて満たしている。
* 一方で、サービス提供型システムとしての配布要件である「Docker Composeで起動できる資産一式が整っている」状態には、資産(Dockerfile・docker-compose.yml・nginx.conf)自体は本フェーズで用意したものの、Dockerデーモンが利用できない本サンドボックスでは実際の起動確認ができておらず、`docs/P302-deliver.md` 作成時点で「整備済みで動作確認済み」とは言い切れない。
* 加えて、TLS終端コンポーネント・初期管理者アカウント作成手段という、実運用に入る前に必ず解決が必要な未整備事項が残っている(§10参照)。
* これらは軽微ではなく実運用開始前に必ず対応が必要な事項だが、いずれも「人間が実行環境でDockerビルド・起動確認を行い、TLS終端と初期データ投入手順を用意すれば解消できる」性質のものであり、テスト結果自体に矛盾や失敗があるわけではないため、`NG`ではなく`保留`と判定する。人間が実行環境でのDocker Compose起動確認・TLS終端整備・初期管理者投入手順の確定を行った上で、最終リリース可否を判断すること。
