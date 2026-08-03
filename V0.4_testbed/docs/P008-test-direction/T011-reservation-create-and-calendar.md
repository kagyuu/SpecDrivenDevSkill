あなたはExecutor(実装担当)です。以下の1テストタスクだけを実施してください。

# 【テストID】T011

## 【目的】

* 予約が正しく作成でき、`GET /api/reservations` の日付範囲検索で取得できることを確認する(S02カレンダー・S03予約作成・予約APIのモジュール間連携)。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1(S02行・S03行)

## 【対象モジュール】

* `server/app/api/reservations.py`、`server/app/services/reservation_service.py`、`server/app/repositories/reservation_repository.py`

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* U001・U002・U003が完了していること。会議室「会議室A」(id=1)、参加者候補ユーザー`E0002`が登録済みであること。

## 【使用するテストデータ】

* `{"room_id": 1, "date": "<テスト実行日+1日>", "start_time": "10:00", "end_time": "11:00", "title": "定例MTG", "participant_ids": [], "notes": null}`

## 【事前準備】

* 一般ユーザー `E0001` でログインしCookieを取得する。

## 【実行手順】

1. `POST /api/reservations` に上記データを送信する。
2. `GET /api/reservations?date_from=<同日>&date_to=<同日>` を呼ぶ。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_api_reservations.py::test_create_and_list -v`

## 【期待結果】

* 手順1: `201 Created`。
* 手順2: レスポンスの `reservations` に手順1の予約が含まれる。

## 【合否判定基準】

* 両手順が期待結果どおりであればPASS。

## 【失敗時に記録する内容】

* 実際のステータスコード・レスポンスボディを記録する。

## 【修正禁止事項】

* アプリケーションコードを修正しないでください。

## 【次タスクへ進む条件】

* 記録完了後、T012の指示を待つ。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* 次のテストタスクには進まないでください。
