あなたはExecutor(実装担当)です。以下の1テストタスクだけを実施してください。

# 【テストID】T001

## 【目的】

* 正しい社員ID・パスワードでログインでき、発行されたセッションCookieで `GET /api/me` から自分自身の情報が取得できることを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1(S01行)

## 【対象モジュール】

* `server/app/api/auth.py`、`server/app/services/auth_service.py`、`server/app/repositories/user_repository.py`、`server/app/repositories/session_repository.py`

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* U001(foundation-auth)の全タスクが完了していること。

## 【使用するテストデータ】

* シードスクリプトで投入する一般ユーザー: `employee_id=E0001`, `password=Passw0rd1`, `is_active=true`

## 【事前準備】

* テスト用DBを初期化し、上記シードデータを投入する。

## 【実行手順】

1. `POST /api/auth/login` に `{"employee_id": "E0001", "password": "Passw0rd1"}` を送信する。
2. レスポンスの `Set-Cookie` を保持する。
3. 同一Cookieを付けて `GET /api/me` を呼ぶ。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_api_auth.py::test_login_success_then_me -v`

## 【期待結果】

* 手順1: `200 OK`、レスポンスボディに `{"user": {"employee_id": "E0001", ...}}`、`Set-Cookie` ヘッダあり。
* 手順3: `200 OK`、`employee_id` が `E0001` と一致する。

## 【合否判定基準】

* 手順1・手順3の両方が期待結果どおりであればPASS。いずれか一方でも異なればFAIL。

## 【失敗時に記録する内容】

* 実際のステータスコード、レスポンスボディ、Set-Cookieヘッダの有無を `docs/test-records/` に記録する。

## 【修正禁止事項】

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。

## 【次タスクへ進む条件】

* PASS/FAIL/BLOCKEDいずれであっても、テスト記録への記載が完了したら次のテストタスク(T002)の指示を待つ。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* 次のテストタスクには進まないでください。
