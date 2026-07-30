# Build History

| Build ID | Version | Date/Time | Commit | Build Command | Test Command | Result | Notes |
|---|---|---|---|---|---|---|---|
| B001 | 0.1.0 | 2026-07-30 16:00 (V0.3ルール再実行) | b877a93 | `cd server && python3 -c "from app.main import create_app; create_app(':memory:')"` | `cd server && python3 -m unittest discover -s tests -p "test_*.py"` | PASS | フェーズ6完了時点。Unit 45件+スプリント内結合10件、計55件PASS |
| B002 | 0.1.0 | 2026-07-30 16:04 | 96077e3 | 同上 | 同上(system含む) | PASS | フェーズ7完了時点。T001〜T005含め全66件PASS(F001相当の不具合は再現せず) |
| B003 | 0.1.0 | 2026-07-30 16:05 | 2b22a5d | 同上 | 同上 | PASS | フェーズ8完了時点。修正対象0件のためコード変更なし |
| B004 | 0.1.0 | 2026-07-30 16:05 | d675465 | 同上 | 同上 | PASS | フェーズ9成果物整備完了時点 |
| B005 | 0.1.0 | 2026-07-30 17:00 | dcafeff | 同上 | 同上 | **FAIL** | 確認観点2・3検証のため意図的にF002バグ(room capacity検証漏れ)を導入。67件中66件PASS、T004手順6のみFAIL |
| B006 | 0.1.0 | 2026-07-30 17:30 | c713bc9 | 同上 | 同上 | PASS | F002修正完了。67件全PASS。確認観点2(ALL_RESOLVED)・確認観点3(fixed/リンク付け替え)を実地検証済み |

`uv sync` によるビルドは、本検証環境がPyPIへのネットワークアクセスを持たないため未実行(事前インストール済みシステムパッケージで動作確認)。
