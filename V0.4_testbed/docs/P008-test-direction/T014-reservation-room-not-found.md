あなたはExecutor(実装担当)です。以下の1テストタスクだけを実施してください。

# 【テストID】T014

## 【目的】

* 存在しない会議室IDへの予約作成が `404 NOT_FOUND` になることを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.2(POST /api/reservations行)

## 【対象モジュール】

* `server/app/services/reservation_service.py`、`server/app/repositories/room_repository.py`

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* U003が完了していること。

## 【使用するテストデータ】

* `{"room_id": 99999, "date": "<未来日>", "start_time": "10:00", "end_time": "11:00", ...}`

## 【事前準備】

* 一般ユーザーでログインしCookieを取得する。

## 【実行手順】

1. 存在しない `room_id` で `POST /api/reservations` を呼ぶ。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_api_reservations.py::test_room_not_found -v`

## 【期待結果】

* `404 NOT_FOUND`。

## 【合否判定基準】

* 期待結果どおりであればPASS。

## 【失敗時に記録する内容】

* 実際のステータスコードを記録する。

## 【修正禁止事項】

* アプリケーションコードを修正しないでください。

## 【次タスクへ進む条件】

* 記録完了後、T015(sprint4)の指示を待つ。sprint3の全テスト(T011〜T014)が完了した時点でP008目次のU003行相当のチェックを進める。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* 次のテストタスクには進まないでください。
