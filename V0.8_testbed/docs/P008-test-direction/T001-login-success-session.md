あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T001

## 【目的】

* 正しい社員ID・パスワードでのログインが、DBへのセッション作成とCookie発行という複数モジュール(APIハンドラ・Service層・Repository層・DB)の連携を通じて正しく完了することを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` 2.1節(バックエンドAPI単体テストとは別に、Service〜DB間の結合を確認する)

## 【対象モジュール】

* `server/app/routers/auth.py`, `server/app/services/auth_service.py`, `server/app/repositories/session_repository.py`, `server/app/repositories/user_repository.py`, SQLite(`sessions`, `users` テーブル)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* U001の全タスク(`docs/P007-impl-direction/U001-foundation-and-auth.md`)が完了していること

## 【使用するテストデータ】

* シードデータの管理者アカウント(`user_id=admin`, パスワード `ChangeMe123!`。`docs/P007-impl-direction/U001-foundation-and-auth.md` U001-T2参照)

## 【事前準備】

* テスト用の一時SQLiteファイルにマイグレーションを適用し、シードデータを投入した状態でサーバーを起動する

## 【実行手順】

1. `POST /api/auth/login` に `{"employee_id": "admin", "password": "ChangeMe123!"}` を送信する
2. レスポンスヘッダーの `Set-Cookie` を確認する
3. SQLiteファイルを直接クエリし、`sessions` テーブルに新規行が作成されていること、`expires_at` が現在時刻から約8時間後であることを確認する
4. 手順1で取得したCookieを使い `GET /api/me` を呼び出す

## 【実行コマンド】

* `cd server && python -m pytest tests/integration/test_login_session_integration.py -v`(結合テスト専用ディレクトリに実装する)

## 【期待結果】

* 手順1: 200、`Set-Cookie: session_id=...` が含まれる
* 手順3: `sessions` テーブルに1行、`user_id='admin'`
* 手順4: 200、`{"employee_id": "admin", "name": "システム管理者", "role": "admin"}`

## 【合否判定基準】

* 上記期待結果をすべて満たせばPASS。いずれか1つでも満たさなければFAIL。

## 【失敗時に記録する内容】

* 実際のレスポンスステータス・ボディ、`sessions` テーブルの実際の内容、失敗した手順番号

## 【修正禁止事項】

* アプリケーションコードを修正しない。テストコードをその場で都合よく変更しない。失敗したテストをスキップしない。期待値を変更して成功扱いにしない。同じ失敗に対して場当たり的な再テストを繰り返さない。

## 【次タスクへ進む条件】

* 結果(PASS/FAIL/BLOCKED)を`docs/test-records/YYYYMMDD-HHMM-test-record.md`に記録したら、T002へ進む

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Executor Stepの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
