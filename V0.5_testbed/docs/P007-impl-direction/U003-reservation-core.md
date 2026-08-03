あなたはExecutor(実装担当)です。このスプリント(U003: reservation-core)には6個のタスク(U003-1〜U003-6)があります。**1回に1タスクだけ**実施し、完了条件を満たしたら報告し、次タスクの指示を待ってください。

前提: U001(foundation-auth)・U002(admin-management)が完了していること(会議室一覧・ユーザー一覧APIが利用可能)。
参照する仕様書: `docs/P002-frontend-spec.md`、`docs/P003-backend-spec.md`、`docs/P005-impl-plan.md` §3.3、`docs/P006-test-plan.md`。

---

# 【タスクID】U003-1

## 【目的】

* 予約の作成・一覧取得に関するリクエスト/レスポンス型、および日付・時刻のパース・比較を行う純粋関数を実装する。

## 【作成・編集対象ファイル】

* `server/app/schemas/reservation.py`(Pydanticモデル: `ReservationCreateRequest`、`ReservationListItem`)
* `server/app/core/datetime_utils.py`(`parse_date`、`parse_time`、`is_future_or_today`)

## 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §4.8、§4.11
* `docs/P003-backend-spec.md` §5(区間重複判定の境界の扱い)

## 【実装内容】

* `parse_date`/`parse_time` はそれぞれ `YYYY-MM-DD`/`HH:MM` 形式を検証しパースする。不正形式は `ValueError`。
* `is_future_or_today(date)` は本日以降かを判定する(`docs/P002-frontend-spec.md` §3 S03「過去日付不可」)。
* Pydanticモデルには `docs/P002-frontend-spec.md` §4.11のリクエストボディの型(`room_id: int`、`date: str`、`start_time: str`、`end_time: str`、`title: str`、`participant_ids: list[int]`、`notes: str | None`)を定義する。

## 【実装してはいけないこと】

* DBアクセスを伴うバリデーション(会議室・参加者の存在確認、重複チェックはU003-3/U003-4で行う)。

## 【Unit Test内容】

* テスト対象: `parse_date`/`parse_time`/`is_future_or_today`
* 正常系テスト: 正しい形式の日付・時刻がパースできる。本日・未来日で `is_future_or_today` がTrue。
* 主要な異常系テスト: 不正形式(`2026/08/10` 等)で `ValueError`。過去日で `is_future_or_today` がFalse。
* 実行するテストコマンド: `cd server && uv run pytest tests/test_datetime_utils.py -v`
* 合格条件: 全テストPASS。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_datetime_utils.py -v`

## 【完了条件】

* 上記テストが全てPASSする。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

---

# 【タスクID】U003-2

## 【目的】

* 予約作成のバリデーション純粋関数(終了>開始、件名・備考の文字数)を実装する。

## 【作成・編集対象ファイル】

* `server/app/core/validators.py`(既存ファイルに追記): `validate_time_range`、`validate_title`、`validate_notes`

## 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S03

## 【実装内容】

* `validate_time_range(start, end)`: `end > start` であることを検証する(等しい・逆転はFalse)。
* `validate_title(value)`: 1〜100文字。
* `validate_notes(value)`: 空またはNoneを許容、最大500文字。

## 【実装してはいけないこと】

* 営業時間内チェック(`docs/P002-frontend-spec.md` §3 S03に「時間外予約を妨げない」と明記されているため、時間外だからという理由でFalseにしない)。

## 【Unit Test内容】

* テスト対象: 上記3関数
* 正常系テスト: 開始<終了、1〜100文字の件名、500文字以内の備考でTrue。
* 主要な異常系テスト: 開始=終了、開始>終了でFalse。101文字の件名、501文字の備考でFalse。
* 実行するテストコマンド: `cd server && uv run pytest tests/test_validators.py -v`
* 合格条件: 全テストPASS(既存分含む)。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_validators.py -v`

