あなたはReviewer Loop(実装横断レビュー担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Reviewer Loopの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P009-acceptance-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】A007

## 【目的】

* パスワードが平文で保存されていないこと、Cookieが適切な属性で発行されていること、未ログイン状態での全API拒否を横断的に確認する(`docs/P001-requirement.md` 非機能要件「セキュリティ」)。

## 【参照テスト計画】

* `docs/P006-test-plan.md` 3章(セキュリティ観点)

## 【対象モジュール】

* SQLite(`users`テーブル)、`server/app/routers/auth.py`(Cookie発行)、全APIルーター

## 【前提条件】全モジュールビルドが成功していること

* U001〜U005すべてが完了していること

## 【使用するテストデータ】

* シードデータの管理者アカウント

## 【事前準備】

* サーバーを起動しログインを1回行っておく

## 【実行手順】

1. SQLiteファイルを直接開き `users.password_hash` カラムの値を確認する
2. ログイン成功時のレスポンスヘッダーの `Set-Cookie` 属性(`HttpOnly`, `SameSite=Lax`)を確認する
3. Cookie無しで `GET /api/me`, `GET /api/reservations`, `GET /api/rooms` を呼び出す
4. Cookie無しで `POST /api/reservations`, `POST /api/rooms`, `POST /api/users` を呼び出す

## 【実行コマンド】

* `cd server && python -m pytest tests/acceptance/test_security_crosscheck.py -v`

## 【期待結果】

* 手順1: `password_hash` が `scrypt$...$...` 形式であり、平文パスワードと一致しない(`docs/P003-backend-spec.md` 1.2節)
* 手順2: `HttpOnly`・`SameSite=Lax` が含まれる
* 手順3・4: すべて401 `UNAUTHORIZED`

## 【合否判定基準】

* 上記すべてを満たせばPASS。1件でも平文保存またはCookie無しでの成功アクセスが確認されればFAIL(重大)。

## 【失敗時に記録する内容】

* 実際のDB内容(パスワードハッシュ以外の個人情報を記録に含めないよう注意し、ハッシュ形式の異常のみを記録する)、実際のレスポンス

## 【修正禁止事項】

* アプリケーションコードを修正しない。テストコードをその場で都合よく変更しない。失敗したテストをスキップしない。期待値を変更して成功扱いにしない。同じ失敗に対して場当たり的な再テストを繰り返さない。修正が必要な場合はP202以降に引き渡す。

## 【次タスクへ進む条件】

* 結果を記録したらA008へ進む

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Reviewer Loopの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。
