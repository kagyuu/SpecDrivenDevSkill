---
name: deliver-dev
description: 仕様書・テスト計画・実装指示・テスト記録・修正結果・ソースツリーを確認し、成果物一式をまとめるMarkdownを作成するワークフロー。仕様とテスト仕様とテスト実装が漏れなく対応することを示すトレーサビリティ表、バージョンとビルド履歴、配布・起動資産の整備状況、Docker Compose/CLI/バッチの実行手順を docs/11-deliverable-summary.md にまとめる。ユーザーが「成果物をまとめる」「納品物まとめ」「リリース手順」「配布手順」「仕様とテストの対応表」「Docker Compose で起動できるようにする」「CLI配布形式にする」と依頼した場合、または /deliverable-summary-planner を明示的に呼び出した場合に使う。
---

# 成果物まとめ作成ワークフロー

このSkillは、仕様・実装・テスト・修正結果・配布資産を確認し、成果物一式をまとめるMarkdownを作成する。

目的は、以下を人間がレビューできる形で明確にすることである。

1. 仕様とテスト仕様とテスト実装が漏れなく対応していること
2. ソースツリーにバージョンとビルド履歴が記録されていること
3. 実行モジュールまたは配布物からバージョンを確認できること
4. サービス提供型システムなら Docker Compose で起動できる資産一式が整っていること
5. CLIコマンドまたはバッチ処理なら、実行可能な配布形式になっていること
6. 実行環境で Docker Compose / CLI / バッチを実行できるまでの手順が明確であること

このSkillは、最終成果物の見える化と配布準備を目的とする。必要に応じて設定ファイルやバージョンファイルの作成・更新も行ってよいが、仕様変更や機能追加は行わない。

## 生成する主ファイル

原則として、次のMarkdownを1つ作成または更新する。

```text
docs/11-deliverable-summary.md  成果物まとめ・配布手順・対応表
```

必要に応じて、次の補助ファイルを作成または更新してよい。

```text
VERSION
CHANGELOG.md
BUILD_HISTORY.md
docs/BUILD_HISTORY.md
docs/09-fix-result.md
docs/10-unresolved-tests.md
```

プロジェクトの慣習として既に別ファイルがある場合は、既存ファイルを優先する。

## 入力として確認するファイル

可能な範囲で、以下を確認する。

```text
docs/01-overview.md
docs/02-detailed-spec.md
docs/03-implementation-plan.md
docs/04-test-plan.md
docs/05-implementation-instructions.md
docs/06-test-instractions.md
docs/test-records/*.md
docs/07-test-record.md
docs/08-fix-instructions.md
docs/09-fix-result.md
docs/10-unresolved-tests.md
```

ソースツリーおよび配布資産として、以下も確認する。

```text
package.json
pyproject.toml
setup.py
pom.xml
build.gradle
gradle.properties
Cargo.toml
go.mod
Dockerfile
docker-compose.yml
docker-compose.yaml
compose.yml
compose.yaml
Makefile
README.md
scripts/*
bin/*
cmd/*
src/*
tests/*
```

存在しないファイルがある場合は、存在しないことを記録する。存在しないからといって無理に推測しない。

## 実行前チェック

作業開始時に以下を確認する。

1. `docs/02-detailed-spec.md` が存在するか
2. `docs/04-test-plan.md` が存在するか
3. テスト実装またはテスト記録が存在するか
4. `docs/09-fix-result.md` または `docs/10-unresolved-tests.md` が存在するか
5. ソースツリーからアプリケーション種別を推定できるか
6. `docs/11-deliverable-summary.md` が既に存在するか

判定:

- 仕様書またはテスト計画が不足している場合  
  → 不足ファイルを `docs/11-deliverable-summary.md` の「未整備事項」に記載する。
- テスト記録や修正結果が不足している場合  
  → 最終品質確認が未完了であることを記載する。
- 既に `docs/11-deliverable-summary.md` が存在する場合  
  → 既存内容を読み、必要な差分を追記・更新する。無関係な記述を削除しない。

## アプリケーション種別の判定

ソースツリーと仕様書から、配布・起動方式を判定する。

分類:

1. サービス提供型システム
   - Webアプリケーション
   - APIサーバー
   - バックエンドサービス
   - 常駐プロセス
   - フロントエンド + バックエンド + DB など複数サービス構成
2. CLIコマンド
   - コマンドラインから実行するツール
   - 引数や設定ファイルを受け取り、標準出力またはファイルを生成するもの
3. バッチ処理
   - 定期実行または手動実行の一括処理
   - ジョブ、スクリプト、データ変換、レポート生成など
4. ライブラリ
   - 他システムから利用されるパッケージ
5. 判定不能
   - ソースツリーまたは仕様書から実行形態が判断できない場合

判定不能の場合は、勝手にDocker ComposeやCLI形式を決めず、「未整備事項」に記載する。

## docs/11-deliverable-summary.md の構成

