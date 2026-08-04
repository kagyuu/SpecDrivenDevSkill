あなたはExecutor(実装担当)です。このスプリント(U004: reservation-detail-mine)には6個のタスク(U004-1〜U004-6)があります。**1回に1タスクだけ**実施し、完了条件を満たしたら報告し、次タスクの指示を待ってください。

前提: U003(reservation-core)が完了し、予約の閲覧・作成が可能であること。
参照する仕様書: `docs/P002-frontend-spec.md`、`docs/P003-backend-spec.md`、`docs/P005-impl-plan.md` §3.4、`docs/P006-test-plan.md`。

---

# 【タスクID】U004-1

## 【目的】

* マイ予約一覧の期間フィルタ(`upcoming`/`past`)を判定する純粋関数を実装する。

## 【作成・編集対象ファイル】

* `server/app/core/datetime_utils.py`(既存ファイルに追記): `is_upcoming(date, today)`

## 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S05
* `docs/P003-backend-spec.md` §7.9

## 【実装内容】

* `is_upcoming(date, today)`: `date >= today` ならTrue(当日を含む。時刻は考慮しない、`docs/P003-backend-spec.md` §7.9参照)。

## 【実装してはいけないこと】

* DBアクセス(本タスクは純粋関数のみ)。

## 【Unit Test内容】

* テスト対象: `is_upcoming`
* 正常系テスト: 当日・未来日でTrue。
* 主要な異常系テスト: 過去日でFalse。
* 実行するテストコマンド: `cd server && uv run pytest tests/test_datetime_utils.py -v`
* 合格条件: 全テストPASS(既存分含む)。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_datetime_utils.py -v`

## 【完了条件】

* 上記テストが全てPASSする。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

---

# 【タスクID】U004-2

## 【目的】

* 予約のRepository層に、詳細取得・作成者別一覧・更新・削除を追加する。

## 【作成・編集対象ファイル】

* `server/app/repositories/reservation_repository.py`(既存ファイルに追記): `find_with_detail`、`list_by_creator`、`update_with_participants`、`delete`

## 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §7.9、§7.10、§7.12、§7.13

## 【実装内容】

* `find_with_detail(reservation_id)`: 参加者一覧・作成者名までJOINして返す。存在しなければNone。
* `list_by_creator(user_id, period)`: `is_upcoming` を用いて `upcoming`/`past` をフィルタする。
* `update_with_participants(reservation_id, data)`: `BEGIN IMMEDIATE` で重複再チェック(`has_overlap` に `exclude_reservation_id=reservation_id` を渡す)後、UPDATE、参加者は全削除→再INSERT。重複時は `ROLLBACK` + `OverlapError`。
* `delete(reservation_id)`: `RESERVATIONS` から物理DELETE(`RESERVATION_PARTICIPANTS` はFKの `ON DELETE CASCADE` により自動削除される。U001-1のマイグレーションで設定済みであることを前提とする)。

## 【実装してはいけないこと】

* 権限チェック(Service層U004-3の責務)。

## 【Unit Test内容】

* テスト対象: `find_with_detail`、`list_by_creator`、`update_with_participants`、`delete`
* 正常系テスト: 詳細取得・作成者別一覧・更新・削除がそれぞれ正しく動作する。
* 主要な異常系テスト: 存在しないIDで `find_with_detail` がNone。更新時に自分自身の予約は重複対象から除外され重複エラーにならない。他の予約と重複する内容への更新で `OverlapError`。削除後に `RESERVATION_PARTICIPANTS` の該当行も消えている(CASCADE確認)。
* 実行するテストコマンド: `cd server && uv run pytest tests/test_reservation_repository.py -v`
* 合格条件: 全テストPASS(U003分含む)。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_reservation_repository.py -v`

## 【完了条件】

* 上記テストが全てPASSする。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

---

# 【タスクID】U004-3

## 【目的】

* 予約の参照・更新・削除に関するService層(本人/管理者のみ編集可能という権限判定を含む)を実装する。

## 【作成・編集対象ファイル】

* `server/app/services/reservation_service.py`(既存ファイルに追記): `get_detail`、`list_mine`、`update`、`delete`、`check_editable`

## 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §4、§7.9、§7.10、§7.12、§7.13

## 【実装内容】

* `check_editable(reservation, current_user)`: `reservation.created_by == current_user.id or current_user.role == "admin"` でなければ `ForbiddenError` を送出する。
* `update(reservation_id, data, current_user)`: 存在確認(`NotFoundError`)→`check_editable`→U003-4と同様のバリデーション→`update_with_participants` 呼び出し。
* `delete(reservation_id, current_user)`: 存在確認→`check_editable`→`delete`。
* `list_mine(current_user_id, period)`: `list_by_creator` を呼ぶ薄いラッパー。

## 【実装してはいけないこと】

* HTTPステータスコードへの変換(Handler層U004-4の責務)。

## 【Unit Test内容】

