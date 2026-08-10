# 修正計画(目次) — 会議室予約システム

> 本書は `spec-driven-dev` Skill フェーズP202の成果物です。`docs/P201-review-report.md` で列挙されたPASS以外(FAIL/BLOCKED)のテストの修正計画の目次(OKF形式)です。詳細は `docs/P202-fix-plan/fixed/F0NN-{fix-name}.md` を参照してください(全件修正完了のため `fixed/` 配下に移動済み)。

## 修正タスク一覧(OKF形式)

- [x] F001 [sqlite3スレッド安全性不具合の修正](./P202-fix-plan/fixed/F001-sqlite-thread-safety.md) — `check_same_thread=False`を適用。対応: T009, T012, T013, T014, T015, A001, A003(S05側), A004, A006, A010(計10件、単一根本原因)
- [x] F002 [CalendarPageの日付ナビゲーション(タイムゾーン)不具合の修正](./P202-fix-plan/fixed/F002-calendar-adddays-timezone.md) — `addDays()`をUTC基準に統一。対応: T006
- [x] F003 [ReservationDetailPageの無効化済み会議室名表示不具合の修正](./P202-fix-plan/fixed/F003-reservation-detail-inactive-room.md) — 編集フォームの会議室選択肢に無効化済み会議室を含める。対応: A003(S04側)
- [x] F004 [login_failed構造化ログの実装](./P202-fix-plan/fixed/F004-login-failed-logging.md) — 認証失敗時のWARNINGログ出力を追加。対応: A008

## 補足

* 全4件の修正タスクがP203で完了した(2026-08-09)。詳細は `docs/P202-fix-plan/P202-fix-resolved.md` を参照。
* `docs/P202-fix-plan/P202-fix-unresolved.md` に記載すべき未解決障害は無い。
* いずれも原因区分は「アプリケーションコードの欠陥」であり、「テスト指示側の誤り」に該当するものは無かった(F004について検討したが該当せずと判定した経緯を`docs/P202-fix-plan/fixed/F004-login-failed-logging.md`に記録済み)。
* F001の修正確認の過程で、対象10件のうち3件(T012, T013, A010)はF001適用後も別の原因(いずれも今回P103/P201で新規作成したテストコード自体の作成ミスであり、アプリケーションコードの不具合ではない)で失敗し続けたため、テストコード側を追加で修正した。詳細は`docs/P202-fix-plan/fixed/F001-sqlite-thread-safety.md`の修正経緯を参照。
