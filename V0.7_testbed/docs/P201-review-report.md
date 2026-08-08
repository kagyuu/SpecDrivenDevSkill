# 実装横断レビュー結果(P201)

> 本書は `spec-driven-dev` Skill フェーズP201の成果物です。
> インプット: `docs/test-records/*.md`、`docs/P008-test-direction.md`(目次)、`docs/P009-acceptance-direction.md`(目次)と各 `A0NN-*.md`
> 本書は Reviewer Loop のループ内で複数回更新される。**第1回の内容は第7章に履歴として保存し、第1〜6章は第2回の判定を示す。※CR-001(P903)による第3回の判定は第8章に追記した(最新の判定は第8章)。**

## 0. 本フェーズの実行回数

**2回目**(1回目 = 2026-08-05T16:03Z、2回目 = 2026-08-05T16:20Z の再実行後)。
Reviewer Loopの停止条件は「3回目のP201実行でなお全件PASSにならない場合」であり、**本実行で全件PASSとなったため停止条件には該当しない**。

## 1. P008(結合テスト)目次の状態確認

`docs/P008-test-direction.md` 第4章の全18行(T001〜T018)が `[x]`。第5章の引き渡し状況も FAIL 0 件に更新済み(T016 は F001 で解消)。**Executor Step への差し戻しは不要。**

## 2. P009(受け入れ結合テスト)の実行状況

`docs/P009-acceptance-direction.md` 第4章の全12行(A001〜A012)が `[x]`。未実施(`[ ]`/`[~]`)の項目はない。第5章の引き渡し状況も FAIL 0 件に更新済み(A001 は F002 で解消)。

### 実行方式(P009 3章・P006 1.1に対する実装上の確定事項)

* **実サーバープロセス(uvicorn)+ 実HTTPクライアント**で実行した。A007(停止・再起動)・A009(同時30接続)・A012(SIGTERM停止と起動失敗)は、同一プロセス内呼び出しの `TestClient` では確認対象そのものを再現できないため、`server/tests/acceptance/support.py`(`subprocess` + `urllib.request`)を新設した。
* 画面を伴うテストは実ブラウザを使わず、画面モジュールの描画関数とイベントハンドラを実サーバーに接続して実行した(P009 3章)。実ブラウザでしか確認できない事項は A011 手順7 として **NOT RUN**(理由記録済み)。
* テストコードの配置は A001 等の★FIXME★の想定どおり `client/tests/acceptance/` と `server/tests/acceptance/` に確定した。

### 事前ビルド(P009 2章)

| コマンド | 終了コード |
| --- | --- |
| `cd server && python3 -m compileall -q src` | 0 |
| `cd client && node --check <src配下の全ESモジュール>` | すべて 0 |

★FIXME★ P009 2章のビルドコマンドは `node --check src/main.js` のみだが、同章の読み替え指示に従い `client/src/**/*.js` の全17ファイルを個別に `node --check` する方式に確定した。

## 3. 全テスト結果の集計(第2回・最新)

