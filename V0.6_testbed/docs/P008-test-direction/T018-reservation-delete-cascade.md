あなたはExecutor(実装担当)です。以下の1テストタスクだけを実施してください。

# 【テストID】T018

## 【目的】

* 予約者本人による予約取消が成功し、`RESERVATION_PARTICIPANTS` の関連データもCASCADEで削除されることを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1(S04行)

## 【対象モジュール】

* `server/app/repositories/reservation_repository.py`(`delete`)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* U004が完了していること。参加者付きの予約が1件登録済みであること(本テスト専用に新規作成してよい)。

## 【使用するテストデータ】

* 参加者 `E0002` を含む新規予約(本テスト専用)

## 【事前準備】

* 予約作成者でログインし、参加者付き予約を作成する。

## 【実行手順】

1. `DELETE /api/reservations/{reservation_id}` を呼ぶ。
2. `GET /api/reservations/{reservation_id}` を呼ぶ。
3. DB内の `RESERVATION_PARTICIPANTS` テーブルを直接確認し、該当 `reservation_id` の行が無いことを確認する。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_api_reservations.py::test_delete_cascades_participants -v`

## 【期待結果】

* 手順1: `200 OK`。
* 手順2: `404 NOT_FOUND`。
* 手順3: 該当行が0件。

## 【合否判定基準】

* 3手順すべてが期待結果どおりであればPASS。

## 【失敗時に記録する内容】

* 各手順の実際の結果を記録する。

## 【修正禁止事項】

* アプリケーションコードを修正しないでください。

## 【次タスクへ進む条件】

* 記録完了後、T019の指示を待つ。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* 次のテストタスクには進まないでください。
