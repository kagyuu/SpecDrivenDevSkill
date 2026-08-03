あなたはExecutor(実装担当)です。このスプリント(U006: cr-002-room-description)には2個のタスク(U006-1・U006-2)があります。このタスクを実施したら、Executor Stepの停止条件に該当しない限り自動的に次のタスクへ進んでください。

前提: U001〜U005(既存)が完了していること。
本スプリントは通常の新規スプリントではなく、変更要求 `docs/CR.md` CR-002(反映後は `docs/cr-records/CR-002.md`)に対応する差分実装である。既存のS06実装・テストのうちCR-002と無関係な部分は変更しないこと。
参照する仕様書: `docs/P001-requirement.md`「S06 会議室管理画面」(※CR-002により追加の行)、`docs/P002-frontend-spec.md` §3 S06・§4.4〜§4.6(※CR-002により追記)、`docs/P003-backend-spec.md` §6.3・§7.4〜§7.6(※CR-002により追記)、`docs/P006-test-plan.md` S06行(※CR-002により追記)。

実装するテストコードの関数名・ファイルパスは、`docs/P008-test-direction/T021-room-description-create-and-list.md`・`T022-room-description-update-and-fetch.md`・`T023-room-description-preserved-on-unrelated-update.md` が【実行コマンド】に明記する関数名と厳密に一致させること(V0.5 P102ルール)。

---

# 【タスクID】U006-1(バックエンド)

## 【目的】

* `rooms` テーブルに `description` カラムを追加し、`GET/POST /api/rooms`・`PUT /api/rooms/{room_id}` の入出力に `description` を含める。

## 【作成・編集対象ファイル】

* `server/app/db/migrations/0002_add_room_description.sql`(新規): `ALTER TABLE ROOMS ADD COLUMN description TEXT`。
* `server/app/db/connection.py`(既存ファイルに追記): `init_db()` が複数回実行されても`ALTER TABLE ADD COLUMN`系マイグレーションが冪等に成功するよう、`duplicate column name` エラーを捕捉して無視する処理を追加する。★FIXME★ この冪等化はP003の既存マイグレーション設計(起動のたびに全ファイルを再実行する)を前提にした実装判断であり、マイグレーション適用状況を専用テーブルで管理する方式への変更はCR-002のスコープ外とした。
* `server/app/core/validators.py`(既存ファイルに追記): `validate_room_description(value)`(任意、最大200文字)。
* `server/app/repositories/room_repository.py`(既存ファイルに追記): `insert`/`update` に `description` 引数(既定値 `None`、既存呼び出し元との後方互換のためキーワード可能な末尾引数とする)を追加。
* `server/app/services/room_service.py`(既存ファイルに追記): `create`/`update` で `validate_room_description` を通し、`room_repository.insert`/`update` に `description` を渡す。
* `server/app/api/rooms.py`(既存ファイルに追記): `_room_dict` のレスポンスに `description` を追加。

## 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §6.3(データモデル追加分)、§7.4〜§7.6(API内部仕様)
* `docs/P002-frontend-spec.md` §4.4〜§4.6(API外部仕様)

## 【実装内容】

* 上記5ファイルを編集し、`description` を会議室のCRUD全経路(一覧・作成・更新のリクエスト/レスポンス)に通す。
* `description` は任意項目。未入力時は `None`(DB上は `NULL`)として扱う。

## 【実装してはいけないこと】

* S03(予約作成画面)の会議室プルダウンの変更(`docs/CR.md` CR-002「影響が想定される範囲」のとおりスコープ外)。
* `description` をAPIの必須項目にすること。

## 【Unit Test内容】

* テスト対象: `validate_room_description`(`server/tests/test_validators.py`)、`room_repository.insert`/`update` の `description` 引数(`server/tests/test_room_repository.py`)、`room_service.create` の `description` 検証・伝播(`server/tests/test_room_service.py`)
* 正常系テスト: 200文字以内・Noneが許容される。`insert`/`create` で渡した `description` がDBに保存され `find` で読み出せる。
* 主要な異常系テスト: 201文字で `False`/`ValidationError`。
* 実行するテストコマンド: `cd server && python3 -m unittest tests.test_validators tests.test_room_repository tests.test_room_service -v`
* 合格条件: 全テストPASS。
* 補足: `room_service.update` の `description` 伝播の結合的な確認(更新後に一覧・詳細へ反映されるか)は、本タスクの単体テスト範囲ではなく、T022/T023(`docs/P008-test-direction/`)の結合テストで確認する。

