# 成果物まとめ

> 本書は `spec-driven-dev` Skill フェーズP302の成果物。仕様・実装・テスト・修正結果・配布資産を確認し、リリース判定を行う。

## 1. 概要

会議室予約システム(社内向けWebアプリケーション)。React + TypeScript + Vite(フロントエンド)と Python + FastAPI + SQLite(バックエンド)で構成される。`docs/P001-requirement.md` の要件定義から、Plan Loop Step(P002〜P012、2回のP010で矛盾解消)・Overview Step(P020〜P022)・Executor(P101〜P104)・Reviewer Loop(P201〜P205、2回のP201で全件PASS)を経て、本フェーズ(Closing)で納品準備を行う。

## 2. 参照した成果物

* `docs/P001-requirement.md` 〜 `docs/P009-acceptance-direction.md`(存在確認済み)
* `docs/P010-design-review.md`、`docs/P011-impact-analysis.md`
* `docs/P007-impl-direction/U001〜U004-*.md`、`docs/P008-test-direction/T001〜T009-*.md`、`docs/P009-acceptance-direction/A001〜A009-*.md`
* `docs/test-records/20260811-0500-test-record.md`、`20260811-0530-test-record.md`、`20260811-0545-test-record.md`
* `docs/P201-review-report.md`(2回実行、最新判定=全件PASS)
* `docs/P202-fix-plan.md`、`docs/P202-fix-plan/fixed/F001〜F005-*.md`、`docs/P202-fix-plan/P202-fix-resolved.md`(`docs/P202-fix-plan/P202-fix-unresolved.md` は未解決障害が無いため作成していない)
* `docs/P204-impact-analysis.md`
* `docs/ArchitectureHandbook.md`、`docs/ADR.md`
* `./INDEX.md`(P301で作成)、`server/INDEX.md`、`client/INDEX.md`
* ソースツリー(`server/`、`client/`)、`server/pyproject.toml`・`server/uv.lock`、`client/package.json`・`client/package-lock.json`

## 3. アプリケーション種別と配布方針

**分類: 1. サービス提供型システム**(フロントエンド+バックエンド+DBの複数サービス構成、常駐プロセス)。`docs/P001-requirement.md`・`docs/ArchitectureHandbook.md` §2の構成図から明確に判定できる。

配布方針: Docker Composeで `web`(nginx、静的配信+APIリバースプロキシ)・`server`(FastAPI)の2サービス構成として起動する(`docker-compose.yml`)。詳細は6章・7章参照。

## 4. 仕様・テスト・テスト実装の対応表

### 4.1 画面(S01〜S07)

| 仕様ID | 仕様内容 | 対応するテスト計画 | 対応するテスト指示 | 対応するテスト実装/実行コマンド | 最新結果 | 証跡 | 状態 |
|---|---|---|---|---|---|---|---|
| REQ-SCREEN-001 | S01 ログイン画面 | docs/P006-test-plan.md §2 | docs/P008-test-direction/T001-*.md | `client/src/tests/LoginPage.test.tsx`, `npx playwright test tests/integration/t001_login_flow.spec.ts` | PASS | docs/test-records/20260811-0545-test-record.md | OK |
| REQ-SCREEN-002 | S02 予約カレンダー画面 | docs/P006-test-plan.md §2 | T001, T003, A001 | `client/src/tests/CalendarPage.test.tsx`, 上記E2E一式 | PASS | 同上 | OK |
| REQ-SCREEN-003 | S03 予約作成画面 | docs/P006-test-plan.md §2 | T003, T004, A001, A004 | `client/src/tests/ReservationCreatePage.test.tsx`, 上記E2E一式 | PASS | 同上 | OK(下記4.4参照: 参加者選択サブ機能のみ別枠) |
| REQ-SCREEN-004 | S04 予約詳細・編集画面 | docs/P006-test-plan.md §2 | T006, A001, A002, A006 | `client/src/tests/ReservationDetailPage.test.tsx`, 上記E2E一式 | PASS | 同上 | OK |
| REQ-SCREEN-005 | S05 マイ予約一覧画面 | docs/P006-test-plan.md §2 | T005, A001 | `client/src/tests/MyReservationsPage.test.tsx`, 上記E2E一式 | PASS | 同上 | OK |
| REQ-SCREEN-006 | S06 会議室管理画面 | docs/P006-test-plan.md §2 | T007, A002, A006 | `client/src/tests/RoomAdminPage.test.tsx`, 上記E2E一式 | PASS | 同上 | OK |
| REQ-SCREEN-007 | S07 ユーザー管理画面 | docs/P006-test-plan.md §2 | T008, A002 | `client/src/tests/UserAdminPage.test.tsx`, 上記E2E一式 | PASS | 同上 | OK |

