# 設計書横断レビュー結果 — 会議室予約システム

> 本書は `spec-driven-dev` Skill フェーズP010の成果物です。`docs/P001-requirement.md` 〜 `docs/P009-acceptance-direction.md` を横断的にレビューし、矛盾点を列挙します。

## 実行回数

* 本フェーズの実行: **2回目**(1回目で検出した4件の矛盾点をP011・P012で修正した後の再レビュー。通常フローでの実行のため通算カウントは適用せず、Plan Loop Step内でのカウント上限3回に対し2回目)。

## レビュー観点

* 用語・命名の一貫性
* 参照関係の整合性
* スコープの整合性(P001にない画面・API・データモデルの追加/欠落)
* P004(要求トレーサビリティマトリクス)の状態が全件`OK`になっているか
* P007・P008・P009の目次(OKF形式)がP005・P006の内容と対応しているか
* 図と本文の整合性

## 1回目で検出した矛盾点の解消確認

| # | 概要 | 修正内容 | 解消確認 |
|---|---|---|---|
| 1 | `node --test`にTS/JSXトランスフォームの指定が無い | `docs/P006-test-plan.md` 5章に`tsx`ローダー方式を明記し、`docs/P007-impl-direction/U001-foundation-and-auth.md` U001-T1に依存追加、`docs/P007-impl-direction/*.md`・`docs/P008-test-direction/T0NN-*.md` の全「実行コマンド」を `node --import tsx --test` に統一した(`docs/P009-acceptance-direction.md` 側のクライアント実行コマンドは意図的に対象外とし、その理由も明記した) | 解消。全23箇所の実行コマンドを確認し、`node --import tsx --test` への置換漏れが無いことを確認した。 |
| 2 | 予約の時刻表現がP002内でエンドポイントごとに不統一 | `docs/P002-frontend-spec.md` 4章冒頭に使い分けの理由(★ACCEPTED★)を追記、`docs/P003-backend-spec.md` 4.6〜4.9.2節に変換ロジックの実装方針を追記した | 解消。使い分け自体は残るが、理由が明記されたため矛盾ではなく意図的な設計として扱える。 |
| 3 | `GET /api/users/directory`の外部契約がP003に記載されP002/P003の役割分担に反していた | `docs/P002-frontend-spec.md` 4.10.1節を新設し外部契約を移設、`docs/P003-backend-spec.md` 4.10節は内部実現のみに縮小、`docs/P004-traceability-matrix.md`・`docs/P005-impl-plan.md`・`docs/P007-impl-direction/U003-*.md`・`docs/P009-acceptance-direction/A004-*.md` の参照箇所をすべてP002 4.10.1節を正とする形に更新した | 解消。`docs/P003-backend-spec.md` 4.10節を外部契約の出典として参照している箇所が無いことを再確認した。 |
| 4 | ヘッダーの「ユーザー管理」リンクの表示範囲がP001画面遷移図と食い違っていた | `docs/P002-frontend-spec.md` 3.0節(共通ヘッダー仕様)を新設し「S06画面表示中のみ表示」と明記、`docs/P007-impl-direction/U005-user-management-and-hardening.md` U005-T4の実装内容・Unit Test内容を修正、`docs/P008-test-direction/T015-header-nav-by-role.md` の実行手順・期待結果をS02とS06を区別する形に修正した | 解消。 |

## 追加レビュー結果