## 【完了条件】

* 上記テストが全てPASSする。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

---

# 【タスクID】U003-3

## 【目的】

* 予約のRepository層(一覧取得、重複チェック用SELECT、`BEGIN IMMEDIATE` による排他制御付きINSERT)を実装する。

## 【作成・編集対象ファイル】

* `server/app/repositories/reservation_repository.py`(`list_by_range`、`has_overlap`、`insert_with_participants`)

## 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §5(排他制御の手順)、§7.8、§7.11

## 【実装内容】

* `has_overlap(room_id, date, start_time, end_time, exclude_reservation_id=None)`: `docs/P003-backend-spec.md` §5の区間判定式(`start_time < 既存.end_time AND end_time > 既存.start_time`)でSELECTし、1件でもあればTrueを返す。
* `insert_with_participants(data, current_user_id)`: `BEGIN IMMEDIATE` でトランザクションを開始し、`has_overlap` を再チェックしたうえで `RESERVATIONS` へINSERT、`RESERVATION_PARTICIPANTS` へ一括INSERTし `COMMIT` する。重複を検知した場合は `ROLLBACK` し `OverlapError` を送出する。
* `list_by_range(date_from, date_to, room_ids)`: 参加者・備考をJOINしない軽量なSELECTとする(`docs/P003-backend-spec.md` §7.8)。

## 【実装してはいけないこと】

* 会議室・参加者の存在確認(Service層U003-4の責務)。

## 【Unit Test内容】

* テスト対象: `has_overlap`、`insert_with_participants`、`list_by_range`
* 正常系テスト: 重複のない予約が登録できる。日付範囲内の予約のみ `list_by_range` で取得できる。
* 主要な異常系テスト: 完全に重なる時間帯、一部が重なる時間帯(例: 既存10:00-11:00に対し10:30-11:30)で `has_overlap` がTrue。境界が接する時間帯(既存10:00-11:00に対し11:00-12:00)では重複としない(False)ことを確認する(`docs/P003-backend-spec.md` §5)。重複時間帯への `insert_with_participants` が `OverlapError` を送出する。
* 実行するテストコマンド: `cd server && uv run pytest tests/test_reservation_repository.py -v`
* 合格条件: 全テストPASS。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_reservation_repository.py -v`

## 【完了条件】

* 上記テストが全てPASSする。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

---

# 【タスクID】U003-4

## 【目的】

* 予約作成のService層(会議室・参加者の存在確認、重複チェック呼び出し)を実装する。

## 【作成・編集対象ファイル】

* `server/app/services/reservation_service.py`(`create`、`list_for_calendar`)

## 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §7.11

## 【実装内容】

* `create(data, current_user)`:
  1. `validate_time_range`/`validate_title`/`validate_notes`/`is_future_or_today` を通す(不正なら `ValidationError`)。
  2. `room_repository.find(room_id)` で存在・有効性を確認(存在しなければ `NotFoundError`、無効化済みなら `ValidationError`)。
  3. `user_repository` で `participant_ids` の存在確認(存在しないものがあれば `NotFoundError`)。
  4. `reservation_repository.insert_with_participants` を呼ぶ(`OverlapError` はそのまま呼び出し元に伝播させる)。
* `list_for_calendar(date_from, date_to, room_ids)`: `reservation_repository.list_by_range` をそのまま呼ぶ薄いラッパー。

## 【実装してはいけないこと】

* HTTPステータスコードへの変換(Handler層U003-5の責務)。

## 【Unit Test内容】

* テスト対象: `reservation_service.create`
* 正常系テスト: 正しい入力で予約が作成される。
* 主要な異常系テスト: 存在しない会議室IDで `NotFoundError`。無効化済み会議室で `ValidationError`。存在しない参加者IDで `NotFoundError`。重複時間帯で `OverlapError`。過去日付で `ValidationError`。
* 実行するテストコマンド: `cd server && uv run pytest tests/test_reservation_service.py -v`
* 合格条件: 全テストPASS。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_reservation_service.py -v`