### 4.2 API(17本)

| 仕様ID | 仕様内容 | 対応するテスト計画 | 対応するテスト指示 | 対応するテスト実装/実行コマンド | 最新結果 | 証跡 | 状態 |
|---|---|---|---|---|---|---|---|
| REQ-API-001 | POST /api/auth/login | docs/P006-test-plan.md §2 | T001, T002 | `server/tests/api/test_auth_api.py` | PASS | docs/test-records/20260811-0545-test-record.md | OK |
| REQ-API-002 | POST /api/auth/logout | 同上 | T001, T002 | `server/tests/api/test_auth_api.py` | PASS | 同上 | OK |
| REQ-API-003 | GET /api/me | 同上 | T001, T002 | `server/tests/api/test_auth_api.py` | PASS | 同上 | OK |
| REQ-API-004 | GET /api/rooms | 同上 | T001, T007, T009 | `server/tests/api/test_rooms_api.py` | PASS | 同上 | OK |
| REQ-API-005 | POST /api/rooms | 同上 | T007, A002 | `server/tests/api/test_rooms_api.py` | PASS | 同上 | OK |
| REQ-API-006 | PUT /api/rooms/{room_id} | 同上 | (単体・APIテストのみ) | `server/tests/api/test_rooms_api.py` | PASS | 同上 | OK |
| REQ-API-007 | DELETE /api/rooms/{room_id} | 同上 | T007, A006 | `server/tests/api/test_rooms_api.py` | PASS | 同上 | OK |
| REQ-API-008 | GET /api/reservations | 同上 | T003, T004 | `server/tests/api/test_reservations_api.py` | PASS | 同上 | OK |
| REQ-API-009 | GET /api/reservations/mine | 同上 | T005 | `server/tests/api/test_reservations_api.py` | PASS | 同上 | OK |
| REQ-API-010 | GET /api/reservations/{id} | 同上 | (単体・APIテストのみ) | `server/tests/api/test_reservations_api.py` | PASS | 同上 | OK |
| REQ-API-011 | POST /api/reservations | 同上 | T003, T004, A004 | `server/tests/api/test_reservations_api.py` | PASS | 同上 | OK |
| REQ-API-012 | PUT /api/reservations/{id} | 同上 | T006, A002 | `server/tests/api/test_reservations_api.py` | PASS | 同上 | OK |
| REQ-API-013 | DELETE /api/reservations/{id} | 同上 | A001, A002 | `server/tests/api/test_reservations_api.py` | PASS | 同上 | OK |
| REQ-API-014 | GET /api/users | 同上 | T009 | `server/tests/api/test_users_api.py` | PASS | 同上 | OK |
| REQ-API-015 | POST /api/users | 同上 | T008, A002 | `server/tests/api/test_users_api.py` | PASS | 同上 | OK |
| REQ-API-016 | PUT /api/users/{user_id} | 同上 | (単体・APIテストのみ) | `server/tests/api/test_users_api.py` | PASS | 同上 | OK |
| REQ-API-017 | DELETE /api/users/{user_id} | 同上 | (単体・APIテストのみ) | `server/tests/api/test_users_api.py` | PASS | 同上 | OK |

### 4.3 業務フロー・システムテスト(P009横断シナリオ)

