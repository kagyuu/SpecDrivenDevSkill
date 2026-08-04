あなたはExecutor(実装担当)です。このタスクを実施したら、Executor Stepの停止条件に該当しない限り自動的に次のタスクへ進んでください。

# 【テストID】T027

## 【目的】

* CR-003により、`GET /api/reservations/mine` のレスポンスに `attendee_count` が含まれることを確認する。あわせて、S02(予約カレンダー)が使う `GET /api/reservations` のレスポンスには `attendee_count` が含まれない(CRの指定によりスコープ外)ことを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` S02行・S04行(※CR-003により追記)
* `docs/P002-frontend-spec.md` §4.8・§4.9

## 【対象モジュール】

* `server/app/api/reservations.py`

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* U007-1(CR-003バックエンド)が完了していること。

## 【使用するテストデータ】

* 一般ユーザー: `employee_id=U0001`(シード投入済み)
* 予約: `attendee_count=6` で作成した今後の予約1件

## 【事前準備】

* 一般ユーザーでログインし、`attendee_count=6` の予約を1件作成しておく。

## 【実行手順】

1. `GET /api/reservations/mine?period=upcoming` を呼ぶ。
2. `GET /api/reservations?date_from=...&date_to=...` を呼ぶ。

## 【実行コマンド】

* `cd server && python3 -m unittest tests.test_api_reservations.ReservationsApiTest.test_my_reservations_includes_attendee_count -v`

## 【期待結果】

* 手順1: `200 OK`、`reservations` 配列中の該当予約に `attendee_count` が含まれ、値が `6` である。
* 手順2: `200 OK`、`reservations` 配列の各要素に `attendee_count` キーが**含まれない**(S02の予約サマリには表示しないというCR-003の指定どおり)。

## 【合否判定基準】

* 両手順が期待結果どおりであればPASS。

## 【失敗時に記録する内容】

* 実際のレスポンスボディ(各要素のキー一覧)を記録する。

## 【修正禁止事項】

* アプリケーションコードを修正しないでください。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このタスクを実施したら、Executor Stepの停止条件に該当しない限り自動的に次のタスク(T028)に進んでください。
