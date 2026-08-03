あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F004

## 【対応する失敗テスト】T022, T023

* 複数の失敗テストが単一の根本原因に起因すると判断できるため(`SKILL-P202-fix-plan.md`「例外(複数テスト1根本原因)」)、1件の修正指示ファイルにまとめる。
* T022(`docs/P008-test-direction/T022-room-description-update-and-fetch.md`)・T023(`docs/P008-test-direction/T023-room-description-preserved-on-unrelated-update.md`)はいずれも `PUT /api/rooms/{room_id}` 実行後のレスポンス・DB上の `description` が失われる(常に`None`になる)という同一事象であり、原因調査の結果、同一の根本原因(`room_service.update()` が `room_repository.update()` に `description` を渡し忘れている1箇所)であると特定できた。

## 【障害記録】

* `docs/test-records/20260803-2010-cr002-test-record.md`(T022・T023 FAIL)を参照。
* T022: 説明文なしで登録→PUTで説明文を追加→レスポンス`description`が`None`のまま(期待: 追加した説明文)。
* T023: 説明文つきで登録→PUTでcapacityのみ変更(descriptionは同じ値を再送)→レスポンス`description`が`None`(期待: 変更なしの元の説明文のまま)。

## 【参照ファイル】

* `server/app/services/room_service.py`(`update`関数)
* `server/app/repositories/room_repository.py`(`update`関数、シグネチャは既にdescription引数を持つ。単体テスト`test_update_persists_description_when_passed_explicitly`でRepository層自体は正しいことを確認済み)
* `server/tests/test_api_rooms.py`(`test_update_room_description_then_fetch`、`test_update_room_preserves_description_when_capacity_changes`)

## 【調査方針】

* Repository層(`room_repository.update`)は単体テストでdescriptionを正しく永続化することを確認済みのため、Service層(`room_service.update`)の呼び出し箇所を確認する。
* `room_service.create`はdescriptionをrepositoryへ渡しているが、`update`側で同様の実装になっているか比較する。

## 【修正方針】

* `room_service.update()` の `room_repository.update(...)` 呼び出しに、`data.get("description")` を引数として追加する(`create()`と同様の実装にする)。

## 【試行錯誤してよい範囲】

* `server/app/services/room_service.py` の `update` 関数内のみ。他の関数・他ファイルは変更しない。
* 作業開始前の状態: 本testbedはGit管理下にないため、修正対象ファイル `server/app/services/room_service.py` を `server/app/services/room_service.py.bak-F004` として退避してから着手する。

## 【修正成功時に更新するdocs】

* 該当なし(実装が仕様と異なっていたケースであり、`docs/P002-frontend-spec.md`・`docs/P003-backend-spec.md`はCR-002のP903差分更新時点で既に正しい仕様(descriptionはPUTでも更新対象)を記載済みのため、仕様書側の変更は不要)。
* `docs/P007-impl-direction/U006-cr-002-room-description.md`に、本修正の教訓(Service層のcreate/updateで同じ引数を渡し忘れないこと)を追記するかは任意。今回は`docs/cr-records/CR-002.md`側の対処内容に記録する。

## 【ロールバック条件】

* 3回試行して修正できない場合、`server/app/services/room_service.py.bak-F004` の内容に戻す。

## 【検証コマンド】

* `cd server && python3 -m unittest tests.test_api_rooms.RoomsApiTest.test_update_room_description_then_fetch tests.test_api_rooms.RoomsApiTest.test_update_room_preserves_description_when_capacity_changes -v`
* `cd server && python3 -m unittest discover -s tests -v`(回帰確認)

## 【完了条件】

* T022・T023が共にPASSし、バックエンド単体・結合テスト(134件)に回帰がないこと。

## 重要:

* 作業開始前に現在の変更状態を確認してください。
* 必要な範囲でソースコード変更を試して構いません。
* 修正に成功した場合は、関連する docs/* も必要に応じて更新してください。
* 修正しきれなかった場合は、試行錯誤で変更した未完了のソースコードを元の状態に戻してください。
* 原因が仕様矛盾の場合は、コードで無理に解決せず、人間に判断を促す内容を `docs/P202-fix-plan/P202-fix-unresolved.md` に記録してください。

## 完了条件:

* 全モジュールビルド成功
* すべての Unit Test 成功
* すべての結合テスト成功(P008・P009)
* `docs/P202-fix-plan/P202-fix-resolved.md` に全修正結果が記録されている
* 未解決障害がない、または `docs/P202-fix-plan/P202-fix-unresolved.md` に未解決なしと明記されている

---

## 修正内容の詳細(P203実施結果)

* 対応するテストID: T022, T023
* 対応するテスト記録: `docs/test-records/20260803-2010-cr002-test-record.md`(FAIL検出)、`docs/test-records/20260803-2050-cr002-retest-record.md`(PASS確認)
* 失敗していたテストコマンド: `python3 -m unittest tests.test_api_rooms.RoomsApiTest.test_update_room_description_then_fetch` / `...test_update_room_preserves_description_when_capacity_changes`
* 根本原因: `server/app/services/room_service.py` の `update()` 関数が、`create()` と異なり `room_repository.update(...)` 呼び出しに `data.get("description")` を渡していなかった。そのため `room_repository.update()` は `description` 引数の既定値 `None` を使い、`PUT /api/rooms/{room_id}` を呼ぶたびに(descriptionの変更有無にかかわらず)常に説明文が消去されていた。
* 修正内容: `room_service.update()` の `room_repository.update(...)` 呼び出しに `data.get("description")` を追加した(1行の変更)。
* 変更したソースコード: `server/app/services/room_service.py`
* 更新したdocs: 無し(仕様書側は既に正しい仕様(PUTで説明文も更新対象)を記載済みだったため)。
* 実行したテスト: `python3 -m unittest discover -s tests -v`(134件)、T022・T023の再実行。
* テスト結果: 単体・結合テスト134件全PASS(回帰なし)。T022・T023 PASS。
* 残課題: 無し。
* 修正経緯: 1回目の修正で解決(未解決記録なし)。作業前に `server/app/services/room_service.py.bak-F004` として退避してから着手し、修正確認後に削除した。
