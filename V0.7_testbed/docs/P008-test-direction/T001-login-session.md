あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T001 — ログインとセッションCookieの発行

## 【目的】

* API-01(ログイン)が発行したセッションCookieを使って API-03(`GET /api/me`)が通ることを、HTTP層〜Service層〜Repository層〜DBを通して確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` 4.2(Sprint 1)、3.1 V-F-02 / V-F-04、3.2 V-N-04
* 仕様: `docs/P002-frontend-spec.md` 5.4(API-01・API-03)、`docs/P003-backend-spec.md` 6.1・2.2

## 【対象モジュール】

* `server/src/meeting_room/handlers/auth_handlers.py`、`services/auth_service.py`、`repositories/sessions_repo.py`、`repositories/users_repo.py`、`main.py`

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* Sprint 1 の単体テストが全件PASSしていること。

## 【使用するテストデータ】

* `admin001` / `Passw0rd!23`(管理者)、`user001` / `Passw0rd!23`(一般)

## 【事前準備】

1. DBファイルを削除する。
2. サーバーを起動する(起動時にマイグレーションと初期管理者シードが走る)。
3. 基準データセットのうち、ユーザー4件を投入する。

## 【実行手順】

1. `POST /api/auth/login` に `{"user_id":"user001","password":"Passw0rd!23"}` を送る。
2. 応答の `Set-Cookie` ヘッダーを取得する。
3. 取得したCookieを付けて `GET /api/me` を呼ぶ。
4. DBの `sessions` テーブルの行数を確認する。
5. 同じCookieで `POST /api/auth/logout` を呼び、その後もう一度 `GET /api/me` を呼ぶ。

## 【実行コマンド】

* `cd server && python3 -m unittest tests.integration.test_t001_login_session -v`(★FIXME★ 結合テストのモジュール配置は `server/tests/integration/` を想定。実装時に確定すること)

## 【期待結果】

* 手順1: ステータス200。本文が `{"user":{"user_id":"user001","name":"山田 太郎","role":"general"}}`。
* 手順2: `Set-Cookie` に `sid=`、`HttpOnly`、`SameSite=Lax`、`Secure`、`Path=/` がすべて含まれる。
* 手順3: ステータス200。`user_id` が `user001`。
* 手順4: `sessions` に該当ユーザーの行が1件ある。
* 手順5: ログアウトが204。その後の `GET /api/me` が 401 `UNAUTHENTICATED` で、`sessions` の行が0件。

## 【合否判定基準】

* 上記5点すべてが一致すればPASS。1点でも不一致ならFAIL。

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
