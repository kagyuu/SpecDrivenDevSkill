あなたはExecutor(実装担当)です。このタスクを実施したら、Executor Stepの停止条件に該当しない限り自動的に次のタスクへ進んでください。

# 【テストID】T024

## 【目的】

* CR-003(予約に参加予定人数(attendee_count)を追加)により、参加予定人数を指定した予約を作成でき、`GET /api/reservations/{reservation_id}` のレスポンスにその値が反映されることを確認する。あわせて、参加予定人数を未入力(送信しない)にした予約は `attendee_count` が `null` になることを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` S03行(※CR-003により追記)
* `docs/CR.md` CR-003(反映後は `docs/cr-records/CR-003.md`)「期待する振る舞い」

## 【対象モジュール】

* `server/app/api/reservations.py`、`server/app/services/reservation_service.py`、`server/app/repositories/reservation_repository.py`、`server/app/core/validators.py`

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* U001〜U006(既存)が完了していること。U007(CR-003対応)のバックエンド部分(U007-1)が完了していること。

## 【使用するテストデータ】

* 一般ユーザー: `employee_id=U0001`, `role=general`(シード投入済み)
* 会議室: `capacity=10` の会議室(シード投入済み)
* 予約データA(人数あり): `{"room_id": <上記会議室>, "date": <実行日+1日>, "start_time": "10:00", "end_time": "11:00", "title": "定例MTG", "attendee_count": 8}`
* 予約データB(人数なし): 予約データAから `attendee_count` を除き、`start_time`/`end_time` を `13:00`/`14:00` にしたもの

## 【事前準備】

* 一般ユーザーでログインしCookieを取得する。

## 【実行手順】

1. `POST /api/reservations` に予約データAを送信する。
2. 手順1で作成した予約IDに対して `GET /api/reservations/{reservation_id}` を呼ぶ。
3. `POST /api/reservations` に予約データBを送信する。
4. 手順3で作成した予約IDに対して `GET /api/reservations/{reservation_id}` を呼ぶ。

## 【実行コマンド】

* `cd server && python3 -m unittest tests.test_api_reservations.ReservationsApiTest.test_create_reservation_with_attendee_count_then_fetch -v`

## 【期待結果】

* 手順1: `201 Created`、レスポンスボディの `attendee_count` が `8` である。
* 手順2: レスポンスの `attendee_count` が `8` である。
* 手順3: `201 Created`、レスポンスボディに `attendee_count` キーが存在し、値が `null` である。
* 手順4: レスポンスの `attendee_count` が `null` である。

## 【合否判定基準】

* 4手順すべてが期待結果どおりであればPASS。

## 【失敗時に記録する内容】

* 実際のレスポンスボディ(`attendee_count` フィールドの値・有無)を記録する。

## 【修正禁止事項】

* アプリケーションコードを修正しないでください。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このタスクを実施したら、Executor Stepの停止条件に該当しない限り自動的に次のタスク(T025)に進んでください。
