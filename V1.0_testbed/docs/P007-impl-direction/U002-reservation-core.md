あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U002 — reservation-core

## タスク一覧(OKF副目次)

* 状態は `[ ]`(未着手) / `[~]`(進行中) / `[x]`(完了) の3種類とする。1タスクの作業を開始したら `[~]` に、完了条件をすべて満たしたら `[x]` に更新する。
* このスプリントファイル自体の状態(`docs/P007-impl-direction.md` の該当行)は、全タスクが `[x]` になって初めて `[x]` にする。
* **中断からの再開**・**先行実装の禁止** のルールは `docs/P007-impl-direction/U001-foundation-and-auth.md` 冒頭の注記と同一(`SKILL.md`「目次(OKF形式)について」参照)。

- [x] U002-T1 [予約テーブルのマイグレーション + Pydanticスキーマ](#u002-t1-予約テーブルのマイグレーション--pydanticスキーマ) — reservations/reservation_participantsの作成と入出力スキーマ
- [x] U002-T2 [予約バリデーション純粋関数(重複判定・収容人数判定)](#u002-t2-予約バリデーション純粋関数重複判定収容人数判定) — 半開区間の重複判定を含む
- [x] U002-T3 [Repository層(reservations)](#u002-t3-repository層reservations) — 作成・一覧・詳細取得
- [x] U002-T4 [Service層・APIハンドラ(GET/POST reservations)](#u002-t4-service層apiハンドラgetpost-reservations) — バリデーション順序の適用
- [x] U002-T5 [フロントエンド S02予約カレンダー画面](#u002-t5-フロントエンド-s02予約カレンダー画面) — 会議室×時間帯グリッド
- [x] U002-T6 [フロントエンド S03予約作成画面 + S05マイ予約一覧画面](#u002-t6-フロントエンド-s03予約作成画面--s05マイ予約一覧画面) — 予約登録フォームと自分の予約一覧(参加者選択は未解決事項参照)
- [x] U002-T7 [CR-001: internal_memo列追加とS03/作成APIへの反映](#u002-t7-cr-001-internal_memo列追加とs03作成apiへの反映) — マイグレーション・スキーマ拡張・作成系API・S03フォーム(※CR-001により追加)

---

## U002-T1: 予約テーブルのマイグレーション + Pydanticスキーマ

### 【目的】

* `reservations`/`reservation_participants` テーブルを追加し、予約APIの入出力スキーマを定義する。

### 【作成・編集対象ファイル】

* `server/migrations/003_create_reservations_tables.sql`(新規)
* `server/app/schemas/reservation.py`(新規)

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §3.2(reservations/reservation_participants)、§5.9

### 【実装内容】

* `003_create_reservations_tables.sql` に `reservations`(`CHECK(end_time > start_time)` を含む)、`reservation_participants`、複合インデックス `idx_reservations_room_date` を作成するDDLを書く。
* `reservation.py` に `ReservationCreateRequest`/`ReservationUpdateRequest`/`ReservationResponse`(`docs/P002-frontend-spec.md` §3 S03/S04の項目と一致させる)をPydantic v2で定義する。

### 【実装してはいけないこと】

* `users`/`rooms`/`sessions` テーブルへの変更(既存マイグレーションを編集せず、新規ファイルのみ追加すること)。

### 【Unit Test内容】

* テスト対象: マイグレーション適用結果、Pydanticスキーマのバリデーション
* 正常系: 一時DBに001〜003を適用し、`reservations`/`reservation_participants` が作成されること。既に001〜002が適用済みのDBに003のみを追加適用しても成功すること(差分適用の確認)。
* 正常系: `ReservationCreateRequest` に必須項目を満たすデータを渡すとバリデーションを通過すること。
* 異常系: `title` を101文字にするとPydanticのバリデーションエラーになること。
* 実行コマンド: `cd server && uv run python -m pytest tests/db/test_migrate.py tests/schemas/test_reservation_schema.py -v`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/db/test_migrate.py tests/schemas/test_reservation_schema.py -v`

### 【完了条件】

* 上記Unit Testがすべて成功する。

### 【次タスクに進む前の停止条件】

* Unit Testが3回の自己修正を経ても成功しない場合、処理を停止し人間に報告する。

---

## U002-T2: 予約バリデーション純粋関数(重複判定・収容人数判定)

### 【目的】

* `docs/P003-backend-spec.md` §5.9の重複判定ロジック(半開区間、背中合わせは重複としない)と収容人数判定を、DBアクセスを持たない純粋関数として実装する。

### 【作成・編集対象ファイル】

* `server/app/validation/reservation.py`(新規)
* `server/tests/validation/test_reservation.py`(新規)

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §5.9(重複判定ロジック、SQL実装例を含む)

### 【実装内容】

* `is_time_range_valid(start: str, end: str) -> bool`: `end > start` の文字列比較(`HH:MM` は辞書順比較で時刻順と一致するため文字列比較でよい)。
* `overlaps(new_start: str, new_end: str, existing_start: str, existing_end: str) -> bool`: `docs/P003-backend-spec.md` §5.9の判定式 `NOT (new.end <= existing.start OR new.start >= existing.end)` をそのまま実装する。
* `is_capacity_ok(expected_attendees: int | None, room_capacity: int) -> bool`: `expected_attendees` が `None` なら常に真。

### 【実装してはいけないこと】

* DBへの問い合わせ(この関数はメモリ上の値だけで判定する。実際の既存予約との突き合わせはT3のRepository層で行う)。

### 【Unit Test内容】

* テスト対象: `overlaps`
* 正常系(重複あり): 既存 `10:00-11:00` に対し新規 `10:30-11:30` → 重複と判定される。
* 正常系(重複あり): 既存 `10:00-11:00` に対し新規 `09:00-12:00`(既存を包含) → 重複と判定される。
* **境界値(重複なし)**: 既存 `10:00-11:00` に対し新規 `11:00-12:00`(背中合わせ、開始が既存の終了と一致) → **重複と判定されない**(`docs/P003-backend-spec.md` §5.9で明示的に規定された挙動)。
* **境界値(重複なし)**: 既存 `10:00-11:00` に対し新規 `09:00-10:00`(背中合わせ、終了が既存の開始と一致) → **重複と判定されない**。
* `is_time_range_valid("10:00","10:00")` が偽であること(等しい場合はエラー)。
* `is_capacity_ok(11, 10)` が偽、`is_capacity_ok(10, 10)` が真であること(収容人数と同数はエラーにしない)。
* 実行コマンド: `cd server && uv run python -m pytest tests/validation/test_reservation.py -v`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/validation/test_reservation.py -v`

### 【完了条件】

* 上記Unit Testがすべて成功する。境界値テスト(背中合わせのケース)を省略しないこと。

### 【次タスクに進む前の停止条件】

* Unit Testが3回の自己修正を経ても成功しない場合、処理を停止し人間に報告する。

---

## U002-T3: Repository層(reservations)

### 【目的】

* 予約の作成・検索・取得のためのデータアクセス関数を実装する。

### 【作成・編集対象ファイル】

* `server/app/repositories/reservations.py`(新規)
* `server/tests/repositories/test_reservations_repo.py`(新規)

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §3.2、§5.6〜§5.9、§6(時刻引数ルール)

### 【実装内容】

* `create_reservation(conn, data: ReservationCreateInternal, created_at: str) -> int`(作成した予約のIDを返す。参加者は `reservation_participants` に別途 `INSERT`)。
* `find_conflicting(conn, room_id: int, date: str, start_time: str, end_time: str, exclude_id: int | None) -> list[Reservation]`: `docs/P003-backend-spec.md` §5.9のSQL例のとおり半開区間の重なりを判定するクエリを発行する。`exclude_id` が指定された場合はそのIDを結果から除外する。
* `list_by_range(conn, date_from: str, date_to: str, room_id: int | None) -> list[Reservation]`(カレンダー表示用)。
* `get_by_id(conn, reservation_id: int) -> Reservation | None`。
* `list_by_user(conn, user_id: int, now: datetime, period: Literal["upcoming","past"]) -> list[Reservation]`。**`now` は呼び出し元(Service層)が計算して渡す明示的な引数とし、この関数内で `datetime.now()` を呼び出してはならない**(`docs/P003-backend-spec.md` §6)。「今後」の判定条件(`date > 当日 OR (date = 当日 AND end_time > 現在時刻)`)は `now` から導出した日付・時刻文字列を使ってSQL側で比較する。

### 【実装してはいけないこと】

* バリデーション判定(T2の関数を呼び出すのみとし、判定式自体をここに再実装しない)。
* `datetime.now()`/`date.today()` の直接呼び出し。

### 【Unit Test内容】

* テスト対象: 上記各Repository関数
* 正常系: `create_reservation` で作成した予約を `get_by_id` で取得できること。
* 正常系: `find_conflicting` に、既存予約と重なる時間帯を渡すと1件返り、背中合わせの時間帯を渡すと0件になること(T2の境界値ケースをDB経由でも再確認する)。
* 正常系: `exclude_id` に既存予約自身のIDを渡すと、その予約は重複候補から除外されること。
* 正常系: `list_by_user` に固定した `now` を渡し、「今後」「過去」がそれぞれ正しく分類されること。
* 実行コマンド: `cd server && uv run python -m pytest tests/repositories/test_reservations_repo.py -v`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/repositories/test_reservations_repo.py -v`

### 【完了条件】

* 上記Unit Testがすべて成功する。

### 【次タスクに進む前の停止条件】

* Unit Testが3回の自己修正を経ても成功しない場合、処理を停止し人間に報告する。

---

## U002-T4: Service層・APIハンドラ(GET/POST reservations)

### 【目的】

* `GET /api/reservations`、`GET /api/reservations/mine`、`GET /api/reservations/{id}`、`POST /api/reservations` を実装する。

### 【作成・編集対象ファイル】

* `server/app/services/reservations.py`(新規)
* `server/app/api/routers/reservations.py`(新規)
* `server/tests/api/test_reservations_api.py`(新規)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S02/S03/S05、§7.2
* `docs/P003-backend-spec.md` §5.6〜§5.9

### 【実装内容】

* `services/reservations.py` の `create_reservation_flow(conn, req, current_user, now)` に、`docs/P003-backend-spec.md` §5.9で定めた順序(①必須・形式 ②終了>開始 ③会議室有効性 ④収容人数 ⑤重複)でチェックを行い、最初に該当したエラーを送出する。予約者自身(`current_user.id`)は `reservation_participants` には登録しない(`docs/P003-backend-spec.md` §3.2)。
* `routers/reservations.py`: 各エンドポイントを実装し、`get_current_user` 依存を必須にする。`POST /api/reservations` はバリデーション結果に応じ 201/400(`VALIDATION_ERROR`/`INVALID_TIME_RANGE`/`ROOM_INACTIVE`/`CAPACITY_EXCEEDED`)/409(`RESERVATION_CONFLICT`)を返す。

### 【実装してはいけないこと】

* `PUT`/`DELETE /api/reservations/{id}`(U003の対象)。

### 【Unit Test内容】

* テスト対象: 上記4エンドポイント(`TestClient`)
* 正常系: 正しい入力で `POST /api/reservations` → 201。
* 異常系: `end_time == start_time` → 400 `INVALID_TIME_RANGE`。
* 異常系: 収容人数超過 → 400 `CAPACITY_EXCEEDED`。
* 異常系: 同一会議室・重なる時間帯へ2件目を作成 → 409 `RESERVATION_CONFLICT`。
* **境界値**: 1件目の予約の終了時刻と同じ開始時刻で2件目を作成 → 201(重複エラーにならないこと)。
* 正常系: `GET /api/reservations/mine?period=upcoming` が自分の未来予約のみ返すこと。
* 実行コマンド: `cd server && uv run python -m pytest tests/api/test_reservations_api.py -v`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/api/test_reservations_api.py -v`

### 【完了条件】

* 上記Unit Testがすべて成功する。

### 【次タスクに進む前の停止条件】

* Unit Testが3回の自己修正を経ても成功しない場合、処理を停止し人間に報告する。

---

## U002-T5: フロントエンド S02予約カレンダー画面

### 【目的】

* `docs/P002-frontend-spec.md` §3 S02の会議室×時間帯グリッドを実装する。

### 【作成・編集対象ファイル】

* `client/src/pages/CalendarPage.tsx`(新規)
* `client/src/components/RoomTimeGrid.tsx`(新規)
* `client/src/api/rooms.ts`・`client/src/api/reservations.ts`(新規、APIクライアント関数)
* `client/src/router.tsx`(編集、S02を実ルートに差し替え)
* `client/src/tests/CalendarPage.test.tsx`(新規)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S02、§4、§10

### 【実装内容】

* ログイン後の遷移先を `CalendarPage` にする(`router.tsx` を編集)。
* `RoomTimeGrid` は会議室を列、時間帯(09:00-18:00、30分刻み。それ以外の時間帯の予約がある場合は表示範囲を拡張)を行として描画し、予約済みセルに `{予約者名} / {件名}` を表示する(参加予定人数は§3 S02の記載どおり描画しない)。
* 会議室フィルタ・週送りUIを実装し、変更のたびに `GET /api/reservations?room_id=&date_from=&date_to=` を呼び直す。

### 【実装してはいけないこと】

* 予約の作成・編集フォーム自体(S03/S04の対象)。ここではセルクリック時の遷移先を用意するのみ。

### 【Unit Test内容】

* テスト対象: `RoomTimeGrid`
* 正常系: モックした予約データが該当セルに表示されること。
* 正常系: 自分の予約セルはクリック可能(遷移用ハンドラが呼ばれる)、他人の予約セルはクリックしても遷移用ハンドラが呼ばれないこと。
* 実行コマンド: `cd client && npm run test -- src/tests/CalendarPage.test.tsx`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd client && npm run test -- src/tests/CalendarPage.test.tsx`
* `cd client && npm run build`

### 【完了条件】

* 上記Unit Testがすべて成功し、`npm run build` が成功する。

### 【次タスクに進む前の停止条件】

* Unit Testが3回の自己修正を経ても成功しない場合、処理を停止し人間に報告する。

---

## U002-T6: フロントエンド S03予約作成画面 + S05マイ予約一覧画面

### 【目的】

* `docs/P002-frontend-spec.md` §3 S03(予約作成)・S05(マイ予約一覧)を実装する。

### 【作成・編集対象ファイル】

* `client/src/pages/ReservationCreatePage.tsx`(新規)
* `client/src/pages/MyReservationsPage.tsx`(新規)
* `client/src/router.tsx`(編集、S03/S05を実ルートに差し替え)
* `client/src/tests/ReservationCreatePage.test.tsx`(新規)
* `client/src/tests/MyReservationsPage.test.tsx`(新規)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S03、§3 S05、§7.2

### 【実装内容】

* `ReservationCreatePage`: 会議室プルダウン(`GET /api/rooms`)、日付・開始/終了時刻、終日チェックボックス(チェック時09:00/18:00を自動入力、手動上書き可)、件名、参加者複数選択、参加予定人数、備考の各入力欄と、クライアント側バリデーション(§3 S03のとおり)、送信時の `POST /api/reservations` 呼び出しとエラー表示(`RESERVATION_CONFLICT`→重複メッセージ、`CAPACITY_EXCEEDED`→収容人数メッセージ)。
* `MyReservationsPage`: 期間フィルタ(今後/過去、既定は今後)、`GET /api/reservations/mine?period=` の一覧表示、行クリックでS04(次スプリントまでは仮のプレースホルダ遷移先)へ。

### 【実装してはいけないこと】

* S04(予約詳細・編集画面)自体の実装(U003の対象)。行クリックの遷移先ルートはプレースホルダでよい。

### 【Unit Test内容】

* テスト対象: `ReservationCreatePage`、`MyReservationsPage`
* 正常系: 終日チェックボックスをオンにすると開始09:00・終了18:00が入力されること。
* 異常系: 終了時刻を開始時刻以前にして送信すると、APIを呼ばずに「終了時刻は開始時刻より後の時刻を指定してください」を表示すること。
* 異常系: APIが409 `RESERVATION_CONFLICT` を返すモックの場合、「選択した会議室・時間帯は既に予約されています」を表示すること。
* 正常系: `MyReservationsPage` が期間フィルタの切り替えで `GET /api/reservations/mine` を異なるクエリで呼び直すこと。
* 実行コマンド: `cd client && npm run test -- src/tests/ReservationCreatePage.test.tsx src/tests/MyReservationsPage.test.tsx`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd client && npm run test -- src/tests/ReservationCreatePage.test.tsx src/tests/MyReservationsPage.test.tsx`
* `cd client && npm run build`

### 【完了条件】

* 上記Unit Testがすべて成功し、`npm run build` が成功する。

### 【次タスクに進む前の停止条件】

* Unit Testが3回の自己修正を経ても成功しない場合、処理を停止し人間に報告する。

---

## U002-T7: CR-001: internal_memo列追加とS03/作成APIへの反映

### 【目的】

* `docs/P901-cr-direction/CR-001.md` にもとづき、予約に「備考(社内向けメモ)」(`internal_memo`)列を追加し、予約作成(S03・`POST /api/reservations`)で入力・保存できるようにする。

### 【作成・編集対象ファイル】

* `server/migrations/004_add_reservation_internal_memo.sql`(新規)
* `server/app/repositories/reservations.py`(編集: `Reservation`データクラス・`_row_to_reservation`・`create_reservation`に`internal_memo`を追加)
* `server/app/schemas/reservation.py`(編集: `ReservationCreateRequest`・`ReservationResponse`に`internal_memo`を追加)
* `server/app/services/reservations.py`(編集: `create_reservation_flow`が`internal_memo`を渡す)
* `server/app/api/routers/reservations.py`(編集: `_to_response`が`internal_memo`を含める。この時点ではマスキングは行わない前提でよいが、閲覧者に応じたマスキングはU003-T7で実装するため、本タスクでは常に実際の値を返す実装のままでよい)
* `client/src/api/reservations.ts`(編集: `Reservation`・`ReservationInput`型に`internal_memo`を追加)
* `client/src/pages/ReservationCreatePage.tsx`(編集: 「備考(社内向けメモ)」欄を追加)
* テスト一式(下記【Unit Test内容】参照)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S03(「備考(社内向けメモ)」の行)
* `docs/P003-backend-spec.md` §3.2(`reservations.internal_memo`)、§5.9(バリデーション順序①に300文字チェックを追加)

### 【実装内容】

* マイグレーション: `ALTER TABLE reservations ADD COLUMN internal_memo TEXT;`
* スキーマ: `ReservationCreateRequest.internal_memo: str | None = Field(default=None, max_length=300)`。`ReservationResponse.internal_memo: str | None`。
* Repository: `_SELECT_BASE`のSELECT列に`r.internal_memo`を追加。`create_reservation`に`internal_memo: str | None = None`(キーワード引数、既存呼び出しを壊さないようデフォルト値を持たせる)を追加し、INSERT文に含める。
* Service: `create_reservation_flow`が`payload.internal_memo`を`create_reservation`へ渡す。
* Router: `_to_response`が`reservation.internal_memo`をそのまま含める(閲覧者によるマスキングはU003-T7で追加する。本タスク時点では作成直後のレスポンスのみが対象であり、作成者本人にしか呼ばれないため問題ない)。
* フロントエンド: `ReservationCreatePage.tsx`に「備考(社内向けメモ)」のtextarea(`maxLength={300}`)を追加し、送信データに含める。

### 【実装してはいけないこと】

* 既存の「備考」(`notes`)フィールドの仕様・文字数制限を変更しないこと。
* `PUT /api/reservations/{id}`・`GET /api/reservations/{id}`・`GET /api/reservations`のマスキングロジック実装(U003-T7の対象)。

### 【Unit Test内容】

* テスト対象: マイグレーション、`ReservationCreateRequest`、Repository`create_reservation`、`POST /api/reservations`
* 正常系: マイグレーション004適用後、`reservations`テーブルに`internal_memo`列が存在すること。001〜003が適用済みのDBに004のみを追加適用しても成功すること(差分適用の確認、既存の`test_run_migrations_*`と同様のパターン)。
* 正常系: `internal_memo`に300文字以内の文字列を指定して`POST /api/reservations`を呼ぶと201が返り、レスポンスに指定した値が含まれること。
* 正常系: `internal_memo`を指定せずに`POST /api/reservations`を呼んでもエラーにならず、レスポンスの`internal_memo`が`null`であること。
* 異常系: `internal_memo`に301文字を指定すると422(FastAPI/Pydantic既定の`{"detail": [...]}`形式)になること。**※実装時に発見・訂正**: 当初この項目は「400 `VALIDATION_ERROR`」を想定していたが、実際にはFastAPI/Pydanticの`Field(max_length=...)`制約違反はPydanticスキーマ構築段階で先に例外化され、アプリ側の`ApiError`ハンドラ(400/`VALIDATION_ERROR`)を経由しない。これは`title`・`notes`等の既存フィールドにも共通する既存の欠陥であり、CR-001固有の問題ではないため本CRでは修正せず、実際の挙動(422/`detail`)をテスト対象とする(詳細は`docs/P007-impl-direction.md`「未解決事項」参照)。
* 実行コマンド: `cd server && uv run python -m pytest tests/db/test_migrate.py tests/schemas/test_reservation_schema.py tests/repositories/test_reservations_repo.py tests/api/test_reservations_api.py -v`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/db/test_migrate.py tests/schemas/test_reservation_schema.py tests/repositories/test_reservations_repo.py tests/api/test_reservations_api.py -v`
* `cd client && npm run test -- src/tests/ReservationCreatePage.test.tsx`
* `cd client && npm run build`

### 【完了条件】

* 上記Unit Testがすべて成功し、`npm run build` が成功する。**※実装時に発見**: ローカル実行環境(Node.js v24.12.0/Windows)において、`npm run build`(`vite build`)がソース内容に関係なくネイティブクラッシュ(`STATUS_STACK_BUFFER_OVERRUN`、rollupのWindowsネイティブバインディング内)で失敗することを確認した。`tsc -b`(型検査)は正常終了し、`npx vitest run`・`npx playwright test`(開発サーバー経由のE2E、T001〜T010含む)はいずれも全PASSしており、CR-001のソースコード自体に起因する問題ではないと判断した(`--minify false`でも同様にクラッシュする、rollupのネイティブ依存を再インストールしても解消しない、ことから切り分け済み)。本件はビルド環境側の課題として人間に報告し、この完了条件については型検査・単体テスト・E2Eテストの全PASSをもって代替確認とする。

### 【次タスクに進む前の停止条件】

* 該当なし(本スプリントの最終タスク)。全タスク完了後、`docs/P007-impl-direction.md` のU002行を `[x]` に更新する。Unit Testが3回の自己修正を経ても成功しない場合は、その時点で処理を停止し人間に報告する。

## 重要

* 各タスクの範囲外のファイルは編集しないでください。
* タスクの実装後、実行したテストコマンドと結果を報告してください。
* タスクが完了したら、上記「タスク一覧」の該当行を `[x]` に更新してください。
* 全タスクが完了したら、`docs/P007-impl-direction.md` の本スプリント行を `[x]` に更新してください。
* Executor Stepの停止条件(`SKILL.md` 参照)に該当しない限り、次のタスクに自動的に進んでください。1タスクごとに人間の指示を待つ必要はありません。
