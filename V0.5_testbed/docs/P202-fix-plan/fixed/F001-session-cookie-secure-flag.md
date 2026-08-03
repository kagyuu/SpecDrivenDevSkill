> ## 【対応結果(P203で追記)】
>
> * ステータス: **RESOLVED**(2026-08-03)
> * 変更したソースコード:
>   * `server/app/api/auth.py` — `_cookie_secure()` を追加し、環境変数 `SESSION_COOKIE_SECURE`(既定 `true`)で `set_cookie` の `secure` を切り替え可能にした。既定動作(未指定時)はADR-004どおり `secure=True` のまま変更なし。
> * 更新したdocs:
>   * `docs/ADR.md` ADR-004備考に、`SESSION_COOKIE_SECURE` 環境変数とTLS前提についての注記を追加。
>   * `server/INDEX.md` 実行方法に、TLSなしのローカル動作確認用起動コマンド(`SESSION_COOKIE_SECURE=false`)を追加。
> * 実行したテスト・結果:
>   * `cd server && python3 -m unittest discover -s tests -v` → 121件全PASS(回帰なし)。
>   * `SESSION_COOKIE_SECURE=false` で起動したサーバーに対し `requests` ライブラリで再検証: A001(PASS)・A002(PASS)・A003(PASS)・A004(PASS)・A005(PASS)・A006(PASS)・A007(PASS)・A010(PASS)。詳細は `docs/test-records/20260803-1930-test-record.md`(P205)を参照。
> * 残課題: 本アプリの配布物にTLS終端コンポーネント(リバースプロキシ・証明書)が含まれていないため、本番相当のデプロイでは別途TLS終端を用意する必要がある。`docs/P302-deliver.md` の未整備事項として申し送り済み。
> * 修正経緯: 当初「未解決」記録はなかった(1回目の修正で解決)。

---

あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F001(セッションCookieの`Secure`属性によるログイン後即時未認証化)

## 【対応する失敗テスト】A001 / A002 / A003 / A004 / A005 / A006 / A007 / A010(いずれも同一の根本原因によるFAIL/BLOCKED)、A008(手順1のみ、同一原因)

> ★このF001は、`docs/P201-review-report.md` で判明した「単一の根本原因が8件超のテストIDに共通して波及している」ケースであるため、`SKILL-P202-fix-plan.md` の原則(失敗したテスト1件につき1ファイル)から意図的に外れ、根本原因単位で1ファイルにまとめている。理由と運用は本書末尾の「重要」節、および `docs/test-records/20260803-1900-test-record.md` を参照。個々のテストIDの完了は本ファイル1件の修正の完了をもって一括して扱う。

## 【障害記録】

* `docs/test-records/20260803-1900-test-record.md`(P201第1回実行記録)の「根本原因の分析」節、根本原因1。
* 症状: ログイン(`POST /api/auth/login`)自体は200で成功しSet-Cookieも返るが、同じCookieを使った直後の認証必須API呼び出し(`GET /api/rooms` 等)が例外なく `401 AUTH_REQUIRED` になる。`requests`ライブラリ(RFC 6265準拠、実ブラウザ相当のCookieジャー挙動)で確認・再現済み。

## 【参照ファイル】

* `server/app/api/auth.py`(`login()` の `resp.set_cookie(..., secure=True, ...)`)
* `docs/ADR.md` ADR-004(Cookieの `HttpOnly / Secure / SameSite=Lax` を決定)
* `server/INDEX.md`(現状の起動方法。TLS終端の記載なし)
* `server/tests/test_api_auth.py`(`TestClient(app, base_url="https://testserver")` でこの問題を単体テスト側では回避していた)

## 【調査方針】

* `secure=True` が固定でハードコードされていることを確認する(確認済み、`server/app/api/auth.py` L44)。
* ADR-004自体は「Secure Cookie」を正しい決定として維持する(セキュリティ上望ましい)。一方、本アプリの配布物にTLS終端コンポーネント(リバースプロキシ・証明書)が一切含まれていないため、`server/INDEX.md` に記載の起動方法どおりに実行する限り、実際のHTTPクライアントでは常にこの不具合が再現する。
* この矛盾は「ADR-004が間違っている」のではなく、「ADR-004の前提(HTTPSでのアクセス)を満たす配布資産が現状ない」という配布・環境面の未整備によるものと判断する。