| テストID | 種別 | 結果 | 記録 |
|---|---|---|---|
| T001 | 結合(P008) | PASS | docs/test-records/20260805-1226-test-record.md, 20260805-1620-test-record.md |
| T002 | 結合(P008) | PASS | 同上 |
| T003 | 結合(P008) | PASS | 同上 |
| T004 | 結合(P008) | PASS | 同上 |
| T005 | 結合(P008) | PASS | 同上 |
| T006 | 結合(P008) | PASS | 同上 |
| T007 | 結合(P008) | PASS | 同上 |
| T008 | 結合(P008) | PASS | 同上 |
| T009 | 結合(P008) | PASS | 同上 |
| T010 | 結合(P008) | PASS | 同上 |
| T011 | 結合(P008) | PASS | 同上 |
| T012 | 結合(P008) | PASS | 同上 |
| T013 | 結合(P008) | PASS | 同上 |
| T014 | 結合(P008) | PASS | 同上 |
| T015 | 結合(P008) | PASS | 同上 |
| T016 | 結合(P008) | **PASS**(第1回FAIL → F001で解消) | docs/test-records/20260805-1620-test-record.md |
| T017 | 結合(P008) | PASS | docs/test-records/20260805-1226-test-record.md, 20260805-1620-test-record.md |
| T018 | 結合(P008) | PASS | 同上 |
| A001 | 受け入れ結合(P009) | **PASS**(第1回FAIL → F002で解消) | docs/test-records/20260805-1620-test-record.md |
| A002 | 受け入れ結合(P009) | PASS | docs/test-records/20260805-1603-test-record.md, 20260805-1620-test-record.md |
| A003 | 受け入れ結合(P009) | PASS | 同上 |
| A004 | 受け入れ結合(P009) | PASS | 同上 |
| A005 | 受け入れ結合(P009) | PASS | 同上 |
| A006 | 受け入れ結合(P009) | PASS | 同上 |
| A007 | 受け入れ結合(P009) | PASS | 同上 |
| A008 | 受け入れ結合(P009) | PASS | 同上 |
| A009 | 受け入れ結合(P009) | PASS | 同上 |
| A010 | 受け入れ結合(P009) | PASS | 同上 |
| A011 | 受け入れ結合(P009) | PASS | 同上 |
| A012 | 受け入れ結合(P009) | PASS | 同上 |

* 合計 30件(T001〜T018 / A001〜A012)。**PASS 30件 / FAIL 0件 / BLOCKED 0件 / NOT RUN 0件。**
* A011 手順7(実ブラウザでの目視確認)のみ手順単位で NOT RUN。A011の【合否判定基準】が「手順1〜6が完了すればPASS」と定めているため、テストIDとしての A011 は PASS。

### 実行コマンドと実測件数(すべて実行済み)

| レベル | コマンド | 結果 |
|---|---|---|
| バックエンド単体 | `cd server && python3 -m unittest tests.test_*`(15モジュール) | **Ran 213 tests / OK** |
| バックエンド結合(P008分) | `cd server && python3 -m unittest discover -s tests/integration -t .` | **Ran 13 tests / OK** |
| バックエンド受け入れ(P009分) | `cd server && python3 -m unittest discover -s tests/acceptance -t .` | **Ran 14 tests / OK** |
| バックエンド全体 | `cd server && python3 -m unittest discover -s tests -t .` | **Ran 240 tests / OK** |
| フロントエンド単体 | `cd client && node --test 'tests/*.js'` | **126 tests / 126 pass / 0 fail** |
| フロントエンド結合(P008分) | `cd client && node --test 'tests/integration/*.js'` | **41 tests / 41 pass / 0 fail** |
| フロントエンド受け入れ(P009分) | `cd client && node --test 'tests/acceptance/test_*.js'` | **31 tests / 31 pass / 0 fail** |

