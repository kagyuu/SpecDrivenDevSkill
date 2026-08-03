---
name: deliver-dev
description: 仕様駆動でアプリケーションを開発するときに、納品物まとめ・配布手順指示書を作成する。
---

# 納品物作成

## 目的

* 仕様・実装・テスト・修正結果・配布資産を確認し、成果物一式をまとめる指示書 `docs/P302-deliver.md` を作成する。
* 目的は、以下を人間がレビューできる形で明確にすることである。
  1. 仕様とテスト仕様とテスト実装が漏れなく対応していること
  2. ソースツリーにバージョンとビルド履歴が記録されていること
  3. 実行モジュールまたは配布物からバージョンを確認できること
  4. サービス提供型システムなら Docker Compose で起動できる資産一式が整っていること
  5. CLIコマンドまたはバッチ処理なら、実行可能な配布形式になっていること
  6. 実行環境で Docker Compose / CLI / バッチを実行できるまでの手順が明確であること
* このフェーズは最終成果物の見える化と配布準備を目的とする。必要に応じて設定ファイルやバージョンファイルの作成・更新も行ってよいが、仕様変更や機能追加は行わない。

## インプット文書

* `docs/P001-requirement.md`
* `docs/P002-frontend-spec.md`
* `docs/P003-backend-spec.md`
* `docs/P004-traceability-matrix.md`
* `docs/P005-impl-plan.md`
* `docs/P006-test-plan.md`
* `docs/P007-impl-direction.md` (目次 OKF形式) および `docs/P007-impl-direction/U000-{sprint-name}.md`
* `docs/P008-test-direction.md` (目次 OKF形式) および `docs/P008-test-direction/T000-{test-name}.md`
* `docs/P009-acceptance-direction.md` (目次 OKF形式) および `docs/P009-acceptance-direction/A000-{test-name}.md`
* `docs/test-records/*.md`
* `docs/P202-fix-plan.md` (目次 OKF形式)、`docs/P202-fix-plan/fixed/F000-{fix-name}.md`、`docs/P202-fix-plan/P202-fix-resolved.md`、`docs/P202-fix-plan/P202-fix-unresolved.md`
* `docs/ArchitectureHandbook.md`、`docs/ADR.md`
* `./INDEX.md` および各 `{ソースツリー}/INDEX.md`
* ソースツリーおよび配布資産(`package.json` / `pyproject.toml` / `setup.py` / `pom.xml` / `build.gradle` / `gradle.properties` / `Cargo.toml` / `go.mod` / `Dockerfile` / `docker-compose.yml` / `docker-compose.yaml` / `compose.yml` / `compose.yaml` / `Makefile` / `README.md` / `scripts/*` / `bin/*` / `cmd/*` / `src/*` / `tests/*` など)

存在しないファイルがある場合は、存在しないことを記録する。存在しないからといって無理に推測しない。上流フェーズのドキュメントが不足している場合でも、この SKILL がそれらを新たに書き起こすことはしない(不足として記録するのみ)。

## アウトプット文書

* `docs/P302-deliver.md`

必要に応じて、次の補助ファイルを作成または更新してよい(いずれも任意で、プロジェクトの慣習として既に別ファイルがある場合は既存ファイルを優先する)。

```text
VERSION
CHANGELOG.md
BUILD_HISTORY.md
docs/BUILD_HISTORY.md
```

### アウトプットの記載内容

`docs/P302-deliver.md` は次の構成にする。

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

既に `docs/P302-deliver.md` が存在する場合は、既存内容を読み、必要な差分を追記・更新する。無関係な記述を削除しない。

#### 実行前チェック

作業開始時に以下を確認する。

1. `docs/P002-frontend-spec.md` と `docs/P003-backend-spec.md` が存在するか
2. `docs/P006-test-plan.md` が存在するか
3. `docs/test-records/*.md` (テスト実装またはテスト記録) が存在するか
4. `docs/P202-fix-plan/P202-fix-resolved.md` または `docs/P202-fix-plan/P202-fix-unresolved.md` が存在するか
5. ソースツリーからアプリケーション種別を推定できるか
6. `docs/P302-deliver.md` が既に存在するか

判定:

* 仕様書またはテスト計画が不足している場合 → 不足ファイルを「10. 未整備事項」に記載する。
* テスト記録や修正結果が不足している場合 → 最終品質確認が未完了であることを記載する。

#### アプリケーション種別の判定

ソースツリーと仕様書から、配布・起動方式を判定する。

