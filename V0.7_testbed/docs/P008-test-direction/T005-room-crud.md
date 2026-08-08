あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T005 — 会議室CRUDの一気通貫

## 【目的】

* 会議室の登録・一覧・更新・無効化が、API↔Service↔Repository↔DB を通して仕様どおり動くことを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` 4.2(Sprint 2)、3.1 V-F-02 / V-F-13
* 仕様: `docs/P002-frontend-spec.md` 5.5(API-04〜07)、`docs/P003-backend-spec.md` 6.2

## 【対象モジュール】

* `handlers/room_handlers.py`、`services/room_service.py`、`repositories/rooms_repo.py`、`migrations/002-rooms.sql`

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* Sprint 2 の単体テストが全件PASSしていること。

## 【使用するテストデータ】

* 管理者 `admin001` のセッション。登録する会議室: `会議室A`(収容10、設備「プロジェクタ」、説明文「窓側の大会議室」)。

## 【事前準備】

1. DBファイルを削除し、サーバーを起動し、ユーザー4件を投入する。
2. `admin001` でログインしてCookieを取得する。

## 【実行手順】

1. `POST /api/rooms` で会議室Aを登録する。
2. `GET /api/rooms` を呼ぶ。
3. `PUT /api/rooms/{room_id}` で収容人数を10→12、説明文を変更する。
4. `GET /api/rooms` で反映を確認する。
5. `DELETE /api/rooms/{room_id}` を呼ぶ。
6. `GET /api/rooms`(既定)と `GET /api/rooms?include_inactive=true` をそれぞれ呼ぶ。
7. もう一度 `DELETE /api/rooms/{room_id}` を呼ぶ。

## 【実行コマンド】

* `cd server && python3 -m unittest tests.integration.test_t005_room_crud -v`

## 【期待結果】

* 手順1: 201。本文の `room` に `room_id` が採番され、`description` が保存されている。
* 手順2: 200。`rooms` に1件。
* 手順3: 200。`capacity` が12、`updated_at` が `created_at` より後。
* 手順4: 変更が反映されている。
* 手順5: 204。DBの `is_active` が0(**行は削除されていない**)。
* 手順6: 既定の一覧には現れず、`include_inactive=true` には現れる。
* 手順7: 204(冪等。エラーにならない)。

## 【合否判定基準】

* 上記すべてが一致すればPASS。特に手順5で行が物理削除されていた場合はFAIL。

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
