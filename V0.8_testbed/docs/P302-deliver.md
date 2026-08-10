# 成果物まとめ

> 本書は `spec-driven-dev` Skill フェーズP302の成果物です。Closing Step(P301〜P302)の最終フェーズとして、仕様・実装・テスト・修正結果・配布資産を確認し、人間がリリース可否をレビューできる形でまとめます。

## 1. 概要

* **対象システム**: 会議室予約システム(`docs/P001-requirement.md`)。社員による会議室の空き確認・予約・変更・取消と、管理者による会議室・ユーザー管理を提供する社内向けWebアプリケーション。
* **想定規模**: 従業員300名程度、会議室10室程度、同時接続30程度(`docs/P001-requirement.md`)。
* **技術スタック(実装時に代替を採用)**: フロントエンド React 18 + TypeScript + Vite(ADR-001)、バックエンド FastAPI + 標準ライブラリ `sqlite3`(ADR-002)、認証 Cookieベースサーバーサイドセッション(ADR-003)、マイグレーション バージョン管理テーブル方式(ADR-004)。`docs/P001-requirement.md` はFastAPIのみ指定(フロントエンド技術は未指定)で、`react-router-dom`・`@testing-library/react` 等の具体的な選定はADR-001・P006・P007で行った。
* **現在の状態**: Executor(P101〜P104)・Reviewer Loop(P201〜P205、2ラウンドで収束)が完了し、`docs/P202-fix-plan/P202-fix-resolved.md` は `ALL_RESOLVED`(未解決0件)。本フェーズ(P302)開始時点の `docs/.inprogress` は `P301`。
* **本フェーズで新たに行ったこと**: (1) 配布トポロジーの前提確認(実行前チェック7.)の結果、Docker Compose構成(フロントエンド/バックエンド別コンテナ)がフロントエンドの同一オリジン前提fetchと矛盾することを検出し、nginxリバースプロキシを追加して是正(下記6章)。(2) 再起動冪等性(実行前チェック8.)を実地再検証(`server/tests/acceptance/test_restart_resilience.py` を本フェーズで再実行、PASS)。(3) バージョン確認手段として `GET /version` を追加(5章)。(4) Docker配布資産一式(未整備だった)を新規作成。(5) 全テストスイートを本フェーズ内で再実行し、全件PASSを確認(9章)。

### CR-001対応版(オンライン会議URル追加)の再配布 ※P903内側のP302再実行で追記

* `docs/P901-cr-direction/CR-001.md`(予約へのオンライン会議URL追加)を適用し、P002〜P302を対象範囲(`docs/P903-cr-records/CR-001.md`スコープ決定節: P002・P003・P004・P005・P006・U003/U004分のP007〜P009・P020・P022・P101〜P104・P010・P201・P301・P302)について再実行した。
* 変更点の要約: 予約(S03作成・S04詳細編集)に任意項目「オンライン会議URL」を追加。画面・API(`POST`/`PUT`/`GET /api/reservations*`)・データモデル(`reservations.meeting_url`カラム、マイグレーション`003_add_reservation_meeting_url.sql`)にまたがる変更。`GET /api/reservations`(一覧)には意図的に含めない。
* 本フェーズ(P302再実行)固有の作業: 上記変更にともなうテスト件数・INDEX記載の更新のみ。配布資産(Docker関連ファイル)・起動手順・リリース判定の根拠(9〜11章)に構造的な変更はない(9章の数値のみ更新)。
* 全テストスイートを本CR適用後に再実行し、全件PASSを確認した(下記9章「CR-001対応後の最終確認結果」参照)。

## 2. 参照した成果物