分類:

1. サービス提供型システム(Webアプリケーション、APIサーバー、バックエンドサービス、常駐プロセス、フロントエンド+バックエンド+DBなど複数サービス構成)
2. CLIコマンド(コマンドラインから実行するツール。引数や設定ファイルを受け取り、標準出力またはファイルを生成するもの)
3. バッチ処理(定期実行または手動実行の一括処理。ジョブ、スクリプト、データ変換、レポート生成など)
4. ライブラリ(他システムから利用されるパッケージ)
5. 判定不能(ソースツリーまたは仕様書から実行形態が判断できない場合)

判定不能の場合は、勝手にDocker ComposeやCLI形式を決めず、「10. 未整備事項」に記載する。

#### 仕様・テスト・テスト実装の対応表(4章)

必ず、仕様とテスト仕様とテスト実装が対応することを示す表を作る。

表の基本形:

```markdown
| 仕様ID/項目 | 仕様内容 | 対応するテスト計画 | 対応するテスト指示 | 対応するテスト実装/実行コマンド | 最新結果 | 証跡 | 状態 |
|---|---|---|---|---|---|---|---|
| SPEC-001 | ... | docs/P006-test-plan.md | docs/P009-acceptance-direction/A001-... | `npm run test:integration -- ...` | PASS | docs/test-records/... | OK |
```

仕様IDが既存文書にない場合は、見出しやAPI名・画面名・シナリオ名をもとに一時IDを付ける(例: `SPEC-API-001` `SPEC-SCREEN-001` `SPEC-FLOW-001` `SPEC-NFR-001`)。`docs/P004-traceability-matrix.md` で既に要求IDが振られている場合はそれを使う。

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

対応表作成時のルール:

* `docs/P002-frontend-spec.md` `docs/P003-backend-spec.md` のAPI、画面、データモデル、エラーケース、複雑な処理フローを確認する。
* `docs/P006-test-plan.md` のテスト観点とテストレベルを確認する。
* `docs/P008-test-direction.md` / `docs/P009-acceptance-direction.md` (目次) および各タスクファイルのテストタスクIDを確認する。
* `docs/test-records/*.md` と `docs/P202-fix-plan/P202-fix-resolved.md` / `docs/P202-fix-plan/P202-fix-unresolved.md` の実行結果を確認する。
* 対応が見つからない仕様は、必ず対応表に残す。対応が見つからないことを隠さない。
* 仕様からテストを勝手に生成して「対応済み」にしない。

#### バージョン情報の整備(5章)

ソースツリーにバージョン情報がない場合は、作成または追記する。

優先順位: (1) 既存の言語・フレームワーク標準のバージョン定義を使う (2) 既存の `VERSION` があればそれを使う (3) なければ `VERSION` を作成する (4) 必要に応じて `BUILD_HISTORY.md` または `docs/BUILD_HISTORY.md` を作成する。

言語別の代表例:

```text
Node.js / TypeScript : package.json の version
Python               : pyproject.toml の project.version、または package __version__
Java / Maven         : pom.xml の project.version
Java / Gradle        : build.gradle または gradle.properties の version
Go                   : ビルド時の ldflags または version パッケージ
Rust                 : Cargo.toml の package.version
不明な場合           : VERSION
```

可能であれば、実行モジュールからもバージョンを確認できるようにする。

```text
CLIの場合          : <command> --version / <command> version
Web/APIサービス    : GET /health, GET /version, アプリ起動ログ, 画面フッターまたは管理画面
バッチ処理         : <batch-command> --version
```

実装済みでない場合は、「10. 未整備事項」に記載する。最終仕上げとして軽微な追加で済む場合は実装してよいが、仕様変更を伴う場合は「10. 未整備事項」に記載し、CRの起票候補とする(このフェーズでは仕様変更を行わない)。

ビルド履歴がない場合は `BUILD_HISTORY.md` または `docs/BUILD_HISTORY.md` を作成し、少なくとも以下を記載する。

```markdown
# Build History

| Build ID | Version | Date/Time | Commit | Build Command | Test Command | Result | Notes |
|---|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | PASS/FAIL | ... |
```

日時・コミット・コマンドが取得できない場合は、空欄にせず `未取得` と書く。

#### 配布資産の整備方針(6章)

サービス提供型システムの場合は、Docker Compose から起動できるように資産一式を整備する。

