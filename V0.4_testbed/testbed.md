# testbed.md — spec-driven-dev Skill V0.4 実地検証(テストヘッド)

## これは何か

`spec-driven-dev` Skill(V0.4)を、`V0.2_testbed`(Skill V0.2でのフルパイプライン実地検証。会議室予約システムを題材にした、フェーズ1〜9通しのEnd-to-End実地検証)を土台に再構築したテストヘッド。

V0.3_testbedがV0.2_testbedの `docs/` を丸ごとコピーして「SKILLのルール差分のみ」を確認する差分検証だったのに対し、V0.4はフェーズ構成そのものが大きく変わっている(9フェーズ→Step構成+約30フェーズへの再編、ドキュメントのファイル名がP番号方式に変更、フェーズごとの人間レビュー廃止、ADR/CR/ArchitectureHandbookの新設)ため、本テストヘッドは **V0.2_testbedのフェーズ1成果物(要求仕様)のみを移植し、P002以降は白紙からV0.4のルールで生成させる** 前提でセットアップしている。

* 要求仕様: [`docs/P001-requirement.md`](./docs/P001-requirement.md)(V0.2_testbedの `docs/01-requirement.md` を、V0.4のドキュメント命名・フェーズ番号に合わせて移植したもの。内容は変更していない)
* 技術スタック(P001時点の想定): フロントエンド React 18 + TypeScript + Vite / バックエンド Python + FastAPI / データストア SQLite
* Skillソース: `.claude/skills/spec-driven-dev/`(`V0.4/` のコピー)

## V0.2_testbedを土台にした理由

* V0.3_testbedではなくV0.2_testbedを土台にしたのは、ユーザーからの指示による。V0.4はP002以降のフェーズ構成・ドキュメント形式そのものを作り直しているため、V0.3_testbedの `docs/02-frontend-spec.md` 以降(V0.3の9フェーズ形式で書かれた成果物)をそのまま引き継ぐと、V0.4のP番号・OKF形式・INDEX形式・ADR/CRといった新形式との整合性を保ったまま移植するコストが、P002から再生成するコストを上回ると判断した。
* 一方でP001(要求仕様)は、V0.2→V0.3でも「変更不要」として素通ししていた実績があり、V0.4でもフェーズ構成の変更は要求仕様の内容そのものには影響しないため、そのまま移植している。

## 検証範囲(次回実行時にAgentが確認すべきスコープ)

ユーザー承認のスコープ: **フルパイプライン、かつ人間レビューなしの連続実行**。

* P002〜P302をSkillの指示(`.claude/skills/spec-driven-dev/SKILL.md` 以下)に従って、**フェーズ完了ごとに停止せず**通しで自動実行する。V0.3までの「1フェーズごとに人間レビューで停止」がV0.4では撤廃されていることそのものが検証対象である。
* Executor(P101〜P104)・Reviewer Loop(P201〜P205)は、Skillが本来別セッション/別性能のAgentに委ねる実装・テスト・修正担当の役も本テストヘッドの実行の中で兼ねる。実際にコード(FastAPI + SQLite バックエンド、フロントエンド)を書き、テストを実際に走らせ、不具合が出れば修正サイクルも回す。
* Refactor(P901〜P905)は、Closing(P302)完了後に検証者が意図的にCRを1件起票し、Refactorステップが実際にP002〜P302の該当部分だけを再実行できるかを確認する回として別途行う(本編とは別ラウンドでよい)。

## V0.4で新設・変更された要素のうち、確認すべき観点

### 観点1: 人間レビューなしの連続実行

* V0.3までは1フェーズ完了ごとに停止していたが、V0.4は `docs/.inprogress` の判定にもとづき、Plan Loop Step(P002〜P012)・Executor(P101〜P104)・Reviewer Loop(P201〜P205)を人間の確認なしに連続実行できるか。
* 各Stepの「停止条件」(3回差し戻しでも解消しない等)に該当しない限り、Closing(P302)まで自動的に到達するか。

### 観点2: P004 要求トレーサビリティマトリクス

* `docs/P004-traceability-matrix.md` が、P001の要求事項とP002/P003の対応を実際に検証できているか。
* 意図的にP002またはP003の記述を一部欠落させた場合に、`MISSING`/`PARTIAL` が検出され、P002への差し戻しが機能するか(補足ラウンドで検証)。

