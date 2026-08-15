# Build History

対象コミット: 作業ツリー(未コミット)。直近のコミット `7d13b77`(リポジトリ `SpecDrivenDevSkill`)からの新規追加分。`V0.9_testbed/` 配下はこのコミットの時点ではリポジトリに含まれていない。

| Build ID | Version | Date/Time | Commit | Build Command | Test Command | Result | Notes |
|---|---|---|---|---|---|---|---|
| BUILD-001 | 1.0.0 | 2026-08-11 (P102完了時) | 未コミット(7d13b77起点) | `cd server && uv sync` / `cd client && npm install && npm run build` | `cd server && uv run python -m pytest tests/ -v` / `cd client && npx vitest run` | PASS | P102(Executor)完了時点。バックエンド94件・フロントエンド20件、全PASS |
| BUILD-002 | 1.0.0 | 2026-08-11 (P205完了時) | 未コミット(7d13b77起点) | 同上 | `cd server && uv run python -m pytest tests/ -v`(104件) / `cd client && npx vitest run`(22件) / `cd client && npx playwright test tests/integration/`(8件) / `cd client && npx playwright test tests/acceptance/`(9件、うちA003/A005/A008/A009はserver側pytestに含まれる) | PASS | P202(F001〜F005)修正後、P205で全18件のT0NN/A0NNを再実行し全PASSを確認 |
| BUILD-003 | 1.0.0 | 2026-08-11 (P302作成時) | 未コミット(7d13b77起点) | `cd server && uv sync` / `cd client && npm install && npm run build` | `cd server && uv run python -m pytest tests/ -v`(104件PASS) / `cd client && npx vitest run`(22件PASS) | PASS | P302(納品物作成)時点の最終確認。`server/Dockerfile`・`client/Dockerfile`・`docker-compose.yml` を新規追加したが、本ビルド環境にDocker CLIが存在しないため、コンテナビルド・起動そのものは未検証(docs/P302-deliver.md §9参照) |
| BUILD-004 | 1.1.0 | 2026-08-11 (CR-001対応、P302再実行時) | 未コミット(7d13b77起点) | `cd server && <venv>/python.exe -m pip` (uv非導入環境のため`.venv`を直接使用) / `cd client && npm install` | `cd server && <venv>/python.exe -m pytest tests/ -v`(121件PASS) / `cd client && npx vitest run`(25件PASS) / `cd client && npx tsc -b`(成功) / `cd client && npx playwright test tests/integration/`(9件PASS) / `cd client && npx playwright test tests/acceptance/`(5件PASS) | **PASS(ただし`npm run build`のみ未検証)** | CR-001(予約への「備考(社内向けメモ)」追加)対応。データモデル変更(`internal_memo`列追加)+API契約変更(後方互換な追加のみ)のため、セマンティックバージョニング方針にもとづきMINORを上げた(1.0.0→1.1.0)。`npm run build`(`vite build`)がこのローカル実行環境(Node.js v24.12.0/Windows)でソース内容によらずネイティブクラッシュする問題を発見したが、切り分けの結果CR-001のコードに起因しないと判断し、`tsc -b`・vitest・Playwright(dev-mode E2E)の全PASSを代替確認とした。詳細は`docs/test-records/20260811-CR001-test-record.md`参照 |

## バージョン付番方針

* 初回リリース(1.0.0)として、`server/pyproject.toml` の `project.version` と `client/package.json` の `version` をいずれも `1.0.0` に統一した(スキャフォールド既定値の `0.1.0`/`0.0.0` から変更)。ルートの `VERSION` ファイルにも同じ値を記録する。
* 今後CR(変更要求)経由での改修が入った場合の版数更新方針は `SKILL-P302-deliver.md`「CR対応後の版数更新方針」(セマンティックバージョニング)に従う。
* **CR-001対応(BUILD-004)**: `docs/P903-cr-records/CR-001.md` のスコープ決定で「API契約変更」「データモデル変更」の両方に分類されたCRであり、規定により少なくともMINORを上げる。実際の変更内容(既存フィールド・既存APIの契約を壊さない、新規の任意項目1つの追加のみ)を踏まえ、MAJORではなくMINORを選択した(1.0.0→1.1.0)。
