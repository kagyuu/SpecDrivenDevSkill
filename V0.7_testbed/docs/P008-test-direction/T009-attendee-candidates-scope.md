あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T009 — 参加者候補スコープの権限と射影

## 【目的】

* `GET /api/users?scope=attendee_candidates` が一般ユーザーでも呼べること、および返却内容が `user_id` と `name` だけに限定されていることを確認する(P001の「管理者のみ」の制約を、必要最小限の射影に限って緩和した箇所)。

## 【参照テスト計画】

* `docs/P006-test-plan.md` 4.2(Sprint 2)、3.1 V-F-05
* 仕様: `docs/P002-frontend-spec.md` 5.6(API-08、`scope`)、`docs/P003-backend-spec.md` 6.3、`docs/P004-traceability-matrix.md` 4章 差し戻し#1

## 【対象モジュール】

* `handlers/user_handlers.py`、`services/user_service.py`、`repositories/users_repo.py`(`list_active_id_and_name`)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* Sprint 2 の単体テストが全件PASSしていること。

## 【使用するテストデータ】

* 有効ユーザー3件(`admin001` / `user001` / `user002`)、無効ユーザー1件(`user003`)。

## 【事前準備】

1. DBファイルを削除し、サーバーを起動し、ユーザー4件を投入する。
2. `user001`(一般)でログインする。

## 【実行手順】

1. 一般ユーザーのCookieで `GET /api/users?scope=attendee_candidates` を呼ぶ。
2. 返却された各要素のキー集合を確認する。
3. 返却件数と、無効ユーザーが含まれるかを確認する。
4. 一般ユーザーのCookieで `GET /api/users?scope=management` を呼ぶ。
5. 管理者のCookieで `GET /api/users?scope=attendee_candidates` を呼ぶ。

## 【実行コマンド】

* `cd server && python3 -m unittest tests.integration.test_t009_attendee_candidates_scope -v`

## 【期待結果】

* 手順1: 200。
* 手順2: 各要素のキーが **`user_id` と `name` の2つだけ**。`role` `is_active` `created_at` `updated_at` `password_hash` のいずれも含まれない。
* 手順3: 3件(有効ユーザーのみ)。`user003` を含まない。
* 手順4: 403 `FORBIDDEN`。
* 手順5: 200(管理者も同じ射影で取得できる)。

## 【合否判定基準】

* 上記すべてが一致すればPASS。手順2に `role` が含まれる場合はFAIL(権限情報の漏えいにあたる)。

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
