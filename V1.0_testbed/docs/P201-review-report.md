# 実装横断レビュー結果

> 本書は `spec-driven-dev` Skill フェーズP201の成果物。P103(結合テスト実行)の結果と、`docs/P009-acceptance-direction.md` にもとづく受け入れ結合テストの実行結果をあわせて判定する。複数回実行しているため、最新の判定を本文冒頭に、過去の実行結果を末尾の「実行履歴」章に保持する。

## 最新の判定(2回目実行、2026-08-11)

### 前提確認

* `docs/P008-test-direction.md` の全T0NN(T001〜T009)が `[x]` であることを確認した。
* `docs/P009-acceptance-direction.md` の全A0NN(A001〜A009)が `[x]` であることを確認した。
* P202(F001〜F005)・P203(修正実施)・P204(影響分析)・P205(結合テスト再実施)を経て、`docs/test-records/20260811-0545-test-record.md` に全18件の再実行結果を記録済み。

### 全テスト集計

| テストID | 種別 | 結果 | 記録 |
|---|---|---|---|
| T001 | 結合(P008) | PASS | docs/test-records/20260811-0545-test-record.md |
| T002 | 結合(P008) | PASS | docs/test-records/20260811-0545-test-record.md |
| T003 | 結合(P008) | PASS | docs/test-records/20260811-0545-test-record.md |
| T004 | 結合(P008) | PASS | docs/test-records/20260811-0545-test-record.md |
| T005 | 結合(P008) | PASS | docs/test-records/20260811-0545-test-record.md |
| T006 | 結合(P008) | PASS | docs/test-records/20260811-0545-test-record.md |
| T007 | 結合(P008) | PASS | docs/test-records/20260811-0545-test-record.md |
| T008 | 結合(P008) | PASS | docs/test-records/20260811-0545-test-record.md |
| T009 | 結合(P008) | PASS | docs/test-records/20260811-0545-test-record.md |
| A001 | 受け入れ結合(P009) | PASS | docs/test-records/20260811-0545-test-record.md |
| A002 | 受け入れ結合(P009) | PASS | docs/test-records/20260811-0545-test-record.md |
| A003 | 受け入れ結合(P009) | PASS | docs/test-records/20260811-0545-test-record.md |
| A004 | 受け入れ結合(P009) | PASS | docs/test-records/20260811-0545-test-record.md |
| A005 | 受け入れ結合(P009) | PASS | docs/test-records/20260811-0545-test-record.md |
| A006 | 受け入れ結合(P009) | PASS | docs/test-records/20260811-0545-test-record.md |
| A007 | 受け入れ結合(P009) | PASS | docs/test-records/20260811-0545-test-record.md |
| A008 | 受け入れ結合(P009) | PASS | docs/test-records/20260811-0545-test-record.md |
| A009 | 受け入れ結合(P009) | PASS | docs/test-records/20260811-0545-test-record.md |

**18件中18件PASS。**

### 判定

* 全件PASSのため、Closing(P301〜)に進む。

### 本フェーズの実行回数

* 2回目(1回目実行で8件のFAILを検出、P202〜P205で修正し本ラウンドで全件PASSを確認)。

---

## 実行履歴

### 1回目実行(2026-08-11)

#### 前提確認

* `docs/P008-test-direction.md` の全T0NN(T001〜T009)が `[x]` であることを確認した(P103で完了済み)。
* `docs/P009-acceptance-direction.md` は全項目が `[ ]`(未実施)だったため、本フェーズでA001〜A009をすべて新規実行した(テストコードも本フェーズで新規作成)。詳細は `docs/test-records/20260811-0530-test-record.md`。

#### 全テスト集計

| テストID | 種別 | 結果 | 記録 |
|---|---|---|---|
| T001 | 結合(P008) | FAIL | docs/test-records/20260811-0500-test-record.md |
| T002 | 結合(P008) | PASS | docs/test-records/20260811-0500-test-record.md |
| T003 | 結合(P008) | FAIL | docs/test-records/20260811-0500-test-record.md |
| T004 | 結合(P008) | PASS | docs/test-records/20260811-0500-test-record.md |
| T005 | 結合(P008) | PASS | docs/test-records/20260811-0500-test-record.md |
| T006 | 結合(P008) | FAIL | docs/test-records/20260811-0500-test-record.md |
| T007 | 結合(P008) | PASS | docs/test-records/20260811-0500-test-record.md |
| T008 | 結合(P008) | PASS | docs/test-records/20260811-0500-test-record.md |
| T009 | 結合(P008) | PASS | docs/test-records/20260811-0500-test-record.md |
| A001 | 受け入れ結合(P009) | FAIL | docs/test-records/20260811-0530-test-record.md |
| A002 | 受け入れ結合(P009) | FAIL | docs/test-records/20260811-0530-test-record.md |
| A003 | 受け入れ結合(P009) | PASS | docs/test-records/20260811-0530-test-record.md |
| A004 | 受け入れ結合(P009) | FAIL | docs/test-records/20260811-0530-test-record.md |
| A005 | 受け入れ結合(P009) | PASS | docs/test-records/20260811-0530-test-record.md |
| A006 | 受け入れ結合(P009) | FAIL | docs/test-records/20260811-0530-test-record.md |
| A007 | 受け入れ結合(P009) | FAIL | docs/test-records/20260811-0530-test-record.md |
| A008 | 受け入れ結合(P009) | PASS | docs/test-records/20260811-0530-test-record.md |
| A009 | 受け入れ結合(P009) | FAIL | docs/test-records/20260811-0530-test-record.md |

