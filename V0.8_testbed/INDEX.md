# V0.8_testbed リポジトリ全体 INDEX

> `spec-driven-dev` Skillフェーズ P301(初版作成)・P302(配布資産リンクの最終更新)の成果物です。会議室予約システム(`docs/P001-requirement.md`)の全体像を素早く把握するための入口として使ってください。INDEX形式(進捗管理の意味は持たない、単純なパス+一言概要の一覧。`SKILL.md`「INDEX形式について」参照。OKF形式ではないため状態チェックボックスは使いません)。

## ソースツリー

* `server/` — [`server/INDEX.md`](./server/INDEX.md) — バックエンド。Python + FastAPI + 標準ライブラリ`sqlite3`(ADR-002)。`/api/*` 群 + `GET /health` + `GET /version`(P302で新規追加)
* `client/` — [`client/INDEX.md`](./client/INDEX.md) — フロントエンド。React + TypeScript + Vite(ADR-001)。7画面(S01〜S07)のSPA

## docs/ 主要ドキュメント

### Plan Loop(P001〜P012)

* [P001 要件定義](./docs/P001-requirement.md) — 会議室予約システムの要件・画面一覧・API一覧・非機能要求
* [P002 フロントエンド仕様](./docs/P002-frontend-spec.md) — 画面7つの外部契約
* [P003 バックエンド仕様](./docs/P003-backend-spec.md) — API内部実現・DB設計・マイグレーション方式
* [P004 トレーサビリティマトリクス](./docs/P004-traceability-matrix.md) — 要求ID30件、全件OK(CR-001でREQ-SCREEN-003/004・REQ-API-010/011/012を再検証、引き続き全件OK)
* [P005 実装計画](./docs/P005-impl-plan.md)
* [P006 テスト計画](./docs/P006-test-plan.md) — 4テストレベルの方針
* [P007 実装指示(目次、OKF形式)](./docs/P007-impl-direction.md) — U001〜U005、全件完了(CR-001: U003-T7〜T9・U004-T6〜T7を追加、完了)
* [P008 結合テスト指示(目次、OKF形式)](./docs/P008-test-direction.md) — T001〜T016、全件完了・PASS(CR-001でT016追加)
* [P009 受入テスト指示(目次、OKF形式)](./docs/P009-acceptance-direction.md) — A001〜A011、全件完了・PASS(CR-001でA001を改訂・再実行)
* [P010 設計レビュー](./docs/P010-design-review.md) — CR-001対応レビュー(1回目、矛盾0件)を追記済み
* [P011 影響分析](./docs/P011-impact-analysis.md)

### Overview(P020〜P022)

* [ArchitectureHandbook](./docs/ArchitectureHandbook.md) — 全体構成・技術スタック・既知の制約(9章に★ACCEPTED★4件・★FIXME★1件)
* [ADR一覧](./docs/ADR.md) — ADR-001(フロントエンド技術)〜ADR-004(マイグレーション方式)

### Executor(P101〜P104)

* [P101 実装コンテキスト](./docs/P101-impl-context.md)

### Reviewer Loop(P201〜P205)

* [P201 レビュー報告(通常フロー第2回 + CR-001対応1回目)](./docs/P201-review-report.md) — 通常フロー26/26 PASS、CR-001対応分(T016・A001)2/2 PASS
* [P202 修正計画(目次、OKF形式)](./docs/P202-fix-plan.md) — F001〜F004
* [解決済み修正一覧](./docs/P202-fix-plan/P202-fix-resolved.md) — ALL_RESOLVED(4件)
* [未解決一覧](./docs/P202-fix-plan/P202-fix-unresolved.md) — 0件
* [P204 影響分析](./docs/P204-impact-analysis.md)

### Closing(P301〜P302)

* `./INDEX.md`(本ファイル)
* [P302 成果物まとめ・配布手順・リリース判定](./docs/P302-deliver.md) — リリース判定: 保留(Docker未検証、9〜11章参照)。CR-001対応版として再配布(テスト228/228 PASS、9章「CR-001対応後の最終確認結果」参照)

### テスト記録

* [20260809-1500 P103結合テスト記録](./docs/test-records/20260809-1500-test-record.md)
* [20260809-1900 P201第1回受入テスト記録](./docs/test-records/20260809-1900-test-record.md)
* [20260809-2100 P205再実行記録](./docs/test-records/20260809-2100-test-record.md)
* [20260809-2200 CR-001: P103内T016記録](./docs/test-records/20260809-2200-test-record.md)
* [20260809-2230 CR-001: P201内A001再実行記録](./docs/test-records/20260809-2230-test-record.md)

### CR(Change Request)関連

* [`docs/CR.md`](./docs/CR.md) — CR状態台帳。CR-001(オンライン会議URL追加)、状態`完了`(P904反映確認済み)
* [`docs/P901-cr-direction/CR-001.md`](./docs/P901-cr-direction/CR-001.md) — CR-001の変更要求書
* [`docs/P903-cr-records/CR-001.md`](./docs/P903-cr-records/CR-001.md) — CR-001の対処記録

## 配布資産(P302で新規作成。ビルド・起動はDocker未使用のため未検証 — `docs/P302-deliver.md` 6・9〜11章参照)

* [`docker-compose.yml`](./docker-compose.yml) — `server`(バックエンド)・`client`(nginx配信のSPA + `/api/`リバースプロキシ)の2サービス構成
* [`.env.example`](./.env.example) — `CLIENT_PORT` / `COOKIE_SECURE` の設定例
* [`server/Dockerfile`](./server/Dockerfile) — バックエンドイメージ(`python:3.11-slim`)
* [`server/.dockerignore`](./server/.dockerignore)
* [`client/Dockerfile`](./client/Dockerfile) — フロントエンドイメージ(マルチステージ: `node:20-alpine` ビルド → `nginx:1.27-alpine` 配信)
* [`client/nginx.conf`](./client/nginx.conf) — SPA配信 + `/api/`リバースプロキシ(実行前チェック7.の是正そのもの。`docs/P302-deliver.md` 6章参照)
* [`client/.dockerignore`](./client/.dockerignore)
* [`docs/BUILD_HISTORY.md`](./docs/BUILD_HISTORY.md) — ビルド・テスト実行履歴(B1〜B4)
* バージョン定義: `server/pyproject.toml` / `client/package.json`(いずれも `0.1.0`)。実行時確認は `GET /version`(P302で新規追加)
