# 解決済み修正障害一覧

## 概要

* 修正完了した障害数: 4(F001〜F004。対応する失敗テストは延べ13件: T006, T009, T012, T013, T014, T015, A001, A003, A004, A006, A008, A010。A003は1テストで2根本原因(F001・F003)に対応するため、失敗テストの実数は11件)
* 未解決の障害数: 0
* 全体状態: **ALL_RESOLVED**(検出された修正課題を全件解決)

## 解決済障害一覧

| 修正タスク | 対応障害 | 結果 | テスト日付 | 修正日付 |
|---|---|---|---|---|
| F001 | T009, T012, T013, T014, T015, A001, A003(S05側), A004, A006, A010 | RESOLVED | 2026/08/09 | 2026/08/09 |
| F002 | T006 | RESOLVED | 2026/08/09 | 2026/08/09 |
| F003 | A003(S04側) | RESOLVED | 2026/08/09 | 2026/08/09 |
| F004 | A008 | RESOLVED | 2026/08/09 | 2026/08/09 |

## 解決済障害

### F001: sqlite3スレッド安全性不具合

* 対応するテストID: T009, T012, T013, T014, T015, A001, A003(S05側), A004, A006, A010
* 対応するテスト記録: `docs/test-records/20260809-1500-test-record.md`(T009等)、`docs/test-records/20260809-1900-test-record.md`(A001等)
* 失敗していたテストコマンド: `cd client && node --import tsx --test tests/integration/calendarListDisplay.test.tsx` 等(詳細は`docs/P202-fix-plan/fixed/F001-sqlite-thread-safety.md`参照)
* 修正内容: `server/app/db/connection.py`の`get_connection()`で`sqlite3.connect()`に`check_same_thread=False`を追加した。
* 変更したソースコード: `server/app/db/connection.py`
* 更新したdocs: なし(当初計画時に想定していた`server/INDEX.md`更新は、P204で内容を確認のうえ本ラウンドでは追加更新不要と判断)
* 実行したテスト: `server/tests/`全件(127件)、`client/tests/*.test.tsx`全件(38件)、対応する結合・受け入れ結合テスト
* テスト結果: 全件PASS
* 残課題: なし
* 修正経緯: `docs/P202-fix-plan/fixed/F001-sqlite-thread-safety.md`参照。

### F002: CalendarPageの日付ナビゲーション(タイムゾーン)不具合

* 対応するテストID: T006
* 対応するテスト記録: `docs/test-records/20260809-1500-test-record.md`
* 失敗していたテストコマンド: `cd client && node --import tsx --test tests/integration/reservationCreateSuccess.test.tsx`
* 修正内容: `client/src/pages/CalendarPage.tsx`の`addDays()`を`Date.UTC(...)`+`setUTCDate`ベースの実装に置き換えた。
* 変更したソースコード: `client/src/pages/CalendarPage.tsx`
* 更新したdocs: なし
* 実行したテスト: `client/tests/CalendarPage.test.tsx`、`client/tests/integration/reservationCreateSuccess.test.tsx`(3回連続実行)
* テスト結果: 全件PASS
* 残課題: なし
* 修正経緯: `docs/P202-fix-plan/fixed/F002-calendar-adddays-timezone.md`参照。

### F003: ReservationDetailPageの無効化済み会議室名表示不具合

* 対応するテストID: A003(S04側)
* 対応するテスト記録: `docs/test-records/20260809-1900-test-record.md`
* 失敗していたテストコマンド: `cd client && node --import tsx --test tests/acceptance/inactiveRoomHistory.test.tsx`
* 修正内容: `client/src/pages/ReservationDetailPage.tsx`に、現在の予約が参照する会議室が`rooms`一覧に無い場合にその1件を合成して選択肢に追加する`roomOptions`を導入した。
* 変更したソースコード: `client/src/pages/ReservationDetailPage.tsx`
* 更新したdocs: なし
* 実行したテスト: `client/tests/ReservationDetailPage.test.tsx`、`client/tests/acceptance/inactiveRoomHistory.test.tsx`(3回連続実行)
* テスト結果: 全件PASS
* 残課題: なし
* 修正経緯: `docs/P202-fix-plan/fixed/F003-reservation-detail-inactive-room.md`参照。

### F004: login_failed構造化ログの実装

* 対応するテストID: A008
* 対応するテスト記録: `docs/test-records/20260809-1900-test-record.md`
* 失敗していたテストコマンド: `cd server && python -m pytest tests/acceptance/test_structured_logging.py -v`
* 修正内容: `server/app/services/auth_service.py`の`login`関数に`log_event("WARNING", "login_failed", ...)`の呼び出しを追加した。
* 変更したソースコード: `server/app/services/auth_service.py`
* 更新したdocs: なし
* 実行したテスト: `server/tests/test_auth_service.py`、`server/tests/test_auth_api.py`、`server/tests/acceptance/test_structured_logging.py`
* テスト結果: 全件PASS
* 残課題: なし
* 修正経緯: `docs/P202-fix-plan/fixed/F004-login-failed-logging.md`参照。