### 観点3: P010〜P012 設計書横断レビューループ

* P010が実際に矛盾点を検出できるか(意図的な矛盾を1件仕込んで検証)。
* P011(影響分析)→P012(設計書修正)→P010再実行のループが、Plan Loop Stepの停止条件(3回差し戻し)を超えずに収束するか。

### 観点4: P008/P009 のテスト定義分割

* V0.3では単一の「結合テスト定義」だったものが、P008(スプリント内/モジュール間、Executorが実行)とP009(スプリント横断/システム/受入、Reviewer Loopが実行)に分割されている。
* 各テストが意図通りP008/P009のどちらに分類され、それぞれP103/P201で実行されるか。

### 観点5: Overview Step(P020〜P022)

* `{ソースツリー}/INDEX.md`(P020)、`docs/ArchitectureHandbook.md`(P021)、`docs/ADR.md`(P022)が、Executor開始前に実際に生成され、Executor・Reviewer Loopがこれらを参照するだけで詳細仕様を読み直さずに済んでいるか。

### 観点6: Refactor(P901〜P905)とCR

* 納品(P302)完了後にCRを1件起票し、`docs/CR.md` → P902(要件定義更新、原本リネーム)→ P903(P002〜P302再実行)→ P904(`docs/cr-records/` への退避)→ P905(ADR更新確認)が、一連の流れとして機能するか。
* CRと無関係な既存の仕様・実装・テストが変更されていないか。

## 進め方(次回の実行時のメモ)

* `docs/P001-requirement.md` は移植済みでそのまま使う。`docs/.inprogress` に `P002` を設定済みのため、次回の実行はP002(ユーザインタフェース設計)から始まる。
* 観点2・3・6は、意図的に不備(仕様の欠落・矛盾)やCRを仕込まないと確認できない。本編(不備なしでのフルパイプライン実行)と、補足ラウンド(意図的な不備・CRを用いた検証)を分けて実施すること。V0.3_testbedでも同様に、本編とは別に補足ラウンドでバグを仕込んで修正サイクルを検証した実績がある。
* 検証結果は、本ファイルの「進捗記録」を更新するとともに、`e2e-validation-report.md` としてV0.2_testbed/V0.3_testbedと同じ構成で作成すること。

## 進捗記録

