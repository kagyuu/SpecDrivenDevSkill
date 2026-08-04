あなたはExecutor(実装担当)です。このタスクを実施したら、Executor Stepの停止条件に該当しない限り自動的に次のタスクへ進んでください。

# 【テストID】T025

## 【目的】

* CR-003により、S04(予約詳細・編集画面)から参加予定人数を編集でき、更新後の値が `GET /api/reservations/{reservation_id}` に反映されることを確認する。あわせて、参加予定人数だけを変更する更新で他の項目(件名・備考・参加者)が壊れないことを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` S04行(※CR-003により追記)
* `docs/CR.md` CR-003「期待する振る舞い」

## 【対象モジュール】

* `server/app/api/reservations.py`、`server/app/services/reservation_service.py`、`server/app/repositories/reservation_repository.py`

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* U007-1(CR-003バックエンド)が完了していること。

## 【使用するテストデータ】

* 一般ユーザー: `employee_id=U0001`(シード投入済み)
* 会議室: `capacity=10` の会議室(シード投入済み)
* 初期登録データ: `attendee_count=4`、`title="定例MTG"`、`notes="資料は事前配布"`
* 更新データ: 初期登録データと同一内容で `attendee_count` のみ `9` に変更したもの

## 【事前準備】

* 一般ユーザーでログインし、初期登録データで予約を1件作成しておく。

## 【実行手順】

1. `PUT /api/reservations/{reservation_id}` に更新データを送信する。
2. `GET /api/reservations/{reservation_id}` を呼ぶ。

## 【実行コマンド】

* `cd server && python3 -m unittest tests.test_api_reservations.ReservationsApiTest.test_update_reservation_attendee_count_then_fetch -v`

## 【期待結果】

* 手順1: `200 OK`、レスポンスの `attendee_count` が `9` である。
* 手順2: `attendee_count` が `9`、`title` が `"定例MTG"`、`notes` が `"資料は事前配布"` のまま保たれている。

## 【合否判定基準】

* 両手順が期待結果どおりであればPASS。

## 【失敗時に記録する内容】

* 実際のレスポンスボディ(`attendee_count`・`title`・`notes` の値)を記録する。

## 【修正禁止事項】

* アプリケーションコードを修正しないでください。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このタスクを実施したら、Executor Stepの停止条件に該当しない限り自動的に次のタスク(T026)に進んでください。