| 仕様ID | 仕様内容 | 対応するテスト指示 | 対応するテスト実装/実行コマンド | 最新結果 | 証跡 | 状態 |
|---|---|---|---|---|---|---|
| SPEC-FLOW-001 | 一般ユーザーの標準的な業務フロー(予約作成〜編集〜取消〜ログアウト) | docs/P009-acceptance-direction/A001-*.md | `npx playwright test tests/acceptance/a001_general_user_journey.spec.ts` | PASS | docs/test-records/20260811-0545-test-record.md | OK |
| SPEC-FLOW-002 | 管理者の標準的な業務フロー(会議室・ユーザー登録〜代理編集) | docs/P009-acceptance-direction/A002-*.md | `npx playwright test tests/acceptance/a002_admin_journey.spec.ts` | PASS | 同上 | OK |
| SPEC-FLOW-003 | 認証・認可の横断確認(全リソース×全ロール) | docs/P009-acceptance-direction/A003-*.md | `server/tests/acceptance/test_a003_cross_cutting_authorization.py` | PASS | 同上 | OK |
| SPEC-FLOW-004 | 予約重複防止の境界値(背中合わせ予約) | docs/P009-acceptance-direction/A004-*.md(P202 F004で期待値訂正済み) | `npx playwright test tests/acceptance/a004_reservation_conflict_system_check.spec.ts` | PASS | 同上 | OK |
| SPEC-NFR-002-運用 | アプリケーション再起動耐性(マイグレーション冪等性) | docs/P009-acceptance-direction/A005-*.md | `server/tests/acceptance/test_a005_restart_resilience.py` | PASS | 同上(§9・項目8で詳述) | OK |
| SPEC-FLOW-005 | 会議室無効化後の既存予約の扱い(★ACCEPTED★の実装確認) | docs/P009-acceptance-direction/A006-*.md | `npx playwright test tests/acceptance/a006_room_deactivation_existing_reservations.spec.ts` | PASS | 同上 | OK |
| REQ-NFR-001 | 性能(カレンダー表示3秒以内) | docs/P009-acceptance-direction/A007-*.md | `npx playwright test tests/acceptance/a007_performance_calendar.spec.ts` | PASS(参考値、実測3回とも3秒未満) | 同上 | OK(開発環境上の参考値。本番相当の負荷試験は未実施、10章参照) |
| REQ-NFR-003 | セキュリティ(パスワード非露出) | docs/P009-acceptance-direction/A008-*.md | `server/tests/acceptance/test_a008_password_exposure.py` | PASS | 同上 | OK |
| REQ-NFR-006 | 運用(構造化ログ出力) | docs/P009-acceptance-direction/A009-*.md(P202 F005でerror_code追加済み) | `server/tests/acceptance/test_a009_structured_logging.py` | PASS | 同上 | OK |

### 4.4 既知の未実装・委譲事項(隠さず記載)

| 仕様ID | 仕様内容 | 状態 | 理由・参照 |
|---|---|---|---|
| SPEC-SCREEN-003-参加者選択 | S03「参加者(社員)」の複数選択 | NO_TEST_IMPL | 一般ユーザーが呼べる社員一覧APIが存在しない(`docs/P007-impl-direction.md` 未解決事項参照)。UIは「現在利用不可」の注記付きで実装し、`participant_ids` は常に空配列を送信する。人間の判断(新規API追加/CR起票)が必要。 |
| REQ-NFR-002 | 可用性(平日日中99%以上) | BLOCKED | アプリケーションコード側の前提(ステートレス化、セッション外部化)は満たすが、実際の可用性はインフラ構成(冗長化・監視)に依存し、本フェーズの範囲外(`docs/P003-backend-spec.md` §7)。10章参照。 |
| REQ-NFR-004 | スケーラビリティ | BLOCKED | 同上。単一SQLiteファイルを前提とした設計であり、書き込みスケールアウトは対象外(`docs/P003-backend-spec.md` §7、ADR-003)。 |
| REQ-NFR-005 | 想定同時利用者数(ピーク30接続) | NOT_RUN | 実際の負荷試験(30同時接続を模したテスト)は未実施。A007は単一ユーザーでの応答時間のみ確認。`docs/P003-backend-spec.md` §7の記載どおり、実施はP302(本書、実際の配布インフラ整備時)に委譲されているが、本ビルド環境では実施できていない。10章参照。 |
| REQ-NFR-006-集約 | ログ集約基盤(CloudWatch Logs等)への転送 | BLOCKED | アプリケーションは標準出力への構造化ログ出力までを担当し、集約基盤への転送設定は実インフラの範囲(`docs/P003-backend-spec.md` §7)。本ビルド環境では実クラウド環境が無いため未実施。 |