## 【修正方針】

* `secure=True` の固定値をやめ、環境変数(例: `SESSION_COOKIE_SECURE`、既定値 `true` でADR-004の本番相当の挙動を維持)で切り替え可能にする。
* ローカル/本サンドボックスでのTLSなし動作確認時のみ `SESSION_COOKIE_SECURE=false` を明示的に指定して起動する運用とする。
* `docs/ADR.md` ADR-004の「備考」に、上記の環境変数による切り替えと、本番相当の配布ではTLS終端(リバースプロキシ等)を前提とする旨を追記する(仕様書の明確化、原則の範囲内)。
* `server/INDEX.md` の「実行方法」に、プレーンHTTPでの動作確認時は `SESSION_COOKIE_SECURE=false` を指定する旨を追記する。
* TLS終端コンポーネント自体をこのF001で新設することはしない(範囲を無制限に広げないため)。TLS終端が配布物に含まれていないこと自体は `docs/P302-deliver.md` の「未整備事項」として申し送る。

## 【試行錯誤してよい範囲】

* `server/app/api/auth.py` の該当箇所、および関連する起動スクリプト・設定。
* 作業前バックアップ: 本プロジェクトはGit管理されていないため、作業前に `server/app/api/auth.py` を `server/app/api/auth.py.bak-F001` として退避してから修正する。

## 【修正成功時に更新するdocs】

* `docs/ADR.md`(ADR-004備考に追記)
* `server/INDEX.md`(実行方法に環境変数を追記)
* `docs/P202-fix-plan/P202-fix-resolved.md`

## 【ロールバック条件】

* 環境変数の追加だけでADR-004の本番既定動作(`secure=true`)が変わらないことを確認できない場合はロールバックする。
* 既存の単体テスト(121+35件)が1件でも壊れた場合はロールバックする。

## 【検証コマンド】

* `cd server && python3 -m unittest discover -s tests -v`(既存121件、回帰確認)
* `SESSION_COOKIE_SECURE=false DATABASE_PATH=/tmp/a9_test_data/app.db python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8811` を起動し、`requests` でログイン→`GET /api/me` が200になることを確認する。
* A001・A002・A003・A005・A006・A007を再実行する(P205で実施)。

## 【完了条件】

* `SESSION_COOKIE_SECURE=false` 起動時、ログイン後の後続の認証必須APIが200になる。
* `SESSION_COOKIE_SECURE` 未指定(既定)時は従来どおり `secure=true` のままである(ADR-004の本番相当動作を破壊しない)。
* 既存単体テスト121+35件が全PASS。

## 重要:

* 作業開始前に現在の変更状態を確認してください(バックアップファイル作成済み)。
* 必要な範囲でソースコード変更を試して構いません。
* 修正に成功した場合は、関連する docs/* も必要に応じて更新してください。
* 修正しきれなかった場合は、試行錯誤で変更した未完了のソースコードを元の状態に戻してください。
* 原因が仕様矛盾の場合は、コードで無理に解決せず、人間に判断を促す内容を `docs/P202-fix-plan/P202-fix-unresolved.md` に記録してください(本件はTLS終端の配布未整備という環境面の申し送りを伴うが、コード修正自体は可能なため「未解決」ではなく「解決」として扱い、TLS配布状況のみ申し送り事項とする)。

## 完了条件:

* 全モジュールビルド成功
* すべての Unit Test 成功
* すべての結合テスト成功(P008・P009のうち本F001が対象とするテスト)
* `docs/P202-fix-plan/P202-fix-resolved.md` に全修正結果が記録されている
* 未解決障害がない、または `docs/P202-fix-plan/P202-fix-unresolved.md` に未解決なしと明記されている

## 未解決時の記録方法:

* 修正しきれなかった障害が1件でもある場合、`TEMPLATE-P202-fix-unresolved.md` の構成に従って `docs/P202-fix-plan/P202-fix-unresolved.md` を作成または更新するよう指示する。