* 上記4件の修正によって新たな矛盾が生じていないかを確認した。`docs/P002-frontend-spec.md` の見出し番号(3.0〜3.7、4.1〜4.11.2)に重複・欠番は無い。`docs/P004-traceability-matrix.md` は全要求ID `OK` のままである(5章まとめ参照、今回の修正はP002/P003内の記載箇所の移動が中心でありP001要求の充足状況自体には影響しない)。
* `docs/P005-impl-plan.md`・`docs/P007-impl-direction.md` の目次は `docs/P006-test-plan.md` の内容と引き続き対応している。
* 図(Mermaid)と本文の食い違いは新たに発見されなかった(`docs/P001-requirement.md` 画面遷移図と `docs/P002-frontend-spec.md` 3.0節の整合性は今回の矛盾点#4の修正により確保された)。
* 新たな矛盾点は検出されなかった。

## 結論(通常フロー、初回納品時点)

* 矛盾点0件。Plan Loop Stepを終了し、Overview Step(P020〜)へ移行する条件を満たす。ただし本タスクの指示範囲(P002〜P010の実行)により、実際のP020以降への移行は本ラウンドでは行わない。

---

## CR-001対応レビュー(P903内側のP010、1回目)

> `docs/P901-cr-direction/CR-001.md`(オンライン会議URL追加)にともない、P903内側でP002〜P009を差分更新した後のレビュー。`SKILL.md` 「停止条件」の規定どおり、このCRについてのP010実行回数は1回目としてカウントする(通算ではなく対象CRごとにリセット)。

### レビュー対象範囲

* CR-001で更新された文書のみ: `docs/P001-requirement.md`、`docs/P002-frontend-spec.md`(3.3/3.4/4.6〜4.9.1/5.2節)、`docs/P003-backend-spec.md`(2.2/3/4.6〜4.9.2節)、`docs/P004-traceability-matrix.md`、`docs/P005-impl-plan.md`、`docs/P006-test-plan.md`、`docs/P007-impl-direction.md`+`U003`/`U004`、`docs/P008-test-direction.md`+`T016`、`docs/P009-acceptance-direction.md`+`A001`。

### 確認結果

1. **用語・命名の一貫性**: 全文書で項目名を「オンライン会議URL」(画面表示・要求文書)/`meeting_url`(API・DB・コード識別子)に統一。表記ゆれ(「会議URL」「Web会議URL」等)は無い。
2. **バリデーションルールの一致**: 「`http://`/`https://` 始まり」「最大500文字」の2ルールと、対応するエラーメッセージ文言が `docs/P001-requirement.md`・`docs/P002-frontend-spec.md` 3.3節・`docs/P003-backend-spec.md` 4.6〜4.9.2節・`docs/P006-test-plan.md`・`docs/P007-impl-direction/U003-*.md`(U003-T7/T8)・`docs/P007-impl-direction/U004-*.md`(U004-T6/T7)のすべてで同一であることを確認した。
3. **除外仕様の一致**: 「`GET /api/reservations`(一覧)には `meeting_url` を含めない」という決定が、P002 4.6節・P003 4.6〜4.9.2節・P004(REQ-API-008行)・P006・P007 U003-T7(実装してはいけないこと)・P008 T016(手順3)のすべてで一貫している。
4. **参照するスキーマ名の一致**: `ReservationCreateRequest`/`ReservationUpdateRequest`/`ReservationDetailResponse` への追加が必要という記述が、P002 4.7/4.9/4.9.1節の記載内容とP007 U003-T7/U004-T6の「作成・編集対象ファイル」で一致している(`ReservationListItemResponse`/`MyReservationListItemResponse` には追加しないことも一致)。
5. **P004の状態確認**: 全要求IDが `OK` を維持しており(4章参照)、`PARTIAL`/`MISSING` は無い。
6. **P007/P008/P009目次とP005/P006内容の対応**: P005 3章(U003/U004の「CR-001対応」節)・P006(2.1/2.2節の「CR-001対応」)に記載された観点が、P007のU003-T7/T8・U004-T6/T7、P008のT016、P009のA001(★CR-001マーク箇所)にすべて反映されていることを確認した。取りこぼしは無い。
7. **マイグレーション回帰の記録一貫性**: `docs/P903-cr-records/CR-001.md`(対処内容節)が記録した `server/tests/test_migration.py` の2件のFAILが、P007 U003-T9として実装タスク化されていることを確認した(記録と実装指示の対応漏れなし)。
8. **図と本文の整合性**: P002 6.2節(予約作成時の重複チェックフロー、Mermaidシーケンス図)にオンライン会議URLは登場しないが、これは同図が「重複チェック」という排他制御の流れのみを示す図であり、他の入力項目(件名・備考等)も同様に描かれていない(図の目的上の対象外)。本文とも矛盾しない。

### 新たに検出した矛盾点

* 0件。

### 結論(CR-001対応)

* 矛盾点0件。CR-001についてPlan Loop Stepを終了し、Overview Step(P020〜)へ移行する条件を満たす。P011・P012(差し戻し)は発生しない。
