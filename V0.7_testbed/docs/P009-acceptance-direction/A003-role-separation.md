あなたはReviewer Loop(実装横断レビュー担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Reviewer Loopの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P009-acceptance-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】A003 — 権限分離の横断確認

## 【目的】

* 一般ユーザーが管理者専用の画面・APIに到達できないことを、画面とAPIの両面から横断的に確認する(P001のテスト方針で必須とされた観点)。

## 【参照テスト計画】

* `docs/P006-test-plan.md` 3.1 V-F-05、3.2 V-N-05、4.3
* 仕様: `docs/P001-requirement.md` 非機能要件(権限チェック)、`docs/P002-frontend-spec.md` 2.3・5.1、`docs/P003-backend-spec.md` 4.3

## 【対象モジュール】

* `auth.py`、全ハンドラ、`client/src/components/header.js`、`client/src/views/s06-room-admin.js`、`s07-user-admin.js`

## 【前提条件】全モジュールビルドが成功していること

* 第2章のビルドコマンドが終了コード0で完了していること。

## 【使用するテストデータ】

* 一般 `user001`、管理者 `admin001`、会議室1件、`user001` 以外の利用者の予約1件。

## 【事前準備】

1. DBファイルを削除し、基準データセットと予約1件(`user002` の予約)を投入してサーバーを起動する。
2. `user001` でログインする。

## 【実行手順】

1. 共通ヘッダーに「会議室管理」「ユーザー管理」リンクが描画されないことを確認する。
2. `#/admin/rooms` と `#/admin/users` を直接開く。
3. 管理者専用API 8本(`POST/PUT/DELETE /api/rooms`、`GET(scope=management)/POST/PUT/DELETE /api/users`、`GET /api/rooms?include_inactive=true`)を一般ユーザーのCookieで呼ぶ。
4. `user002` の予約に対して `PUT` と `DELETE` を呼ぶ。
5. `user002` の予約に対して `GET` を呼ぶ。
6. Cookieを付けずに、上記のAPIおよび `GET /api/reservations` を呼ぶ。
7. `admin001` でログインし直し、手順3の8本を呼ぶ。

## 【実行コマンド】

* `cd server && python3 -m unittest tests.acceptance.test_a003_role_separation -v`
* `cd client && node --test tests/acceptance/test_a003_role_separation_ui.js`

## 【期待結果】

* 手順1: 2リンクが存在しない。
* 手順2: どちらも「この画面を表示する権限がありません。」のみが表示され、一覧データを取得しない。
* 手順3: 8本すべて 403 `FORBIDDEN`。
* 手順4: 403 `FORBIDDEN`。
* 手順5: 200(閲覧は許可)。
* 手順6: すべて 401 `UNAUTHENTICATED`。
* 手順7: 8本すべて成功(200 / 201 / 204)。

## 【合否判定基準】

* 手順3・4・6が1本でも成功応答を返した場合はFAIL(重大度「高」)。それ以外が一致すればPASS。

## 【失敗時に記録する内容】

* テストID、実行日時、実行コマンド、終了コード
* 期待結果と実際の結果(HTTPステータス、レスポンス本文、DBの該当行、画面の描画結果、計測値のうち該当するもの)
* サーバーの標準出力ログのうち当該操作に対応する行(`sid`・パスワードは伏せる)
* 失敗が再現するかどうか(同一手順を1回だけ再実行して確認する。3回以上繰り返さない)
* 関連しそうな仕様箇所(`docs/P001-requirement.md` / `docs/P002-frontend-spec.md` / `docs/P003-backend-spec.md` の節番号)

## 【修正禁止事項】

* アプリケーションコードを修正しない
* テストコードをその場で都合よく変更しない
* 失敗したテストをスキップしない
* 期待値を変更して成功扱いにしない
* 同じ失敗に対して場当たり的な再テストを繰り返さない
* 修正が必要な場合はP202(修正計画)以降に引き渡す

## 【次タスクへ進む条件】

* 本テストの結果(PASS / FAIL / BLOCKED のいずれか)が `docs/test-records/YYYYMMDD-HHMM-test-record.md` に記録されていること。
* `docs/P009-acceptance-direction.md` の該当行のチェックボックスが `[x]` になっていること。
* **FAILであっても次のテストタスクへ進む**(修正はP202以降で行う)。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Reviewer Loopの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
