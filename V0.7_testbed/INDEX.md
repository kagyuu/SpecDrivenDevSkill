# INDEX — 会議室予約システム(プロジェクト全体の目次)

> 本書は `spec-driven-dev` Skill フェーズP301の成果物(INDEX形式)です。
> インプット: `server/INDEX.md`、`client/INDEX.md`、`docs/ArchitectureHandbook.md`、`docs/ADR.md`、`docs/P001-requirement.md` 〜 `docs/P009-acceptance-direction.md`
> **更新(CR-001 / P903 2026-08-05)**: CR-001(予約にオンライン会議URL)の対応にともない、第3章・第4章を更新しました(`docs/CR.md` / `docs/P901-cr-direction/` / `docs/P903-cr-records/` の追加、ADR-011、テスト記録2件)。
> 主にAIが参照する。人間がプロジェクト全体を把握する入口としても使う。
> ソースツリーの内容そのものは転記せず、各ソースツリーの `INDEX.md` へのリンクのみを載せる(`SKILL.md`「INDEX形式について」)。

## 0. このプロジェクトは何か

社内の会議室予約システム(従業員300名・会議室10室規模)。7画面(S01〜S07)と17本のREST API(API-01〜API-17)、SQLite単一ファイルのデータストアからなる。1つのASGIプロセスが API と フロントエンドの静的ファイルの**双方を同一オリジンで**配信する(ADR-010)。

* 現在の到達点: 設計(P001〜P012)・概観(P020〜P022)・実装(P101〜P104)・最終確認ループ(P201〜P205)まで完了。結合テストT001〜T018 と受け入れ結合テストA001〜A012 は全30件PASS。
* 配布・起動方法とリリース判定は `docs/P302-deliver.md` を参照する。

## 1. ソースツリー

| パス | 目次 | 概要 |
| --- | --- | --- |
| `server/` | [server/INDEX.md](./server/INDEX.md) | バックエンド(Python 3.11 + Starlette + Pydantic v2、外部DBプロセスなしのSQLite)。API-01〜API-17、静的ファイル配信、差分適用マイグレーション、単体/結合/受け入れテスト |
| `client/` | [client/INDEX.md](./client/INDEX.md) | フロントエンド(ビルドツールを使わない素のHTML/CSS + ESモジュール)。S01〜S07の7画面、ハッシュルーティングSPA、単体/結合/受け入れテスト |

* この2つ以外のソースツリーはない。ソースツリー内の個々のファイルの説明は、それぞれの `INDEX.md` を参照する。

## 2. 配布・実行資産(リポジトリ直下)

| パス | 概要 |
| --- | --- |
| [Dockerfile](./Dockerfile) | 単一イメージ(`server/` と `client/` を同一イメージに同梱し、1プロセスで両方を配信する。ADR-010) |
| [docker-compose.yml](./docker-compose.yml) | サービス提供型システムとしての起動定義(既定は `app` 単体。TLS終端リバースプロキシは `tls` プロファイル) |
| [.env.example](./.env.example) | 環境変数のひな形(`DB_PATH` / セッション期限 / 初期管理者) |
| `.dockerignore` | イメージに含めないもの(`__pycache__` / `*.db` / `docs/` / `.env` / 証明書) |
| [deploy/nginx.conf.example](./deploy/nginx.conf.example) | TLS終端リバースプロキシの設定例(同一オリジンを保ったまま `/` と `/api/*` の双方を `app` へ渡す) |
| [VERSION](./VERSION) | 配布単位のバージョン |
| [BUILD_HISTORY.md](./BUILD_HISTORY.md) | ビルド・テスト実行履歴 |
| [README.md](./README.md) | 最短の起動手順と本INDEXへの入口 |

## 3. 設計・計画ドキュメント(`docs/`)

### 3.1 要件定義・設計(Plan Loop Step)

