あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T011 — 予約の登録→一覧→詳細→更新→取消

## 【目的】

* 予約APIのモジュール間連携(Handler↔Service↔Repository↔DB、および `reservation_attendees` との連動)が一連の流れで正しく動くことを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` 4.2(Sprint 3)、3.1 V-F-02
* 仕様: `docs/P002-frontend-spec.md` 5.7(API-12〜17)、`docs/P003-backend-spec.md` 6.4

## 【対象モジュール】

* `handlers/reservation_handlers.py`、`services/reservation_service.py`、`repositories/reservations_repo.py`、`migrations/003-reservations.sql`

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* Sprint 3 の単体テストが全件PASSしていること。

## 【使用するテストデータ】

* `user001` のセッション、会議室A(収容10)、日付は「本日+1日」、時刻 10:00-11:00、件名「定例会議」、参加者 `user002`、参加予定人数 8。

## 【事前準備】

1. DBファイルを削除し、サーバーを起動し、基準データセット(ユーザー・会議室)を投入する。
2. `user001` でログインする。

## 【実行手順】

1. `POST /api/reservations` で予約を登録する。
2. `GET /api/reservations?date_from={本日}&date_to={本日+6日}` を呼ぶ。
3. `GET /api/reservations/{id}` を呼ぶ。
4. `GET /api/reservations/mine?period=upcoming` を呼ぶ。
5. `PUT /api/reservations/{id}` で件名を「臨時会議」に変更し、参加者を `user002` から空に変更する。
6. `GET /api/reservations/{id}` で反映を確認する。
7. `DELETE /api/reservations/{id}` を呼び、その後 `GET /api/reservations/{id}` を呼ぶ。
8. `reservation_attendees` の行数を確認する。

## 【実行コマンド】

* `cd server && python3 -m unittest tests.integration.test_t011_reservation_lifecycle -v`

## 【期待結果】

* 手順1: 201。`reservation.user_id` が `user001`(リクエストで指定していなくても予約者になる)。
* 手順2: 200。該当予約が1件含まれ、`room_name` と `user_name` が入っている。`attendees` は空配列。
* 手順3: 200。`attendees` に `user002` が1件含まれる。
* 手順4: 200。1件返る。
* 手順5: 200。件名が変わる。
* 手順6: `attendees` が空配列になる。
* 手順7: 204 → 404。
* 手順8: 0件(CASCADEまたは明示削除で参加者行が残らない)。

## 【合否判定基準】

* 上記すべてが一致すればPASS。

## 【失敗時に記録する内容】

* テストID、実行日時、実行コマンド、終了コード
* 期待結果と実際の結果(HTTPステータス、レスポンス本文、DBの該当行、画面の描画結果のうち該当するもの)
* サーバーの標準出力ログのうち、当該リクエストに対応する行(`sid`・パスワードは伏せる)
* 失敗が再現するかどうか(同一手順を1回だけ再実行して確認する。3回以上繰り返さない)
* 関連しそうな仕様箇所(`docs/P002-frontend-spec.md` / `docs/P003-backend-spec.md` の節番号)

## 【修正禁止事項】

* アプリケーションコードを修正しない
* テストコードをその場で都合よく変更しない
* 失敗したテストをスキップしない
* 期待値を変更して成功扱いにしない
* 同じ失敗に対して場当たり的な再テストを繰り返さない

## 【次タスクへ進む条件】

* 本テストの結果(PASS / FAIL / BLOCKED のいずれか)が `docs/test-records/YYYYMMDD-HHMM-test-record.md` に記録されていること。
* `docs/P008-test-direction.md` の該当行のチェックボックスが `[x]` になっていること。
* **FAILであっても次のテストタスクへ進む**(修正はReviewer Loopで行う)。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Executor Stepの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