## 【完了条件】

* 上記テストが全てPASSする。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

---

# 【タスクID】U003-5

## 【目的】

* `GET /api/reservations`、`POST /api/reservations` のAPI Handler層を実装する。

## 【作成・編集対象ファイル】

* `server/app/api/reservations.py`(新規、GET一覧・POST作成のみ。詳細/mine/更新/削除はU004で追記)
* `server/app/main.py`(ルーター登録)

## 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §4.8、§4.11

## 【実装内容】

* `GET /api/reservations` は `require_auth`。クエリ `date_from`/`date_to`/`room_ids` を受け、`reservation_service.list_for_calendar` を呼ぶ。`date_from`/`date_to` 欠落・不正形式は `400 VALIDATION_ERROR`。
* `POST /api/reservations` は `require_auth`。`reservation_service.create` を呼び、`ValidationError`→400、`NotFoundError`→404、`OverlapError`→409(`RESERVATION_CONFLICT`)に変換する。

## 【実装してはいけないこと】

* `GET /api/reservations/mine`、`GET/PUT/DELETE /api/reservations/{id}` の実装(U004の範囲)。

## 【Unit Test内容】

* テスト対象: `GET /api/reservations`、`POST /api/reservations`
* 正常系テスト: 認証済みユーザーが予約一覧を取得できる。正しい入力で予約作成が201で成功する。
* 主要な異常系テスト: 未ログインで401。不正な日付範囲で400。重複時間帯で409。存在しない会議室IDで404。
* 実行するテストコマンド: `cd server && uv run pytest tests/test_api_reservations.py -v`
* 合格条件: 全テストPASS。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_api_reservations.py -v`

## 【完了条件】

* 上記テストが全てPASSする。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

---

# 【タスクID】U003-6(結合確認用の薄いタスク)

## 【目的】

* S02予約カレンダー画面・S03予約作成画面を実装し、U002の会議室一覧APIおよびU003-5の予約API群と接続する。

## 【作成・編集対象ファイル】

* `client/src/pages/CalendarPage.tsx`(S02)
* `client/src/pages/ReservationCreatePage.tsx`(S03)
* `client/src/api/reservationApi.ts`(`listReservations`、`createReservation`)
* `client/src/App.tsx`(ルーティング追加)

## 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S02、§3 S03、§6.2、§6.3

## 【実装内容】

* `CalendarPage` は `roomApi.list` と `reservationApi.listReservations` を呼び、会議室×時間帯(9:00-18:00、30分刻み)のグリッドを描画する。
* `ReservationCreatePage` は会議室プルダウン(`roomApi.list`)、参加者複数選択(`userApi.list`)、フォーム入力、送信時に `reservationApi.createReservation` を呼ぶ。409時に重複エラーメッセージを表示する。

## 【実装してはいけないこと】

* S04・S05(U004の範囲)の実装。

## 【Unit Test内容】

* テスト対象: `CalendarPage`、`ReservationCreatePage`(APIはモック化)
* 正常系テスト: モック一覧データがグリッドに描画される。正しい入力で `createReservation` が呼ばれ成功後にカレンダーへ遷移する。
* 主要な異常系テスト: `createReservation` が409相当のモックを返すとき重複エラーメッセージが表示される。
* 実行するテストコマンド: `cd client && npm run test -- CalendarPage ReservationCreatePage`
* 合格条件: 全テストPASS。

## 【実行コマンド】

* `cd client && npm run test`
* `cd server && uv run pytest -v`

## 【完了条件】

* 上記テストが全てPASSする。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

## 重要

* 各タスクの範囲外のファイルは編集しないでください。
* 各タスク完了後、実行したテストコマンドと結果を報告してください。
* 次のタスクには自己判断で進まないでください。
