# プロジェクトリポジトリ全体 INDEX

> 本ファイルは `spec-driven-dev` Skill フェーズP301の成果物。プロジェクト全体の入口となる目次(INDEX形式)。
> 各ソースツリーの詳細は `client/INDEX.md`・`server/INDEX.md` を参照(本ファイルには内容を転記しない)。

## アプリケーション概要

会議室予約システム(社内向けWebアプリケーション)。フロントエンド(`client/`)+ バックエンドAPI(`server/`)+ SQLite の構成。詳細は `docs/P001-requirement.md`・`docs/ArchitectureHandbook.md` を参照。

## ソースツリー

* [`server/INDEX.md`](./server/INDEX.md) — バックエンド(Starlette + Pydantic 2 + SQLite、ADR-002のFastAPI代替)。API実装・Repository/Service層・単体テスト121件の目次。
* [`client/INDEX.md`](./client/INDEX.md) — フロントエンド(プレーンHTML/CSS/JavaScript、ADR-001のReact+TS+Vite代替)。画面(S01〜S07)実装・単体テスト38件の目次(CR-001対応で35件→38件)。

## 設計ドキュメント(`docs/`)

* [`docs/P001-requirement.md`](./docs/P001-requirement.md) — システム要件定義書
* [`docs/P002-frontend-spec.md`](./docs/P002-frontend-spec.md) — ユーザインタフェース設計書
* [`docs/P003-backend-spec.md`](./docs/P003-backend-spec.md) — システム詳細設計書
* [`docs/P004-traceability-matrix.md`](./docs/P004-traceability-matrix.md) — 要求トレーサビリティマトリクス
* [`docs/P005-impl-plan.md`](./docs/P005-impl-plan.md) — 実装計画書
* [`docs/P006-test-plan.md`](./docs/P006-test-plan.md) — テスト計画書
* [`docs/P007-impl-direction.md`](./docs/P007-impl-direction.md) — プログラム実装定義(目次、U001〜U005。U005はCR-001対応で追加)
* [`docs/P008-test-direction.md`](./docs/P008-test-direction.md) — 結合テスト定義(目次、T001〜T020、全PASS)
* [`docs/P009-acceptance-direction.md`](./docs/P009-acceptance-direction.md) — 受け入れ結合テスト定義(目次、A001〜A010、全PASS)
* [`docs/P010-design-review.md`](./docs/P010-design-review.md) — 設計書横断レビュー結果(第1回で矛盾0件)
* [`docs/P101-impl-context.md`](./docs/P101-impl-context.md) — 実装コンテキスト(サンドボックス制約・deviation一覧)
* [`docs/P201-review-report.md`](./docs/P201-review-report.md) — 実装横断レビュー結果(第2回で全件PASS)
* [`docs/P202-fix-plan.md`](./docs/P202-fix-plan.md) — 修正計画書(目次、F001〜F003、全解決済み)
* [`docs/P204-impact-analysis.md`](./docs/P204-impact-analysis.md) — 修正による影響分析結果(回帰なし)
* [`docs/P302-deliver.md`](./docs/P302-deliver.md) — 成果物まとめ・配布手順指示書
* [`docs/ArchitectureHandbook.md`](./docs/ArchitectureHandbook.md) — アプリケーションの技術的側面のハンドブック
* [`docs/ADR.md`](./docs/ADR.md) — 現在有効な設計判断(ADR-001〜ADR-007)

## 修正計画の詳細(P202-fix-plan/)

* [`docs/P202-fix-plan/P202-fix-resolved.md`](./docs/P202-fix-plan/P202-fix-resolved.md) — 解決済み修正障害一覧(F001〜F003、全件RESOLVED)
* [`docs/P202-fix-plan/P202-fix-unresolved.md`](./docs/P202-fix-plan/P202-fix-unresolved.md) — 未解決テスト・未修正障害一覧(該当なし)
* [`docs/P202-fix-plan/fixed/`](./docs/P202-fix-plan/fixed/) — 対応済み修正指示書(詳細付き)

## テスト実行記録(`docs/test-records/`)

* [`docs/test-records/20260803-1830-test-record.md`](./docs/test-records/20260803-1830-test-record.md) — P103結合テスト実行記録(T001〜T020、全PASS)
* [`docs/test-records/20260803-1900-test-record.md`](./docs/test-records/20260803-1900-test-record.md) — P201受け入れ結合テスト実行記録・第1回(A001〜A010、PASS以外10件)
* [`docs/test-records/20260803-1930-test-record.md`](./docs/test-records/20260803-1930-test-record.md) — P205受け入れ結合テスト再実行記録(A001〜A010、全PASS)
* [`docs/test-records/20260803-1810-cr001-test-record.md`](./docs/test-records/20260803-1810-cr001-test-record.md) — Refactor(P903、CR-001対応)テスト実行記録(フロントエンド38件・バックエンド121件、全PASS)

## CR / cr-records

* [`docs/CR.md`](./docs/CR.md) — 現在未対応・対応中のCR一覧(本ラウンド終了時点で該当なし)。
* [`docs/cr-records/CR-001.md`](./docs/cr-records/CR-001.md) — 対応完了したCRの記録(終日チェックボックス追加、2026-08-03完了)。

## 参照

* [`testbed.md`](./testbed.md)(このプロジェクトの検証メモ、リポジトリルート直下)は `spec-driven-dev` Skillの成果物ではなく、検証者が実行記録を残すための別ファイルである。
