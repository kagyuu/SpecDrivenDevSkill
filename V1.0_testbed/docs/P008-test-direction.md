# 結合テスト定義(スプリント内/モジュール間) 兼 結合テスト指示書 — 目次

> 本書は `spec-driven-dev` Skill フェーズP008の成果物。`docs/P006-test-plan.md`・`docs/P007-impl-direction.md` にもとづき、各スプリントに閉じた結合テスト(画面とAPIの接続、DB・Repository・Service・APIの組み合わせ)を定義する。実行はP103(Executor)が行う。純粋な関数単位の単体テストは対象外(`docs/P007-impl-direction.md` 側で指示済み)。スプリントをまたぐ結合テスト・システムテスト・受け入れテストは `docs/P009-acceptance-direction.md` を参照。

## テストケース一覧(OKF形式)

- [x] T001 [ログイン〜自分情報〜会議室一覧の結合確認](./P008-test-direction/T001-login-me-rooms-flow.md) — U001範囲、正常系の一連疎通(PASS、P202 F001対応後。`docs/test-records/20260811-0545-test-record.md` 参照)
- [x] T002 [未認証・無効セッションでの401結合確認](./P008-test-direction/T002-unauthenticated-access.md) — U001範囲(PASS)
- [x] T003 [予約作成→カレンダー一覧反映の結合確認](./P008-test-direction/T003-reservation-create-reflects-calendar.md) — U002範囲、画面/API/DB結合(PASS、P202 F002対応後)
- [x] T004 [予約重複エラーのフロント表示結合確認](./P008-test-direction/T004-reservation-conflict-display.md) — U002範囲(PASS)
- [x] T005 [マイ予約一覧periodフィルタの結合確認](./P008-test-direction/T005-my-reservations-period-filter.md) — U002範囲(PASS)
- [x] T006 [予約編集(自己除外重複)の結合確認](./P008-test-direction/T006-reservation-update-self-exclusion.md) — U003範囲(PASS、P202 F003対応後)
- [x] T007 [会議室論理削除が予約作成画面の選択肢から除外される結合確認](./P008-test-direction/T007-room-deactivation-removes-from-picker.md) — U003範囲(PASS)
- [x] T008 [社員ID重複登録エラーの結合確認](./P008-test-direction/T008-duplicate-employee-id.md) — U004範囲(PASS)
- [x] T009 [管理者専用画面への一般ユーザーアクセス時のフロント+APIガード結合確認](./P008-test-direction/T009-admin-screen-guard.md) — U004範囲(PASS)
- [x] T010 [予約「備考(社内向けメモ)」の閲覧範囲マスキング結合確認](./P008-test-direction/T010-reservation-internal-memo-masking.md) — U002/U003範囲(※CR-001により追加、PASS)

## 備考

* T001〜T009は全件PASS(P205再実施、2026-08-11)。P103実行時点ではT001・T003・T006がFAILだったが、P202〜P205(F001〜F003)で修正済み。経緯は `docs/test-records/20260811-0500-test-record.md`(初回)・`docs/test-records/20260811-0545-test-record.md`(再実施)を参照。
* T010はCR-001対応(Refactor)にともない新規追加。PASS(2026-08-11、`docs/test-records/20260811-CR001-test-record.md` 参照)。