★FIXME★ `node --test tests` のようにディレクトリを渡す形はモジュール解決エラーになり、Nodeの既定パターンは既存の `test_*.js` という命名に一致しない。実行時は `node --test 'tests/*.js'` のようにグロブでファイルを指定する必要がある(P006 1.1 の「`node --test client/tests`」はそのままでは動かない。`docs/P007-impl-direction.md` 5章 #6 と同じ事象)。

## 4. PASS以外の一覧

**PASS以外は0件。** したがって P202(修正計画)への新規の引き渡しはない。

第1回で検出した2件は、いずれも Reviewer Loop 内で解決済みである。

| # | テストID | 手順 | 事象 | 結論 | 修正タスク |
|---|---|---|---|---|---|
| 1 | T016 | 手順7 | 収容人数超過で `POST /api/reservations` に到達しない | **テスト指示(期待結果)の誤り**。P002 3.3 が「送信時にクライアント側で検証する」と定め、同 3.3「表示項目」が収容人数超過エラー領域を「400 `CAPACITY_EXCEEDED` 時」の表示先と定め、同 7.2 の図が400分岐を「サーバー側検出」と明記しているため、実装が仕様どおり。期待結果を修正した(実装コードは変更なし) | F001 |
| 2 | A001 | 手順5 | 13:00-13:30 の予約に対し 13:30 のセルが空き | **テスト指示(期待結果)の誤り**。ADR-007 が重複判定を半開区間 `[start, end)` と決定しており、終了時刻のスロットは占有しない。A001 自身の手順8も半開区間と整合していた。期待結果を修正した(実装コードは変更なし) | F002 |

* 2件の根本原因は別であるため、`SKILL-P202-fix-plan.md` の「複数テスト1根本原因」の例外は適用せず **1テスト1ファイル**で修正指示を作成した。
* 詳細: `docs/P202-fix-plan/P202-fix-resolved.md`、`docs/P202-fix-plan/fixed/F001-*.md`、`docs/P202-fix-plan/fixed/F002-*.md`、`docs/P204-impact-analysis.md`。

## 5. 合否に含めないが記録・申し送りする事項

| 項目 | 内容 | 引き継ぎ先 |
|---|---|---|
| A004 手順4 | 収容人数を 10→5 に変更した後、既存予約(参加予定人数8)の件名だけを変更する `PUT` は 400 `CAPACITY_EXCEEDED` になる(実測)。A004の★FIXME★どおり仕様未明示 | `docs/P302-deliver.md`(仕様判断) |
| A011 手順7 | 実ブラウザでのレイアウト崩れ・実クリック・エラーメッセージの表示位置の目視確認は環境上実施不能(NOT RUN)。静的配信は実HTTPで確認済み(`/` 200 text/html、`/src/main.js` 200 text/javascript、`/src/styles.css` 200 text/css) | `docs/P302-deliver.md`(環境制約) |
| A003 手順7 | 【使用するテストデータ】を「会議室1件」と厳密に読むと、その1室に予約がある状態では管理者の `DELETE /api/rooms/{id}` が業務制約で409になり「8本すべて成功」と両立しない。実施時は今後の予約を持たない会議室Bを対象にした(読み替え内容はテスト記録に明記) | 文書整備(重大度「低」。必要ならCR) |
| A007 手順8 | SQLiteは最終接続クローズ時にWALを削除するため、「WALファイルが残っている状態」を作るには接続を保持する必要がある(実施時にそのように読み替えた) | 文書整備(重大度「低」。必要ならCR) |
| A006 手順5 | 401時に `api.js` は遷移とメッセージ設定の後に例外を再送出するため、呼び出し側が捕捉していない経路(S02の週送りなど)では未処理のPromise拒否が残る。P002 2.4は遷移とメッセージのみを規定しており仕様違反ではない | `docs/P302-deliver.md`(所見) |
| TLS(HTTPS) | アプリケーション外(リバースプロキシ)の責務。`docs/P003-backend-spec.md` 8章の委譲による。ADRの決定は正しく前提が本環境に無いだけなので、コード・テスト・仕様書はいずれも変更していない | `docs/P302-deliver.md`(既知の制約) |

## 6. 判定

* **結合テスト(T001〜T018)・受け入れ結合テスト(A001〜A012)の全30件がPASS**であることを確認した。BLOCKED・NOT RUN も0件。
* 単体テスト(バックエンド213件 / フロントエンド126件)も全件PASS。
* 未解決の修正課題は0件(`docs/P202-fix-plan/P202-fix-unresolved.md` に未解決なしと明記)。
* **Reviewer Loop の終了条件を満たした。Closing(P301〜)に進む。**
* 停止条件(3回目のP201実行でなお全件PASSにならない)には該当しない。

## 7. 履歴: 第1回の判定(2026-08-05T16:03Z)

第1回のP201では、P009の A001〜A012 を新規に実行し、次の結果を得た。

* 集計: 30件中 **PASS 28件 / FAIL 2件**(T016 手順7 / A001 手順5)/ BLOCKED 0 / NOT RUN 0。
* A001〜A012 の個別結果: A001 **FAIL**(10手順中9手順PASS。手順5のみFAIL)、A002〜A012 **PASS**(A011 手順7 は NOT RUN)。
* T016 は P103 から未解決のまま持ち込まれた FAIL。
* 判定: 全件PASSでないため Closing に進まず、**P202(修正計画)へ差し戻した**。
* 記録: `docs/test-records/20260805-1603-test-record.md`(A001〜A012 の全12件分のブロック)。
* この差し戻しにより P202 → P203 → P204 → P205 を1周実行し、第2回のP201(本書 第1〜6章)で全件PASSに到達した。**差し戻し回数は1回**(停止条件の3回に対して余裕あり)。

## 8. 第3回の判定(※CR-001 / P903 2026-08-05T17:26Z)

* 実施タイミング: CR-001(予約にオンライン会議URL)のP903実行における Reviewer Loop。**3回目のP201実行**にあたるが、これはCR-001対応における1回目の実行であり、同一の失敗に対する差し戻しの結果ではない(第1回・第2回はCR-001以前の別の課題に対するもの)。★ACCEPTED★ 「P201の実行回数」を通算で数えるかCRごとに数えるかは `SKILL.md` に明示がないため、**CRごとに数え直す**と解釈した。停止条件の趣旨が「同じ失敗が3回の差し戻しで解消しないこと」の検出であり、別のCRの実行回数を持ち越すと本来止める必要のない場面で停止してしまうためである。残る制約は、この解釈がSKILL側に明記されていないことであり、`SKILL.md` への追記が望ましい(本報告で指摘済み)。

### 8.1 目次の状態

* `docs/P008-test-direction.md` 第4章: 全19行(T001〜T019。T019はCR-001で追加)が `[x]`。
* `docs/P009-acceptance-direction.md` 第4章: 全12行(A001〜A012)が `[x]`。

### 8.2 テスト結果(CR-001 反映後の全件再実行)

| 区分 | コマンド | 結果 |
|---|---|---|
| サーバー単体 | `cd server && python3 -m unittest discover -s tests -t .`(結合・受入を含む全件) | **262 tests / OK** |
| サーバー結合(T001・T002・T004〜T009・T011〜T014・**T019**) | `cd server && python3 -m unittest discover -s tests/integration -t .` | **14 tests / OK** |
| サーバー受入(A002・A003・A004・A006〜A010・A012) | `cd server && python3 -m unittest discover -s tests/acceptance -t .` | **14 tests / OK** |
| クライアント単体 | `cd client && node --test 'tests/*.js'` | **146 tests / 146 pass / 0 fail** |
| クライアント結合(T003・T010・T015〜T018) | `cd client && node --test 'tests/integration/*.js'` | **46 tests / 46 pass / 0 fail** |
| クライアント受入(A001・A003〜A006・A008・A011) | `cd client && node --test 'tests/acceptance/test_*.js'` | **32 tests / 32 pass / 0 fail** |

* 結合テスト **T001〜T019 の19件すべてPASS**、受け入れ結合テスト **A001〜A012 の12件すべてPASS**。FAIL・BLOCKED は0件。
* NOT RUN は A011 手順7 のみで、実ブラウザが必要という既知の制約(★ACCEPTED★ 済み)。CR-001 によって状況は変わっていない。
* 実行記録: `docs/test-records/20260805-1723-test-record.md`(P103)および `docs/test-records/20260805-1731-test-record.md`(P201 第3回)。

### 8.3 CR-001 に固有の確認

* データモデル変更(`004-meeting-url.sql`)の冪等性を、テスト(T004 / T019 手順12 / A007)と手動確認の両方で確認した。同一DBファイルに対する実プロセスの3回起動がすべて成功し、`schema_migrations` は4行のまま。
* S02(カレンダー)に変更が入っていないことを確認した(`client/src/views/s02-calendar.js` / `client/src/lib/grid.js` に差分なし。`test_grid.js` に「セル表示にURLが混入しない」退行テストを追加してPASS)。

### 8.4 判定(第3回)

* **CR-001 反映後も全テストPASS。Reviewer Loop の終了条件を満たした。P202〜P205(修正フェーズ)は不要。** Closing(P301 → P302)に進む。
* 停止条件には該当しない(差し戻し0回)。