18件中10件PASS、8件FAIL。

#### FAILの一覧と推定根本原因(P202での調査対象)

| # | 対象テスト | 推定根本原因(暫定、P202で確定) |
|---|---|---|
| 1 | T001 | S02(`CalendarPage.tsx`)にログインユーザー名の表示・ログアウト導線が実装されていない(未実装、`docs/P002-frontend-spec.md` §4・§1が要求する機能の欠落) |
| 2 | T003, A001 | 日付計算が`toISOString()`(UTC変換)を使っており、ローカルタイムゾーンによっては「今日」の日付がずれる(`client/src/pages/CalendarPage.tsx` 等) |
| 3 | T006, A002, A006, A007 | 実サーバー(uvicorn)の複数ワーカースレッド下で `sqlite3.Connection` を跨スレッド使用しようとして `sqlite3.ProgrammingError` が発生する(`server/app/db/connection.py`・`server/app/api/deps.py`) |
| 4 | A004 | `docs/P003-backend-spec.md` §5.9(半開区間・背中合わせ予約は重複としない)と、`docs/P009-acceptance-direction/A004-*.md` 手順3・4の期待結果(409を期待)が矛盾している。P202で「テスト指示側の誤り」に該当するか判定する。 |
| 5 | A009 | ログミドルウェア(`server/app/main.py` の `access_log_middleware`)が、エラーレスポンス時に `error_code` をログへ含めていない |

PASS以外(FAIL)が8件あるため、P202(修正計画)に進んだ。

#### 判定内訳(P202での最終確定)

* F001(T001)・F002(T003, A001)・F003(T006, A002, A006, A007)・F005(A009): アプリケーションコードの欠陥として修正。
* F004(A004): `docs/P003-backend-spec.md` §5.9と矛盾する「テスト指示側の誤り」として、コード修正を伴わずテスト指示・テストコードの期待値を訂正。詳細は `docs/P202-fix-plan/fixed/F004-a004-back-to-back-expectation.md` を参照。

#### 本ラウンドの実行回数

* 1回目。

---

## CR-001対応(Refactor経由、1回目実行)

### 前提確認

* `docs/P008-test-direction.md` のT010が `[x]` であることを確認した。
* CR-001は既存のT001〜T009・A001〜A009が対象とする画面・APIの外部契約を変更しないため(新規フィールドの追加のみ)、これらは再実行のみ行い、内容の変更は不要と判断した(`docs/P903-cr-records/CR-001.md` 対象外フェーズの理由参照)。

### 全テスト集計

| テストID | 種別 | 結果 | 記録 |
|---|---|---|---|
| T001〜T009 | 結合(P008) | 全PASS | docs/test-records/20260811-CR001-test-record.md |
| T010 | 結合(P008、※CR-001により新規追加) | PASS | docs/test-records/20260811-CR001-test-record.md |
| A001, A002, A004, A005, A007 | 受け入れ結合(P009) | 全PASS | docs/test-records/20260811-CR001-test-record.md |
| A003, A006, A008, A009 | 受け入れ結合(P009、`server/tests/acceptance/`側) | 全PASS(`server/.venv/python.exe -m pytest`実行分に含む) | docs/test-records/20260811-CR001-test-record.md |

**T001〜T010(10件)・A001〜A009(9件)、合わせて19件中19件PASS。** サーバー単体テスト(pytest)121件、クライアント単体テスト(vitest)25件もあわせて全PASS。

### 判定

* 全件PASSのため、修正(P202〜P205)は不要。Closing相当(CR-001分のP301・P302再実行)に進む。

### 本フェーズの実行回数

* CR-001対応分、Refactor経由のためリセットしてカウント: 1回。
