# 修正計画書 — 目次

> 本書は `spec-driven-dev` Skill フェーズP202の成果物。`docs/P201-review-report.md`(1回目実行)で列挙されたFAILを修正する計画をまとめる。

## 修正タスク一覧(OKF形式)

- [x] F001 [S02にログインユーザー名表示・ログアウト導線を実装する](./P202-fix-plan/fixed/F001-calendar-page-username-logout.md) — 対応: T001
- [x] F002 [日付計算のタイムゾーン処理を修正する](./P202-fix-plan/fixed/F002-date-timezone-fix.md) — 対応: T003, A001
- [x] F003 [sqlite3接続のスレッド不整合を修正する](./P202-fix-plan/fixed/F003-sqlite-thread-safety.md) — 対応: T006, A002, A006, A007
- [x] F004 [A004のテスト指示の期待値を訂正する(テスト指示側の誤り)](./P202-fix-plan/fixed/F004-a004-back-to-back-expectation.md) — 対応: A004
- [x] F005 [失敗時のアクセスログにerror_codeを含める](./P202-fix-plan/fixed/F005-access-log-error-code.md) — 対応: A009

## 備考

* F002・F003は、複数の失敗テストが単一の根本原因に起因すると判断できたため、`SKILL-P202-fix-plan.md` の例外規定にもとづき1ファイルにまとめた(根拠は各ファイル内の【障害記録】参照)。
* 全5件が解決済み。詳細は `docs/P202-fix-plan/P202-fix-resolved.md` を参照。未解決の障害は無い(`docs/P202-fix-plan/P202-fix-unresolved.md` は作成していない)。