| ドキュメント | 概要 |
| --- | --- |
| [docs/P001-requirement.md](./docs/P001-requirement.md) | システム要件定義書。48件の要求ID(REQ-PRE / REQ-TECH / REQ-SCREEN / REQ-TRANS / REQ-ITEM / REQ-API / REQ-NFR / REQ-TEST)の出発点 |
| [docs/P001-requirement_20260805_CR-001.md](./docs/P001-requirement_20260805_CR-001.md) | CR-001 による更新前の P001 原本(P902が退避) |
| [docs/P002-frontend-spec.md](./docs/P002-frontend-spec.md) | ユーザインタフェース設計書。S01〜S07の画面項目・入力ルール・画面遷移、および**API契約の単一の正**(第5章。ADR-002) |
| [docs/P003-backend-spec.md](./docs/P003-backend-spec.md) | システム詳細設計書。層構成・データモデル・重複チェック・認証認可・API内部処理・静的配信、および**非機能要件の担当フェーズと委譲先**(第8章) |
| [docs/P004-traceability-matrix.md](./docs/P004-traceability-matrix.md) | 要求トレーサビリティマトリクス。全**49**要求ID(CR-001による REQ-ITEM-008 を含む)がP002・P003で満たされていることの検証結果、技術要求の逸脱2件、過剰実装6件 |
| [docs/P005-impl-plan.md](./docs/P005-impl-plan.md) | 実装計画書。Sprint 1〜4への分割と、インフラ専用スプリントを設けない判断(第4章) |
| [docs/P006-test-plan.md](./docs/P006-test-plan.md) | テスト計画書。テスト観点(V-F / V-N / V-O)、テストレベル別計画、基準データセット(第5章)、合否判定 |

### 3.2 実装・テストの作業指示書(Agent向け。OKF形式の目次 + 子ドキュメント)

| ドキュメント | 概要 |
| --- | --- |
| [docs/P007-impl-direction.md](./docs/P007-impl-direction.md) | プログラム実装定義 兼 プログラミング指示書の目次。子: [U001](./docs/P007-impl-direction/U001-foundation-auth.md) 共通基盤・認証 / [U002](./docs/P007-impl-direction/U002-master-management.md) マスタ管理 / [U003](./docs/P007-impl-direction/U003-reservation-core.md) 予約コア / [U004](./docs/P007-impl-direction/U004-reservation-ui.md) 予約UI |
| [docs/P008-test-direction.md](./docs/P008-test-direction.md) | 結合テスト定義(スプリント内/モジュール間)の目次。子: [T001〜T018](./docs/P008-test-direction/)(全18件 `[x]`) |
| [docs/P009-acceptance-direction.md](./docs/P009-acceptance-direction.md) | 受け入れ結合テスト定義(スプリント横断/システム/受入)の目次。子: [A001〜A012](./docs/P009-acceptance-direction/)(全12件 `[x]`) |
| [docs/P101-impl-context.md](./docs/P101-impl-context.md) | 実装担当Agent向けの実装コンテキスト要約(Executor Stepの入口) |

### 3.3 レビュー・影響分析・修正の記録

| ドキュメント | 概要 |
| --- | --- |
| [docs/P010-design-review.md](./docs/P010-design-review.md) | 設計書横断レビュー結果(矛盾点一覧と解消状況) |
| [docs/P011-impact-analysis.md](./docs/P011-impact-analysis.md) | P010の矛盾点に対する影響分析(修正はP012で実施) |
| [docs/P201-review-report.md](./docs/P201-review-report.md) | 実装横断レビュー結果。T001〜**T019** / A001〜A012 の最終結果一覧と、合否に含めない申し送り事項(第5章)。**※CR-001 反映後の判定は第8章** |
| [docs/P202-fix-plan.md](./docs/P202-fix-plan.md) | 修正計画書の目次。子(対応済み): [F001](./docs/P202-fix-plan/fixed/F001-t016-capacity-expectation.md) T016期待値 / [F002](./docs/P202-fix-plan/fixed/F002-a001-half-open-slot-expectation.md) A001期待値 |
| [docs/P202-fix-plan/P202-fix-resolved.md](./docs/P202-fix-plan/P202-fix-resolved.md) | 解決済み修正障害一覧(F001 / F002) |
| [docs/P202-fix-plan/P202-fix-unresolved.md](./docs/P202-fix-plan/P202-fix-unresolved.md) | 未解決テスト・未修正障害一覧(**未解決0件**)+ 人間の確認を要する事項5件 |
| [docs/P204-impact-analysis.md](./docs/P204-impact-analysis.md) | 修正による影響分析結果(他機能を壊していないことの確認) |

