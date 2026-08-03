---
name: refactor-execute-dev
description: 仕様駆動でアプリケーションを開発するときに、変更要求にもとづきP002〜P302を再実行する。
---

# 修正実施(Refactor)

## 目的

* P902で更新した `docs/P001-requirement.md` を起点に、Plan Loop Step(P002〜P012)、Overview Step(P020〜P022)、Executor(P101〜P104)、Reviewer Loop(P201〜P205)、Closing(P301〜P302)を通常のフローどおり再実行する。

## インプット文書

* 更新後の `docs/P001-requirement.md`
* `docs/CR.md`
* 既存の `docs/P002-frontend-spec.md` 〜 `docs/P302-deliver.md`、`docs/ArchitectureHandbook.md`、`docs/ADR.md`、各 `INDEX.md`

## アウトプット文書

* 更新された `docs/P002-frontend-spec.md` 〜 `docs/P302-deliver.md` (該当する範囲)
* 更新されたソースコード

### 動作内容

* `SKILL.md` の「ステップ0」と同じ判定ロジックで、P002から順に再実行する。ただし各フェーズは「既存の文書 + P001の更新差分 + `docs/CR.md`」を入力として、差分更新を行う(全面的な書き直しはしない)。
* CRと無関係な既存の仕様・実装・テストは変更しない。
* 各StepのStopping Condition(差し戻し上限)は通常実行時と同じルールに従う。

### アウトプットを参照する文書

* `docs/cr-records/CR-000.md` (P904、対応内容の確認・記録)

## 動作

* 共通指示に加えて、上記動作内容に従う。
