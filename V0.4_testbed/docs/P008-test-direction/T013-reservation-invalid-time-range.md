あなたはExecutor(実装担当)です。以下の1テストタスクだけを実施してください。

# 【テストID】T013

## 【目的】

* 終了時刻が開始時刻以前の予約作成リクエストが `400 VALIDATION_ERROR` になることを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1(S03行)

## 【対象モジュール】

* `server/app/core/validators.py`(`validate_time_range`)、`server/app/services/reservation_service.py`

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* U003が完了していること。

## 【使用するテストデータ】

* `{"room_id": 1, "date": "<未来日>", "start_time": "11:00", "end_time": "10:00", ...}`(終了<開始)
* `{"room_id": 1, "date": "<未来日>", "start_time": "10:00", "end_time": "10:00", ...}`(終了=開始)

## 【事前準備】

* 一般ユーザーでログインしCookieを取得する。

## 【実行手順】

1. 終了<開始のデータで `POST /api/reservations` を呼ぶ。
2. 終了=開始のデータで `POST /api/reservations` を呼ぶ。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_api_reservations.py::test_invalid_time_range -v`

## 【期待結果】

* 両手順とも `400 VALIDATION_ERROR`。

## 【合否判定基準】

* 両手順が期待結果どおりであればPASS。

## 【失敗時に記録する内容】

* 実際のステータスコードを記録する。

## 【修正禁止事項】

* アプリケーションコードを修正しないでください。

## 【次タスクへ進む条件】

* 記録完了後、T014の指示を待つ。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* 次のテストタスクには進まないでください。