| 分類 | ファイル | 有無 |
|---|---|---|
| 要件 | `docs/P001-requirement.md` | あり |
| 仕様 | `docs/P002-frontend-spec.md`(432行、画面7つ・API外部契約) | あり |
| 仕様 | `docs/P003-backend-spec.md`(220行、API内部実現・DB設計) | あり |
| トレーサビリティ | `docs/P004-traceability-matrix.md`(要求ID 30件、全件OK) | あり |
| 実装計画 | `docs/P005-impl-plan.md` | あり |
| テスト計画 | `docs/P006-test-plan.md` | あり |
| 実装指示 | `docs/P007-impl-direction.md`(U001〜U005、目次OKF形式、全件`[x]`) + `docs/P007-impl-direction/U0NN-*.md` | あり |
| 結合テスト指示 | `docs/P008-test-direction.md`(T001〜T015、全件`[x]`・PASS) + `docs/P008-test-direction/T0NN-*.md` | あり |
| 受入テスト指示 | `docs/P009-acceptance-direction.md`(A001〜A011、全件`[x]`・PASS) + `docs/P009-acceptance-direction/A0NN-*.md` | あり |
| テスト記録 | `docs/test-records/20260809-1500-test-record.md`(P103)、`20260809-1900-test-record.md`(P201第1回)、`20260809-2100-test-record.md`(P205再実行)、`20260809-2200-test-record.md`(CR-001: P103内T016)、`20260809-2230-test-record.md`(CR-001: P201内A001再実行) | あり(5件) |
| CR(Change Request) | `docs/CR.md`(CR-001、状態`反映確認中`予定)、`docs/P901-cr-direction/CR-001.md`、`docs/P903-cr-records/CR-001.md` | あり(P903内側で新規作成) |
| 修正計画・結果 | `docs/P202-fix-plan.md`、`docs/P202-fix-plan/fixed/F001〜F004-*.md`、`docs/P202-fix-plan/P202-fix-resolved.md`(ALL_RESOLVED)、`docs/P202-fix-plan/P202-fix-unresolved.md`(0件) | あり |
| レビュー結果 | `docs/P201-review-report.md`(第2回: 26/26 PASS)、`docs/P204-impact-analysis.md` | あり |
| 設計 | `docs/ArchitectureHandbook.md`、`docs/ADR.md`(ADR-001〜004) | あり |
| INDEX | `./INDEX.md`(P301で新規作成、本フェーズで最終更新)、`server/INDEX.md`、`client/INDEX.md`(いずれもP104で更新済み) | あり |
| 配布資産(実行前) | `Dockerfile` / `docker-compose.yml` / `compose.yml` / `VERSION` | **P302開始時点でいずれも無し**(本フェーズで新規作成、6章参照) |
| バージョン定義 | `server/pyproject.toml`([project].version)、`client/package.json`(version) | あり(いずれも `0.1.0`、一致) |
| README | `README.md`(ルート) | **無し**(10章に記載) |

## 3. アプリケーション種別と配布方針

**判定: 1. サービス提供型システム**(Webアプリケーション、フロントエンド+バックエンドの2サービス構成、常駐プロセス)。

根拠:
* `docs/P001-requirement.md` に「社内向けWebアプリケーションとしてクラウド環境(例: AWS)にデプロイ」と明記。
* `server/app/main.py` はFastAPIの常駐プロセス(`uvicorn` で起動)、`client/` はビルドして配信するSPA。
* CLI・バッチ・ライブラリとしての実行形態を示す `bin/`・`cmd/`・スケジューラ登録等は存在しない。

配布方針: Docker Composeで `server`(バックエンド)・`client`(nginx配信のSPA + リバースプロキシ)の2サービスを起動する構成とする(6章)。DBは外部ミドルウェアではなくSQLiteファイル(`server`コンテナ内の永続ボリューム)のため、専用DBサービスは持たない。

## 4. 仕様・テスト・テスト実装の対応表

`docs/P004-traceability-matrix.md` の要求ID(REQ-SCREEN-0NN / REQ-API-0NN / REQ-NFR-0NN、全30件、いずれもP004時点で `OK`)を仕様IDとして流用する。テスト結果は `docs/test-records/20260809-2100-test-record.md`(P205最終再実行)および本フェーズで実際に再実行した結果(9章)にもとづく最新値。

凡例: T0NN=`docs/P008-test-direction.md`(結合テスト)、A0NN=`docs/P009-acceptance-direction.md`(受入/システムテスト)。A0NN のうちクライアント側(`client/tests/acceptance/*.test.tsx`)は、`docs/P006-test-plan.md` 5章に★ACCEPTED★で明記されたとおり、当初設計(ビルド成果物をPlaywright等のヘッドレスブラウザで操作)の代わりにjsdom直接レンダリング方式(P008と同じ手法)を採用した代替実装であるため、該当行は状態 `DEVIATED` とする(★ACCEPTED★理由は `docs/P006-test-plan.md` 5章に記載済み、再提起不要)。

**CR-001対応(オンライン会議URL追加)の反映**: 下表のREQ-SCREEN-003・REQ-SCREEN-004・REQ-API-010・REQ-API-011・REQ-API-012行は、CR-001によりmeeting_url項目が追加されたが、対応するテストタスク(T006〜T008、T010、A004、A011、および新規T016)がいずれも引き続きPASSしているため状態・対応関係に変更はない。新規追加された`docs/P008-test-direction/T016-reservation-meeting-url.md`(`client/tests/integration/reservationMeetingUrl.test.tsx`)は、上記5つの仕様IDのうちS03/S04・POST/PUT/GET系APIにまたがる横断確認であるため、個別の行には転記せず本段落にまとめて記載する。

### 4.1 画面要求