いずれもDEVIATEDには該当しない(要件どおりReact+TS+Vite・Python+FastAPIで実装できており、環境制約による代替実装は発生していない。詳細は `docs/ADR.md` ADR-001・ADR-002参照)。

## 5. バージョン情報とビルド履歴

* バージョン: `1.1.0`(ルート `VERSION` ファイル、`server/pyproject.toml` の `project.version`、`client/package.json` の `version` のいずれも統一。CR-001対応にともないMINORを更新、詳細は末尾「CR-001対応」節参照)。
* ビルド履歴: `BUILD_HISTORY.md`(BUILD-001〜BUILD-004、いずれもPASS。BUILD-004はCR-001対応分)。
* 実行モジュールからのバージョン確認手段: **未整備**。`GET /health` や `GET /version` エンドポイント、画面フッターへのバージョン表示は実装していない。10章に記載し、CR起票候補とする。

## 6. 配布資産一覧

| 資産 | 状態 |
|---|---|
| `server/Dockerfile` | 新規作成(本フェーズ) |
| `server/.dockerignore` | 新規作成 |
| `client/Dockerfile`(マルチステージ: node build → nginx配信) | 新規作成 |
| `client/nginx.conf`(静的配信 + `/api` リバースプロキシ) | 新規作成。7章「実行前チェック項目7」への対応として追加 |
| `client/.dockerignore` | 新規作成 |
| `docker-compose.yml`(ルート、`web`・`server` の2サービス、`db-data` 永続ボリューム) | 新規作成 |
| `.env.example` | 新規作成 |
| `README.md`(ルート) | 新規作成 |
| `VERSION` | 新規作成(`1.0.0`) |
| `BUILD_HISTORY.md` | 新規作成 |

**Docker Compose動作未検証**: 本ビルド環境にはDocker CLI自体が存在しない(`docker --version` がコマンド未検出、PowerShellでも同様に確認)。上記のDocker関連資産は作成・整備したが、実際にビルド・起動して動作確認はできていない。9章・11章参照。

## 7. 起動・実行手順

### Docker Compose 起動手順(未検証、7章参照)

1. Docker Engine / Docker Composeが利用可能な環境を用意する。
2. リポジトリルートで `docker compose up --build` を実行する。
3. `web` サービスのヘルスチェック(`http://localhost/`)、`server` サービスのヘルスチェック(`http://localhost:8000/openapi.json`)が通ることを確認する。
4. ブラウザで `http://localhost:8080` を開き、S01ログイン画面が表示されることを確認する。
5. マイグレーションはバックエンド起動時に自動実行される(`server/app/main.py` の `lifespan`)ため、手動実行手順は不要。ただし初回起動時は管理者・一般ユーザーのシードデータ(`admin001`/`user001`/`user002`、パスワードは全員 `TestPassw0rd!`)のみが投入される。
6. **既知の制約**: 本構成はTLS終端を含まないため、ログインセッションCookie(Secure属性付き、ADR-005)がプレーンHTTP(`http://localhost:8080`)では保存されない可能性が高い。本番相当のTLS終端を行うロードバランサ配下での動作を前提とする(`docs/P003-backend-spec.md` §7)。ローカルでの完全な動作確認には、別途セルフ署名証明書の追加、またはリバースプロキシでのTLS終端が必要(10章参照)。

