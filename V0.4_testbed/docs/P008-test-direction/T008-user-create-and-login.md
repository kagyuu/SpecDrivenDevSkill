あなたはExecutor(実装担当)です。以下の1テストタスクだけを実施してください。

# 【テストID】T008

## 【目的】

* 管理者が新規ユーザーを初期パスワード付きで登録し、そのユーザーが初期パスワードでログインできることを確認する(sprint2のユーザー登録機能とsprint1で実装済みのログインAPIとの連携確認)。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1(S07行)

## 【対象モジュール】

* `server/app/api/users.py`、`server/app/services/user_service.py`、`server/app/services/auth_service.py`(sprint1実装分を利用)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* U001・U002が完了していること。

## 【使用するテストデータ】

* `{"employee_id": "E0002", "name": "鈴木花子", "role": "general", "is_active": true, "initial_password": "Passw0rd2"}`

## 【事前準備】

* 管理者でログインしCookieを取得する。

## 【実行手順】

1. 管理者Cookieで `POST /api/users` に登録データを送信する。
2. `POST /api/auth/login` に `E0002`/`Passw0rd2` を送信する。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_api_users.py::test_create_then_login -v`

## 【期待結果】

* 手順1: `201 Created`(レスポンスに `initial_password` は含まれない)。
* 手順2: `200 OK`。

## 【合否判定基準】

* 両手順が期待結果どおりであればPASS。

## 【失敗時に記録する内容】

* 手順1・2それぞれの実際のステータスコード・レスポンスボディを記録する。

## 【修正禁止事項】

* アプリケーションコードを修正しないでください。

## 【次タスクへ進む条件】

* 記録完了後、T009の指示を待つ。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* 次のテストタスクには進まないでください。
