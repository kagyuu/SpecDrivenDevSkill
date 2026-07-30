# 解決済み修正障害一覧

> V0.3ルールでの再実行(2026-07-30)。当初(16:00時点)はテスト失敗0件だったため本ファイルは0件の内容で作成していたが、確認観点2・3(「検出した修正課題を全件解決した場合の`ALL_RESOLVED`表記」「OKF目次の`fixed/`付け替え」)を実地検証するため、意図的に1件のバグ(F002)を仕込みフェーズ8の修正サイクルを実際に回した(17:00にFAIL検出→17:30に修正・全件PASS)。以下はその結果を反映した最新の内容。

## 概要

* 修正完了した障害数: 1
* 未解決の障害数: 0
* 全体状態: ALL_RESOLVED(検出された修正課題を全件解決)

## 解決済障害一覧

| 修正タスク | 対応障害 | 結果 | テスト日付 | 修正日付 |
|---|---|---|---|---|
| F002 | T004 | RESOLVED | 2026/07/30 | 2026/07/30 |

## 解決済障害

### F002: 会議室登録時の不正なcapacity(1未満)による500エラー

* 対応するテストID: T004(`test_step6_invalid_room_capacity_400_not_500`)
* 対応するテスト記録: `docs/test-records/20260730-1700-test-record.md`
* 失敗していたテストコマンド: `cd server && python3 -m unittest tests.system.test_t004_error_handling -v`
* 修正内容: `server/app/routers/rooms.py` の `create_room_handler` に `payload.capacity < 1` の場合 `400 VALIDATION_ERROR` を返すチェックを復元した。DBの `CHECK (capacity > 0)` 制約は最終防衛線としてそのまま維持。
* 変更したソースコード: `server/app/routers/rooms.py`
* 更新したdocs: `docs/03-backend-spec.md`(4章「会議室系」)
* 実行したテスト: Unit Test 45件 + スプリント内結合10件 + システムテスト12件(計67件)
* テスト結果: 67件中67件PASS
* 残課題: なし
* 修正経緯: 詳細は `docs/08-fix-plan/fixed/F002-invalid-room-capacity-500.md` を参照。

> 注記: F001(参加者ID実在チェック)はV0.2実行分の記録であり、今回のフェーズ6実装は当該修正を最初から組み込んでいるため今回の解決件数には含めていない(過去の記録は `docs/08-fix-plan/fixed/F001-invalid-participant-id-500.md` に保持)。