### 開発環境での起動手順(検証済み、本セッション中に実際に使用)

1. `cd server && uv sync`
2. `cd server && uv run uvicorn app.main:app --reload --port 8000`
3. `cd client && npm install`
4. `cd client && npm run dev`(Viteの開発サーバーが `/api` をバックエンドへプロキシする)
5. `http://localhost:5173` を開く。

## 8. テスト実行手順

| レベル | コマンド | 件数 | 合格条件 |
|---|---|---|---|
| バックエンド単体・結合・受け入れ(pytest) | `cd server && uv run python -m pytest tests/ -v` | 104件 | 全PASS |
| フロントエンド単体(Vitest) | `cd client && npx vitest run` | 22件 | 全PASS |
| フロントエンドE2E結合(Playwright) | `cd client && npx playwright test tests/integration/` | 8件 | 全PASS |
| フロントエンドE2E受け入れ結合(Playwright) | `cd client && npx playwright test tests/acceptance/` | 5件(A003/A005/A008/A009は上記pytestの104件に含む) | 全PASS |

テスト結果の格納先: `docs/test-records/*.md`(直近: `docs/test-records/20260811-0545-test-record.md`)。BUILD-003(本フェーズ実施)でも上記のうちpytest・Vitest・buildを再実行し、全PASSを確認済み(`BUILD_HISTORY.md` 参照)。

## 9. 最終確認結果

* **実行前チェック1〜6**: `docs/P002-frontend-spec.md`・`docs/P003-backend-spec.md`・`docs/P006-test-plan.md` はいずれも存在。`docs/test-records/*.md` 3件存在。`docs/P202-fix-plan/P202-fix-resolved.md` 存在(未解決障害なし)。アプリケーション種別はサービス提供型システムと判定可能。`docs/P302-deliver.md`(本書)は本フェーズで新規作成。
* **実行前チェック7(接続前提とトポロジーの整合)**: `client/src/api/client.ts` の `apiFetch` を確認したところ、`VITE_API_BASE_URL` 未設定時は相対パス(`/api/...`)でfetchし、`credentials: "include"` でCookieを送出する実装になっている。これは「フロントエンドとバックエンドが同一オリジンであること」を前提とする実装である。P103(結合テスト実行)時に、開発環境でフロントエンド(Vite, port 5173)とバックエンド(uvicorn, port 8000)を別オリジンのまま連携させようとして、ログイン後のCookieがAPI呼び出しに送出されず認証が機能しない問題を実際に確認しており(`client/vite.config.ts` のコメント参照)、その対策として開発サーバーに `/api` プロキシを追加した経緯がある。**この懸念は開発時特有の問題ではなく、これから組み立てる実際の配布トポロジー(Docker Compose)にも等しく当てはまる**ため、`client/`・`server/` を別コンテナのまま素朴に公開するのではなく、`client/nginx.conf` で静的配信と `/api` リバースプロキシを1つのオリジン(`web` サービス)に統合する構成にしたうえで `docker-compose.yml` を作成した(6章参照)。これにより、フロントエンドの接続前提と配布トポロジーの矛盾は解消したと判断する。ただし、Docker自体が本ビルド環境に無いため、この構成が実際に意図どおり動作することの実機検証はできていない(次項参照)。
* **実行前チェック8(データストアの再起動耐性)**: `docs/P009-acceptance-direction/A005-restart-resilience.md` に対応するテスト(`server/tests/acceptance/test_a005_restart_resilience.py`)が、同一の観点(同一SQLiteファイルに対する複数回のプロセス再起動、マイグレーションの冪等性、データの非欠落)を既に確認・記録済みである(`docs/test-records/20260811-0530-test-record.md`・`20260811-0545-test-record.md` にPASSとして記録。3回連続の起動でいずれもマイグレーションエラー無し、データ欠落無しを確認)。`SKILL-P302-deliver.md` の規定により、本フェーズでの重複再実行は行わず、この既存記録を引用するにとどめた。
* **Docker Compose の実機検証**: 本ビルド環境で `docker --version` を実行したところ、Bash・PowerShellのいずれでも `docker` コマンド自体が見つからず(`command not found` / `not recognized`)、Docker CLIが利用できないことを確認した。したがって `server/Dockerfile`・`client/Dockerfile`・`docker-compose.yml` は作成・整備したが、実際にビルド・起動して動作確認することはできていない。これを「動作確認済み」であるかのように記載しない。
* バックエンド104件・フロントエンド単体22件・E2E結合8件・E2E受け入れ結合5件(残り4件はバックエンド104件に含む)、合計すべてPASS(BUILD-003時点で再確認済み)。