| 仕様ID | 仕様内容 | 対応するテスト計画 | 対応するテスト指示 | 対応するテスト実装/実行コマンド | 最新結果 | 証跡 | 状態 |
|---|---|---|---|---|---|---|---|
| REQ-SCREEN-001 | S01 ログイン画面 | P006 2.2/2.4節 | T001, T002, A001, A010 | `server/tests/integration/test_login_session_integration.py`、`client/tests/integration/loginFailure.test.tsx`、`client/tests/acceptance/mainBusinessFlow.test.tsx`、`client/tests/acceptance/setupToOperation.test.tsx` | PASS | 20260809-2100-test-record.md | DEVIATED(A0NN分。T0NNはOK相当) |
| REQ-SCREEN-002 | S02 予約カレンダー画面 | P006 2.2/2.4/3節 | T009, A001, A006 | `client/tests/integration/calendarListDisplay.test.tsx`、`client/tests/acceptance/mainBusinessFlow.test.tsx`、`client/tests/acceptance/calendarPerformance.test.tsx` | PASS | 同上 | DEVIATED(A0NN分) |
| REQ-SCREEN-003 | S03 予約作成画面 | P006 2.2/2.4節 | T006, T007, T008, A004, A011 | `client/tests/integration/reservationCreateSuccess.test.tsx`、`reservationConflict.test.tsx`、`capacityExceeded.test.tsx`、`client/tests/acceptance/participantSelectionFlow.test.tsx`、`errorHandlingSequence.test.tsx` | PASS | 同上 | DEVIATED(A0NN分) |
| REQ-SCREEN-004 | S04 予約詳細・編集画面 | P006 2.2/2.4節 | T010, T011, A003 | `server/tests/integration/test_reservation_update_self_exclude.py`、`client/tests/integration/reservationCancelReflect.test.tsx`、`client/tests/acceptance/inactiveRoomHistory.test.tsx` | PASS | 同上 | DEVIATED(A0NN分) |
| REQ-SCREEN-005 | S05 マイ予約一覧画面 | P006 2.2/2.4節 | T012, A003 | `client/tests/integration/mylistPeriodFilter.test.tsx`、`client/tests/acceptance/inactiveRoomHistory.test.tsx` | PASS | 同上 | DEVIATED(A0NN分) |
| REQ-SCREEN-006 | S06 会議室管理画面 | P006 2.2/2.4節 | T004, T005, A010 | `client/tests/integration/roomCreateAndList.test.tsx`、`server/tests/integration/test_room_deactivate_integration.py`、`client/tests/acceptance/setupToOperation.test.tsx` | PASS | 同上 | DEVIATED(A0NN分) |
| REQ-SCREEN-007 | S07 ユーザー管理画面 | P006 2.2/2.4節 | T013, T014, A010 | `client/tests/integration/userCrud.test.tsx`、`userProtectionDisplay.test.tsx`、`client/tests/acceptance/setupToOperation.test.tsx` | PASS | 同上 | DEVIATED(A0NN分) |

### 4.2 API要求

| 仕様ID | 仕様内容 | 対応するテスト計画 | 対応するテスト指示 | 対応するテスト実装/実行コマンド | 最新結果 | 証跡 | 状態 |
|---|---|---|---|---|---|---|---|
| REQ-API-001 | POST /api/auth/login | P006 2.1節 | T001, T002 | `server/tests/test_auth_api.py`, `server/tests/integration/test_login_session_integration.py` | PASS | test-record 1500/2100 | OK |
| REQ-API-002 | POST /api/auth/logout | P006 2.1節 | T003 | `server/tests/integration/test_logout_integration.py` | PASS | 同上 | OK |
| REQ-API-003 | GET /api/me | P006 2.1節 | T015, A002 | `client/tests/integration/headerNavByRole.test.tsx`, `client/tests/acceptance/authorizationCrosscheck.test.tsx` | PASS | 同上 | DEVIATED(A002分) |
| REQ-API-004 | GET /api/rooms | P006 2.1節 | T004, T005 | `server/tests/test_rooms_api.py`, `client/tests/integration/roomCreateAndList.test.tsx` | PASS | 同上 | OK |
| REQ-API-005 | POST /api/rooms | P006 2.1節 | T004 | `server/tests/test_rooms_api.py` | PASS | 同上 | OK |
| REQ-API-006 | PUT /api/rooms/{room_id} | P006 2.1節 | T005 | `server/tests/integration/test_room_deactivate_integration.py` | PASS | 同上 | OK |
| REQ-API-007 | DELETE /api/rooms/{room_id} | P006 2.1節 | T005 | `server/tests/test_rooms_api.py` | PASS | 同上 | OK |
| REQ-API-008 | GET /api/reservations | P006 2.1節 | T009 | `server/tests/test_reservations_api.py`, `client/tests/integration/calendarListDisplay.test.tsx` | PASS | 同上 | OK |
| REQ-API-009 | GET /api/reservations/mine | P006 2.1節 | T012 | `client/tests/integration/mylistPeriodFilter.test.tsx` | PASS | 同上 | OK |
| REQ-API-010 | GET /api/reservations/{reservation_id} | P006 2.1節 | T010, A003 | `server/tests/integration/test_reservation_update_self_exclude.py`, `client/tests/acceptance/inactiveRoomHistory.test.tsx` | PASS | 同上 | DEVIATED(A003分) |
| REQ-API-011 | POST /api/reservations | P006 2.1節 | T006, T007, T008 | `client/tests/integration/reservationCreateSuccess.test.tsx`, `reservationConflict.test.tsx`, `capacityExceeded.test.tsx` | PASS | 同上 | OK |
| REQ-API-012 | PUT /api/reservations/{reservation_id} | P006 2.1節 | T010, T011 | `server/tests/integration/test_reservation_update_self_exclude.py`, `client/tests/integration/reservationCancelReflect.test.tsx` | PASS | 同上 | OK |
| REQ-API-013 | DELETE /api/reservations/{reservation_id} | P006 2.1節 | T011 | `client/tests/integration/reservationCancelReflect.test.tsx` | PASS | 同上 | OK |
| REQ-API-014 | GET /api/users | P006 2.1節 | T013 | `server/tests/test_users_api.py`, `client/tests/integration/userCrud.test.tsx` | PASS | 同上 | OK |
| REQ-API-015 | POST /api/users | P006 2.1節 | T013 | 同上 | PASS | 同上 | OK |
| REQ-API-016 | PUT /api/users/{user_id} | P006 2.1節 | T013, T014 | `server/tests/test_users_api.py`, `client/tests/integration/userProtectionDisplay.test.tsx` | PASS | 同上 | OK |
| REQ-API-017 | DELETE /api/users/{user_id} | P006 2.1節 | T013, T014 | 同上 | PASS | 同上 | OK |
| (過剰実装ではない) GET /api/users/directory | `docs/P004-traceability-matrix.md` 4章参照(REQ-SCREEN-003の必須詳細化と判定済み) | P006 2.1節 | A004 | `server/tests/test_users_directory_api.py`, `client/tests/acceptance/participantSelectionFlow.test.tsx` | PASS | 同上 | DEVIATED(A004分) |

