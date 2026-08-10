あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F004

## 【対応する失敗テスト】A008

## 【障害記録】

* 症状: 誤った認証情報でのログイン試行時に、`event="login_failed"`の構造化ログ(JSON Lines、WARNINGレベル)が標準出力に出力されない。
* 発生条件: 常に発生する(未実装のため100%再現)。
* 原因区分: **アプリケーションコードの欠陥**(U005-T5実行時に、この特定のログ出力箇所への配線が明示的にスコープ外として先送りされていた。`server/app/logging_utils.py`のモジュールdocstring参照)。
* 判定根拠(テスト指示側の誤りではないことの確認): `docs/P003-backend-spec.md` 6章は「警告レベル(WARNING)で出力するもの: 認証失敗の連続発生」と記載しており、文言上「連続発生(N回以上)」を要求しているように読める余地はあるが、(1) P001〜P003のいずれにも具体的なしきい値Nの記載が無く、しきい値ベースの実装はそもそも不可能である、(2) 同章の直後の★ACCEPTED★注記は「アカウントロック機能」の要否についての検討であり、対象はロック機能でありログ出力のしきい値ではない、(3)「ログ出力のみ行い、自動ロックは実装しない」という対比構造から、単純に「(ロックはしないが)ログだけは毎回出す」という意図と読むのが自然である。よって「テスト指示側の誤り」には該当しない。

## 【参照ファイル】

* `server/app/services/auth_service.py`(`login`関数、`InvalidCredentialsError`を送出する箇所)
* `server/app/logging_utils.py`(`log_event`関数、既存の汎用ヘルパー)
* `docs/P003-backend-spec.md` 6章
* `docs/test-records/20260809-1900-test-record.md` A008の詳細な原因分析

## 【調査方針】

* `log_event`関数の呼び出し規約(`log_event(level, event, *, request_id=None, user_id=None, **extra)`)を確認し、`auth_service.login`から呼び出す際に必要な情報(社員ID等)をどう渡すか検討する。
  * ★注意: ログに残す`user_id`について、存在しない社員IDでのログイン試行の場合は該当ユーザーが無いため`user_id`は付与できない(社員ID自体をログに残すかどうかは、社員IDが個人情報に準ずる可能性があるため、`docs/P003-backend-spec.md` 6章の記載範囲(`timestamp`, `level`, `event`, `user_id`(取得できる場合), `request_id`)に厳密に従い、「取得できる場合」のみ付与する = 実在する社員IDで単にパスワードが違う場合のみ`user_id`を付与し、存在しない社員IDの場合は`user_id`を付与しない、という判断で良いか確認する)。

## 【修正方針】

* `server/app/services/auth_service.py`の`login`関数内、`InvalidCredentialsError`を送出する直前(ユーザーが存在しない場合、およびパスワードが一致しない場合の両方)に、`log_event("WARNING", "login_failed", user_id=employee_id if user is not None else None)`のような呼び出しを追加する。
  * ただし、`app/services/auth_service.py`は`app/logging_utils.py`のような横断的関心事のモジュールに依存すること自体は許容範囲と判断する(Service層がRepository層以外に依存しないという制約は、業務ロジックの依存関係についてのものであり、ログ出力という横断的関心事はこの制約の対象外と解釈する)。

## 【試行錯誤してよい範囲】

* `server/app/services/auth_service.py`の変更が主。`server/app/logging_utils.py`側のインターフェース変更が必要な場合は最小限にとどめる。

## 【修正成功時に更新するdocs】

* `server/INDEX.md`: `app/services/auth_service.py`の項目があれば、`login_failed`イベントのログ出力に対応した旨を追記する(現状は個別関数レベルの詳細記載は無いため、必要に応じて追加)。

## 【ロールバック条件】

* 修正後、既存の認証関連の単体テスト(`server/tests/test_auth_service.py`, `server/tests/test_auth_api.py`)のいずれかが新たに失敗する場合。

## 【検証コマンド】

* `cd server && python -m pytest tests/test_auth_service.py tests/test_auth_api.py -v`(既存単体テストの回帰確認)
* `cd server && python -m pytest tests/acceptance/test_structured_logging.py -v`(A008相当)

## 【完了条件】

* 上記検証コマンドがすべてPASSする。

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

## 【修正結果(P203実施)】

* 修正日: 2026-08-09
* 実施内容: `server/app/services/auth_service.py`の`login`関数に`app/logging_utils.py`の`log_event`呼び出しを追加した。存在しない社員IDの場合は`user_id`を付与せず`log_event("WARNING", "login_failed")`、実在する社員IDでパスワードが不一致の場合は`log_event("WARNING", "login_failed", user_id=user["user_id"])`を、いずれも`InvalidCredentialsError`を送出する直前に呼び出す。
* 変更したソースコード: `server/app/services/auth_service.py`(import追加+2箇所のログ呼び出し追加)
* 更新したdocs: なし
* 実行したテスト・結果:
  * `cd server && python -m pytest tests/test_auth_service.py tests/test_auth_api.py -v` → 17件PASS(回帰なし)
  * `cd server && python -m pytest tests/acceptance/test_structured_logging.py -v` → PASS(修正前は決定的にFAILしていた)
* テスト結果: A008がPASSに転じたことを確認した。
* 残課題: なし。`docs/P003-backend-spec.md` 6章が例示する他のイベント(`reservation_conflict`等)への配線は、A008自体が要求する範囲外のため本タスクでは行っていない。
* 修正経緯: 一発で修正が成功し、追加の試行錯誤は不要だった。
