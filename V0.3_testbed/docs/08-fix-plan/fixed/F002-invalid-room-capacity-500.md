あなたは障害修正担当です。以下の1修正タスクを実施してください。

【修正タスクID】F002
【対応する失敗テスト】T004(`server/tests/system/test_t004_error_handling.py::test_step6_invalid_room_capacity_400_not_500`)
【障害記録】`docs/test-records/20260730-1700-test-record.md` の「T004」節を参照。`capacity`が1未満(例: 0)の`POST /api/rooms`リクエストを送ると、`rooms`テーブルへのINSERT時に`sqlite3.IntegrityError: CHECK constraint failed: capacity > 0`が未捕捉のまま送出され、共通500ハンドラ経由で`500 INTERNAL_ERROR`になる。`docs/02-frontend-spec.md` 1章S06「収容人数: 必須。1以上の整数」を満たすには`400 VALIDATION_ERROR`であるべき。
【参照ファイル】`server/app/routers/rooms.py`(`create_room_handler`)、`server/app/repositories/rooms.py`(`create_room`)、`docs/02-frontend-spec.md` 1章S06、`docs/03-backend-spec.md` 4章「会議室系」
【調査方針】`create_room_handler`が`capacity`の下限チェックを行っていないことを確認する(`update_room_handler`側には同等のチェックが残っているかも確認する)。
【修正方針】`create_room_handler`で`payload.capacity < 1`の場合に`400 VALIDATION_ERROR`を返すチェックを復元する。DBレベルのCHECK制約はそのまま維持する(最終防衛線として残す)。
【試行錯誤してよい範囲】`server/app/routers/rooms.py`の`create_room_handler`のみ。他のエンドポイント・DBスキーマは変更しない。
【修正成功時に更新するdocs】`docs/03-backend-spec.md`(4章「会議室系」にcapacity検証をアプリケーション層で明示的に行う旨を明記する。仕様の曖昧さを明確化する変更のため追記する)。
【ロールバック条件】修正後に既存のUnit Test(45件)・スプリント内結合テスト(10件)・T001〜T003,T005,T004の他の手順が1件でもFAILした場合は変更を元に戻す。
【検証コマンド】`cd server && python3 -m unittest discover -s tests -p "test_*.py"`(unittest discoverはtests/system, tests/integration配下も含めて再帰的に発見する)
【完了条件】上記検証コマンドが全てPASSし、かつ`test_step6_invalid_room_capacity_400_not_500`がPASSすること。

重要:
- 作業開始前に現在の変更状態を確認してください(本プロジェクトはGit管理下にあるため、`git status`/`git log -1`で作業開始時点を記録する)。
- 必要な範囲でソースコード変更を試して構いません。
- 修正に成功した場合は、関連する docs/* も必要に応じて更新してください。
- 修正しきれなかった場合は、試行錯誤で変更した未完了のソースコードを元の状態に戻してください。
- 原因が仕様矛盾の場合は、コードで無理に解決せず、人間に判断を促す内容を `docs/08-fix-plan/08-fix-unresolved.md` に記録してください。

完了条件:

- 全モジュールビルド成功
- すべての Unit Test 成功
- すべての結合テスト成功
- 必要なシステムテスト/E2Eテスト成功
- `docs/08-fix-plan/08-fix-resolved.md` に全修正結果が記録されている
- 未解決障害がない、または `docs/08-fix-plan/08-fix-unresolved.md` に未解決なしと明記されている

---

## 修正内容の詳細(対応済み)

* 対応するテストID: T004(`test_step6_invalid_room_capacity_400_not_500`)
* 対応するテスト記録: `docs/test-records/20260730-1700-test-record.md`
* 失敗していたテストコマンド: `cd server && python3 -m unittest tests.system.test_t004_error_handling -v`
* 修正内容: `server/app/routers/rooms.py` の `create_room_handler` に `payload.capacity < 1` の場合 `400 VALIDATION_ERROR` を返すチェックを復元した。DBの `CHECK (capacity > 0)` 制約は最終防衛線としてそのまま維持。
* 変更したソースコード: `server/app/routers/rooms.py`(`create_room_handler` に capacity チェックを追加)
* 更新したdocs: `docs/03-backend-spec.md` 4章「会議室系」(capacity検証をアプリケーション層で明示的に行う旨を明記)
* 実行したテスト: `cd server && python3 -m unittest discover -s tests -p "test_*.py"`(Unit Test 45件、スプリント内結合10件、T001〜T005のシステムテスト12件(T004は6ステップ)、計67件)
* テスト結果: 67件中67件PASS(修正前にFAILしていた1件を含め全件PASS。既存テストの回帰なし)
* 残課題: なし
* 修正経緯: T004手順6実行(2026-07-30 17:00、`docs/test-records/20260730-1700-test-record.md`)でFAILを検出(`sqlite3.IntegrityError: CHECK constraint failed: capacity > 0` が未捕捉のまま500になっていた) → 原因調査(`create_room_handler` にはcapacityの下限チェックがなく、`update_room_handler` 側には同等チェックが残っていることを確認) → `create_room_handler` にチェックを追加 → 全テスト再実行しPASSを確認(`docs/test-records/20260730-1730-test-record.md`) → `docs/03-backend-spec.md` を更新 → 本ファイルを`fixed/`に移動し、`docs/08-fix-plan/F002-invalid-room-capacity-500.md`は削除、`docs/08-fix-plan/08-fix-resolved.md`に概要を記載。

> 注記: このF002は、V0.3の確認観点2・3(修正サイクルが実際に回った場合の`ALL_RESOLVED`表記・OKF目次の`fixed/`付け替え)を実地検証する目的で意図的に仕込んだバグに対する修正である。実運用中に見つかった不具合ではない。詳細は `e2e-validation-report.md` 参照。
