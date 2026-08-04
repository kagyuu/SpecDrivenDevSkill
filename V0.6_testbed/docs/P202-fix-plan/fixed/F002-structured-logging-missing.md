> ## 【対応結果(P203で追記)】
>
> * ステータス: **RESOLVED**(2026-08-03)
> * 変更したソースコード:
>   * `server/app/core/logging_utils.py`(新設) — `log_event(level, event, **fields)`。
>   * `server/app/main.py` — `AccessLogMiddleware`(全リクエストのアクセスログ)を追加。
>   * `server/app/api/errors.py` — `app_error_handler` 内で `AppError` 発生時にエラーログを出力。
> * 更新したdocs: `server/INDEX.md`(ロギング実装の追記)。
> * 実行したテスト・結果:
>   * `cd server && python3 -m unittest discover -s tests -v` → 121件全PASS(回帰なし)。
>   * `GET /api/health`(正常)・`GET /api/reservations/99999`(404エラー)を実行し、標準出力にJSON Lines形式のログ(`{"timestamp":...,"level":"info","event":"http_request",...}` / `{"timestamp":...,"level":"error","event":"app_error",...}`)が出力されることを確認。A009 PASS(`docs/test-records/20260803-1930-test-record.md`参照)。
> * 残課題: なし。
> * 修正経緯: 当初「未解決」記録はなかった(1回目の修正で解決)。

---

あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F002(構造化ログ(JSON Lines)が標準出力に一切出力されていない)

## 【対応する失敗テスト】A009

## 【障害記録】

* `docs/test-records/20260803-1900-test-record.md` 根本原因2。
* `docs/P003-backend-spec.md` §8は「アプリケーションは構造化ログ(JSON Lines)を標準出力に出力する(アクセスログ・Service層でのエラーログ)」と明記しているが、`server/app/main.py`・`server/app/api/errors.py` にログ出力コードが存在しない。実際に確認したところ標準出力にはuvicornの既定アクセスログ(プレーンテキスト)しか出力されない。

## 【参照ファイル】

* `server/app/main.py`
* `server/app/api/errors.py`
* `docs/P003-backend-spec.md` §8

## 【調査方針】

* `server/app/` 配下に `logging`・`log` 関連の実装コードが存在しないことをソース確認済み(grep済み)。単なる実装漏れであり、仕様矛盾ではない。

## 【修正方針】

* `server/app/core/logging_utils.py` を新設し、`log_event(level, event, **fields)` で1行1JSONを `print()` で標準出力に出す薄いユーティリティを実装する。
* `server/app/main.py` にStarletteのミドルウェアを追加し、すべてのリクエストについて `{"level": "info", "event": "http_request", "method", "path", "status_code", "duration_ms", "timestamp"}` 形式でアクセスログを出力する。
* `server/app/api/errors.py` の `app_error_handler` で、`AppError` 発生時に `{"level": "error", "event": "app_error", "code", "message", "path", "timestamp"}` 形式でエラーログを出力してからレスポンスを返す。
* 新規モジュール追加とmain.py/errors.pyへの数行の呼び出し追加のみに留め、既存のレスポンス形式・ステータスコードは変更しない。

## 【試行錯誤してよい範囲】

* `server/app/core/logging_utils.py`(新設)、`server/app/main.py`、`server/app/api/errors.py`。
* 作業前バックアップ: `server/app/main.py`・`server/app/api/errors.py` を `*.bak-F002` として退避してから修正する。

## 【修正成功時に更新するdocs】

* `server/INDEX.md`(ロギング実装の追記)
* `docs/P202-fix-plan/P202-fix-resolved.md`

## 【ロールバック条件】

* 既存の単体テスト(121+35件)またはP008結合テスト(T001〜T020)が1件でも壊れた場合はロールバックする。

## 【検証コマンド】

* `cd server && python3 -m unittest discover -s tests -v`
* サーバー起動後 `GET /api/health` と `GET /api/reservations/99999` を実行し、標準出力に1行1JSON形式のログが出力されることを目視確認する。

## 【完了条件】

* 正常リクエスト・エラーリクエストともに標準出力にJSON Lines形式のログが1行以上出力される。
* 既存単体テスト121+35件が全PASS。

## 重要:

* 作業開始前に現在の変更状態を確認してください(バックアップファイル作成済み)。
* 必要な範囲でソースコード変更を試して構いません。
* 修正に成功した場合は、関連する docs/* も必要に応じて更新してください。
* 修正しきれなかった場合は、試行錯誤で変更した未完了のソースコードを元の状態に戻してください。

## 完了条件:

* 全モジュールビルド成功
* すべての Unit Test 成功
* すべての結合テスト成功(P008・P009のうち本F002が対象とするテスト)
* `docs/P202-fix-plan/P202-fix-resolved.md` に全修正結果が記録されている
* 未解決障害がない、または `docs/P202-fix-plan/P202-fix-unresolved.md` に未解決なしと明記されている

## 未解決時の記録方法:

* 修正しきれなかった障害が1件でもある場合、`TEMPLATE-P202-fix-unresolved.md` の構成に従って `docs/P202-fix-plan/P202-fix-unresolved.md` を作成または更新するよう指示する。
