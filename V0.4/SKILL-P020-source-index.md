---
name: source-index-dev
description: 仕様駆動でアプリケーションを開発するときに、ソースツリーの目次(INDEX.md)を作成・修正する。
---

# 実装構造生成/修正

## 目的

* コードベースが既にある場合は、その目次となる `{ソースツリー}/INDEX.md` を作る。無ければ空の目次ファイルを作る。
* 目的は、後続のExecutor・Reviewer LoopがソースコードをすべてReadし直さなくても、ディレクトリ構成と主要ファイルの役割を把握できるようにすることである。

## インプット文書

* 既存のソースツリー(`app/` または `client/` `server/` など、`docs/P005-impl-plan.md` で定めたコード格納先)

## アウトプット文書

* `{ソースツリー}/INDEX.md` (ソースツリーごとに1つ。例: `client/INDEX.md` `server/INDEX.md`、単一アプリなら `app/INDEX.md`)

### アウトプットの記載内容

* INDEX形式(`SKILL.md` の「INDEX形式について」参照)にもとづき、そのソースツリー配下の主要ディレクトリ・主要ファイルを一覧し、各項目に一言概要を添える。
* 記載例:

```markdown
# server/ INDEX

- app/main.py — FastAPIアプリのエントリポイント
- app/routers/ — APIハンドラ層
  - reservations.py — 予約関連API
  - rooms.py — 会議室関連API
- app/repositories/ — データアクセス層
- app/schemas.py — Pydanticスキーマ定義
- tests/ — Unit Test / 結合テスト
```

* コードベースがまだ存在しない場合(P001完了直後など)は、`{ソースツリー}/INDEX.md` を空の目次(見出しと「(実装前)」の注記のみ)として作成する。
* 既に `INDEX.md` がある場合は、現在のソースツリーの実態と差分がないかを確認し、差分があれば更新する。実装されていないのに記載されている項目、実装されているのに記載がない項目の両方を確認する。

### アウトプットを参照する文書

* `docs/ArchitectureHandbook.md` (P021)
* `docs/P101-impl-context.md` (P101、Executorの実装コンテキスト構築)
* `./INDEX.md` (P301、全体INDEX作成)

## 動作

* 共通指示に加えて、上記アウトプット記載内容に定めた事項に従う。
* 本フェーズはExecutor開始前(P101前)とExecutor完了後(P104)の両方で実行される。P104側の詳細は `SKILL-P104-source-index-update.md` を参照。
