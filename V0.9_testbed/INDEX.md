# プロジェクトリポジトリ全体 INDEX

会議室予約システム(`spec-driven-dev` Skillにより作成)。バージョン `1.1.0`(`VERSION` 参照。CR-001対応によりMINORを更新)。**リリース判定: 保留**(理由は `docs/P302-deliver.md` 11章・「CR-001対応」節参照)。

## ソースツリー

- [server/INDEX.md](./server/INDEX.md) — バックエンド(Python + FastAPI + SQLite)の目次
- [client/INDEX.md](./client/INDEX.md) — フロントエンド(React + TypeScript + Vite)の目次

## 主要ドキュメント(docs/)

| ドキュメント | 内容 |
| --- | --- |
| [docs/P001-requirement.md](./docs/P001-requirement.md) | システム要件定義書 |
| [docs/P002-frontend-spec.md](./docs/P002-frontend-spec.md) | ユーザインタフェース設計書 |
| [docs/P003-backend-spec.md](./docs/P003-backend-spec.md) | システム詳細設計書 |
| [docs/P004-traceability-matrix.md](./docs/P004-traceability-matrix.md) | 要求トレーサビリティマトリクス |
| [docs/P005-impl-plan.md](./docs/P005-impl-plan.md) | 実装計画書(スプリント構成) |
| [docs/P006-test-plan.md](./docs/P006-test-plan.md) | テスト計画書 |
| [docs/P007-impl-direction.md](./docs/P007-impl-direction.md) | プログラム実装定義(目次) |
| [docs/P008-test-direction.md](./docs/P008-test-direction.md) | 結合テスト定義(目次) |
| [docs/P009-acceptance-direction.md](./docs/P009-acceptance-direction.md) | 受け入れ結合テスト定義(目次) |
| [docs/P010-design-review.md](./docs/P010-design-review.md) | 設計書横断レビュー結果(2回実行、矛盾解消済み) |
| [docs/P011-impact-analysis.md](./docs/P011-impact-analysis.md) | 設計矛盾の影響分析結果 |
| [docs/P101-impl-context.md](./docs/P101-impl-context.md) | 実装コンテキスト要約 |
| [docs/P201-review-report.md](./docs/P201-review-report.md) | 実装横断レビュー結果(2回実行+CR-001対応分、全件PASS) |
| [docs/P202-fix-plan.md](./docs/P202-fix-plan.md) | 修正計画(目次、F001〜F005全件解決済み) |
| [docs/P204-impact-analysis.md](./docs/P204-impact-analysis.md) | 修正による影響分析結果 |
| [docs/P302-deliver.md](./docs/P302-deliver.md) | 納品物まとめ・リリース判定(保留、根拠あり) |
| [docs/ArchitectureHandbook.md](./docs/ArchitectureHandbook.md) | アプリケーション技術ハンドブック |
| [docs/ADR.md](./docs/ADR.md) | 有効な設計判断(ADR-001〜005) |
| [docs/test-records/](./docs/test-records/) | テスト実行記録一式 |

## 配布資産(P302で整備。Docker実機検証は未実施、docs/P302-deliver.md §9参照)

| 資産 | 内容 |
| --- | --- |
| [docker-compose.yml](./docker-compose.yml) | `web`(nginx)・`server`(FastAPI)の2サービス構成 |
| [server/Dockerfile](./server/Dockerfile) | バックエンドイメージ定義 |
| [client/Dockerfile](./client/Dockerfile) | フロントエンドイメージ定義(マルチステージ、nginx配信) |
| [client/nginx.conf](./client/nginx.conf) | 静的配信 + `/api` リバースプロキシ(同一オリジン化) |
| [.env.example](./.env.example) | 環境変数の例 |
| [VERSION](./VERSION) | バージョン `1.1.0` |
| [BUILD_HISTORY.md](./BUILD_HISTORY.md) | ビルド履歴(BUILD-001〜BUILD-004、全PASS。BUILD-004はCR-001対応分) |
| [README.md](./README.md) | クイックスタート・開発環境起動手順 |

## 変更要求(CR)

* [docs/CR.md](./docs/CR.md) — CR状態台帳。CR-001(完了)・CR-002(却下)。
* CR-001(予約への「備考(社内向けメモ)」欄追加): [変更要求](./docs/P901-cr-direction/CR-001.md) / [対処記録](./docs/P903-cr-records/CR-001.md)。バージョン`1.0.0`→`1.1.0`(MINOR)の起点。
* CR-002(社内チャット機能追加の要望): [変更要求](./docs/P901-cr-direction/CR-002.md) / [対処記録](./docs/P903-cr-records/CR-002.md)(却下、起票時点でスコープ外と判断)。

---
_本ファイルはP301(全体INDEX作成)で新規作成し、P302(納品物作成)完了時に配布資産へのリンクを追記した。_