### 4.3 非機能要求

| 仕様ID | 仕様内容 | 対応するテスト計画 | 対応するテスト指示 | 対応するテスト実装/実行コマンド | 最新結果 | 証跡 | 状態 |
|---|---|---|---|---|---|---|---|
| REQ-NFR-001 | 性能(カレンダー表示3秒以内) | P006 3章 | A006 | `client/tests/acceptance/calendarPerformance.test.tsx`(実測、参考値) | PASS(3回連続3秒以内) | test-record 2100 | DEVIATED(A0NN、実ブラウザでの実測ではなくjsdom計測。参考値扱いは元々A006自身の但し書き) |
| REQ-NFR-002 | 可用性(平日日中99%以上) | P006 3章 | (該当するテストタスク無し) | — | — | — | **NO_TEST_CASE**(P003 5章で本番監視基盤側への委譲を明記済みだが、稼働率を実測するテストタスクはP008/P009に存在しない。実測には本番相当の長時間運用が必要なため、テストベッドの期間内実行は設計上そもそも対象外) |
| REQ-NFR-003 | セキュリティ | P006 3章 | A007 | `server/tests/acceptance/test_security_crosscheck.py` | PASS | test-record 1900(初回からPASS) | OK |
| REQ-NFR-004 | スケーラビリティ | P006(委譲) | (該当するテストタスク無し) | — | — | — | NO_TEST_CASE(P003 5章でP005へ委譲を明記済み。将来の多拠点展開時の設計課題であり、本テストベッドの対象外) |
| REQ-NFR-005 | 同時利用者数(同時30接続) | P006 3章 | A005 | `server/tests/acceptance/test_concurrent_booking.py` | PASS | test-record 1900(初回からPASS) | OK |
| REQ-NFR-006 | ログ出力先・監視方法 | P006 3章 | A008 | `server/tests/acceptance/test_structured_logging.py` | PASS | test-record 2100(F004修正後) | OK |

**対応漏れの明記**: REQ-NFR-002(可用性)・REQ-NFR-004(スケーラビリティ)は、対応する具体的テストタスクが存在しない(`NO_TEST_CASE`)。いずれも `docs/P003-backend-spec.md` 5章で本番運用フェーズ・将来設計への委譲が明記されており、P004トレーサビリティマトリクスでもその委譲の明記自体を充足条件として`OK`と判定済み(P004 3章)。本表ではテスト対応表としての性質上、テスト未存在の事実は隠さず記載する。

## 5. バージョン情報とビルド履歴

* **バージョン定義の所在**: `server/pyproject.toml` の `[project].version = "0.1.0"`、`client/package.json` の `"version": "0.1.0"`。両者は一致している。優先順位(P302 5章)にもとづき、専用の `VERSION` ファイルは作成しなかった(言語標準の定義が既に存在するため)。
* **実行モジュールからのバージョン確認**: 本フェーズで `GET /version` エンドポイントを追加した(`server/app/main.py`、`importlib.metadata.version()` で `pyproject.toml` の値を実行時に読み戻す。パッケージ未インストール環境向けのフォールバック値もハードコードしてあるが、`pyproject.toml` の値と食い違わないようコメントで明記)。テスト: `server/tests/test_version.py`(新規作成、PASS)。フロントエンド側(画面フッター等)へのバージョン表示は行っていない(10章に記載)。
* **ビルド履歴**: `docs/BUILD_HISTORY.md` を本フェーズで新規作成。P103時点の初回結合テスト(FAIL含む)からP205再実行(全件PASS)、本フェーズの最終フルテスト実行(194/194 PASS)までの4ビルドを記録。コミットハッシュは全ビルド時点で「未コミット(作業ツリー)」(このリポジトリは本ドキュメント作成時点で一度も `git commit` されていない)。

