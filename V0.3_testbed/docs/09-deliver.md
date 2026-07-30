# 成果物まとめ

> 本書は `spec-driven-dev` Skill フェーズ9の成果物です(V0.3ルールでの再実行、フェーズ2〜9を通しで実行)。
> 作成日: 2026-07-30。

## 1. 概要

会議室予約システム(社内Webアプリ)を、`spec-driven-dev` Skill(V0.3)のフェーズ2〜9を無人での自己レビュー方式(`testbed.md`参照)で連続実行して実装した。フェーズ1(要件定義)は`V0.2_testbed`でレビュー済みのものをそのまま再利用している。バックエンド(Python/Starlette+Pydantic、仕様上はFastAPI)・フロントエンド(素のHTML/JS、仕様上はReact+TS+Vite)を実装し、Unit Test 45件・スプリント内結合10件・スプリントをまたぐ結合/システムテスト12件(T004は6ステップのサブテストを含む)の計67件を実行し、全件PASSしている(うちT004手順6は確認観点2・3検証のため意図的に仕込んだバグで一度FAILし、フェーズ8のF002修正後にPASS)。

本実行は「V0.2→V0.3の差分検証」を主目的とし、フェーズ6のコードにV0.2で見つかった不具合(F001: 参加者ID未検証による500エラー)の修正を実装時点から組み込んだ状態でスタートしているため、フェーズ7は全件PASSし、フェーズ8は修正課題0件で完了した。詳細は `e2e-validation-report.md` を参照。

## 2. 参照した成果物

* `docs/01-requirement.md`(V0.2_testbedから再利用、確定済み)
* `docs/02-frontend-spec.md`(フェーズ2、V0.3ルールで再生成)
* `docs/03-backend-spec.md`(フェーズ3、V0.3ルールで再生成)
* `docs/04-impl-plan.md`(フェーズ4)
* `docs/05-test-plan.md`(フェーズ5)
* `docs/06-impl-direction.md` および `docs/06-impl-direction/U001〜U004-*.md`(フェーズ6)
* `docs/07-test-direction.md` および `docs/07-test-direction/T001〜T005-*.md`(フェーズ7)
* `docs/test-records/20260730-1600-test-record.md`
* `docs/08-fix-plan.md`(未解決0件)、`docs/08-fix-plan/08-fix-resolved.md`、`docs/08-fix-plan/08-fix-unresolved.md`(いずれも0件)
* ソースツリー: `server/`(`pyproject.toml`, `app/`, `tests/`)、`client/`(`index.html`, `app.js`, `api.js`, `style.css`, `views/`)
* 配布資産: `Dockerfile`, `docker-compose.yml`, `.env.example`, `README.md`, `VERSION`, `BUILD_HISTORY.md`

## 3. アプリケーション種別と配布方針

**サービス提供型システム**(フロントエンド + バックエンド + SQLiteの構成、常駐プロセス)と判定する。配布方針は Docker Compose によるコンテナ起動を第一候補とし、`README.md` にローカル直接起動の手順も併記した。

## 4. 仕様・テスト・テスト実装の対応表

