あなたは障害修正担当です。以下の1修正タスクを実施してください。

【修正タスクID】F001
【対応障害】F001 / T004(`server/tests/system/test_t004_error_handling.py::test_reservation_with_nonexistent_participant_returns_validation_error`)
【障害記録】`docs/test-records/20260730-1500-test-record.md` の「T004」節を参照。存在しないユーザーIDを`participant_ids`に含めて`POST /api/reservations`を呼ぶと、`reservation_participants`へのINSERT時に`sqlite3.IntegrityError: FOREIGN KEY constraint failed`が未捕捉のまま送出され、共通500ハンドラ経由で`500 INTERNAL_ERROR`になる。`docs/02-frontend-spec.md` 1章S03「参加者(社員): 有効なユーザーのみ選択可能」を満たすには`400 VALIDATION_ERROR`であるべき。
【参照ファイル】`server/app/repositories/reservations.py`(`create`/`update`)、`server/app/routers/reservations.py`、`server/app/validation.py`、`docs/02-frontend-spec.md` 1章S03、`docs/03-backend-spec.md` 4章「予約系」
【調査方針】`create()`/`update()`が参加者IDの実在チェックを行っていないことを確認する。`validate_reservation_input()`にもチェックがないことを確認する。
【修正方針】予約作成・更新時に、`participant_ids`が全て`users`テーブルに実在し`is_active=1`であることを検証し、そうでなければ`400 VALIDATION_ERROR`を返すようにする。DBレベルのFK制約はそのまま維持する(最終防衛線として残す)。
【試行錯誤してよい範囲】`server/app/repositories/reservations.py`、`server/app/routers/reservations.py`の該当関数のみ。DBスキーマ・他のAPIは変更しない。
【修正成功時に更新するdocs】`docs/03-backend-spec.md`(4章「予約系」に参加者IDの実在チェックを明記する。仕様の曖昧さを明確化する変更のため追記する)。
【ロールバック条件】修正後に既存のUnit Test(42件)・スプリント内結合テスト(4件)・T001〜T003,T005が1件でもFAILした場合は変更を元に戻す。
【検証コマンド】`cd server && python3 -m unittest discover -s tests -p "test_*.py"`(unittest discoverはtests/system, tests/integration配下も含めて再帰的に発見する)
【完了条件】上記検証コマンドが全てPASSし、かつ`test_reservation_with_nonexistent_participant_returns_validation_error`がPASSすること。

重要:
- 作業開始前に現在の変更状態を確認してください(本プロジェクトはGit管理下にあるため、`git status`で作業開始時点を記録する)。
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

* 対応するテストID: T004(`test_reservation_with_nonexistent_participant_returns_validation_error`)
* 対応するテスト記録: `docs/test-records/20260730-1500-test-record.md`
* 失敗していたテストコマンド: `cd server && python3 -m unittest tests.system.test_t004_error_handling -v`
* 修正内容: `server/app/repositories/reservations.py` に `find_missing_participant_ids()` を追加し、予約作成・更新の前段で `participant_ids` の実在・有効性を検証するようにした。存在しない/無効なIDが1件でもあれば `400 VALIDATION_ERROR` を返す。DBの外部キー制約(`PRAGMA foreign_keys = ON`)は最終防衛線としてそのまま維持。
* 変更したソースコード: `server/app/repositories/reservations.py`(`find_missing_participant_ids`追加)、`server/app/routers/reservations.py`(`create_reservation`/`update_reservation`に検証呼び出しを追加)
* 更新したdocs: `docs/03-backend-spec.md` 4章「予約系」(参加者IDの実在チェックを明記)
* 実行したテスト: `cd server && python3 -m unittest discover -s tests -p "test_*.py"`(Unit Test 42件、スプリント内結合4件、T001〜T005のシステムテスト9件、計55件)
* テスト結果: 55件中55件PASS(修正前にFAILしていた1件を含め全件PASS。回帰なし)
* 残課題: なし
* 修正経緯: T004実行(2026-07-30 15:00)でFAILを検出 → 原因調査(`reservation_participants`へのINSERT時の`sqlite3.IntegrityError`を確認) → `find_missing_participant_ids`によるアプリケーション層検証を追加 → 全テスト再実行しPASSを確認 → `docs/03-backend-spec.md`を更新 → 本ファイルを`fixed/`に移動し、`docs/08-fix-plan/F001-invalid-participant-id-500.md`は削除、`docs/08-fix-plan/08-fix-resolved.md`に概要を記載。
