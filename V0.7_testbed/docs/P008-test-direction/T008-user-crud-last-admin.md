あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T008 — ユーザーCRUDと最後の管理者の保護

## 【目的】

* ユーザーの登録・更新・無効化が仕様どおり動き、システムから有効な管理者がいなくなる操作が拒否されることを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` 4.2(Sprint 2)、3.1 V-F-08
* 仕様: `docs/P002-frontend-spec.md` 3.7・5.6、`docs/P003-backend-spec.md` 6.3・4.3

## 【対象モジュール】

* `handlers/user_handlers.py`、`services/user_service.py`、`repositories/users_repo.py`、`repositories/sessions_repo.py`

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* Sprint 2 の単体テストが全件PASSしていること。

## 【使用するテストデータ】

* 管理者 `admin001`(唯一の有効な管理者)、一般 `user001` / `user002`、新規登録用 `user900`。

## 【事前準備】

1. DBファイルを削除し、サーバーを起動し、ユーザー4件を投入する。
2. `admin001` でログインする。

## 【実行手順】

1. `POST /api/users` で `user900`(一般、パスワード `Passw0rd!23`)を登録する。
2. 同じ `user900` をもう一度登録する。
3. `user900` でログインできることを確認する。
4. `PUT /api/users/user900` で氏名を変更し、`password` を省略して送る。その後、元のパスワードでログインできることを確認する。
5. `PUT /api/users/admin001` で `role` を `general` に変更しようとする。
6. `DELETE /api/users/admin001` を呼ぶ(自分自身)。
7. `user001` のセッションを作ってから、`admin001` のセッションで `DELETE /api/users/user001` を呼び、その後 `user001` のCookieで `GET /api/me` を呼ぶ。
8. `DELETE /api/users/user001` をもう一度呼ぶ。

## 【実行コマンド】

* `cd server && python3 -m unittest tests.integration.test_t008_user_crud_last_admin -v`

## 【期待結果】

* 手順1: 201。レスポンスに `password` を含むキーがない。DBの `password_hash` が `scrypt$` で始まる。
* 手順2: 409 `DUPLICATE_KEY`。
* 手順3: 200。
* 手順4: 200。パスワードは変わらずログインできる。
* 手順5: 409 `CONSTRAINT_VIOLATION`(最後の有効な管理者)。
* 手順6: 409 `CONSTRAINT_VIOLATION`(自分自身)。
* 手順7: 204。無効化された `user001` のCookieでの `GET /api/me` が 401(セッションが削除されている)。
* 手順8: 204(冪等)。

## 【合否判定基準】

* 上記すべてが一致すればPASS。手順5・6が成功してしまう場合はFAIL(重大度「高」)。

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
