# 修正計画書(目次) — 会議室予約システム

> 本書は `spec-driven-dev` Skill フェーズ8の成果物です(V0.3ルールで再生成)。OKF形式(`SKILL.md`参照)の目次です。
> インプット: `docs/07-test-direction.md`、`docs/test-records/20260730-1730-test-record.md`(最新)

## 概要

`docs/test-records/20260730-1600-test-record.md` を確認した時点では、T001〜T005のいずれにも失敗(FAIL/BLOCKED)は1件もなかった(Unit Test 45件・スプリント内結合10件・スプリント横断結合/システムテスト11件、計66件すべてPASS)。

その後、V0.3の確認観点2・3(修正サイクルが実際に回る場合の`ALL_RESOLVED`表記・OKF目次の`fixed/`付け替え)を実地検証する目的で、意図的に1件のバグ(`POST /api/rooms`のcapacity検証漏れによる500エラー)を仕込み、T004手順6として追加した(`docs/07-test-direction/T004-error-handling.md`補足参照)。`docs/test-records/20260730-1700-test-record.md`で1件のFAILを検出したため、`SKILL-08-fix-plan.md`の規定に従い修正指示ファイル `docs/08-fix-plan/F002-invalid-room-capacity-500.md` を作成し、修正・全件PASSの再テスト(`docs/test-records/20260730-1730-test-record.md`)まで完了した。

## 修正タスク一覧(OKF形式)

- [x] F002 [会議室登録時の不正なcapacity(1未満)による500エラー](./08-fix-plan/fixed/F002-invalid-room-capacity-500.md) — T004手順6で検出(確認観点2・3検証のため意図的に仕込んだバグ)。capacity下限チェックを復元し400に修正済み(解決済み)。

修正完了に伴い、`docs/08-fix-plan/F002-invalid-room-capacity-500.md`(未対応版)は削除し、`docs/08-fix-plan/fixed/F002-invalid-room-capacity-500.md` に詳細付きで移動済み。概要は `docs/08-fix-plan/08-fix-resolved.md` を参照。未解決障害はない(`docs/08-fix-plan/08-fix-unresolved.md`参照)。

## フェーズ9への引き渡し

未解決の修正課題は0件(検出1件・全件解決)のため、フェーズ8を完了とみなし、続けてフェーズ9(`docs/09-deliver.md`)に進む。詳細は `docs/08-fix-plan/08-fix-unresolved.md`(0件・ALL_RESOLVED)、`docs/08-fix-plan/08-fix-resolved.md`(F002を1件解決・ALL_RESOLVED)を参照。
