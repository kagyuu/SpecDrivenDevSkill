あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T007 — 管理者専用APIの認可

## 【目的】

* 一般ユーザーのセッションで管理者専用API(会議室の登録・更新・無効化、ユーザーの一覧・登録・更新・無効化)を呼んだ場合に、いずれも 403 `FORBIDDEN` になることを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` 3.1 V-F-05、4.2(Sprint 2)。`docs/P001-requirement.md` テスト方針「権限まわりは結合テストで必ず確認する」
* 仕様: `docs/P002-frontend-spec.md` 5.1・5.5・5.6、`docs/P003-backend-spec.md` 4.3

## 【対象モジュール】

* `auth.py`(`require_admin`)、`handlers/room_handlers.py`、`handlers/user_handlers.py`

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* Sprint 2 の単体テストが全件PASSしていること。

## 【使用するテストデータ】

* 一般ユーザー `user001` のセッション、既存の会議室1件。

## 【事前準備】

1. DBファイルを削除し、サーバーを起動し、ユーザーと会議室Aを投入する。
2. `user001` でログインしてCookieを取得する。

## 【実行手順】

1. `POST /api/rooms` を呼ぶ。
2. `PUT /api/rooms/{room_id}` を呼ぶ。
3. `DELETE /api/rooms/{room_id}` を呼ぶ。
4. `GET /api/rooms?include_inactive=true` を呼ぶ。
5. `GET /api/users`(`scope` 未指定)を呼ぶ。
6. `POST /api/users` / `PUT /api/users/user002` / `DELETE /api/users/user002` を呼ぶ。
7. `GET /api/rooms`(既定)を呼ぶ。

## 【実行コマンド】

* `cd server && python3 -m unittest tests.integration.test_t007_admin_authz -v`

## 【期待結果】

* 手順1〜6: **すべて 403 `FORBIDDEN`**(404にマスクしない)。DBの状態が変化していない。
* 手順7: 200(一般ユーザーでも有効な会議室の一覧は取得できる)。

## 【合否判定基準】

* 手順1〜6が8本すべて403、手順7が200であればPASS。1本でも200/201/204が返ればFAIL(重大度「高」として記録)。

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