## 10. 未整備事項・人間による確認事項

* **Docker Composeの動作未検証**(本ビルド環境にDocker CLIが存在しないため。6章・9章参照)。人間側の環境でのビルド・起動確認を推奨する。
* **TLS未終端**(6章・7章参照)。`docker-compose.yml` の構成のみではログインCookie(Secure属性)が機能しない。本番相当運用にはTLS終端を行うロードバランサ/リバースプロキシが別途必要(`docs/P003-backend-spec.md` §7の既存delegationの範囲内であり、新たな仕様矛盾ではない)。
* **実行モジュールからのバージョン確認手段が無い**(`GET /health`・`GET /version` 等の未実装。5章参照)。軽微な追加で対応可能と考えられるため、CR起票候補とする。
* **S03「参加者(社員)」選択が未実装**(4.4節参照)。一般ユーザー向けの社員一覧取得手段が要件・設計のいずれにも定義されていないため。人間の判断(新規API追加または認可範囲の見直し)が必要。CR起票候補。
* **想定同時接続数(30)の実負荷試験が未実施**(4.4節参照)。A007は単一ユーザーでの応答時間確認にとどまる。
* **可用性・スケーラビリティ・ログ集約基盤の実インフラ整備は本フェーズの範囲外**(`docs/P003-backend-spec.md` §7で明示的に委譲済み。新たな不備ではない)。
* ★ACCEPTED★として既に判断済みの項目(会議室無効化時に既存予約が残る、セッション期限切れ行の物理削除を行わない、ORM不使用など)は `docs/ArchitectureHandbook.md` §9に記載済みであり、リリース判定を妨げる理由には数えない。

## 11. リリース判定

**判定: 保留**

根拠:

* 仕様どおりのテスト(単体97+7=104件、E2E17件、合計121件相当)はすべてPASSしており、機能面・既知バグの是正(P202 F001〜F005)は完了している。テスト失敗・仕様矛盾は現時点で残っていない。
* 一方で、`SKILL-P302-deliver.md` の規定どおり、**Docker Composeによる実際のビルド・起動確認ができていない**(本ビルド環境にDocker CLI自体が存在しないため)。配布資産(Dockerfile・docker-compose.yml・nginxリバースプロキシ)は実行前チェック項目7の懸念に対応する形で整備したが、実機で動作することを確認できていない以上、無条件の `OK` とはしない。
* 加えて、TLS未終端によるログインCookie不動作の可能性、バージョン確認手段の欠如、S03参加者選択機能の未実装、想定同時接続数の実負荷試験未実施という、いずれも「軽微」とは言い切れないが「テスト失敗・仕様矛盾」でもない未整備事項が複数ある。これらは人間がリリース可否を最終判断すべき事項であり、`SKILL-P302-deliver.md` の定義する `保留`(軽微な未整備事項があるが、人間判断でリリース可否を決められる)に該当すると判断した。
* `NG` としなかった理由: テスト失敗・仕様矛盾・「配布不能」と断定できる事実は無い(配布資産自体は一式整備済みで、動作確認ができていないだけである)。
* 人間が確認すべき最優先事項: (1) Docker環境でのビルド・起動確認、(2) TLS終端の配置方針、(3) S03参加者選択機能の扱い(新規API追加のCR起票の要否)。

---

## CR-001対応(Refactor経由、P302再実行、2026-08-11)

### 概要