## 6. 配布資産一覧

P302開始時点では配布資産が一切存在しなかった(2章参照)。本フェーズで以下を新規作成した(いずれも実行前チェック7.の是正を兼ねる)。

| ファイル | 内容 |
|---|---|
| `server/Dockerfile` | バックエンド用。`python:3.11-slim` ベース、`pip install -e .` で `app/` を editable install、`uvicorn app.main:app --host 0.0.0.0 --port 8000` で起動。`DATABASE_PATH=/app/data/app.db`、`COOKIE_SECURE=false`(理由は下記参照)を既定値としてイメージに埋め込み。 |
| `server/.dockerignore` | `.venv` / `__pycache__` / `data` / `tests` 等をビルドコンテキストから除外。 |
| `client/Dockerfile` | フロントエンド用。マルチステージ: `node:20-alpine` で `npm ci && npm run build`、`nginx:1.27-alpine` に `dist/` と `nginx.conf` を配置して配信。 |
| `client/nginx.conf` | **実行前チェック7.の是正そのもの**。`location /api/` で `server` コンテナ(`http://server:8000`)へリバースプロキシし、`location /` でSPAの `index.html` にフォールバック(react-router-dom対応)。これにより、ブラウザからは「1つの同一オリジン」に見え、`client/src/api/*.ts` の相対パスfetch(`fetch('/api/...')`)の前提を無変更で満たす。 |
| `client/.dockerignore` | `node_modules` / `dist` / テストファイルを除外。 |
| `docker-compose.yml`(ルート) | `server`・`client` の2サービス。`server` は named volume(`server-data:/app/data`)でSQLiteファイルを永続化し、healthcheckを設定。`client` は `depends_on: server (service_healthy)`、ポートは `.env` の `CLIENT_PORT`(既定 `8080`)で公開。 |
| `.env.example`(ルート) | `CLIENT_PORT` と `COOKIE_SECURE` の設定例。 |

**実行前チェック7.の是正内容(詳細)**: `client/src/api/authApi.ts` / `reservationApi.ts` / `roomApi.ts` / `userApi.ts` を全数grepし、すべてのAPI呼び出しが `fetch('/api/...', { credentials: 'include' })` という相対URL・同一オリジン前提であることを確認した(`BASE_URL` 環境変数やクロスオリジン設定は存在しない)。一方、当初検討していた素朴なdocker-compose構成(`client`をポート80、`server`をポート8000で別々に公開するだけの構成)はこの前提と矛盾する(ブラウザから見て異なるオリジンになり、相対パスfetchが`client`自身に飛んでしまい404になる)。この矛盾は「7.の是正はコード修正の範囲を超えない」(P302本文の判定基準)と判断した: フロントエンド・バックエンドのソースコードは一切変更せず、`client/nginx.conf` のリバースプロキシ設定という配布構成側の追加のみで解消できたため、仕様変更(CR起票)は不要と判断し、実際に是正した。

**認証Cookieに関する追加の是正**: 上記のnginxリバースプロキシ構成は平文HTTP(ポート80、TLS終端なし)で `client` サービスを公開する。`server/app/routers/auth.py` の既定値 `COOKIE_SECURE=true` のままだと、ブラウザがSecure属性付きCookieを非HTTPS接続で送信しなくなりログインが機能しない。これは実行前チェック7.が検出する「接続前提とトポロジーの不整合」と同種の問題であるため、`docker-compose.yml`・`server/Dockerfile` の両方で `COOKIE_SECURE=false` を既定値とし、`.env.example` にコメントで理由を明記した(将来TLS終端を追加する場合の対応は10章に記載)。

## 7. 起動・実行手順

### Docker Compose 起動手順

1. 前提ソフトウェア: Docker Engine + Docker Compose v2(本サンドボックスには **無い**。`docker --version` / `docker info` / `docker compose version` はいずれも `command not found`、exit 127。デーモン未起動ではなくDocker自体が未インストール。9章参照)
2. `.env.example` を `.env` にコピーする: `cp .env.example .env`
3. 必要に応じて `.env` の `CLIENT_PORT`・`COOKIE_SECURE` を編集する(TLS終端を追加しない限り `COOKIE_SECURE=false` のまま)
4. イメージをビルドする: `docker compose build`
5. 起動する: `docker compose up -d`
6. ヘルスチェックを確認する: `docker compose ps`(`server` が `healthy` になること)、`curl http://localhost:8000/health`(compose内部から)、ブラウザで `http://localhost:${CLIENT_PORT:-8080}/` にアクセス
7. マイグレーションは `server` コンテナの起動時(FastAPI lifespan、`app/main.py`)に自動適用される。初回起動時に `admin` ユーザーが作成される(初期パスワード `ChangeMe123!`、10章参照)。追加の手動マイグレーション手順は不要
8. `http://localhost:${CLIENT_PORT:-8080}/` にブラウザでアクセスし、`admin` / `ChangeMe123!` でログインできることを確認する