生成するMarkdownは、次の構成にする。

```markdown
# 成果物まとめ

## 1. 概要

## 2. 参照した成果物

## 3. アプリケーション種別と配布方針

## 4. 仕様・テスト・テスト実装の対応表

## 5. バージョン情報とビルド履歴

## 6. 配布資産一覧

## 7. 起動・実行手順

## 8. テスト実行手順

## 9. 最終確認結果

## 10. 未整備事項・人間による確認事項

## 11. リリース判定
```

## 仕様・テスト・テスト実装の対応表

必ず、仕様とテスト仕様とテスト実装が対応することを示す表を作る。

表の基本形:

```markdown
| 仕様ID/項目 | 仕様内容 | 対応するテスト計画 | 対応するテスト指示 | 対応するテスト実装/実行コマンド | 最新結果 | 証跡 | 状態 |
|---|---|---|---|---|---|---|---|
| SPEC-001 | ... | TP-001 | TST001 | `npm run test:integration -- ...` | PASS | docs/test-records/... | OK |
```

仕様IDが既存文書にない場合は、見出しやAPI名・画面名・シナリオ名をもとに一時IDを付ける。

一時IDの例:

```text
SPEC-API-001
SPEC-SCREEN-001
SPEC-FLOW-001
SPEC-NFR-001
```

状態の分類:

```text
OK              仕様・テスト計画・テスト指示・実行結果が対応し、合格している
NO_TEST_PLAN    仕様に対するテスト計画が見つからない
NO_TEST_CASE    テスト計画はあるが具体的テスト指示が見つからない
NO_TEST_IMPL    テスト実装または実行コマンドが見つからない
NOT_RUN         テストが未実行
FAILED          テストが失敗している
BLOCKED         環境不備や仕様不明で実行できない
SPEC_CONFLICT   仕様とテスト期待値が矛盾している
UNKNOWN         対応関係を判断できない
```

### 対応表作成時のルール

- `docs/02-detailed-spec.md` のAPI、画面、データモデル、エラーケース、複雑な処理フローを確認する。
- `docs/04-test-plan.md` のテスト観点とテストレベルを確認する。
- `docs/06-test-instractions.md` のテストタスクIDを確認する。
- `docs/test-records/*.md` と `docs/09-fix-result.md` の実行結果を確認する。
- 対応が見つからない仕様は、必ず対応表に残す。
- 対応が見つからないことを隠さない。
- 仕様からテストを勝手に生成して「対応済み」にしない。

## バージョン情報の整備

ソースツリーにバージョン情報がない場合は、作成または追記する。

優先順位:

1. 既存の言語・フレームワーク標準のバージョン定義を使う
2. 既存の `VERSION` があればそれを使う
3. なければ `VERSION` を作成する
4. 必要に応じて `BUILD_HISTORY.md` または `docs/BUILD_HISTORY.md` を作成する

### 言語別の代表例

Node.js / TypeScript:

```text
package.json の version
```

Python:

```text
pyproject.toml の project.version
または package __version__
```

Java / Maven:

```text
pom.xml の project.version
```

Java / Gradle:

```text
build.gradle または gradle.properties の version
```

Go:

```text
ビルド時の ldflags または version パッケージ
```

Rust:

```text
Cargo.toml の package.version
```

不明な場合:

```text
VERSION
```

## 実行モジュールからバージョンを確認できるようにする

可能であれば、実行モジュールからバージョンを確認できるようにする。

CLIの場合:

```bash
<command> --version
<command> version
```

Web/APIサービスの場合:

```text
GET /health
GET /version
アプリ起動ログ
画面フッターまたは管理画面
```

バッチ処理の場合:

```bash
<batch-command> --version
```

実装済みでない場合は、`docs/11-deliverable-summary.md` の「未整備事項」に記載する。最終仕上げとして軽微な追加で済む場合は、実装してよいが、仕様変更を伴う場合は人間レビュー対象にする。

## ビルド履歴の整備

ソースツリーにビルド履歴がない場合は、次のいずれかを作成する。

```text
BUILD_HISTORY.md
docs/BUILD_HISTORY.md
```

ビルド履歴には、少なくとも以下を記載する。

```markdown
# Build History

| Build ID | Version | Date/Time | Commit | Build Command | Test Command | Result | Notes |
|---|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | PASS/FAIL | ... |
```

日時・コミット・コマンドが取得できない場合は、空欄にせず `未取得` と書く。

## 配布資産の整備方針

### サービス提供型システムの場合

サービス提供型システムの場合は、Docker Compose から起動できるように資産一式を整備する。

確認・整備対象:

```text
Dockerfile
docker-compose.yml または compose.yml
.env.example
README.md または docs/11-deliverable-summary.md の起動手順
必要な初期化スクリプト
DBマイグレーション手順
ヘルスチェック
ログ出力先
永続ボリューム
ネットワーク設定
```

Docker Compose ファイルには、可能な範囲で以下を含める。

