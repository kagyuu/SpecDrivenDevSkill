# 実装コンテキスト(Executor向け要約)

> 本書は `spec-driven-dev` Skill フェーズP101の成果物。Executorは、詳細仕様(`docs/P002-frontend-spec.md` 等)を最初からすべて読む代わりに、まずこの文書と、着手対象の `docs/P007-impl-direction/U00N-*.md` だけを読めば着手できる。本書は未完了スプリントが残る限り、Executor Step開始のたびに同一文書として更新する(今回は初回作成)。

## 1. 現在のソースツリーの状態

* `client/INDEX.md`・`server/INDEX.md` はいずれも「(実装前)」のプレースホルダ(P020時点)。ディレクトリ自体は作成済みだが、コードは0行。
* これから `uv init` 相当(`server/pyproject.toml` 新規作成)・`npm create vite` 相当(`client/package.json` 新規作成)による初期化を、U001-T1・U001-T5でそれぞれ行う。

## 2. 遵守すべき技術的決定(`docs/ADR.md` より転記)

| ADR | タイトル | 状態 |
| --- | --- | --- |
| ADR-001 | フロントエンド技術としてReact + TypeScript + Viteを採用 | 採用 |
| ADR-002 | バックエンド技術としてFastAPIを採用 | 採用 |
| ADR-003 | データアクセスに標準ライブラリsqlite3を直接使用(ORM不使用) | 採用 |
| ADR-004 | パスワードハッシュにbcryptを採用 | 採用 |
| ADR-005 | セッション管理をSQLite永続化+Cookie方式で実装(JWT不採用) | 採用 |

* 特に注意: ADR-003によりSQLAlchemy等のORMは使わない。ADR-005によりセッションは `sessions` テーブルに永続化し、JWTは使わない。
* Repository層は現在時刻・現在日付を内部で取得しない(呼び出し元がすべて明示的な引数として渡す。`docs/P003-backend-spec.md` §6、`docs/ArchitectureHandbook.md` §5)。

## 3. これから着手するスプリント

`docs/P007-impl-direction.md` の目次で次に `[ ]` になっている先頭のスプリントは **U001-foundation-and-auth**。

実行順序(`docs/P005-impl-plan.md` §2):

1. U001-foundation-and-auth(未着手)
2. U002-reservation-core(未着手)
3. U003-reservation-management-and-rooms(未着手)
4. U004-user-administration(未着手)

## 4. Executorが迷ったときに参照すべき詳細仕様の場所

| 疑問の種類 | 参照先 |
| --- | --- |
| 画面の入力項目・バリデーション・エラーメッセージ文言 | `docs/P002-frontend-spec.md` §3(画面ごと) |
| APIの外部契約(ステータスコード・エラーコード) | `docs/P002-frontend-spec.md` §9 |
| APIの内部実現・バリデーション順序・重複判定ロジック | `docs/P003-backend-spec.md` §5 |
| テーブル定義 | `docs/P003-backend-spec.md` §3.2 |
| マイグレーション方式 | `docs/P003-backend-spec.md` §4 |
| ディレクトリ構成・技術スタック全体像 | `docs/ArchitectureHandbook.md` |
| 個別タスクの詳細(作成対象ファイル・実装内容・完了条件) | `docs/P007-impl-direction/U00N-*.md` の該当タスク |

## 5. 結合テストとの命名対応について

`docs/P008-test-direction/T0NN-*.md` はU001〜U004完了後にP103でまとめて実行される。P102時点では、対応するT0NNファイルに具体的なテスト関数名・ファイルパスの明記は無い(Playwright仕様書ベースのシナリオ記述のみ)ため、`SKILL-P102-implement.md` の「命名を厳密一致させる」規則は本スプリント群では強制対象外(該当P008テストに具体的な関数名記載が無いケース)。P102側では通常のPythonファイル・関数命名規則(`tests/{layer}/test_{module}.py::test_{case}`)に従う。

## 6. 未解決事項の扱い

* `docs/P007-impl-direction.md` の「未解決事項」欄には現時点で記載なし。実装中に不足・矛盾を見つけた場合はここに追記し、実装を進めない。
