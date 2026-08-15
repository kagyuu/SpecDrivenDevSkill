# 設計書横断レビュー結果

> 本書は `spec-driven-dev` Skill フェーズP010の成果物。`docs/P001-requirement.md` 〜 `docs/P009-acceptance-direction.md` を横断レビューし、矛盾点を列挙する。

## 実施したレビュー観点

* 用語・命名の一貫性
* 参照関係の整合性(参照先の存在、内容の食い違い)
* スコープの整合性(P001にない画面・API・データモデルの追加/欠落)
* P004(トレーサビリティマトリクス)の状態が全件 `OK` か
* P007・P008・P009 の目次(OKF形式)が P005・P006 の内容と対応しているか
* 図と本文の整合性

---

## 1回目実行

### 矛盾点一覧

| # | 矛盾点の概要 | 関連文書1 | 関連文書2 | 重大度 |
|---|---|---|---|---|
| 1 | `docs/P007-impl-direction.md`「コード格納先」節が、ADR-001・ADR-002を暫定番号ではなく確定番号であるかのように(「ADR-001参照」「ADR-002参照」)記載している。P021(ADR整理)はP010完了後のOverview Stepでのみ実行されるため、本フェーズ時点で `docs/ADR.md` はまだ存在せず、`SKILL.md` 各フェーズ共通指示「ADR番号の暫定参照について」に従い「ADR-001見込み」+★FIXME★の形式にする必要がある。加えて同節は「React + TypeScript + Vite」「Python + FastAPI」という技術スタック名を目次に直接ハードコードしており、`SKILL-P007-impl-direction.md`「目次・見出し・概要文などに...技術スタック名を直接ハードコードしない」に反する。 | `docs/P007-impl-direction.md`(コード格納先節) | `SKILL.md`(ADR番号の暫定参照について)、`SKILL-P007-impl-direction.md` | 中 |
| 2 | ADR番号の割り当てが `docs/P003-backend-spec.md` と `docs/P007-impl-direction.md` の間で食い違っている。`docs/P003-backend-spec.md` §0は「ADR-002見込み」をsqlite3直接アクセス(ORM不使用)の決定に割り当てているが、`docs/P007-impl-direction.md` は「ADR-002」をバックエンド技術(FastAPI)の選定そのものに割り当てている。同じ番号が異なる決定を指しており、このままP021を実行すると、どちらの決定にADR-002を割り当てるべきか一意に定まらない。また `docs/P003-backend-spec.md` はバックエンド技術(FastAPI)選定自体にはADR番号を割り当てておらず、認証のセッション保存方式(§2.1、DBへの永続化・JWT不採用)の決定にもADR番号(暫定含む)が付与されていない。 | `docs/P003-backend-spec.md` §0, §2.1 | `docs/P007-impl-direction.md`(コード格納先節) | 中 |

### 判定

* 矛盾点が2件あるため、P011(影響分析)・P012(設計書修正)を実行し、再度本フェーズを実行する。
* 本フェーズの実行回数: 1回目。

---

## 2回目実行(P012修正後)

`docs/P011-impact-analysis.md` の分析にもとづき、`docs/P003-backend-spec.md` §0・§2.1 と `docs/P007-impl-direction.md`(コード格納先節)を修正した(修正内容は両文書の該当箇所の「※P011矛盾点#1/#2にもとづき修正」の注記を参照)。ADRの粒度・番号割り当てを次のとおり整理し、両文書で一致させた。

| 暫定ADR番号 | 対象の決定 |
| --- | --- |
| ADR-001見込み | フロントエンド技術(React + TypeScript + Vite)の採用 |
| ADR-002見込み | バックエンド技術(FastAPI)の採用 |
| ADR-003見込み | データアクセス方式(標準ライブラリ`sqlite3`直接使用、ORM不使用)の採用 |
| ADR-004見込み | パスワードハッシュ方式(bcrypt)の採用 |
| ADR-005見込み | セッション管理方式(DBテーブルへの永続化、JWT不採用)の採用 |

### 再レビュー結果

| # | 確認内容 | 結果 |
|---|---|---|
| 1 | `docs/P007-impl-direction.md` の記載が「ADR-001見込み ★FIXME★」「ADR-002見込み ★FIXME★」の形式になっているか、目次から技術スタック名のハードコードが除かれているか | 解消 |
| 2 | `docs/P003-backend-spec.md` と `docs/P007-impl-direction.md` のADR番号が指す決定内容が一致しているか、認証まわりの2決定(bcrypt/セッション管理)にも暫定番号が付与されているか | 解消 |

* 矛盾点は0件。実施したレビュー観点(冒頭参照)はすべて満たされていることを確認した。
* P004(トレーサビリティマトリクス)は全件 `OK`(2回目実行時点、`docs/P004-traceability-matrix.md` 参照)。
* P007・P008・P009の目次は、P005のスプリント構成(U001〜U004)・P006のテスト観点と対応している。
* 図と本文の整合性: `docs/P002-frontend-spec.md` の画面遷移図・ER図・シーケンス図と、それぞれの周辺本文の記述に食い違いは見つからなかった。

### 判定

* 矛盾点0件のため、Plan Loop Stepを終了し、Overview Step(P020〜)に進む。
* 本フェーズの実行回数: 2回。

---

## CR-001対応(Refactor経由、1回目実行)

`docs/P901-cr-direction/CR-001.md`(「備考(社内向けメモ)」欄追加)にもとづき更新した `docs/P002-frontend-spec.md`・`docs/P003-backend-spec.md`・`docs/P004-traceability-matrix.md`・`docs/P005-impl-plan.md`・`docs/P006-test-plan.md`・`docs/P007-impl-direction.md`(U002-T7・U003-T7)・`docs/P008-test-direction.md`(T010)を横断的にレビューした。

* 用語・命名の一貫性: 「備考(社内向けメモ)」の表記、`internal_memo` のフィールド名がP002・P003・P007・P008で統一されていることを確認した。
* 参照関係の整合性: P004が参照するP002 §3 S03/S04・§6、P003 §3.2/§4/§5.6/§5.8/§5.9がいずれも実在し、内容も対応していることを確認した。P005 §6が参照するU002-T7・U003-T7が実在することを確認した。P008 T010が参照するP006の新規観点(閲覧範囲のマスキング)が実在することを確認した。
* スコープの整合性: 新規追加された項目(`internal_memo`)は、`docs/P901-cr-direction/CR-001.md` の「変更要求の内容」の範囲内にとどまっている(新たな画面・APIエンドポイントの追加は無い)。
* P004の状態: CR-001分の要求ID(REQ-CR001-001〜003)はすべて`OK`。
* 矛盾点: 0件。

### 判定

* 矛盾点0件のため、CR-001に関するPlan Loop Stepの差分更新を終了し、Overview Step相当(P020のINDEX更新)・Executor(P101〜P104)に進む。
* 本フェーズの実行回数(CR-001対応分、Refactor経由のためリセットしてカウント): 1回。
