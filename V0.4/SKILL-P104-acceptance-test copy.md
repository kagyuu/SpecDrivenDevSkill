---
name: integration-test-dev
description: 仕様駆動でアプリケーションを開発するときに、スプリント内/モジュール間の結合テストを実行する。
---

# 結合テスト実行

## 目的

* `docs/P008-test-direction.md` の目次にもとづき、未実施(`[ ]`または`[~]`)のテストタスクを実行する。
* 結合テストに失敗しても、この場では修正しない。記録に残すのみとする。

## インプット文書

* `docs/P008-test-direction.md` (目次 OKF形式) および各 `T000-{test-name}.md`
* `docs/P101-impl-context.md`

## アウトプット文書

* `docs/test-records/YYYYMMDD-HHMM-test-record.md`

### 動作内容

* `docs/P008-test-direction/T000-{test-name}.md` に記載された手順どおりにテストを実行する。
* テストの結果(PASS/FAIL/BLOCKED/NOT RUN)を、指定された記録形式で `docs/test-records/YYYYMMDD-HHMM-test-record.md` に残す。
* FAILまたはBLOCKEDになったテストについて、その場でアプリケーションコード・テストコードを修正しない。期待値を変更して成功扱いにしない。
* テストタスクが完了したら(結果にかかわらず記録が残った時点で)、`docs/P008-test-direction.md` の該当行のチェックボックスを `[x]` に更新する。
* 全テストタスクが `[x]` になったら本フェーズを完了とする。結合テストに失敗があってもよい(そのままP104、続けてReviewer Loopに進む)。

### アウトプットを参照する文書

* `docs/P201-review-report.md` (P201、Reviewer Loopの実装横断レビュー)が、本フェーズの実行結果を確認する。

## 動作

* 共通指示に加えて、上記動作内容に従う。