| 仕様ID/項目 | 仕様内容 | 対応するテスト計画 | 対応するテスト指示 | 対応するテスト実装/実行コマンド | 最新結果 | 証跡 | 状態 |
|---|---|---|---|---|---|---|---|
| SPEC-API-001 | POST /api/auth/login | docs/05-test-plan.md 2章 | docs/06-impl-direction/U001 | `tests.test_auth_api` | PASS | docs/06-impl-direction.md実施結果サマリ | OK |
| SPEC-API-002 | POST /api/auth/logout | 同上 | docs/06-impl-direction/U001 | `tests.test_auth_api` | PASS | 同上 | OK |
| SPEC-API-003 | GET /api/me | 同上 | docs/06-impl-direction/U001 | `tests.test_auth_api` | PASS | 同上 | OK |
| SPEC-API-004〜007 | /api/rooms (GET/POST/PUT/DELETE) | 同上 | docs/06-impl-direction/U002 | `tests.test_rooms_repo`, `tests.integration.test_u002_rooms_calendar` | PASS | 同上 | OK |
| SPEC-API-008〜010 | /api/reservations 参照系(一覧/mine/詳細) | 同上 | docs/06-impl-direction/U002 | `tests.test_reservations_repo_read`, `tests.integration.test_u002_rooms_calendar` | PASS | 同上 | OK |
| SPEC-API-011〜013 | /api/reservations 更新系(POST/PUT/DELETE、参加者ID実在チェック含む) | 同上 | docs/06-impl-direction/U003 | `tests.test_validation`, `tests.test_reservations_repo_write`, `tests.integration.test_u003_reservation_flow` | PASS | 同上 | OK |
| SPEC-API-014〜017 | /api/users (GET/POST/PUT/DELETE) | 同上 | docs/06-impl-direction/U004 | `tests.test_users_repo`, `tests.integration.test_u004_users_and_authz` | PASS | 同上 | OK |
| SPEC-SCREEN-S01 | ログイン画面 | docs/05-test-plan.md 3章 | docs/07-test-direction/T001 | `tests.system.test_t001_full_user_journey` | PASS | docs/test-records/20260730-1600 | OK |
| SPEC-SCREEN-S02/S03/S04/S05 | カレンダー/予約作成/詳細編集/マイ予約(APIシナリオで代替、下記10章参照) | 同上 | docs/07-test-direction/T001 | `tests.system.test_t001_full_user_journey` | PASS | 同上 | OK(UI自体のブラウザテストはNO_TEST_IMPL、10章参照) |
| SPEC-SCREEN-S06/S07 | 会議室管理/ユーザー管理(APIシナリオで代替) | 同上 | docs/07-test-direction/T002 | `tests.system.test_t002_cross_cutting_authorization` | PASS | 同上 | OK(UI自体はNO_TEST_IMPL) |
| SPEC-FLOW-001 | 予約重複エラーのシーケンス(docs/02-frontend-spec.md 4.2) | docs/05-test-plan.md 3章 | docs/07-test-direction/T001, U003結合確認 | `tests.system.test_t001_full_user_journey`, `tests.integration.test_u003_reservation_flow` | PASS | 同上 | OK |
| SPEC-NFR-001 | 性能(カレンダー表示3秒以内目標) | docs/05-test-plan.md 4章 | docs/07-test-direction/T005 | `tests.system.test_t005_performance_calendar` | PASS(参考値: 平均1〜2ms) | docs/test-records/20260730-1600 | OK(本番相当ロード試験は未実施、10章参照) |
| SPEC-NFR-002 | 同時実行時の排他制御(二重予約防止) | docs/05-test-plan.md 4章 | docs/07-test-direction/T003 | `tests.system.test_t003_concurrent_booking` | PASS | 同上 | OK |
| SPEC-NFR-003 | 権限制御(一般ユーザーが管理者機能にアクセス不可) | docs/01-requirement.md テスト方針, docs/05-test-plan.md 4章 | docs/07-test-direction/T002 | `tests.system.test_t002_cross_cutting_authorization` | PASS | 同上 | OK |
| SPEC-NFR-004 | エラーハンドリング共通方針(参加者ID実在チェック・会議室capacity検証含む) | docs/05-test-plan.md 2章 | docs/07-test-direction/T004 | `tests.system.test_t004_error_handling` | PASS(手順6は確認観点2・3検証のため意図的に仕込んだF002で一度FAIL、修正後PASS) | docs/test-records/20260730-1600, 1700, 1730, docs/08-fix-plan/08-fix-resolved.md | OK |
| SPEC-NFR-005 | ログ出力(標準出力) | docs/01-requirement.md 非機能要件 | (テスト指示なし) | (未実装確認) | NOT_RUN | - | NO_TEST_CASE(uvicornの標準出力ログのみで、専用の確認テストは作成していない) |
| SPEC-NFR-006 | 社内SSO連携 | docs/01-requirement.md(将来検討、対象外) | - | - | - | - | 対象外(仕様上スコープ外) |
| SPEC-NFR-007 | 受入テスト(本番相当環境での確認) | docs/05-test-plan.md 1章 | (指示なし) | - | NOT_RUN | - | NO_TEST_PLAN(本番相当環境が本検証にないため実施していない、10章参照) |

## 5. バージョン情報とビルド履歴

* バージョン定義: `VERSION`(`0.1.0`)。`server/app/__init__.py` の `__version__` にも同値を保持。
* 実行モジュールからの確認手段: `GET /health` が `{"status":"ok","version":"0.1.0"}` を返す(実測確認済み、本章作成時に`curl`で確認)。
* ビルド履歴: `BUILD_HISTORY.md`(B001〜B004)。コミットIDは `git log --oneline` で確認可能。

## 6. 配布資産一覧

* `Dockerfile`, `docker-compose.yml`, `.env.example`, `README.md`(いずれも新規作成)
* `server/pyproject.toml`(uvビルド定義。ただし`uv sync`は本検証環境では未実行、10章参照)
* `client/`(静的フロントエンド一式、ビルド不要)

## 7. 起動・実行手順

### ローカル直接起動(実地検証済み)

1. `cd server`
2. `python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
3. ブラウザで `http://localhost:8000/` を開く
4. `admin`/`admin12345` 等でログインする
5. `curl http://localhost:8000/health` でバージョン確認

