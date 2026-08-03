# 解決済み修正障害一覧

## 概要

* 修正完了した障害数: 3(F001・F002・F003)
* 未解決の障害数: 0
* 全体状態: ALL_RESOLVED(検出された修正課題を全件解決)

## 解決済障害一覧

| 修正タスク | 対応障害 | 結果 | テスト日付 | 修正日付 |
|---|---|---|---|---|
| F001 | A001, A002, A003, A004, A005, A006, A007, A008(手順1), A010 | RESOLVED | 2026/08/03 | 2026/08/03 |
| F002 | A009 | RESOLVED | 2026/08/03 | 2026/08/03 |
| F003 | A008(手順2) | RESOLVED | 2026/08/03 | 2026/08/03 |

## 解決済障害

### F001: セッションCookieの`Secure`属性によるログイン後即時未認証化

* 対応するテストID: A001, A002, A003, A004, A005, A006, A007, A008(手順1), A010
* 対応するテスト記録: `docs/test-records/20260803-1900-test-record.md`(P201第1回、FAIL/BLOCKED検出)、`docs/test-records/20260803-1930-test-record.md`(P205再実行、PASS確認)
* 失敗していたテストコマンド: `requests` によるログイン後の `GET /api/rooms` 等の認証必須API呼び出し(すべて401)
* 修正内容: `server/app/api/auth.py` の `login()` が発行するセッションCookieの `secure` 属性を、環境変数 `SESSION_COOKIE_SECURE`(既定 `true`、ADR-004どおり)で切り替え可能にした。TLSなしのローカル動作確認・受け入れテスト時のみ `SESSION_COOKIE_SECURE=false` を指定する。
* 変更したソースコード: `server/app/api/auth.py`
* 更新したdocs: `docs/ADR.md`(ADR-004備考)、`server/INDEX.md`(実行方法)
* 実行したテスト: `python3 -m unittest discover -s tests -v`(121件)、A001〜A007・A010の再実行(`requests`ベース)
* テスト結果: 単体テスト121件PASS(回帰なし)。A001〜A007・A010すべてPASS。
* 残課題: 本アプリの配布物にTLS終端コンポーネントが含まれていないため、本番相当のデプロイでは別途TLS終端(リバースプロキシ等)を用意する必要がある(`docs/P302-deliver.md` 未整備事項へ申し送り)。
* 修正経緯: 1回目の修正で解決(未解決記録なし)。

### F002: 構造化ログ(JSON Lines)が標準出力に一切出力されていない

* 対応するテストID: A009
* 対応するテスト記録: `docs/test-records/20260803-1900-test-record.md`(FAIL検出)、`docs/test-records/20260803-1930-test-record.md`(PASS確認)
* 失敗していたテストコマンド: `GET /api/health`・`GET /api/reservations/99999` 実行後の標準出力目視確認
* 修正内容: `server/app/core/logging_utils.py` を新設し、リクエストごとのアクセスログ(`AccessLogMiddleware`)とエラー発生時のエラーログ(`app_error_handler`)をJSON Lines形式で標準出力に出力するようにした。
* 変更したソースコード: `server/app/core/logging_utils.py`(新設)、`server/app/main.py`、`server/app/api/errors.py`
* 更新したdocs: `server/INDEX.md`
* 実行したテスト: `python3 -m unittest discover -s tests -v`(121件)、A009の再実行
* テスト結果: 単体テスト121件PASS(回帰なし)。A009 PASS。
* 残課題: なし。
* 修正経緯: 1回目の修正で解決(未解決記録なし)。

### F003: A008手順2の期待結果がbcrypt前提のままで承認済みのscrypt代替実装と食い違っている

* 対応するテストID: A008(手順2)
* 対応するテスト記録: `docs/test-records/20260803-1900-test-record.md`(FAIL検出)、`docs/test-records/20260803-1930-test-record.md`(PASS確認)
* 失敗していたテストコマンド: DBの`users.password_hash`形式確認(期待: bcrypt `$2b$...`、実際: `scrypt1$...`)
* 修正内容: ソースコードは変更せず、`docs/P009-acceptance-direction/A008-security-password-and-sql-injection.md` の期待結果をP101で承認済みのscrypt代替実装に合わせて更新した。
* 変更したソースコード: なし
* 更新したdocs: `docs/P009-acceptance-direction/A008-security-password-and-sql-injection.md`
* 実行したテスト: A008の再実行(手順1〜3)
* テスト結果: A008 PASS(3手順すべて)。
* 残課題: なし。
* 修正経緯: 1回目の修正で解決(未解決記録なし)。
