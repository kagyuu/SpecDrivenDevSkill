あなたはExecutor(実装担当)です。このタスクを実施したら、Executor Stepの停止条件に該当しない限り自動的に次のタスクへ進んでください。

# 【テストID】T026

## 【目的】

* CR-003により、参加予定人数が予約先会議室の収容人数(`ROOMS.capacity`)を超える場合に `400 VALIDATION_ERROR` になることを、作成(`POST`)・更新(`PUT`)の双方で確認する。あわせて、収容人数と等しい値は許容されることを確認する(境界値)。

## 【参照テスト計画】

* `docs/P006-test-plan.md` S03行・S04行の異常系(※CR-003により追記)
* `docs/P002-frontend-spec.md` §4.11・§4.12、`docs/P003-backend-spec.md` §7.11・§7.12

## 【対象モジュール】

* `server/app/services/reservation_service.py`、`server/app/api/errors.py`

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* U007-1(CR-003バックエンド)が完了していること。

## 【使用するテストデータ】

* 一般ユーザー: `employee_id=U0001`(シード投入済み)
* 会議室: `capacity=10` の会議室(シード投入済み)
* 超過データ: `attendee_count=11`
* 境界データ: `attendee_count=10`

## 【事前準備】

* 一般ユーザーでログインしCookieを取得する。

## 【実行手順】

1. `POST /api/reservations` に超過データ(`attendee_count=11`)を送信する。
2. `POST /api/reservations` に境界データ(`attendee_count=10`)を送信する。
3. 手順2で作成した予約に対して、`attendee_count=11` に変更する `PUT /api/reservations/{reservation_id}` を送信する。

## 【実行コマンド】

* `cd server && python3 -m unittest tests.test_api_reservations.ReservationsApiTest.test_attendee_count_exceeding_room_capacity_is_rejected -v`

## 【期待結果】

* 手順1: `400`、エラーコードが `VALIDATION_ERROR`、`details` に `field="attendee_count"` を含む。
* 手順2: `201 Created`(収容人数と等しい値は許容される)。
* 手順3: `400`、エラーコードが `VALIDATION_ERROR`、`details` に `field="attendee_count"` を含む。

## 【合否判定基準】

* 3手順すべてが期待結果どおりであればPASS。

## 【失敗時に記録する内容】

* 実際のHTTPステータス・エラーコード・`details` の内容を記録する。

## 【修正禁止事項】

* アプリケーションコードを修正しないでください。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このタスクを実施したら、Executor Stepの停止条件に該当しない限り自動的に次のタスク(T027)に進んでください。