| Step | フェーズ | 状態 | 備考 |
| --- | --- | --- | --- |
| Require Development Step | P001 | ✅ 完了(V0.2_testbedから移植) | `docs/P001-requirement.md`(内容変更なし、ファイル名・フェーズ番号のみV0.4形式に変更) |
| Plan Loop Step | P002〜P012 | ✅ 完了(P010第1回で矛盾0件、P011/P012は不要) | `docs/P002-frontend-spec.md`〜`docs/P010-design-review.md`(P007〜P009は目次+子ドキュメント含む)。次回実行はP020から開始(`docs/.inprogress` = `P020`) |
| Overview Step | P020〜P022 | ✅ 完了 | `client/INDEX.md`・`server/INDEX.md`(P020、コード未着手のため空の目次として作成)、`docs/ArchitectureHandbook.md`(P021)、`docs/ADR.md`(P022、ADR-001〜ADR-007を新規作成)。次回実行はP101から開始(`docs/.inprogress` = `P101`) |
| Executor | P101〜P104 | ✅ 完了(全4スプリントU001〜U004、単体テスト全PASS、結合テストT001〜T020全PASS) | バックエンド: Python + Starlette/Pydantic(SQLite、`hashlib.scrypt`)。フロントエンド: プレーンHTML/CSS/JS(ES Modules)。いずれもADR-001/ADR-002/ADR-004の指定技術(React+TS+Vite、FastAPI、bcrypt)から代替した(サンドボックスがpypi.org/registry.npmjs.orgに接続できずインストール不可のため、`docs/P101-impl-context.md`に記録)。単体テストはpytestの代わりに`unittest`、フロントエンドは`node --test`(jsdom不可のためDOM非依存コントローラ関数を単体テスト対象に設計)。単体テスト121+35=156件PASS。結合テスト(P008 T001〜T020)20件全PASS、記録: `docs/test-records/20260803-1830-test-record.md`。次回実行はP201から開始(`docs/.inprogress` = `P201`) |
| Reviewer Loop | P201〜P205 | ✅ 完了(P201は2回実行。第1回: P009 A001〜A010が10/10件PASS以外、P202〜P205を1ラウンド実施して第2回で全件PASS) | 検出した根本原因3件(いずれもP202-F001〜F003で解決済み): (1) `server/app/api/auth.py` のセッションCookie`Secure`属性が本番向けに無条件固定されており、TLS終端のないプレーンHTTP環境ではログイン直後から認証が維持できない(A001〜A007・A010・A008手順1に波及、環境変数`SESSION_COOKIE_SECURE`で解消)。(2) `docs/P003-backend-spec.md` §8が要求する構造化ログ(JSON Lines)が未実装だった(A009、`server/app/core/logging_utils.py`新設で解消)。(3) A008指示書の期待結果がbcrypt前提のまま承認済みのscrypt代替実装を反映していなかった(ドキュメント更新のみで解消)。修正後、単体156件・P008 20件・P009 10件の計186件が全PASS(回帰なし、`docs/P204-impact-analysis.md`)。記録: `docs/test-records/20260803-1900-test-record.md`(第1回)、`docs/test-records/20260803-1930-test-record.md`(P205)、`docs/P201-review-report.md`、`docs/P202-fix-plan.md`。次回実行はP301から開始予定だったが、本ラウンドでP301・P302まで完了したため `docs/.inprogress` は削除済み |
| Closing | P301〜P302 | ✅ 完了 | `./INDEX.md`(P301)、`docs/P302-deliver.md`(P302、リリース判定: **保留**)。P302で `VERSION`・`BUILD_HISTORY.md`・`server/Dockerfile`・`client/Dockerfile`・`docker-compose.yml`・`nginx.conf`・`.env.example` を新規作成。ただし本サンドボックスにDockerデーモンが存在せず(`docker info`がソケット接続エラー)、Docker Compose資産は実際のビルド・起動確認ができていない(捏造せず`docs/P302-deliver.md` §10に限界として明記)。全フェーズ完了につき `docs/.inprogress` を削除した(`SKILL.md`の規定どおり) |
| Refactor | P901〜P905 | ✅ 完了(CR-001で検証) | CR-001「S03予約作成画面に終日チェックボックスを追加」を起票し、P901(`docs/CR.md`)→P902(`docs/P001-requirement.md`更新、原本を`docs/P001-requirement_20260803.md`に退避)→P903(`docs/P002-frontend-spec.md`/`docs/P006-test-plan.md`/`docs/P007-impl-direction.md`+新規U005を更新し、`client/js/pages/reservationCreatePage.js`を実装、テスト3件追加)→P904(`docs/cr-records/CR-001.md`に退避)→P905(ADR更新不要と確認)まで一貫して完了。バックエンド変更なし。テスト: 156件(既存、回帰なし再確認)+3件(新規)=159件PASS。記録: `docs/test-records/20260803-1810-cr001-test-record.md`。`docs/.inprogress`は削除済み |

**テスト件数サマリ(P302完了時点)**: 単体テスト156件(バックエンド121+フロントエンド35)+ P008結合テスト20件(T001〜T020)+ P009受け入れ結合テスト10件(A001〜A010)= **合計186件、全PASS**(P201第1回ではP009 10件が全件PASS以外だったが、P202〜P205の1ラウンドの実修正サイクルで全件PASSに収束)。CR-001(Refactor)適用後はフロントエンド単体テストが38件(+3)、合計189件、全PASS。

## 検証結果

Skillの不備・曖昧点を23件(高5・中13・低5、致命的なものはなし)発見し、実際のアプリケーション不具合も2件+テスト指示書の記述漏れ1件を、P009受け入れ結合テストが実際に検出・修正した。詳細は [`e2e-validation-report.md`](./e2e-validation-report.md) を参照。V0.5での対応方針も同レポート末尾に記載している。

## 参照

* Skillソース: `V0.4/`(このテストヘッドの `.claude/skills/spec-driven-dev/` はそのコピー)
* 土台にした実地検証: `V0.2_testbed/testbed.md`、`V0.2_testbed/e2e-validation-report.md`
* V0.4での変更点まとめ: `V0.4/SKILL.md` および本リポジトリの回答(V0.3→V0.4のフェーズ再編・ADR/CR/ArchitectureHandbook新設)
* 本検証の結果: [`e2e-validation-report.md`](./e2e-validation-report.md)