確認・整備対象: `Dockerfile` / `docker-compose.yml` または `compose.yml` / `.env.example` / `README.md` または `docs/P302-deliver.md` の起動手順 / 必要な初期化スクリプト / DBマイグレーション手順 / ヘルスチェック / ログ出力先 / 永続ボリューム / ネットワーク設定。

Docker Compose ファイルには、可能な範囲でアプリケーションサービス、フロントエンド/バックエンドサービス、DBやキューなど依存ミドルウェア、必要な環境変数、ポート公開、ボリューム、healthcheck、depends_on を含める。ただし、実装言語や構成により適切な内容は異なるため、既存の構成を優先する。

CLIコマンドの場合は、実行可能な配布形式を整備する。確認・整備対象: 実行コマンド / インストール手順 / 依存関係の導入手順 / 設定ファイル例 / 入力ファイル例 / 出力ファイル例 / `--help` / `--version` / 配布パッケージ作成手順(例: `npm pack` / `python -m build` / `pipx install dist/*.whl` / `java -jar app.jar --version` / `go build -o dist/app ./cmd/app` / `cargo build --release`)。

バッチ処理の場合は、実行可能な配布形式と運用実行手順を整備する。確認・整備対象: 実行スクリプト / 設定ファイル例 / 入力データ配置場所 / 出力データ配置場所 / ログ出力先 / 再実行可否 / 異常終了時の扱い / スケジューラ登録例 / `--version` または実行ログ上のバージョン表示。

#### 実行環境で実行できるまでの手順(7章)

`docs/P302-deliver.md` には、実行環境で実行できるまでの手順を必ず書く。

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

#### テスト実行手順(8章)

`docs/P302-deliver.md` には、最終確認として以下を記載する: Unit Test 実行コマンド / 結合テスト実行コマンド / 必要なE2E・システムテスト実行コマンド / テスト結果の格納先 / 合格条件。

全テストが合格していない場合は、リリース判定を `NG` または `保留` にする。

#### リリース判定(11章)

判定は次のいずれかとし、根拠を必ず書く。

```text
OK       主要成果物が揃い、テスト合格、配布手順あり
保留     軽微な未整備事項があるが、人間判断でリリース可否を決められる
NG       テスト失敗、仕様矛盾、配布不能など重要な未解決事項がある
UNKNOWN  根拠資料不足で判定できない
```

#### 未整備事項・人間による確認事項(10章)

以下がある場合は必ず記載する: 対応するテストがない仕様 / 実行結果がないテスト / 失敗したままのテスト(`docs/P202-fix-plan/P202-fix-unresolved.md` に記録が残っているもの) / 仕様矛盾 / Docker Compose 未整備 / CLI配布形式未整備 / バージョン確認手段がない / ビルド履歴がない / 実行手順が未確認 / 本番環境固有の値が未確認。

未整備事項のうち、仕様変更を要するものは、そのままCR(`docs/CR.md`)の起票候補として明記する。

#### 作業時の禁止事項

* 仕様上存在しない機能を追加しない
* テスト未実行なのに合格扱いにしない
* 配布資産が未確認なのに整備済みと書かない
* 実行していないコマンドを実行済みと書かない
* バージョンやビルド履歴を推測で捏造しない
* Docker Compose のサービス構成を根拠なく作らない
* 既存のリリース手順を無視して別方式に置き換えない

### アウトプットを参照する文書

`docs/P302-deliver.md` はワークフローの最終フェーズの成果物であり、後続フェーズはない(通常のフローでは)。人間がリリース判断を行うための最終資料として参照する。改善要望が出た場合は、Refactor(P901〜)の起点として `docs/CR.md` に反映される。

## 動作

* 共通指示に加えて、上記アウトプット記載内容(実行前チェック〜作業時の禁止事項)に従う。
* `docs/P302-deliver.md` を作成または更新したら、そこで停止する。ユーザーには、作成・更新したファイル、アプリケーション種別、対応表の状態、バージョン/ビルド履歴の整備状況、配布資産の整備状況、実行手順の有無、リリース判定、未整備事項の有無を簡潔に報告する。
* 品質基準: 参照した成果物が列挙されている / 仕様・テスト計画・テスト指示・テスト実装または実行結果の対応表がある / 対応漏れが隠されていない / バージョン情報とビルド履歴の所在が明記されている / 実行モジュールからバージョン確認できるかどうかが明記されている / サービス型ならDocker Compose起動手順がある / CLI・バッチなら配布・実行手順がある / テスト実行手順と合格条件がある / リリース判定と根拠がある / 未整備事項と人間確認事項が明記されている。