上記手順4〜8は、Docker自体がこのサンドボックスに存在しないため**実行できていない**(9章参照)。手順1〜3・資産の構文自体は本フェーズで確認済み(`docker-compose.yml` はPython `yaml.safe_load()` でパース成功を確認)。

### ローカル(Dockerなし)での起動手順(実際に確認済み)

Dockerが使えない環境向けに、本フェーズで実際に動作確認した手順を記載する(`docs/USER_GUIDE.md` 相当の内容はまだ存在しないため、ここに残す。10章参照)。

1. `cd server && python -m venv .venv && .venv/Scripts/pip install -e .[dev]`
2. `cd client && npm install`
3. `cd server && .venv/Scripts/python -m uvicorn app.main:app --port 8000`(別ターミナル)。起動時にマイグレーションが自動適用され `admin` ユーザーが作成される
4. `curl http://127.0.0.1:8000/health` → `{"status":"ok"}`、`curl http://127.0.0.1:8000/version` → `{"version":"0.1.0"}`
5. `cd client && npm run build`(本フェーズで実行・確認済み、エラー・警告なし)。開発時は `npm run dev` でも可(ただしdevサーバーには`server`へのプロキシが設定されていないため、`server`とは別オリジンになり同一オリジン前提のfetchが機能しない。本番相当確認には上記Docker Compose構成または `npm run build` 成果物をnginx等で配信する構成を使うこと)

## 8. テスト実行手順

| レベル | コマンド | 格納先 |
|---|---|---|
| バックエンド単体+結合+受入(pytest一括) | `cd server && python -m pytest tests/ -v` | 本フェーズ実行結果は本書9章、過去分は `docs/test-records/*.md` |
| バックエンド単体テストのみ | `cd server && python -m pytest tests/ --ignore=tests/acceptance --ignore=tests/integration -v` | 同上 |
| バックエンド結合テストのみ | `cd server && python -m pytest tests/integration -v` | 同上 |
| バックエンド受入テストのみ | `cd server && python -m pytest tests/acceptance -v` | 同上 |
| フロントエンド単体テスト | `cd client && node --import tsx --test 'tests/*.test.tsx'` | 同上 |
| フロントエンド結合テスト | `cd client && node --import tsx --test 'tests/integration/*.test.tsx'` | 同上 |
| フロントエンド受入テスト | `cd client && node --import tsx --test 'tests/acceptance/*.test.tsx'` | 同上 |

**合格条件**: 上記すべてのコマンドが非ゼロ終了コードを返さず(pytestは失敗テストがあれば非ゼロ、`node --test` は失敗テストがあれば非ゼロ)、各コマンドの `fail` 件数が0であること。クォート付きglob(`'tests/*.test.tsx'` 等)は必須 — クォート無しではシェル展開の結果ファイル数によって一部しか渡らない場合があり、`tests/` のようなディレクトリ指定単体ではNode.jsのモジュール解決エラーになる(本フェーズで実際に `tests/integration/*.js` という誤ったglob(拡張子違い)を試して0件収集になることを確認済み。正しいglobは `*.test.tsx`)。

## 9. 最終確認結果

すべて本フェーズ内で実際にコマンドを実行し、出力を確認した(表示された数値は実行結果そのもの、事前の記録からの転記ではない)。

| コマンド | 結果 |
|---|---|
| `cd server && python -m pytest tests/ -v` | **128 passed**(1 warning: `StarletteDeprecationWarning`、`httpx` 関連、既知・機能に影響なし) |
| 内訳: 単体117 / 結合4 / 受入7 | `pytest tests/acceptance -q` → 7 passed、`pytest tests/integration -q` → 4 passed、残り117が単体(`GET /version` のテスト `tests/test_version.py` を含む、本フェーズ新規追加) |
| `cd client && node --import tsx --test 'tests/*.test.tsx'` | **38 passed**, 0 failed |
| `cd client && node --import tsx --test 'tests/integration/*.test.tsx'` | **16 passed**, 0 failed |
| `cd client && node --import tsx --test 'tests/acceptance/*.test.tsx'` | **12 passed**, 0 failed |
| **合計** | **194 / 194 PASS**(サーバー128 + クライアント66) |
| `cd client && npm run build` | 成功。`tsc -b && vite build`、エラー・警告なし。`dist/index.html` + `dist/assets/index-*.js` を生成(本フェーズで実際に生成・確認) |
| 実行前チェック8.(再起動冪等性)の再検証 | `cd server && python -m pytest tests/acceptance/test_restart_resilience.py -v` → **PASSED**(1件)。実サブプロセスで `uvicorn` を3回連続起動・SIGTERM停止し、2回目・3回目の起動でもマイグレーションが例外なく完了し、投入済みデータ(予約等)が保持されたままAPIが正常応答することを実地確認(`server/tests/acceptance/test_restart_resilience.py` のシナリオそのもの。本フェーズで改めて単独実行し、既存の合格記録に依存しない形で再確認した) |
| `docker --version` / `docker info` / `docker compose version` | いずれも `/usr/bin/bash: line 1: docker: command not found`(exit 127)。Docker CLI自体が本サンドボックスにインストールされていない(デーモン未起動ではない) |
| `docker-compose.yml` の構文チェック | `python -c "import yaml; yaml.safe_load(open('docker-compose.yml'))"` で正常にパースできることを確認(Docker本体でのバリデーションではない点に注意) |
| `docker compose build` / `docker compose up` | **未実行**(Docker自体が使えないため)。よって配布資産のビルド成功・起動成功・コンテナ間通信(nginxのリバースプロキシ経由でのログイン等)は**未検証** |