* テスト対象: `check_editable`、`update`、`delete`、`list_mine`、`get_detail`
* 正常系テスト: 予約者本人・管理者がそれぞれ編集・削除できる。
* 主要な異常系テスト: 予約者本人でも管理者でもないユーザーが編集・削除しようとして `ForbiddenError`。存在しないIDで `NotFoundError`。更新時の重複で `OverlapError`。
* 実行するテストコマンド: `cd server && uv run pytest tests/test_reservation_service.py -v`
* 合格条件: 全テストPASS(U003分含む)。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_reservation_service.py -v`

## 【完了条件】

* 上記テストが全てPASSする。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

---

# 【タスクID】U004-4

## 【目的】

* `GET /api/reservations/mine`、`GET /api/reservations/{reservation_id}`、`PUT /api/reservations/{reservation_id}`、`DELETE /api/reservations/{reservation_id}` のAPI Handler層を実装する。

## 【作成・編集対象ファイル】

* `server/app/api/reservations.py`(既存ファイルに追記)

## 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §4.9、§4.10、§4.12、§4.13

## 【実装内容】

* 各エンドポイントは `require_auth` を課し、対応するService層関数を呼ぶ。
* 例外変換: `NotFoundError`→404、`ForbiddenError`→403、`ValidationError`→400、`OverlapError`→409。
* ルート順序に注意する(`GET /api/reservations/mine` が `GET /api/reservations/{reservation_id}` に `mine` という文字列がIDとして誤って渡らないよう、`mine` を固定パスとして先に定義する)。

## 【実装してはいけないこと】

* U003-5で実装済みの `GET /api/reservations`、`POST /api/reservations` の変更(必要な場合を除き触らない)。

## 【Unit Test内容】

* テスト対象: 上記4エンドポイント
* 正常系テスト: 自分の予約一覧取得、詳細取得、本人による更新・削除が成功する。
* 主要な異常系テスト: 他人の予約を一般ユーザーが更新・削除しようとして403。存在しないIDで404。未ログインで401。重複時間帯への更新で409。
* 実行するテストコマンド: `cd server && uv run pytest tests/test_api_reservations.py -v`
* 合格条件: 全テストPASS(U003分含む)。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_api_reservations.py -v`

## 【完了条件】

* 上記テストが全てPASSする。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

---

# 【タスクID】U004-5

## 【目的】

* S04予約詳細・編集画面、S05マイ予約一覧画面のフロントエンドコンポーネントを実装する。

## 【作成・編集対象ファイル】

* `client/src/pages/ReservationDetailPage.tsx`(S04)
* `client/src/pages/MyReservationsPage.tsx`(S05)
* `client/src/api/reservationApi.ts`(既存ファイルに追記): `getDetail`、`getMine`、`update`、`remove`

## 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S04、§3 S05

## 【実装内容】

* `ReservationDetailPage` は予約内容表示、本人/管理者のみ編集可能な入力欄、取消ボタン(確認ダイアログ付き)を実装する。編集不可の場合は入力欄を読み取り専用にする。
* `MyReservationsPage` は期間フィルタ(既定 `upcoming`)付きの一覧を実装する。

## 【実装してはいけないこと】

* S01〜S03(既存スプリントの範囲)への変更。

## 【Unit Test内容】

* テスト対象: `ReservationDetailPage`、`MyReservationsPage`(APIモック)
* 正常系テスト: 本人ログイン時に編集フォームが活性化する。一覧がモックデータどおりに表示される。
* 主要な異常系テスト: 他人の予約閲覧時に編集フォームが非活性(読み取り専用)になる。
* 実行するテストコマンド: `cd client && npm run test -- ReservationDetailPage MyReservationsPage`
* 合格条件: 全テストPASS。

## 【実行コマンド】

* `cd client && npm run test -- ReservationDetailPage MyReservationsPage`
* `cd client && npm run build`

## 【完了条件】

* 上記テストがPASSし、ビルドが成功する。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

---

# 【タスクID】U004-6(結合確認用の薄いタスク)

## 【目的】

* 予約の作成→詳細表示→編集→取消→マイ予約一覧反映という一連の流れが、実装済みの画面とAPIで実際に繋がることを確認する。

## 【作成・編集対象ファイル】

* `client/src/pages/ReservationDetailPage.tsx`、`client/src/pages/MyReservationsPage.tsx`(モックからAPI接続への切り替え)
* `client/src/App.tsx`(ルーティングにS04/S05を追加)

## 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S04、§3 S05

## 【実装内容】

* `reservationApi` の実呼び出しに接続する。

## 【実装してはいけないこと】

* 新規の画面・APIの追加。

## 【Unit Test内容】

* テスト対象: 画面とAPIの結線(モックした `reservationApi` を使用)
* 正常系テスト: 詳細画面での編集操作で `reservationApi.update` が呼ばれ、成功後にカレンダーへ遷移する。取消操作で `reservationApi.remove` が呼ばれる。
* 主要な異常系テスト: 更新APIが409エラーを返した場合、詳細画面にエラーが表示され画面遷移しない。
* 実行するテストコマンド: `cd client && npm run test -- ReservationDetailPage MyReservationsPage`
* 合格条件: 全テストPASS。

## 【実行コマンド】

* `cd client && npm run test`
* `cd server && uv run pytest -v`

## 【完了条件】

* 上記テストが全てPASSする。全スプリント(U001〜U004)のUnit Testが揃ってPASSしていることを確認する。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

## 重要

* 各タスクの範囲外のファイルは編集しないでください。
* 各タスク完了後、実行したテストコマンドと結果を報告してください。
* 次のタスクには自己判断で進まないでください。
