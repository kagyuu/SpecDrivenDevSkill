あなたはExecutor(実装担当)です。以下の1テストタスクだけを実施してください。

# 【テストID】T012

## 【目的】

* 既存予約と時間帯が重なる予約作成が `409 RESERVATION_CONFLICT` になることを確認する(境界が接するだけの場合は重複としないことも合わせて確認する)。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1(S03行)、§3(負荷・同時実行観点の前提となる基本ロジック確認)

## 【対象モジュール】

* `server/app/repositories/reservation_repository.py`(`has_overlap`)、`server/app/services/reservation_service.py`

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* U003が完了していること。T011の予約(会議室A、同日10:00-11:00)が存在すること。

## 【使用するテストデータ】

* 重複ケース: `{"room_id": 1, "date": "<T011と同日>", "start_time": "10:30", "end_time": "11:30", ...}`
* 境界ケース: `{"room_id": 1, "date": "<T011と同日>", "start_time": "11:00", "end_time": "12:00", ...}`

## 【事前準備】

* 一般ユーザーでログインしCookieを取得する。

## 【実行手順】

1. 重複ケースのデータで `POST /api/reservations` を呼ぶ。
2. 境界ケースのデータで `POST /api/reservations` を呼ぶ。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_api_reservations.py::test_overlap_conflict_and_boundary -v`

## 【期待結果】

* 手順1: `409 RESERVATION_CONFLICT`。
* 手順2: `201 Created`(境界が接するのみで重複としない、`docs/P003-backend-spec.md` §5)。

## 【合否判定基準】

* 両手順が期待結果どおりであればPASS。

## 【失敗時に記録する内容】

* 両手順の実際のステータスコードを記録する。

## 【修正禁止事項】

* アプリケーションコードを修正しないでください。

## 【次タスクへ進む条件】

* 記録完了後、T013の指示を待つ。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* 次のテストタスクには進まないでください。