### 3.4 横断ドキュメント(仕様の背景と技術概観)

| ドキュメント | 概要 |
| --- | --- |
| [docs/ADR.md](./docs/ADR.md) | 現在有効な設計判断(ADR-001〜**ADR-011**)。「なぜ今の仕様・構成になっているか」の一次情報。ADR-011 は CR-001(予約のオンライン会議URL)による追加 |
| [docs/ArchitectureHandbook.md](./docs/ArchitectureHandbook.md) | アプリケーションの技術的側面のハンドブック。「どこに何が書いてあるか」と実装・運用の要点 |

### 3.5 テスト実行記録

| ドキュメント | 概要 |
| --- | --- |
| [docs/test-records/20260805-1152-test-record.md](./docs/test-records/20260805-1152-test-record.md) | P103 第1回: T001〜T010 |
| [docs/test-records/20260805-1226-test-record.md](./docs/test-records/20260805-1226-test-record.md) | P103 第2回: T011〜T018、およびT001〜T010の退行確認 |
| [docs/test-records/20260805-1603-test-record.md](./docs/test-records/20260805-1603-test-record.md) | P201 第1回: A001〜A012(A001手順5・T016手順7のFAILを検出) |
| [docs/test-records/20260805-1620-test-record.md](./docs/test-records/20260805-1620-test-record.md) | P205 再実施: T016 / A001 の再実行と全件PASSの確認 |
| [docs/test-records/20260805-1723-test-record.md](./docs/test-records/20260805-1723-test-record.md) | P103(※CR-001): T019新規 / T016・T017・T004・A007・A001 の再実行、マイグレーション冪等性の手動確認 |
| [docs/test-records/20260805-1731-test-record.md](./docs/test-records/20260805-1731-test-record.md) | P201 第3回(※CR-001): 結合19件 / 受入12件の全件再実行と集計 |

### 3.6 納品

| ドキュメント | 概要 |
| --- | --- |
| [docs/P302-deliver.md](./docs/P302-deliver.md) | 成果物まとめ・配布手順指示書。仕様/テスト/テスト実装の対応表、バージョンとビルド履歴、配布資産一覧、起動・テスト実行手順、未整備事項、**リリース判定** |

## 4. 変更要求(CR)

| パス | 内容 |
| --- | --- |
| [docs/CR.md](./docs/CR.md) | **CR状態の台帳**(一覧表のみ。CR本文は持たない)。状態・優先度の唯一の正。完了したCRの行も削除せず残す |
| [docs/P901-cr-direction/CR-001.md](./docs/P901-cr-direction/CR-001.md) | 変更要求 CR-001「予約にオンライン会議URLを登録できるようにしてほしい」(何をなぜ変えてほしいか) |
| [docs/P903-cr-records/CR-001.md](./docs/P903-cr-records/CR-001.md) | CR-001 の対処記録(スコープ決定 / 対処内容 / 反映確認 / ADR更新確認) |

* CR一覧(2026-08-05 時点): **CR-001 = 完了(優先度 中)**。詳細と状態は `docs/CR.md` を参照する。
* 納品後に改善・修正の要望が出た場合は、Refactor Step の P901(変更要求作成)から入る。CRの目次は `docs/CR.md` が兼ねるため `docs/P901-cr-direction.md` は作らない。

## 5. 読む順番の目安

* **仕様を知りたい**: `docs/P001-requirement.md` → `docs/P002-frontend-spec.md` → `docs/P003-backend-spec.md`
* **なぜこの構成なのかを知りたい**: `docs/ADR.md` → `docs/ArchitectureHandbook.md`
* **コードを触りたい**: `docs/ArchitectureHandbook.md` → `server/INDEX.md` / `client/INDEX.md` → `docs/P007-impl-direction.md`
* **動かしたい・配りたい**: `README.md` → `docs/P302-deliver.md`
* **品質状況を知りたい**: `docs/P201-review-report.md` → `docs/P202-fix-plan/P202-fix-unresolved.md` → `docs/test-records/`
