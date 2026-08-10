# Build History

P302 (docs/P302-deliver.md 5章)。バージョンの一次情報は `server/pyproject.toml`
の `[project].version` と `client/package.json` の `version`(現在いずれも
`0.1.0`、一致)。本ファイルはそれに対するビルド・テスト実行履歴を記録する。

コミットハッシュ列: このリポジトリ(`V0.8_testbed/`)は本ドキュメント作成時点で
一度も `git commit` されておらず(`git status` で全ファイルが未追跡)、各ビルド
時点のコミットは存在しない。空欄にせず「未コミット(作業ツリー)」と明記する。

| Build ID | Version | Date/Time | Commit | Build Command | Test Command | Result | Notes |
|---|---|---|---|---|---|---|---|
| B1 | 0.1.0 | 2026-08-09 15:00 (JST) | 未コミット(作業ツリー) | `cd client && npm install && npm run build` / `cd server && python -m pip install -e .` | `cd server && python -m pytest`(結合込み) / `cd client && node --import tsx --test tests/integration/*.test.tsx`(当時未整備分は新規作成しつつ実行) | **FAIL** | P103結合テスト初回実行。T006(カレンダーのタイムゾーン計算)・T009等がFAIL。詳細: `docs/test-records/20260809-1500-test-record.md` |
| B2 | 0.1.0 | 2026-08-09 19:00 (JST) | 未コミット(作業ツリー) | (B1と同じソース、追加テストファイルのみ新規作成) | `cd server && python -m pytest tests/acceptance` / `cd client && node --import tsx --test tests/acceptance/*.test.tsx` | **FAIL** | P201(第1回)受け入れテスト初回実行。A001/A003/A004/A006/A010がFAIL/BLOCKED。B1と同じ2根本原因(F001 sqlite3スレッド問題、F002 日付のタイムゾーン計算)に収束。詳細: `docs/test-records/20260809-1900-test-record.md`、`docs/P202-fix-plan.md` |
| B3 | 0.1.0 | 2026-08-09 21:00 (JST) | 未コミット(作業ツリー) | (P203でF001〜F004を修正後、再ビルド不要 - Pythonは実行時import、フロントは同一`vite`設定) | B1・B2でFAILした全11件 + P204で影響ありと判定した既存PASS分を再実行 | **PASS** | P205再実行。全件PASS(一部は3〜4回連続実行で非決定性がないことを確認)。詳細: `docs/test-records/20260809-2100-test-record.md` |
| B4 | 0.1.0 | 2026-08-09 (P302実行時, 本ドキュメント作成時点) | 未コミット(作業ツリー) | `cd client && npm run build`(実行・確認済み、警告なし) / `cd server && pip install -e .` | `cd server && python -m unittest` は未使用(pytestベースのプロジェクトのため下記を使用) — `cd server && python -m pytest tests/ -v`(全128件) / `cd client && node --import tsx --test 'tests/*.test.tsx'`(38件) / `cd client && node --import tsx --test 'tests/integration/*.test.tsx'`(16件) / `cd client && node --import tsx --test 'tests/acceptance/*.test.tsx'`(12件) | **PASS**(194/194) | P302納品確認のための最終フルテスト実行(本フェーズで実際に実行し、以下の内訳を確認: server unit 117 / server integration 4 / server acceptance 7 / client unit 38 / client integration 16 / client acceptance 12 = 194)。このビルドで `GET /version`(`server/app/main.py`)を追加し、`server/tests/test_version.py` を新規作成(128件のうち1件)。Docker配布資産(`server/Dockerfile`, `client/Dockerfile`, `client/nginx.conf`, `docker-compose.yml`)も新規作成したが、本サンドボックスにDocker CLI/デーモンが存在しないため、Dockerビルド・起動そのものは未検証(下記参照)。詳細: `docs/P302-deliver.md` 9章 |
| B5 | 0.1.0 | 2026-08-09 (CR-001対応、P903内側のP302再実行) | 未コミット(作業ツリー) | `cd client && npm run build`(実行・確認済み、警告なし) | `cd server && python -m pytest tests/ -q`(全153件) / `cd client && node --import tsx --test 'tests/*.test.tsx'`(46件) / `cd client && node --import tsx --test 'tests/integration/*.test.tsx'`(17件) / `cd client && node --import tsx --test 'tests/acceptance/*.test.tsx'`(12件) | **PASS**(228/228) | CR-001(`docs/P901-cr-direction/CR-001.md`、予約へのオンライン会議URL追加)適用後の最終フルテスト実行。B4からの差分: server +25件(`test_reservation_repository.py`+5、`test_reservation_service.py`+11、`test_reservations_api.py`+9。`test_migration.py`は既存2件の期待値更新のみでテスト数の純増は無い。128→153、内訳は`docs/test-records/20260809-2200-test-record.md`参照)、client unit +8件(ReservationCreatePage 3件・ReservationDetailPage 5件)、client integration +1件(T016)、client acceptance ±0件(A001は既存1件を改訂・再実行、新規追加ではない)。Docker配布資産は変更していないため検証状況(未検証)に変化なし。詳細: `docs/P302-deliver.md` 9章「CR-001対応後の最終確認結果」 |

## Docker ビルド検証について

`docker --version` / `docker info` / `docker compose version` はいずれも
`command not found`(exit 127)で、本サンドボックスにDocker自体がインストール
されていない(デーモン未起動ではなくCLIバイナリが存在しない)。そのため、上記
B4を含め、`server/Dockerfile` / `client/Dockerfile` / `docker-compose.yml` の
実際の `docker compose build` / `docker compose up` は一度も実行できておらず、
「ビルド成功」を記録した行は存在しない。整備状況は
`docs/P302-deliver.md` 9章・10章・11章を参照。
