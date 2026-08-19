# 受け入れ結合テスト定義(スプリント横断/システム/受入) 兼 テスト指示書 — 目次

> 本書は `spec-driven-dev` Skill フェーズP009の成果物。`docs/P001-requirement.md`・`docs/P006-test-plan.md` にもとづき、スプリントをまたぐ結合テスト・システムテスト・受け入れテストを定義する。実行はP201(Reviewer Loop)が行う。純粋な単体テスト・単一スプリントに閉じた結合テストは対象外(`docs/P007-impl-direction.md`・`docs/P008-test-direction.md` 側で指示済み)。

## テスト実行環境(全テスト共通)

本システムはクライアント・サーバを別プロセス・別ポートで起動する構成であるため、テストハーネスのトポロジーは `docs/ADR.md` **ADR-006**(開発サーバのproxyによる同一オリジン化、CORS不採用)に従う。本書および各A0NNテストで独自にトポロジーを決めない(`docs/P003-backend-spec.md` §2.3 参照)。

* ブラウザを用いるテスト(Playwright)は、`client/playwright.config.ts` の `webServer` 設定によりバックエンド(uvicorn, `:8000`)とフロントエンド(Vite, `:5173`)の両方を起動し、**ブラウザからは同一オリジン `http://localhost:5173` にのみアクセスする**。API呼び出しはVite開発サーバのproxy経由でバックエンドへ転送される。
* テストコードからバックエンドへ直接(`http://localhost:8000`)アクセスしないこと。直接アクセスすると同一オリジン前提が検証されず、`docs/P302-deliver.md` 実行前チェック項目7で検出されるべき不整合を見逃す。
* サーバ側で完結するテスト(A003・A005・A008・A009)は、この限りではない(ブラウザを介さないため)。

**テストデータのライフサイクル**: `docs/P006-test-plan.md` §5「テストデータのライフサイクル方針」に従う。ブラウザを用いるテストは、スイート実行ごとに1回、**バックエンド起動前**にE2E用データストアをベースライン(マイグレーション適用直後)へ復元する(`client/scripts/reset-e2e-db.mjs`、`client/playwright.config.ts` の `webServer` 起動コマンドから実行)。各テストに復元手順を書かない。これによりスイートを続けて何度実行しても同じ結果になる。

* 再起動耐性を確認するA005は、データが永続すること自体を検証するテストであるため、上記の復元と衝突しないよう**サーバ側のpytestスイート**(`server/tests/acceptance/test_a005_restart_resilience.py`)に置き、ブラウザ側のE2E用データストアとは別のデータストアを用いる。

## テストケース一覧(OKF形式)

- [x] A001 [一般ユーザーの標準的な業務フロー(ログイン〜予約作成〜編集〜取消)](./P009-acceptance-direction/A001-general-user-journey.md) — 受け入れテスト相当、複数スプリントをまたぐ(PASS、P202 F001・F002対応後)
- [x] A002 [管理者の標準的な業務フロー(会議室登録〜ユーザー登録〜代理編集)](./P009-acceptance-direction/A002-admin-journey.md) — 受け入れテスト相当(PASS、P202 F003対応後)
- [x] A003 [認証・認可をまたぐ横断確認(一般ユーザー/管理者/他人のリソース)](./P009-acceptance-direction/A003-cross-cutting-authorization.md) — システムテスト相当(PASS)
- [x] A004 [予約重複防止のシステム全体確認(境界値を含む)](./P009-acceptance-direction/A004-reservation-conflict-system-check.md) — 複数APIをまたぐ業務フロー(PASS、P202 F004でテスト指示を訂正後)
- [x] A005 [アプリケーション再起動耐性確認](./P009-acceptance-direction/A005-restart-resilience.md) — 運用観点、`docs/P003-backend-spec.md` §4・`docs/P006-test-plan.md` §4の担当フェーズ(PASS)
- [x] A006 [会議室無効化後の既存予約の扱い確認](./P009-acceptance-direction/A006-room-deactivation-existing-reservations.md) — 業務シナリオ(PASS、P202 F003対応後)
- [x] A007 [非機能: カレンダー表示の応答性確認](./P009-acceptance-direction/A007-performance-calendar.md) — 非機能テスト(実行可能な範囲)(PASS、P202 F003対応後。実測3回とも3秒以内)
- [x] A008 [非機能: パスワードの非露出確認](./P009-acceptance-direction/A008-security-password-exposure.md) — 非機能テスト(セキュリティ)(PASS)
- [x] A009 [運用者視点: 構造化ログ出力確認](./P009-acceptance-direction/A009-structured-logging.md) — 受け入れテスト相当(運用者視点)(PASS、P202 F005対応後)

## 備考

* 全テストが `[x]`、かつ全件PASS(P205再実施、2026-08-11)。P201初回実行時点では5件FAILだったが、P202〜P205(F001〜F005)で修正済み。経緯は `docs/test-records/20260811-0530-test-record.md`(初回)・`docs/test-records/20260811-0545-test-record.md`(再実施)を参照。
* 再起動耐性(A005)は、`docs/P006-test-plan.md` §4で明記したとおり、単体テスト(P007)・スプリント内結合テスト(P008)ではなく本フェーズが担当する(結果: PASS)。
