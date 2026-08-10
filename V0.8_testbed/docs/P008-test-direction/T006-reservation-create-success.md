あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T006

## 【目的】

* S03予約作成画面から正常な入力で予約を作成すると、DBに保存されS02カレンダー画面に反映されることを確認する(画面+API+DBの結合、正常系)。

## 【参照テスト計画】

* `docs/P006-test-plan.md` 2.3〜2.4節

## 【対象モジュール】

* `client/src/pages/ReservationCreatePage.tsx`, `client/src/pages/CalendarPage.tsx`, `server/app/routers/reservations.py`, `server/app/services/reservation_service.py`, `server/app/repositories/reservation_repository.py`, SQLite(`reservations`, `reservation_participants`テーブル)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* U003の全タスク(`docs/P007-impl-direction/U003-reservation-core-and-calendar.md`)が完了していること。会議室「第一会議室」(収容人数8)が登録済みであること(U002完了が前提)。

## 【使用するテストデータ】

* 会議室: 第一会議室、日付: 翌営業日、時間帯: 10:00-11:00、件名: 「週次定例会議」、参加者: なし、参加予定人数: 5、備考: なし

## 【事前準備】

* 一般ユーザーでログインし、S02からS03へ空きセルクリックで遷移した状態にする

## 【実行手順】

1. テストデータでフォームを入力し登録する
2. S02へ遷移後、該当セルに「週次定例会議」が表示されることを確認する
3. SQLiteを直接クエリし `reservations` テーブルに該当行が存在することを確認する

## 【実行コマンド】

* `cd client && node --import tsx --test tests/integration/reservationCreateSuccess.test.tsx`

## 【期待結果】

* 手順1: 201、S02へ遷移
* 手順2: 該当セルに予約者名・「週次定例会議」が表示され、参加予定人数(5)は表示されない
* 手順3: `reservations` テーブルに `title='週次定例会議', attendee_count=5` の行が存在する

## 【合否判定基準】

* 上記すべてを満たせばPASS

## 【失敗時に記録する内容】

* 実際のレスポンス、画面表示内容、DBの内容

## 【修正禁止事項】

* アプリケーションコードを修正しない。テストコードをその場で都合よく変更しない。失敗したテストをスキップしない。期待値を変更して成功扱いにしない。同じ失敗に対して場当たり的な再テストを繰り返さない。

## 【次タスクへ進む条件】

* 結果を記録したらT007へ進む

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Executor Stepの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。
