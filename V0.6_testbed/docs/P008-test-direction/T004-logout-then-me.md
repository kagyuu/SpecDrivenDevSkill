あなたはExecutor(実装担当)です。以下の1テストタスクだけを実施してください。

# 【テストID】T004

## 【目的】

* ログアウト後、同じCookieで `GET /api/me` を呼んでも `401 AUTH_REQUIRED` になること(セッション失効の確認)を検証する。同一スプリント内の複数モジュール(auth.login/logout/me)の連携テストである。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.2(GET /api/me行)

## 【対象モジュール】

* `server/app/api/auth.py`、`server/app/services/auth_service.py`、`server/app/repositories/session_repository.py`

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* U001が完了していること。T001のシードデータが利用可能であること。

## 【使用するテストデータ】

* `employee_id=E0001`, `password=Passw0rd1`

## 【事前準備】

* T001と同様にログインしてCookieを取得する。

## 【実行手順】

1. `POST /api/auth/login` でログインしCookieを取得する。
2. 同一Cookieで `POST /api/auth/logout` を呼ぶ。
3. 同一Cookieで `GET /api/me` を呼ぶ。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_api_auth.py::test_logout_invalidates_session -v`

## 【期待結果】

* 手順2: `200 OK`。
* 手順3: `401 AUTH_REQUIRED`。

## 【合否判定基準】

* 両手順が期待結果どおりであればPASS。

## 【失敗時に記録する内容】

* 手順3の実際のステータスコードを記録する。

## 【修正禁止事項】

* アプリケーションコードを修正しないでください。

## 【次タスクへ進む条件】

* 記録完了後、T005(sprint2)の指示を待つ。sprint1の全テスト(T001〜T004)が完了した時点でP008目次のU001行相当のチェックを進める。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* 次のテストタスクには進まないでください。