- アプリケーションサービス
- フロントエンドサービスがある場合はフロントエンド
- バックエンドサービスがある場合はバックエンド
- DBやキューなど依存ミドルウェア
- 必要な環境変数
- ポート公開
- ボリューム
- healthcheck
- depends_on

ただし、実装言語や構成により適切な内容は異なるため、既存の構成を優先する。

### CLIコマンドの場合

CLIコマンドの場合は、実行可能な配布形式を整備する。

確認・整備対象:

```text
実行コマンド
インストール手順
依存関係の導入手順
設定ファイル例
入力ファイル例
出力ファイル例
--help
--version
配布パッケージ作成手順
```

例:

```bash
npm pack
python -m build
pipx install dist/*.whl
java -jar app.jar --version
go build -o dist/app ./cmd/app
cargo build --release
```

### バッチ処理の場合

バッチ処理の場合は、実行可能な配布形式と運用実行手順を整備する。

確認・整備対象:

```text
実行スクリプト
設定ファイル例
入力データ配置場所
出力データ配置場所
ログ出力先
再実行可否
異常終了時の扱い
スケジューラ登録例
--version または実行ログ上のバージョン表示
```

## 実行環境で実行できるまでの手順

`docs/11-deliverable-summary.md` には、実行環境で実行できるまでの手順を必ず書く。

サービス提供型システムの例:

```markdown
### Docker Compose 起動手順

1. 必要な前提ソフトウェアを確認する
2. `.env.example` を `.env` にコピーする
3. 環境変数を設定する
4. Dockerイメージをビルドする
5. Docker Compose で起動する
6. ヘルスチェックを確認する
7. 初期データまたはマイグレーションを実行する
8. ブラウザまたはAPIで動作確認する
```

CLIの例:

```markdown
### CLI 実行手順

1. 配布物を取得する
2. 依存関係をインストールする
3. バージョンを確認する
4. `--help` を確認する
5. サンプル入力で実行する
6. 出力結果を確認する
```

バッチの例:

```markdown
### バッチ実行手順

1. 配布物を配置する
2. 設定ファイルを配置する
3. 入力データを配置する
4. バージョンを確認する
5. バッチを実行する
6. ログと出力ファイルを確認する
7. 異常終了時の再実行条件を確認する
```

## テスト実行手順

`docs/11-deliverable-summary.md` には、最終確認として以下を記載する。

- Unit Test 実行コマンド
- 結合テスト実行コマンド
- 必要なE2E/システムテスト実行コマンド
- テスト結果の格納先
- 合格条件

全テストが合格していない場合は、リリース判定を `NG` または `保留` にする。

## リリース判定

最後に、リリース可能かどうかを明記する。

判定:

```text
OK       主要成果物が揃い、テスト合格、配布手順あり
保留     軽微な未整備事項があるが、人間判断でリリース可否を決められる
NG       テスト失敗、仕様矛盾、配布不能など重要な未解決事項がある
UNKNOWN  根拠資料不足で判定できない
```

判定の根拠を必ず書く。

## 未整備事項・人間による確認事項

以下がある場合は必ず記載する。

- 対応するテストがない仕様
- 実行結果がないテスト
- 失敗したままのテスト
- 仕様矛盾
- Docker Compose 未整備
- CLI配布形式未整備
- バージョン確認手段がない
- ビルド履歴がない
- 実行手順が未確認
- 本番環境固有の値が未確認

## 作業時の禁止事項

- 仕様上存在しない機能を追加しない
- テスト未実行なのに合格扱いにしない
- 配布資産が未確認なのに整備済みと書かない
- 実行していないコマンドを実行済みと書かない
- バージョンやビルド履歴を推測で捏造しない
- Docker Compose のサービス構成を根拠なく作らない
- 既存のリリース手順を無視して別方式に置き換えない

## 出力後の動作

`docs/11-deliverable-summary.md` を作成または更新したら、そこで停止する。

ユーザーには次を簡潔に報告する。

- 作成・更新したファイル
- アプリケーション種別
- 仕様・テスト・テスト実装対応表の状態
- バージョン情報の整備状況
- ビルド履歴の整備状況
- Docker Compose / CLI / バッチ配布資産の整備状況
- 実行手順の有無
- リリース判定
- 未整備事項の有無

## 品質基準

`docs/11-deliverable-summary.md` は、以下を満たすこと。

- 参照した成果物が列挙されている
- 仕様、テスト計画、テスト指示、テスト実装または実行結果の対応表がある
- 対応漏れが隠されていない
- バージョン情報の所在が明記されている
- ビルド履歴の所在が明記されている
- 実行モジュールからバージョン確認できるかどうかが明記されている
- サービス型なら Docker Compose 起動手順がある
- CLI/バッチなら配布・実行手順がある
- テスト実行手順と合格条件がある
- リリース判定と根拠がある
- 未整備事項と人間確認事項が明記されている