## 【実行コマンド】

* `cd server && python3 -m unittest discover -s tests -v`(既存121件に回帰がないことも合わせて確認する)

## 【完了条件】

* 上記テストが全てPASSする。

---

# 【タスクID】U006-2(フロントエンド)

## 【目的】

* S06(会議室管理画面)の登録フォーム・編集フォームに説明文の入力欄を追加し、一覧表示にも説明文を表示する。

## 【作成・編集対象ファイル】

* `client/js/pages/roomManagementPage.js`(既存ファイルに追記): `validateRoomInput` に説明文の検証(任意、200文字以内)を追加。`createRoomManagementController` に編集(`startEdit`/`submitUpdate`/`cancelEdit`)を追加(既存は登録・無効化のみで編集UIが未実装だったため、CR-002の「編集フォーム」要件を満たすためにあわせて実装する)。`mountRoomManagementPage` の一覧表示に説明文の列を追加し、行ごとに「編集」ボタンを追加。編集ボタン押下で編集フォーム(登録フォームと同じ項目+説明文、既存値をプリフィル)を表示する。
* `client/tests/roomManagementPage.test.mjs`(既存ファイルに追記)

## 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S06(※CR-002により追記)

## 【実装内容】

* `validateRoomInput(name, capacity, description)`: 説明文が200文字を超える場合 `"説明文は200文字以内で入力してください"` を返す。
* `createRoomManagementController(roomApi)`:
  * `submitCreate(name, capacity, equipment, isActive, description)`: `roomApi.create` に `description` を含めて送信する。
  * `startEdit(roomId)`: `state.editingRoomId = roomId` を設定する。
  * `submitUpdate(roomId, name, capacity, equipment, isActive, description)`: バリデーション後 `roomApi.update(roomId, {...})` を呼び、成功時は `state.editingRoomId = null` にして一覧を再取得する。
  * `cancelEdit()`: `state.editingRoomId = null` にする。
* `mountRoomManagementPage`: 一覧テーブルに「説明文」列を追加。各行に「編集」ボタンを追加し、押下で `controller.startEdit(id)` を呼び再描画、編集対象行のみ入力フォームに切り替える。

## 【実装してはいけないこと】

* S03(予約作成画面)の会議室プルダウン表示項目の変更(`docs/CR.md` CR-002「影響が想定される範囲」のとおりスコープ外)。

## 【Unit Test内容】

* テスト対象: `validateRoomInput`、`createRoomManagementController`(`submitCreate`/`startEdit`/`submitUpdate`/`cancelEdit`)
* 正常系テスト: 200文字以内の説明文でバリデーション通過。`submitCreate`/`submitUpdate` が `roomApi.create`/`roomApi.update` に `description` を含めて渡す。`submitUpdate` 成功後に `editingRoomId` が `null` に戻り一覧が再取得される。
* 主要な異常系テスト: 201文字の説明文でエラーメッセージが返る。`submitUpdate` がAPIエラー時に一覧を再取得しない。
* 実行するテストコマンド: `cd client && node --test tests/roomManagementPage.test.mjs`
* 合格条件: 全テストPASS(既存6件+追加分)。

## 【実行コマンド】

* `cd client && node --test tests/*.test.mjs`(既存の他画面のテストに回帰がないことも合わせて確認する)

## 【完了条件】

* 上記テストが全てPASSする。

## 【次タスクに進む前の停止条件】(U006-1・U006-2共通)

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

## 重要

* 各タスクの範囲外のファイルは編集しないでください。
* 各タスク完了後、実行したテストコマンドと結果を報告してください。
* 停止条件に該当しない限り、次のタスクへ自動的に進んでください(V0.5 defect 1-4対応。P903全体を通じて人間の指示待ちで停止しません)。
