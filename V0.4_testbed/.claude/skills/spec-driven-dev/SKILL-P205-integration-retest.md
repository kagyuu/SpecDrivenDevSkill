---
name: integration-retest-dev
description: 仕様駆動でアプリケーションを開発するときに、結合テストを再実施する。
---

# 結合テスト再実施

## 目的

* P203の修正後、`docs/P008-test-direction.md` と `docs/P009-acceptance-direction.md` のうち、これまで失敗していたテスト、および P204 で影響が疑われたテストを再実行する。
* 再実行結果をもとに、P201(実装横断レビュー)の判定に戻る。

## インプット文書

* `docs/P008-test-direction.md` / `docs/P009-acceptance-direction.md`
* `docs/P202-fix-plan/fixed/F000-{fix-name}.md`
* `docs/P204-impact-analysis.md`

## アウトプット文書

* `docs/test-records/YYYYMMDD-HHMM-test-record.md` (追記)

### 動作内容

* P103・P201と同じテスト実行ルール(修正禁止・期待値改ざん禁止・記録必須)に従う。
* 再実行の対象は、直近のテスト記録でFAIL/BLOCKEDだったテスト、および `docs/P204-impact-analysis.md` で影響が疑われたテストとする。全件を無条件に再実行する必要はない。
* 再実行結果を記録したら、P201(実装横断レビュー)を再実行し、全件PASSかどうかを再判定する。
* 全件PASSでなければ、再度P202(修正計画)に差し戻す。Reviewer Loopの停止条件(3回差し戻しても全件PASSにならない)に該当した場合は、処理を停止して人間に報告する。

## 動作

* 共通指示に加えて、上記動作内容に従う。
