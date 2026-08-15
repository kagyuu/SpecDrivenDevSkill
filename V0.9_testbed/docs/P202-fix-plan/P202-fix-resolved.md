# 解決済み修正障害一覧

## 概要

* 修正完了した障害数: 5(F001〜F005)
* 未解決の障害数: 0
* 全体状態: ALL_RESOLVED(検出された修正課題を全件解決)

## 解決済障害一覧

| 修正タスク | 対応障害 | 結果 | テスト日付 | 修正日付 |
|---|---|---|---|---|
| F001 | T001 | RESOLVED | 2026/08/11 | 2026/08/11 |
| F002 | T003, A001 | RESOLVED | 2026/08/11 | 2026/08/11 |
| F003 | T006, A002, A006, A007 | RESOLVED | 2026/08/11 | 2026/08/11 |
| F004 | A004 | RESOLVED | 2026/08/11 | 2026/08/11 |
| F005 | A009 | RESOLVED | 2026/08/11 | 2026/08/11 |

## 解決済障害

### F001: S02にログインユーザー名表示・ログアウト導線が実装されていない

* 対応するテストID: T001
* 対応するテスト記録: docs/test-records/20260811-0500-test-record.md
* 失敗していたテストコマンド: `cd client && npx playwright test tests/integration/t001_login_flow.spec.ts`
* 修正内容: `client/src/pages/CalendarPage.tsx` にログインユーザー名表示・ログアウトボタンを追加。
* 変更したソースコード: `client/src/pages/CalendarPage.tsx`, `client/src/tests/CalendarPage.test.tsx`
* 更新したdocs: `docs/P002-frontend-spec.md` §3 S02
* 実行したテスト: `npm run build`, `npx vitest run src/tests/CalendarPage.test.tsx`, `npx playwright test tests/integration/t001_login_flow.spec.ts`
* テスト結果: 全PASS
* 残課題: なし
* 修正経緯: 詳細は `docs/P202-fix-plan/fixed/F001-calendar-page-username-logout.md` 参照。

### F002: 日付計算がUTC基準でタイムゾーンによりずれる

* 対応するテストID: T003, A001
* 対応するテスト記録: docs/test-records/20260811-0500-test-record.md, docs/test-records/20260811-0530-test-record.md
* 失敗していたテストコマンド: `npx playwright test tests/integration/t003_reservation_create_reflects_calendar.spec.ts`, `npx playwright test tests/acceptance/a001_general_user_journey.spec.ts`
* 修正内容: `CalendarPage.tsx` の `toDateString()` をローカルタイムゾーン基準に変更。関連するテストコードの日付計算も統一。
* 変更したソースコード: `client/src/pages/CalendarPage.tsx`, `client/src/tests/CalendarPage.test.tsx`, `client/tests/integration/helpers.ts`, `client/tests/integration/t003_reservation_create_reflects_calendar.spec.ts`, `client/tests/acceptance/a001_general_user_journey.spec.ts`
* 更新したdocs: なし
* 実行したテスト: 上記実行コマンド一式
* テスト結果: 全PASS
* 残課題: なし
* 修正経緯: 詳細は `docs/P202-fix-plan/fixed/F002-date-timezone-fix.md` 参照。

### F003: sqlite3接続のスレッド不整合(実サーバーでのみ再現)

* 対応するテストID: T006, A002, A006, A007
* 対応するテスト記録: docs/test-records/20260811-0500-test-record.md, docs/test-records/20260811-0530-test-record.md
* 失敗していたテストコマンド: `npx playwright test tests/integration/t006_reservation_update_self_exclusion.spec.ts`, `npx playwright test tests/acceptance/a002_admin_journey.spec.ts`, `npx playwright test tests/acceptance/a006_room_deactivation_existing_reservations.spec.ts`, `npx playwright test tests/acceptance/a007_performance_calendar.spec.ts`
* 修正内容: `server/app/db/connection.py` の `sqlite3.connect()` に `check_same_thread=False` を指定。
* 変更したソースコード: `server/app/db/connection.py`
* 更新したdocs: なし
* 実行したテスト: `uv run python -m pytest tests/ -v`(104件PASS)、上記Playwrightテスト一式
* テスト結果: 全PASS。サーバーログから `sqlite3.ProgrammingError` が消えたことを確認。
* 残課題: なし
* 修正経緯: 詳細は `docs/P202-fix-plan/fixed/F003-sqlite-thread-safety.md` 参照。**重大度が高い不具合**(実サーバー運用で断続的な500エラーを引き起こしうるもの)であったため優先して対応した。

### F004: A004のテスト指示がP003 §5.9(背中合わせ予約の扱い)と矛盾していた

* 対応するテストID: A004
* 対応するテスト記録: docs/test-records/20260811-0530-test-record.md
* 失敗していたテストコマンド: `cd client && npx playwright test tests/acceptance/a004_reservation_conflict_system_check.spec.ts`
* 修正内容: `docs/P009-acceptance-direction/A004-reservation-conflict-system-check.md` の手順3・4の期待結果を、P003 §5.9の規定(背中合わせは重複にならない=201)に合わせて訂正。テストコードの期待値も合わせて訂正。
* 変更したソースコード: **なし(テスト指示側の誤りのため、docs/P009-acceptance-direction/A004-*.mdとテストコードを修正)**
* 更新したdocs: `docs/P009-acceptance-direction/A004-reservation-conflict-system-check.md`
* 実行したテスト: `npx playwright test tests/acceptance/a004_reservation_conflict_system_check.spec.ts`
* テスト結果: PASS
* 残課題: なし
* 修正経緯: 詳細は `docs/P202-fix-plan/fixed/F004-a004-back-to-back-expectation.md` 参照。判定根拠(矛盾する上位文書の引用、コードが仕様どおり実装されていることの確認、カバレッジが失われないことの確認)は同ファイルに記載。

### F005: 失敗時のアクセスログにerror_codeが含まれていない

* 対応するテストID: A009
* 対応するテスト記録: docs/test-records/20260811-0530-test-record.md
* 失敗していたテストコマンド: `cd server && uv run python -m pytest tests/acceptance/test_a009_structured_logging.py -v`
* 修正内容: `server/app/main.py` の `access_log_middleware` が、400以上のレスポンスの場合にボディから `error_code` を取り出してログへ含めるよう修正。
* 変更したソースコード: `server/app/main.py`
* 更新したdocs: なし
* 実行したテスト: `uv run python -m pytest tests/ -v`(104件PASS)、`uv run python -m pytest tests/acceptance/test_a009_structured_logging.py -v`
* テスト結果: 全PASS
* 残課題: なし
* 修正経緯: 詳細は `docs/P202-fix-plan/fixed/F005-access-log-error-code.md` 参照。
