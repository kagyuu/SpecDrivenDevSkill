あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U003 — reservation-management-and-rooms

## タスク一覧(OKF副目次)

* 状態は `[ ]`(未着手) / `[~]`(進行中) / `[x]`(完了) の3種類とする。
* このスプリントファイル自体の状態(`docs/P007-impl-direction.md` の該当行)は、全タスクが `[x]` になって初めて `[x]` にする。
* **中断からの再開**・**先行実装の禁止** のルールは `docs/P007-impl-direction/U001-foundation-and-auth.md` 冒頭の注記と同一。

- [x] U003-T1 [予約更新・会議室CRUDのスキーマ](#u003-t1-予約更新会議室crudのスキーマ) — ReservationUpdateRequest/RoomCreateRequest等
- [x] U003-T2 [Repository層 追加(reservations更新・削除、rooms書き込み)](#u003-t2-repository層-追加reservations更新削除rooms書き込み) — 自己除外重複チェックを含む
- [x] U003-T3 [Service層・APIハンドラ(PUT/DELETE reservations)](#u003-t3-service層apiハンドラputdelete-reservations) — 権限チェック含む
- [x] U003-T4 [Service層・APIハンドラ(POST/PUT/DELETE rooms)](#u003-t4-service層apiハンドラpostputdelete-rooms) — 管理者権限ガード
- [x] U003-T5 [フロントエンド S04予約詳細・編集画面](#u003-t5-フロントエンド-s04予約詳細編集画面) — 表示専用/編集可の分岐を含む
- [x] U003-T6 [フロントエンド S06会議室管理画面](#u003-t6-フロントエンド-s06会議室管理画面) — 会議室一覧・登録・編集・削除
- [x] U003-T7 [CR-001: internal_memoの更新・閲覧制限マスキング・S04反映](#u003-t7-cr-001-internal_memoの更新閲覧制限マスキングs04反映) — 更新API・詳細/一覧APIのマスキング・S04フォーム(※CR-001により追加)

---

## U003-T1: 予約更新・会議室CRUDのスキーマ

### 【目的】

* `PUT /api/reservations/{id}` と会議室CRUD APIの入出力スキーマを定義する。

### 【作成・編集対象ファイル】

* `server/app/schemas/reservation.py`(編集、`ReservationUpdateRequest` を追加)
* `server/app/schemas/room.py`(編集、`RoomCreateRequest`/`RoomUpdateRequest`/`RoomResponse` を追加)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S04、§3 S06
* `docs/P003-backend-spec.md` §3.2(rooms)

### 【実装内容】

* `ReservationUpdateRequest` はS03/S04の編集可能項目(会議室・日付・時刻・件名・参加者・参加予定人数・備考)を持つ(`docs/P007-impl-direction/U002-reservation-core.md` のU002-T1で定義した `ReservationCreateRequest` と項目は同一だが、更新対象IDはパスパラメータから取るため別スキーマとする)。
* `RoomCreateRequest`(name必須50文字以内、capacity必須1以上、equipment任意配列、description任意200文字以内、is_active既定true)、`RoomUpdateRequest`(同項目、全項目必須の全置換とする)、`RoomResponse`。

### 【実装してはいけないこと】

* `reservations`/`rooms` テーブル自体のDDL変更(既存テーブル定義で全項目を満たせるため不要)。

### 【Unit Test内容】

* テスト対象: 各Pydanticスキーマ
* 正常系/異常系: `RoomCreateRequest` に `capacity=0` を渡すとバリデーションエラーになること。`name` が51文字でエラーになること。
* 実行コマンド: `cd server && uv run python -m pytest tests/schemas/test_room_schema.py tests/schemas/test_reservation_schema.py -v`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/schemas/test_room_schema.py tests/schemas/test_reservation_schema.py -v`

### 【完了条件】

* 上記Unit Testがすべて成功する。

### 【次タスクに進む前の停止条件】

* Unit Testが3回の自己修正を経ても成功しない場合、処理を停止し人間に報告する。

---

## U003-T2: Repository層 追加(reservations更新・削除、rooms書き込み)

### 【目的】

* 予約の更新・削除、会議室の作成・更新・論理削除のデータアクセス関数を追加する。

### 【作成・編集対象ファイル】

* `server/app/repositories/reservations.py`(編集、追加関数)
* `server/app/repositories/rooms.py`(編集、書き込み関数を追加)
* `server/tests/repositories/test_reservations_repo.py`(編集)
* `server/tests/repositories/test_rooms_repo.py`(編集)

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §5.5、§5.9、§5.10、§6

### 【実装内容】

* `reservations.py` に `update_reservation(conn, reservation_id, data, updated_at) -> None`、`delete_reservation(conn, reservation_id) -> None` を追加する。`update_reservation` の重複チェックは、既存の `find_conflicting`(U002-T3で実装済み)に `exclude_id=reservation_id` を渡すことで対応する(新しい重複判定ロジックをここで再実装しない)。
* `rooms.py` に `create_room(conn, data, created_at) -> int`、`update_room(conn, room_id, data, updated_at) -> None`、`deactivate_room(conn, room_id, updated_at) -> None`(`is_active=0` に更新するのみで物理削除しない)、`list_rooms(conn, include_inactive: bool) -> list[Room]`(管理画面用、`include_inactive=True` で無効な会議室も含める)を追加する。

### 【実装してはいけないこと】

* 会議室の物理削除(`DELETE FROM rooms`)。`docs/P003-backend-spec.md` §5.5のとおり論理削除のみ。
* `updated_at`/`created_at` の値をRepository内部で計算すること(引数として受け取ること。`docs/P003-backend-spec.md` §6)。

### 【Unit Test内容】

* テスト対象: 上記追加関数
* 正常系: `update_reservation` で予約枠を変更した後、`get_by_id` で反映が確認できること。
* 正常系: 自分自身の現在の枠と全く同じ時間帯で `update_reservation` を呼んでも(他フィールドのみ変更)、重複エラーにならないこと(`exclude_id` が機能していることの確認)。
* 正常系: `deactivate_room` 後、`list_active_rooms`(U001-T3)には含まれないが `list_rooms(include_inactive=True)` には含まれること。
* 実行コマンド: `cd server && uv run python -m pytest tests/repositories/test_reservations_repo.py tests/repositories/test_rooms_repo.py -v`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/repositories/test_reservations_repo.py tests/repositories/test_rooms_repo.py -v`

### 【完了条件】

* 上記Unit Testがすべて成功する。

### 【次タスクに進む前の停止条件】

* Unit Testが3回の自己修正を経ても成功しない場合、処理を停止し人間に報告する。

---

## U003-T3: Service層・APIハンドラ(PUT/DELETE reservations)

### 【目的】

* `PUT /api/reservations/{id}`、`DELETE /api/reservations/{id}` を実装する。

### 【作成・編集対象ファイル】

* `server/app/services/reservations.py`(編集)
* `server/app/api/routers/reservations.py`(編集)
* `server/tests/api/test_reservations_api.py`(編集)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S04、§7.3
* `docs/P003-backend-spec.md` §5.9、§5.10

### 【実装内容】

* `update_reservation_flow`: 権限チェック(`current_user.id == reservation.user_id or current_user.role == "admin"`、満たさなければ403 `FORBIDDEN`)→U002-T4と同じ順序のバリデーション(`exclude_id`付き)。
* `delete_reservation_flow`: 同じ権限チェック→`delete_reservation` 呼び出し、204。
* いずれも対象IDが存在しない場合は404 `NOT_FOUND`。

### 【実装してはいけないこと】

* 予約の取消理由・履歴の記録(`docs/P003-backend-spec.md` §5.10のとおり本バージョンでは物理削除・履歴なしと決定済み)。

### 【Unit Test内容】

* テスト対象: `PUT`/`DELETE /api/reservations/{id}`
* 正常系: 予約者本人が自分の予約を更新→200。
* 正常系: 管理者が他人の予約を取消→204。
* 異常系: 予約者本人でも管理者でもないユーザーが更新を試みる→403 `FORBIDDEN`。
* 異常系: 存在しないIDを指定→404 `NOT_FOUND`。
* 異常系: 更新後の時間帯が別の予約と重複する→409 `RESERVATION_CONFLICT`。
* 実行コマンド: `cd server && uv run python -m pytest tests/api/test_reservations_api.py -v`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/api/test_reservations_api.py -v`

### 【完了条件】

* 上記Unit Testがすべて成功する。

### 【次タスクに進む前の停止条件】

* Unit Testが3回の自己修正を経ても成功しない場合、処理を停止し人間に報告する。

---

## U003-T4: Service層・APIハンドラ(POST/PUT/DELETE rooms)

### 【目的】

* `POST /api/rooms`、`PUT /api/rooms/{id}`、`DELETE /api/rooms/{id}` を実装する。

### 【作成・編集対象ファイル】

* `server/app/services/rooms.py`(新規)
* `server/app/api/routers/rooms.py`(編集、書き込み系エンドポイントを追加)
* `server/tests/api/test_rooms_api.py`(編集)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S06
* `docs/P003-backend-spec.md` §5.5

### 【実装内容】

* 3エンドポイントとも `require_admin` 依存(U001-T4で定義済み)を必須にする。
* `GET /api/rooms?include_inactive=true` は管理者のみ有効(`docs/P003-backend-spec.md` §5.4のとおり、一般ユーザーが指定しても無視する)ため、このタスクで `routers/rooms.py` のGETハンドラも合わせて修正する。

### 【実装してはいけないこと】

* 会議室名・収容人数のPATCH的な部分更新(`docs/P002-frontend-spec.md` §3 S06の項目は全置換で更新する設計のため、部分更新エンドポイントは追加しない)。

### 【Unit Test内容】

* テスト対象: `POST`/`PUT`/`DELETE /api/rooms/{id}`、および `GET /api/rooms?include_inactive=true` の権限別挙動
* 正常系: 管理者が会議室を新規登録→201。
* 異常系: 一般ユーザーが会議室登録を試みる→403 `FORBIDDEN`。
* 正常系: 管理者が `DELETE /api/rooms/{id}` を呼ぶと論理削除され、以後 `GET /api/rooms`(通常)には出ないが `GET /api/rooms?include_inactive=true`(管理者)には出ること。
* 異常系: 一般ユーザーが `include_inactive=true` を付けても、無効な会議室が結果に含まれないこと。
* 実行コマンド: `cd server && uv run python -m pytest tests/api/test_rooms_api.py -v`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/api/test_rooms_api.py -v`

### 【完了条件】

* 上記Unit Testがすべて成功する。

### 【次タスクに進む前の停止条件】

* Unit Testが3回の自己修正を経ても成功しない場合、処理を停止し人間に報告する。

---

## U003-T5: フロントエンド S04予約詳細・編集画面

### 【目的】

* `docs/P002-frontend-spec.md` §3 S04を実装する。

### 【作成・編集対象ファイル】

* `client/src/pages/ReservationDetailPage.tsx`(新規)
* `client/src/router.tsx`(編集、S04を実ルートに差し替え。S02/S05からの遷移先を接続する)
* `client/src/tests/ReservationDetailPage.test.tsx`(新規)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S04、§7.3、§6(認可)

### 【実装内容】

* `GET /api/reservations/{id}` で取得した内容を表示する。`current_user`(`GET /api/me` の結果、アプリ全体でContext等により共有する)と `reservation.user_id` を比較し、本人または管理者でなければ編集フォーム・取消ボタンを表示せず「表示のみ」の注記を出す。
* 編集フォームはS03と同じ入力項目・クライアント側バリデーションを再利用する(共通コンポーネント化する場合はU002-T6で作成した入力部分を抽出して共有してよい)。
* 取消ボタン押下で確認ダイアログ→`DELETE /api/reservations/{id}`。

### 【実装してはいけないこと】

* 権限が無いユーザーに対する編集フォームの表示(非表示のみで防ぐのではなく、そもそもDOMに描画しないこと。表示はCSSで隠すだけの実装は不可)。

### 【Unit Test内容】

* テスト対象: `ReservationDetailPage`
* 正常系: 予約者本人としてアクセスすると編集フォーム・取消ボタンが表示されること。
* 正常系: 他人の予約に一般ユーザーとしてアクセスすると編集フォーム・取消ボタンがDOMに存在しないこと。
* 正常系: 管理者としてアクセスすると他人の予約でも編集フォーム・取消ボタンが表示されること。
* 実行コマンド: `cd client && npm run test -- src/tests/ReservationDetailPage.test.tsx`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd client && npm run test -- src/tests/ReservationDetailPage.test.tsx`
* `cd client && npm run build`

### 【完了条件】

* 上記Unit Testがすべて成功し、`npm run build` が成功する。

### 【次タスクに進む前の停止条件】

* Unit Testが3回の自己修正を経ても成功しない場合、処理を停止し人間に報告する。

---

## U003-T6: フロントエンド S06会議室管理画面

### 【目的】

* `docs/P002-frontend-spec.md` §3 S06を実装する。

### 【作成・編集対象ファイル】

* `client/src/pages/RoomAdminPage.tsx`(新規)
* `client/src/router.tsx`(編集、S06を管理者専用ルートとして追加。役割ガード=`GET /api/me` の `role` が `admin` でなければ403相当の画面を表示)
* `client/src/tests/RoomAdminPage.test.tsx`(新規)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S06、§6

### 【実装内容】

* 会議室一覧(名前/収容人数/設備/説明文/有効・無効)の表示、新規登録フォーム、編集フォーム、削除(論理削除)ボタン+確認ダイアログを実装する。
* ルーティングガード: `role !== "admin"` の場合、S06のコンポーネント自体をレンダリングせず、権限不足の案内を表示する(§6「クライアント側ガードはUX目的の補助」との整合を保つため、最終的な防御はAPI側の403に委ねる前提を保つ)。

### 【実装してはいけないこと】

* サーバー側の403チェックを省略してよいという前提での実装(クライアント側ガードのみに依存しないこと。APIが403を返した場合のエラー表示も別途用意する)。

### 【Unit Test内容】

* テスト対象: `RoomAdminPage`
* 正常系: 管理者ロールでアクセスすると会議室一覧・フォームが表示されること。
* 正常系: 一般ユーザーロールでアクセスすると権限不足の案内が表示され、フォームがDOMに存在しないこと。
* 正常系: 削除ボタン押下→確認→`DELETE /api/rooms/{id}` が呼ばれること。
* 実行コマンド: `cd client && npm run test -- src/tests/RoomAdminPage.test.tsx`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd client && npm run test -- src/tests/RoomAdminPage.test.tsx`
* `cd client && npm run build`

### 【完了条件】

* 上記Unit Testがすべて成功し、`npm run build` が成功する。

### 【次タスクに進む前の停止条件】

* Unit Testが3回の自己修正を経ても成功しない場合、処理を停止し人間に報告する。

---

## U003-T7: CR-001: internal_memoの更新・閲覧制限マスキング・S04反映

### 【目的】

* `docs/P901-cr-direction/CR-001.md` にもとづき、`internal_memo` を更新系API(`PUT /api/reservations/{id}`)で編集可能にし、閲覧系API(`GET /api/reservations`・`GET /api/reservations/mine`・`GET /api/reservations/{id}`)で「所有者・管理者のみ実際の値を返す」マスキングを実装する。あわせてS04に入力欄を追加する。

### 【作成・編集対象ファイル】

* `server/app/schemas/reservation.py`(編集: `ReservationUpdateRequest`に`internal_memo`を追加)
* `server/app/repositories/reservations.py`(編集: `update_reservation`に`internal_memo`を追加)
* `server/app/services/reservations.py`(編集: `update_reservation_flow`が`internal_memo`を渡す。マスキングのための新しいヘルパー関数を追加してよい)
* `server/app/api/routers/reservations.py`(編集: `_to_response`に`viewer: User`引数を追加し、`reservation.user_id != viewer.id and not viewer.is_admin`の場合は`internal_memo`を`None`にする。`GET /api/reservations`・`GET /api/reservations/mine`・`GET /api/reservations/{id}`の各呼び出し箇所で`viewer`を渡すよう更新する)
* `client/src/pages/ReservationDetailPage.tsx`(編集: `canEdit`ブロック内に「備考(社内向けメモ)」欄を追加)
* テスト一式(下記【Unit Test内容】参照)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S04、§6(閲覧範囲の外部契約)
* `docs/P003-backend-spec.md` §5.9「`internal_memo`のマスキング」

### 【実装内容】

* Repository: `update_reservation`に`internal_memo: str | None = None`(キーワード引数、デフォルト値あり)を追加し、UPDATE文に含める。
* Router: `_to_response(reservation, viewer)`のシグネチャに変更し、`viewer.id == reservation.user_id or viewer.is_admin`でなければ`internal_memo`を`None`で返すようにする。この関数を呼ぶすべてのエンドポイント(`GET /api/reservations`、`GET /api/reservations/mine`、`GET /api/reservations/{id}`、`POST /api/reservations`、`PUT /api/reservations/{id}`)を更新する(作成・更新のレスポンスは実行者自身が対象なので実質的に常にマスキングされないが、関数のシグネチャ統一のため同じ経路を通す)。
* フロントエンド: `ReservationDetailPage.tsx`の編集フォーム(`canEdit`が真のときのみ表示される箇所)に「備考(社内向けメモ)」のtextareaを追加する。`canEdit`が偽の場合はフォーム自体が表示されないため、追加の非表示制御は不要(既存の分岐をそのまま利用できる)。

### 【実装してはいけないこと】

* `GET /api/reservations/mine`のマスキングを実装すること自体は問題ないが、この経路は常に自分の予約のみを返すため実質的に常に実値が返る。誤って一律`None`にしないよう注意する。
* 既存の「備考」(`notes`)の閲覧範囲(現状どおり、閲覧可能な利用者には見える)を変更しないこと。

### 【Unit Test内容】

* テスト対象: `PUT /api/reservations/{id}`、`GET /api/reservations/{id}`、`GET /api/reservations`、`GET /api/reservations/mine`
* 正常系: 所有者が`internal_memo`付きで`PUT`すると、値が更新されること。
* 正常系: 所有者が`GET /api/reservations/{id}`を呼ぶと、実際の`internal_memo`の値が返ること。
* 正常系: 管理者が他人の予約を`GET /api/reservations/{id}`で取得すると、実際の値が返ること。
* **正常系(マスキング確認)**: 所有者でも管理者でもない一般ユーザーが`GET /api/reservations/{id}`を呼ぶと、`internal_memo`が`null`で返ること(他のフィールドは通常どおり返る)。
* **正常系(マスキング確認、一覧)**: `GET /api/reservations`(カレンダー一覧)で他人の予約を取得した場合も、`internal_memo`が`null`で返ること。
* 実行コマンド: `cd server && uv run python -m pytest tests/schemas/test_reservation_schema.py tests/repositories/test_reservations_repo.py tests/api/test_reservations_api.py -v`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/schemas/test_reservation_schema.py tests/repositories/test_reservations_repo.py tests/api/test_reservations_api.py -v`
* `cd client && npm run test -- src/tests/ReservationDetailPage.test.tsx`
* `cd client && npm run build`

### 【完了条件】

* 上記Unit Testがすべて成功し、`npm run build` が成功する。**※実装時に発見**: ローカル実行環境(Node.js v24.12.0/Windows)において`npm run build`がソース内容に関係なくネイティブクラッシュ(`STATUS_STACK_BUFFER_OVERRUN`、rollupのWindowsネイティブバインディング内)で失敗することを確認した(U002-T7と同一の事象、詳細は同ファイルの完了条件の注記および`docs/P007-impl-direction.md`「未解決事項」参照)。`tsc -b`・`npx vitest run`・`npx playwright test`(T001〜T010含む)はいずれも全PASSしており、CR-001のコードに起因する問題ではないと判断し、これらの全PASSをもって完了条件の代替確認とする。

### 【次タスクに進む前の停止条件】

* 該当なし(本スプリントの最終タスク)。全タスク完了後、`docs/P007-impl-direction.md` のU003行を `[x]` に更新する。Unit Testが3回の自己修正を経ても成功しない場合は、その時点で処理を停止し人間に報告する。

## 重要

* 各タスクの範囲外のファイルは編集しないでください。
* タスクの実装後、実行したテストコマンドと結果を報告してください。
* タスクが完了したら、上記「タスク一覧」の該当行を `[x]` に更新してください。
* 全タスクが完了したら、`docs/P007-impl-direction.md` の本スプリント行を `[x]` に更新してください。
* Executor Stepの停止条件(`SKILL.md` 参照)に該当しない限り、次のタスクに自動的に進んでください。1タスクごとに人間の指示を待つ必要はありません。