### CR-001対応後の最終確認結果(P903内側のP302再実行、2026-08-09)

上表(初回納品時点、194/194 PASS)からCR-001適用後に全コマンドを再実行した結果。数値は実行結果そのもの。

| コマンド | 結果 |
|---|---|
| `cd server && python -m pytest tests/ -q` | **153 passed**(1 warning、既知・機能に影響なし。CR-001でmeeting_url関連25件追加、`test_migration.py`の既存2件を更新) |
| `cd client && node --import tsx --test 'tests/*.test.tsx'` | **46 passed**, 0 failed(CR-001でReservationCreatePage/ReservationDetailPage関連8件追加) |
| `cd client && node --import tsx --test 'tests/integration/*.test.tsx'` | **17 passed**, 0 failed(CR-001でT016「オンライン会議URLの作成・表示・編集」1件追加) |
| `cd client && node --import tsx --test 'tests/acceptance/*.test.tsx'` | **12 passed**, 0 failed(A001「主要業務フロー」をCR-001対応版に更新のうえ再実行、PASS) |
| **合計** | **228 / 228 PASS**(サーバー153 + クライアント75) |
| `cd client && npm run build` | 成功。`tsc -b && vite build`、エラー・警告なし |

* Docker関連の検証状況(9章の初回結果)に変更は無い。CR-001は既存のDocker配布資産(`server/Dockerfile`・`client/Dockerfile`・`docker-compose.yml`・`client/nginx.conf`)に影響しない変更(APIフィールド追加・DBカラム追加のみ)であり、これらのファイル自体は変更していない。したがってDocker検証状況は初回納品時点から変わらず「未検証」のままである。

## 10. 未整備事項・人間による確認事項

以下は隠さず記載する。

1. **Docker Compose のビルド・起動が未検証**(6章・7章・9章参照)。`server/Dockerfile` / `client/Dockerfile` / `docker-compose.yml` / `client/nginx.conf` は内容をレビューし、YAML構文チェックは行ったが、本サンドボックスにDocker自体が存在しないため、実際の `docker compose build` / `up` / コンテナ間通信(リバースプロキシ経由のログイン確認)は一度も実行できていない。Docker CLIが使える環境での初回ビルド・起動確認が必要。
2. **README.md がリポジトリに存在しない**。7章に起動手順を記載したが、`docs/P302-deliver.md` 以外に人間向けの単一のREADMEが無い。将来的に `README.md`(ルート)を作成し、7章の内容を転記・要約することを推奨する(仕様変更を伴わない軽微な追加のため、CR不要で対応可能)。
3. **フロントエンドにバージョン表示が無い**(5章参照)。`GET /version` はバックエンドに追加したが、画面フッター等でのバージョン表示は未実装。優先度は低いと判断し本フェーズでは見送った。
4. **★FIXME★(未解決、要人間確認)が複数残っている**。`docs/P002-frontend-spec.md` に17箇所、`docs/P003-backend-spec.md` に6箇所(grep実測値。`docs/ArchitectureHandbook.md` 9章に記載の「18/7」という数字とはわずかに差異があるが、原因調査・修正は本フェーズの対象外のため実測値のみ報告する)。内容は社員ID書式・パスワードポリシー・カレンダー営業時間帯・週表示の起点・会議室設備の選択肢・TLS終端の具体構成など、`docs/P001-requirement.md` に明記が無く下流文書側で仮定した項目。いずれも実装済みではあるが「仮定が正しいか」の人間確認が済んでいない。P302の対象外(仕様策定はP002/P003の役割)のため、そのまま一覧化するのみに留める。
5. **TLS終端が存在しない**(ADR-002/ADR-003、`docs/ArchitectureHandbook.md` 9章で★ACCEPTED★済みの既知の制約)。本フェーズで追加したDocker Compose構成もTLS終端を持たず(平文HTTP、`COOKIE_SECURE=false` — 6章参照)、`docs/P001-requirement.md` が前提とする本番デプロイ(クラウド環境、HTTPS)とは異なる。本番投入時は、クラウド環境のロードバランサ等でTLS終端を追加したうえで `COOKIE_SECURE=true` に切り替える必要がある(この切り替え自体はコード変更不要、環境変数の変更のみ)。★ACCEPTED★済みの既知の制約であり、11章のリリース判定の根拠には数えない。
6. **初期管理者パスワードが固定値**(`ChangeMe123!`、`docs/P007-impl-direction/U001-foundation-and-auth.md` U001-T2、`docs/ArchitectureHandbook.md` 9章に既存のCR起票候補として記載済み)。本番投入前に変更または強制変更フローの追加が必要。新規の指摘ではなく、既存文書に記録済みの事項の再掲。
7. **REQ-NFR-002(可用性)・REQ-NFR-004(スケーラビリティ)に対応する具体的テストタスクが無い**(`NO_TEST_CASE`、4.3節参照)。いずれも設計判断としてP005・本番運用フェーズへの委譲が明記済みで、P004トレーサビリティマトリクスでも許容済み。
8. ~~`docs/CR.md` / `docs/P901-cr-direction/` / `docs/P903-cr-records/` は存在しない~~ **(CR-001対応版で解消)**: CR-001(オンライン会議URL追加)の適用にともない、`docs/CR.md`・`docs/P901-cr-direction/CR-001.md`・`docs/P903-cr-records/CR-001.md` が作成された。P904(変更要求の反映確認)・P905(ADR更新確認)は本フェーズ(P302)より後に実行される。

