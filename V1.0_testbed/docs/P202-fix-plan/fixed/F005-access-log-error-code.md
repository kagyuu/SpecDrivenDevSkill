あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F005

## 【対応する失敗テスト】A009

## 【障害記録】

* `docs/test-records/20260811-0530-test-record.md` A009参照。認証失敗(401)のアクセスログ行に `error_code` に相当するフィールドが含まれていなかった。
* 原因区分: **アプリケーションコードの欠陥**。
* 調査結果: `server/app/main.py` の `access_log_middleware` は `call_next(request)` が返した `Response` オブジェクトから `method`/`path`/`status_code`/`timestamp` のみを取り出してログ出力しており、レスポンスボディ(JSON、`ApiError.to_body()` が生成する `error_code`/`message`)を見ていない。`docs/P009-acceptance-direction/A009-structured-logging.md` の期待結果はP003 §7(構造化ログ出力)の趣旨に沿った合理的な要求であり、上位文書と矛盾しない。テスト指示側の誤りではなくコード側の未実装と判断する。

## 【参照ファイル】

* `server/app/main.py`(`access_log_middleware`)
* `server/app/api/errors.py`(`ApiError.to_body()`)

## 【調査方針】

* Starletteのミドルウェアで `Response` のボディを読み取る場合、ストリーミングレスポンスのボディを一度読み切ってしまうと後続の送信に影響するため、`StreamingResponse` 化(`body_iterator`の読み直し)が必要になる可能性がある。影響範囲を確認したうえで実装方針を決める。

## 【修正方針】

* `access_log_middleware` で、`response.status_code >= 400` の場合に限り、レスポンスボディ(JSON)から `error_code` を取り出してログに含める。
* 実装例(Starletteの `Response.body` を安全に読み直す方法を用いる):

```python
if response.status_code >= 400:
    body_bytes = b"".join([section async for section in response.body_iterator])
    response.body_iterator = _aiter_bytes(body_bytes)
    try:
        error_code = json.loads(body_bytes.decode("utf-8")).get("error_code")
    except (json.JSONDecodeError, UnicodeDecodeError):
        error_code = None
    if error_code:
        logger.info('{"event": "request", ..., "error_code": "%s"}', ..., error_code)
```

* 具体的な実装詳細(ヘルパー関数名等)はP203の修正実施時に確定してよい。ログ出力全体のJSON構造(既存の `method`/`path`/`status_code`/`timestamp` フィールド)は維持し、`error_code` はエラー時のみ追加するフィールドとする(正常時のログ行の構造を変えない)。

## 【試行錯誤してよい範囲】

* `server/app/main.py` の `access_log_middleware`。
* 必要なら `server/app/api/errors.py` に、ログ出力用のヘルパーを追加してもよい。

## 【修正成功時に更新するdocs】

* 特になし(内部実装の詳細化であり、外部仕様への影響はない)。

## 【ロールバック条件】

* 修正によりレスポンスの実際の返却内容(クライアントが受け取るボディ)が変化した場合、または既存の97件の単体テストのいずれかが壊れた場合は、変更前の状態に戻す。

## 【検証コマンド】

* `cd server && uv run python -m pytest tests/ -v`
* `cd server && uv run python -m pytest tests/acceptance/test_a009_structured_logging.py -v`

## 【完了条件】

* 上記検証コマンドがすべて成功する。
* A009が再実行でPASSになる。

## 重要:

* 作業開始前に現在の変更状態を確認してください。
* 必要な範囲でソースコード変更を試して構いません。
* 修正に成功した場合は、関連する docs/* も必要に応じて更新してください。
* 修正しきれなかった場合は、試行錯誤で変更した未完了のソースコードを元の状態に戻してください。

## 完了条件:

* 全モジュールビルド成功
* すべての Unit Test 成功
* すべての結合テスト成功(P008・P009)
* `docs/P202-fix-plan/P202-fix-resolved.md` に全修正結果が記録されている
* 未解決障害がない、または `docs/P202-fix-plan/P202-fix-unresolved.md` に未解決なしと明記されている

## 未解決時の記録方法:

* 修正しきれなかった障害が1件でもある場合、`TEMPLATE-P202-fix-unresolved.md` の構成に従って `docs/P202-fix-plan/P202-fix-unresolved.md` を作成または更新するよう指示する。

---

## 修正結果(P203)

* 実施日: 2026-08-11
* 変更したソースコード: `server/app/main.py`
  * `_extract_error_code()` を追加し、`access_log_middleware` がレスポンスのステータスコードが400以上の場合にボディから `error_code` を取り出してログに含めるようにした。
  * ログ出力を手動の%書式からJSON構築(`json.dumps`)に変更し、堅牢性を高めた(構造は変えていない)。
* 更新したdocs: なし。
* 実行したテスト: `cd server && uv run python -m pytest tests/ -v`(104件、全PASS)、`cd server && uv run python -m pytest tests/acceptance/test_a009_structured_logging.py -v`
* テスト結果: すべてPASS。A009はFAIL→PASSに変わった。
* 残課題: なし。
* 修正経緯: 初回対応で解決(過去ループでの未解決記録なし)。