* `docs/P901-cr-direction/CR-001.md`(予約に「備考(社内向けメモ)」欄を追加)への対応が完了し、Closing相当の本フェーズを再実行した。対処の詳細は `docs/P903-cr-records/CR-001.md` を参照。

### 追加された仕様・テストの対応表への反映

| 仕様ID | 仕様内容 | 対応するテスト計画 | 対応するテスト指示 | 対応するテスト実装/実行コマンド | 最新結果 | 証跡 | 状態 |
|---|---|---|---|---|---|---|---|
| REQ-CR001-001 | `internal_memo`(備考・社内向けメモ)の入力・保存(S03/S04、POST/PUT) | docs/P006-test-plan.md §2「閲覧範囲のマスキング」 | docs/P008-test-direction/T010-*.md | `server/tests/schemas/test_reservation_schema.py`, `server/tests/api/test_reservations_api.py`, `client/src/tests/ReservationCreatePage.test.tsx`, `client/src/tests/ReservationDetailPage.test.tsx` | PASS | docs/test-records/20260811-CR001-test-record.md | OK |
| REQ-CR001-002 | 閲覧範囲マスキング(所有者・管理者以外は`null`) | 同上 | 同上、`npx playwright test tests/integration/t010_reservation_internal_memo_masking.spec.ts` | `server/tests/api/test_reservations_api.py`(マスキング系4件) | PASS | 同上 | OK |
| REQ-CR001-003 | マイグレーション冪等性(004、2回連続実行) | docs/P006-test-plan.md §4 | (P903スコープ決定「マイグレーション方式の確認」) | `server/tests/db/test_migrate.py::test_run_migrations_applies_004_as_a_pure_diff_on_top_of_001_002_003` | PASS | 同上 | OK |

* 既存の仕様ID(REQ-SCREEN-003/004、REQ-API-008〜012)は契約を壊さない追加のみのため、4.1・4.2節の記載・状態(OK)は変更していない。

### 版数更新

* `docs/P903-cr-records/CR-001.md` のスコープ決定で「API契約変更」「データモデル変更」の両方に分類されており、`SKILL-P302-deliver.md`「CR対応後の版数更新方針」の規定により少なくともMINORを上げる。実際の変更は既存の画面項目・API・データ契約を破壊しない後方互換な追加(新規の任意フィールド1つ)にとどまるため、MAJORではなく**MINOR**を選択し、`1.0.0` → **`1.1.0`** に更新した(`VERSION`・`server/pyproject.toml`・`client/package.json`)。ビルド履歴はBUILD-004として`BUILD_HISTORY.md`に追記した。

### 新たに判明した未整備事項

* **`npm run build`のローカル環境固有のネイティブクラッシュ**: Node.js v24.12.0/Windowsの本ローカル実行環境において、`vite build`(rollup)がソース内容によらずネイティブクラッシュ(`STATUS_STACK_BUFFER_OVERRUN`)することを確認した。切り分けの結果、CR-001のコード変更が原因ではないと判断した(`tsc -b`型検査・vitest単体テスト・Playwright E2E(dev-mode)はいずれも全PASS)。ただし、これは配布用の本番ビルド資産(`client/dist/`)を本環境では最終生成・検証できていないことを意味する。人間の環境(または別のNode.jsバージョン)での`npm run build`の再検証を推奨する。詳細は`docs/test-records/20260811-CR001-test-record.md`参照。

### リリース判定の再確認

* **判定: 保留(変更なし)**。CR-001自体は仕様どおり実装・テスト済みで、CR-001に起因する新たなテスト失敗・仕様矛盾はない。11章に記載した既存の保留理由(Docker実機未検証、TLS未終端、S03参加者選択未実装、負荷試験未実施)に加えて、上記「新たに判明した未整備事項」(`npm run build`のローカル環境クラッシュ)を保留理由に追加する。既存のDocker Compose資産(`client/Dockerfile`のビルドステップに`npm run build`を含む)も、同じ問題の影響を受ける可能性があるため、Docker環境での実機確認時にあわせて確認することを推奨する。