上記のうち、CRの起票候補として明記すべきものは 2(README.md不足)・3(バージョン表示)・6(初期パスワード固定)。ただしいずれも軽微であり、緊急性は低い。5(TLS終端)は既存の★ACCEPTED★事項の再確認であり新規CR不要(既に受容済み)。

## 11. リリース判定

**判定: 保留**

根拠:

* **合格材料**: 仕様・テスト・実装の対応(4章)はREQ-NFR-002/004の`NO_TEST_CASE`(いずれも設計判断で委譲済み、7章参照)を除き全件`OK`または★ACCEPTED★理由付きの`DEVIATED`。テストは本フェーズで実際に再実行し、**194/194 PASS**(9章)。再起動冪等性(実行前チェック8.)も本フェーズで実地再検証しPASS。実行前チェック7.(接続前提とトポロジーの整合)は、矛盾を検出したうえで実際にnginxリバースプロキシを追加して是正済み(6章)。バージョン情報の所在・実行時確認手段(5章)も整備済み。これらは「保留」を選ばない理由にはなるが、以下の未検証事項がある限り「OK」とは判定できない。
* **保留とする決定的理由(未整備事項1、10章)**: Docker Composeによる配布資産一式(`server/Dockerfile` / `client/Dockerfile` / `docker-compose.yml` / `client/nginx.conf`)は本フェーズで新規に整備したが、本サンドボックスにDocker CLI/デーモンが存在しないため、実際の `docker compose build` / `up` / コンテナ間通信は一度も検証できていない。`SKILL-P302-deliver.md`「配布資産の整備方針」に明記された「動作確認していないことを黙って『整備済み』であるかのように書いてはならない…この場合、リリース判定は原則として `保留` とする」という規定に該当する具体的なケースである。
* **NGとしない理由**: アプリケーション自体の品質(仕様適合・機能・非機能・再起動耐性)は実サーバー・実DB・実プロセスに対する194件のテストで裏付けられており、テスト失敗や仕様矛盾は存在しない。未検証なのは「Dockerパッケージング」という配布層のみであり、アプリケーションが動作しないことを示す証拠は無い。これはNG(重要な未解決事項)ではなく、人間が「Docker検証済みの環境で再確認してからreleaseする」か「アプリケーション自体のテスト結果を根拠に、Docker検証を条件付きで許容する」かを判断できる「軽微な未整備事項」である。
* **UNKNOWNとしない理由**: 判定に必要な根拠資料(仕様書・テスト計画・テスト指示・テスト実装・実行結果)はすべて揃っており、判断できないのではなく、判断した結果として人間の最終確認を必要とする一点(Dockerビルド検証)が明確に切り分けられている。
* **付随する保留要素**: 10章の4(★FIXME★ 23件、業務ルールの仮定確認)も、機能自体は実装・テスト済みだが「意図した仕様と一致しているか」の最終確認が人間側に残っている。これも「保留」の性質(人間判断でリリース可否を決められる軽微な未整備事項)に合致する。

**保留解除の条件**: (1) Docker CLIが使える環境で `docker compose build && docker compose up` を実行し、ブラウザから `http://localhost:8080/` でログイン〜予約作成までの一連の操作が実際に成功することを確認する。(2) 10章の★FIXME★(社員ID書式・パスワードポリシー等)について、人間が意図した仕様と一致しているかを確認する(一致していれば追加対応不要)。上記2点が確認できれば、他の未整備事項(README.md、バージョン表示、初期パスワード)は軽微であり `OK` 判定を妨げないと判断する。