上記は本検証中に実際に実行し、動作を確認済み(`GET /health`、`POST /api/auth/login`、`GET /`の静的HTML配信を`curl`で実測)。

### Docker Compose 起動手順

1. 前提ソフトウェア(Docker, Docker Compose)を確認する
2. `.env.example` を `.env` にコピーする
3. `docker compose build`
4. `docker compose up -d`
5. `curl http://localhost:8000/health` でヘルスチェック
6. 初期データはアプリ起動時に自動投入されるため追加のマイグレーション手順は不要
7. ブラウザで動作確認する

`docker compose config` によるYAML構文検証は実施済み(構文エラーなし)。ただし本検証環境はネットワーク分離のためベースイメージ取得ができず、`docker compose build`/`up`自体の実行確認はしていない(10章参照)。

## 8. テスト実行手順

```bash
cd server
python3 -m unittest discover -s tests -p "test_*.py"
```

* 格納先: `server/tests/`(`test_*.py`: Unit Test、`tests/integration/`: スプリント内結合、`tests/system/`: スプリントをまたぐ結合・システムテスト)
* テスト結果格納先: `docs/test-records/*.md`
* 合格条件: 67件全てPASS(2026-07-30 17:30時点で満たしている)

## 9. 最終確認結果

* Unit Test: 45/45 PASS
* スプリント内結合テスト: 10/10 PASS
* スプリントをまたぐ結合・システムテスト: 12/12 PASS(T004手順6は一度F002でフェーズ8に引き渡し、修正後PASS)
* 未解決の修正課題: 0件(`docs/08-fix-plan/08-fix-unresolved.md`に「該当なし・ALL_RESOLVED」と明記、検出1件・全件解決)

## 10. 未整備事項・人間による確認事項

* **Docker Compose起動の実地検証未了**: 本検証環境がネットワーク分離されておりベースイメージ取得ができないため、`docker compose build`/`up`を実際には実行していない(`docker compose config`によるYAML構文検証のみ実施済み)。人間による実環境での確認が必要。
* **技術スタックの逸脱**: `docs/01-requirement.md`が指定するFastAPI/React+TS+Viteを、オフライン環境の制約によりStarlette+Pydantic/素のHTML・JSへ置き換えた。V0.2と同一の制約であり、`testbed.md`のとおりV0.3のSKILLルールにもこの点は反映されていない(実行環境起因のためSKILL自体の欠陥ではないと判断)。本番導入前に、正式なFastAPI/React+Viteへの置き換え(または本逸脱の正式な承認)を人間が判断する必要がある。詳細は`e2e-validation-report.md`参照。
* **`uv sync`未実行**: `server/pyproject.toml`は用意したが、ネットワーク制約により`uv`によるビルドは未検証。
* **UI自体の自動テスト(ブラウザ操作)が存在しない**: `docs/05-test-plan.md`5章の方針により、画面操作はAPIシナリオスクリプトで代替した。ブラウザ自動化ツールを用いた実際のクリック・表示確認は未実施(NO_TEST_IMPL)。
* **本番相当の負荷試験・受入テストは未実施**: SPEC-NFR-001(性能)はローカル参考値のみ、SPEC-NFR-007(受入テスト)は本番相当環境がないため実施していない。
* **ログ監視の専用確認テストがない**: SPEC-NFR-005は目視確認のみでNO_TEST_CASE。
* **本番用の秘密情報管理は未整備**: パスワードハッシュ化は実装済みだが、本番デプロイ時のシークレット管理(環境変数の安全な注入方法等)は本検証の範囲外。
* **確認観点2・3の実地検証のため意図的にバグを1件仕込んだ**: `POST /api/rooms`のcapacity検証漏れ(F002)を意図的に仕込み、フェーズ8の修正サイクルを実際に回した(検出→修正→ALL_RESOLVED→OKFリンクの`fixed/`付け替えまで実施・確認済み)。実運用中に見つかった不具合ではなく検証目的のもの。詳細は`e2e-validation-report.md`参照。

## 11. リリース判定

**保留**。理由: 全67件の自動テストはPASSしており機能面・主要な非機能面(排他制御・権限制御・参加者ID検証・会議室capacity検証)は検証できているが、(1)技術スタックがオフライン制約により仕様と異なる、(2)Docker Compose起動が未実地検証、という2点の重要な未確認事項が残るため、人間判断でのリリース可否決定を要する。これらはいずれも「仕様不足」ではなく「本検証環境の制約」に起因するものであり、正式な開発環境で再ビルド・再検証すればOK判定に近づくと考えられる。
