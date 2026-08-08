# Build History

> 本ファイルは `spec-driven-dev` Skill フェーズP302(納品物作成)で作成した。
> `Commit` 列は、本リポジトリがGit管理下にないため(`git status` → `fatal: not a git repository`)すべて `未取得` である。
> **記載しているのは実際に実行したコマンドと実測結果のみである。**未実行のものは `未実行` と明記する。

| Build ID | Version | Date/Time | Commit | Build Command | Test Command | Result | Notes |
|---|---|---|---|---|---|---|---|
| B-0001 | 1.0.0 | 2026-08-05T11:52Z | 未取得 | `cd server && python3 -m compileall -q src` | `cd server && python3 -m unittest discover -s tests -t .` / `cd client && node --test 'tests/*.js'` / 結合T001〜T010 | PASS | P103 第1回(結合テストT001〜T010)。記録: `docs/test-records/20260805-1152-test-record.md` |
| B-0002 | 1.0.0 | 2026-08-05T12:26Z | 未取得 | 同上 | 結合T011〜T018 + T001〜T010の退行確認 | FAIL | T016 手順7 のみFAIL(期待値の誤り)。記録: `docs/test-records/20260805-1226-test-record.md` |
| B-0003 | 1.0.0 | 2026-08-05T16:03Z | 未取得 | `cd server && python3 -m compileall -q src` / `cd client && node --check <src配下の全ESモジュール>` | 受け入れ結合 A001〜A012 | FAIL | P201 第1回。A001 手順5 FAIL(期待値の誤り)。記録: `docs/test-records/20260805-1603-test-record.md` |
| B-0004 | 1.0.0 | 2026-08-05T16:20Z | 未取得 | 同上 | T016 / A001 の再実行 + 全レベル再実行 | PASS | P205。F001 / F002 の修正反映後、T001〜T018・A001〜A012 の全30件PASS。記録: `docs/test-records/20260805-1620-test-record.md` |
| B-0005 | 1.0.0 | 2026-08-05T16:33Z | 未取得 | `cd server && python3 -m compileall -q src`(終了コード0)/ `cd client && node --check` × src配下16ファイル(すべて終了コード0) | `cd server && python3 -m unittest discover -s tests -t .` → **Ran 240 / OK** / `cd client && node --test 'tests/*.js'` → **126 pass / 0 fail** / `node --test 'tests/integration/*.js'` → **41 pass / 0 fail** / `node --test 'tests/acceptance/test_*.js'` → **31 pass / 0 fail** | PASS | **P302 での最終確認(本フェーズが実際に実行した)。** 合計438件すべて合格 |
| B-0006 | 1.0.0 | 2026-08-05T16:31Z | 未取得 | (ビルドなし。実プロセス起動確認) | 同一DBファイルに対する `python3 -m uvicorn meeting_room.main:app` の**3回連続の起動・停止**。各回 `GET /` = 200、`GET /src/main.js` = 200、`POST /api/auth/login` = 200。`schema_migrations` は3行のまま増えず、`users` は1行のまま | PASS | **P302 実行前チェック#8(再起動時の起動可否・初期化処理の冪等性)。** 詳細は `docs/P302-deliver.md` 9章 |
| B-0007 | 1.1.0 | 2026-08-05T17:26Z | 未取得 | `cd server && python3 -m compileall -q src`(終了コード0)/ `cd client && node --check` × src配下の全ファイル(すべて終了コード0) | `cd server && python3 -m unittest discover -s tests -t .` → **Ran 262 / OK** / `cd client && node --test 'tests/*.js'` → **146 pass / 0 fail** / `node --test 'tests/integration/*.js'` → **46 pass / 0 fail** / `node --test 'tests/acceptance/test_*.js'` → **32 pass / 0 fail** | PASS | **※CR-001(予約のオンライン会議URL)対応後の全件確認(P201第3回 / P302)。** 合計486件すべて合格。マイグレーション `004-meeting-url.sql` を追加 |
| B-0008 | 1.1.0 | 2026-08-05T17:22Z | 未取得 | (ビルドなし。実プロセス起動確認) | 同一DBファイルに対する `python3 -m uvicorn meeting_room.main:app` の**3回連続の起動・停止**(`004-meeting-url.sql` 追加後)。各回 `GET /` = 200。`schema_migrations` は**4行**のまま増えず、`users` は1行のまま。`duplicate column name` なし。あわせて `apply_migrations()` の2回連続実行(1回目4件 / 2回目0件)も確認 | PASS | **※CR-001 のデータモデル変更に対する冪等性確認**(`SKILL-P903-refactor-execute.md`「データモデル変更」の必須手順)。詳細は `docs/test-records/20260805-1723-test-record.md` |
| (docker) | 1.1.0 | - | 未取得 | `docker compose build` | `docker compose up -d` + ヘルスチェック確認 | **未実行** | 検証環境にDockerデーモンが無い(`docker info` → `failed to connect to the docker API at unix:///var/run/docker.sock`)。資産は整備済みだが**ビルド・起動の実機確認はできていない**(`docs/P302-deliver.md` 9章・11章)。デーモン不要の `docker compose config` による構文・変数展開の検証のみ2026-08-05T16:41Zに実施し成功している |

## バージョンの決め方

* 配布単位のバージョンはリポジトリ直下の [`VERSION`](./VERSION)(現在 `1.1.0`。※CR-001 の機能追加で 1.0.0 → 1.1.0)を正とする。
* `client/package.json` の `version` は `1.1.0` で `VERSION` と一致している。
* `server/pyproject.toml` の `version` は `0.1.0` のままであり **`VERSION` と一致していない**。バージョン付けの方針(単一バージョンに揃えるか、コンポーネント別に持つか)は人間の確認事項として `docs/P302-deliver.md` 10章に記載した。

## 次回ビルド時の記入ルール

* 1行 = 1ビルド。`Build ID` は `B-NNNN` の連番とする。
* `Build Command` / `Test Command` は**実際に実行したコマンドをそのまま**書く。実行していないものは `未実行` と書く。
* `Date/Time` はUTC。`Commit` はGit管理下に入れたあとはコミットハッシュを記入する。
