# Build History

> 本プロジェクトはGit管理されていない(`git rev-parse --is-inside-work-tree` が失敗する)ため、Commit列は取得できず「未取得」と記載する。「ビルド」はコンパイル成果物を持たない(バックエンドはPythonインタプリタ実行、フロントエンドはビルド不要のプレーンJS)ため、ここでは「テスト実行(単体・結合・受け入れ結合)の節目」をビルドの単位として記録する。

| Build ID | Version | Date/Time | Commit | Build Command | Test Command | Result | Notes |
|---|---|---|---|---|---|---|---|
| B001 | 0.1.0 | 2026-08-03 18:30 | 未取得 | `python3 -m py_compile` 相当(明示ビルド工程なし、インタプリタ実行のため) | `cd server && python3 -m unittest discover -s tests -v`(121件)、`cd client && node --test tests/*.test.mjs`(35件)、`docs/P008-test-direction.md` T001〜T020個別実行(20件) | PASS | Executor(P101〜P104)完了時点。全156単体テスト+20結合テストPASS。 |
| B002 | 0.1.0 | 2026-08-03 19:00 | 未取得 | 同上 | `docs/P009-acceptance-direction.md` A001〜A010(初回実行) | FAIL | P201第1回。セッションCookieの`Secure`属性(F001)・構造化ログ未実装(F002)・A008期待結果の古さ(F003)により10件中10件がPASS以外。詳細: `docs/test-records/20260803-1900-test-record.md`。 |
| B003 | 0.1.0 | 2026-08-03 19:30 | 未取得 | 同上 | 単体テスト121+35件、P008 T001〜T020(20件)、P009 A001〜A010(10件)を全て再実行 | PASS | P203(F001〜F003適用)後のP204・P205。全186件PASS(回帰なし)。詳細: `docs/test-records/20260803-1930-test-record.md`、`docs/P204-impact-analysis.md`。 |
| B004 | 0.1.0 | 2026-08-03 (P302時点) | 未取得 | 同上 | 単体テスト121+35件、`GET /api/health` でのバージョン表示確認 | PASS | P302(納品物作成)でリポジトリルートに `VERSION`(0.1.0)を新設し、`GET /api/health` がこれを読んで返すよう `server/app/main.py` を修正(軽微な追加、`docs/P302-deliver.md` §5参照)。回帰なしを再確認。 |
