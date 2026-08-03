---
name: requirement-update-dev
description: 仕様駆動でアプリケーションを開発するときに、変更要求にもとづきシステム要件定義書を更新する。
---

# 要件定義更新

## 目的

* `docs/CR.md` のうち状態が `未対応`(または `対応中` で優先度の高いもの)のCRにもとづき、`docs/P001-requirement.md` を更新する。
* 更新前の原本は破棄せず、`docs/P001-requirement_{YYYYMMDD}_{CR番号}.md` としてリネームして保持する。

## インプット文書

* `docs/CR.md`
* 更新前の `docs/P001-requirement.md`

## アウトプット文書

* `docs/P001-requirement.md` (更新後)
* `docs/P001-requirement_{YYYYMMDD}_{CR番号}.md` (更新前の原本)

### アウトプットの記載内容

* 更新前の `docs/P001-requirement.md` を `docs/P001-requirement_{YYYYMMDD}_{CR番号}.md` にコピーしてから、`docs/P001-requirement.md` 本体を更新する。`{CR番号}` は今回対応するCRのID(例: `CR-001`)を使う。日付だけでは同じ日に複数件のCRを処理した場合にバックアップファイルが衝突する(2件目の処理で1件目のバックアップを上書きしてしまう)ため、CR番号を必ずファイル名に含める。
* 更新は、対応するCRの内容にもとづく範囲にとどめる。CRと無関係な既存記述は変更しない。
* どのCR-NNNにもとづく変更かを、変更箇所に注記する(例: 「※CR-001により追加」)。
* 対応したCRは、状態を `対応中` に更新する(完了はP904で行う)。

### アウトプットを参照する文書

* `docs/P002-frontend-spec.md` 以降(P903で再実行されるP002〜P302全体)

## 動作

* 共通指示以外は特になし
