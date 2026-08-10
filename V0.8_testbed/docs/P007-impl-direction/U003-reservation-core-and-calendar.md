あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U003 — reservation-core-and-calendar

> このスプリントは `docs/P005-impl-plan.md` 3章で「技術的難易度: 高」と位置づけられている(予約の重複チェック・排他制御)。他スプリントよりタスクを手厚く分割している。各タスクの完了条件、特に排他制御の同時実行テストは省略せず必ず実施すること。

## タスク一覧(OKF副目次)

* 状態は `[ ]`(未着手) / `[~]`(進行中) / `[x]`(完了) の3種類とする。1タスクの作業を開始したら `[~]` に、完了条件をすべて満たしたら `[x]` に更新する。
* このスプリントファイル自体の状態(`docs/P007-impl-direction.md` の該当行)は、全タスクが `[x]` になって初めて `[x]` にする。1件以上のタスクが `[~]`/`[x]` で残りが `[ ]` の場合は `[~]` とする。
* **中断からの再開**・**先行実装の禁止**: `docs/P007-impl-direction/U001-foundation-and-auth.md` タスク一覧節と同じ規則に従う。

- [x] U003-T1 [予約データアクセス層実装(排他制御含む)](#u003-t1-予約データアクセス層実装排他制御含む) — Repository層、重複判定クエリ、BEGIN IMMEDIATE(同時実行テストを5回連続実行し安定してPASSすることを確認済み)
- [x] U003-T2 [予約作成Service層実装](#u003-t2-予約作成service層実装) — バリデーション、収容人数チェック、参加者保存(★実施メモ: `list_participant_candidates` の内部実現に必要な `user_repository.find_active_for_directory()` は、このタスクのファイル一覧に無いが `docs/P003-backend-spec.md` 4.10節が明示的に要求するため追加した)
- [x] U003-T3 [予約作成・一覧・参加者候補APIハンドラ実装](#u003-t3-予約作成一覧参加者候補apiハンドラ実装) — POST/GET /api/reservations, GET /api/users/directory(★実施メモ: レスポンスに`ReservationDetailResponse`が必要なためU004-T2予定分を前倒しで`schemas/reservation.py`に定義。U004-T2到達時に再定義しない)
- [x] U003-T4 [S02予約カレンダー画面実装](#u003-t4-s02予約カレンダー画面実装) — 会議室×時間帯グリッド(★実施メモ: 3.2節「自分が参加者になっている予約もS04を開ける」は、この画面が呼ぶGET /api/reservations一覧レスポンス(4.6節)に参加者一覧が含まれず判定不能なため、暫定的に「予約者本人または管理者」のみをS04遷移対象とした。★FIXME★としてコード内に記載済み)
- [x] U003-T5 [S03予約作成画面実装](#u003-t5-s03予約作成画面実装) — 予約作成フォーム
- [x] U003-T6 [S02/S03とAPIの接続確認](#u003-t6-s02s03とapiの接続確認) — 重複エラー表示を含む結合確認用の薄いタスク(★実施メモ: U002-T4と同じ理由でブラウザ操作は未実施。「作成→GET一覧に反映→同一時間帯で再作成すると409」をcurlで直接確認した。フロントエンドのクリック操作・画面遷移自体はUnitTestでカバー)
- [x] U003-T7 [CR-001: オンライン会議URL — バックエンド(スキーマ・バリデーション・API)](#u003-t7-cr-001-オンライン会議url--バックエンドスキーマバリデーションapi) — `POST /api/reservations` の `meeting_url` 項目追加(★実施メモ: `server/tests/test_reservation_repository.py`・`test_reservation_service.py`・`test_reservations_api.py` に追加テスト計25件、全件PASS確認済み)
- [x] U003-T8 [CR-001: オンライン会議URL — S03予約作成画面](#u003-t8-cr-001-オンライン会議url--s03予約作成画面) — 入力欄・バリデーション表示(★実施メモ: `client/tests/ReservationCreatePage.test.tsx`に追加した3件を含む全19件PASS確認済み)
- [x] U003-T9 [CR-001: 既存回帰修正 — マイグレーションファイル一覧アサーション更新](#u003-t9-cr-001-既存回帰修正--マイグレーションファイル一覧アサーション更新) — `server/tests/test_migration.py` の2件(★実施メモ: 更新後PASS確認済み)

---

## U003-T1: 予約データアクセス層実装(排他制御含む)

### 【目的】

* 予約テーブル・参加者テーブルへのアクセスと、同一会議室・時間帯の重複判定を、競合状態を発生させない形で実装する。

### 【作成・編集対象ファイル】

* `server/app/repositories/reservation_repository.py`(`find_overlapping(room_id, start, end, exclude_reservation_id=None)`, `create`, `find_by_range(date_from, date_to, room_ids)`, `add_participants`, `begin_immediate_transaction`)
* `server/tests/test_reservation_repository.py`

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` 4.6〜4.9.2節(排他制御、重複判定クエリ、参加者保存)
* `docs/P003-backend-spec.md` 2.2節(インデックス `idx_reservations_room_time`)

### 【実装内容】

* `begin_immediate_transaction()`: SQLite接続に対し `BEGIN IMMEDIATE` を発行してから処理ブロックに入るコンテキストマネージャを実装する。
* `find_overlapping`: `SELECT reservation_id FROM reservations WHERE room_id = ? AND start_datetime < ? AND end_datetime > ?`(`exclude_reservation_id` 指定時は `AND reservation_id != ?` を追加)を実装する(`docs/P003-backend-spec.md` 4.6〜4.9.2節の判定式のとおり)。
* `create`: `reservations` へのINSERTと `reservation_participants` への一括INSERTを同一トランザクション内で行う。
* `find_by_range`: `rooms`・`users` をJOINして `room_name`・`organizer_name` を含む形で返す(`docs/P002-frontend-spec.md` 4.6節のレスポンス形式)。

### 【実装してはいけないこと】

* バリデーション(文字数・収容人数チェック等)はこのタスクに含めない(U003-T2の範囲)。Repository層は受け取った値をそのまま保存する。

### 【Unit Test内容】

* テスト対象: `reservation_repository.py`
* 正常系: 重複の無い時間帯での作成が成功する、時間帯が完全に一致しない(端点が接するだけの)予約は重複と判定されない
* 主要な異常系: 完全に重なる時間帯・部分的に重なる時間帯(前方/後方にはみ出す、内包する)がいずれも重複と判定される
* **同時実行テスト(重要)**: 同一 `room_id`・同一時間帯に対して2つのスレッド(または2つのDBコネクション)からほぼ同時に `create` を呼び出した場合、`BEGIN IMMEDIATE` による排他制御により片方が先に進み、後発側が `find_overlapping` の再チェックまたはSQLiteのロック待ちの後に重複を検出して例外を送出し、結果として `reservations` テーブルに該当時間帯の行が1件しか残らないことを確認する(`threading` モジュールで2スレッドから同時呼び出しするテストケースを実装する)。
* 実行するテストコマンド: `cd server && python -m pytest tests/test_reservation_repository.py -v`
* 合格条件: 全件PASS(同時実行テストを含む)

### 【実行コマンド】

* `cd server && python -m pytest tests/test_reservation_repository.py -v`

### 【完了条件】

* 上記Unit Test(同時実行テストを含む)がすべてPASSする

### 【次タスクに進む前の停止条件】

* 同時実行テストが3回自己修正しても安定してPASSしない(たまに二重予約が発生する)場合は、これは本アプリの信頼性に直結する重大な問題であるため、修正を打ち切って停止し、人間に報告する。他のテストで代替して先に進んではならない。

---

## U003-T2: 予約作成Service層実装

### 【目的】

* U003-T1のRepository層を使い、`docs/P002-frontend-spec.md` 3.3節の全バリデーションルールと収容人数チェックを実装する。

### 【作成・編集対象ファイル】

* `server/app/services/reservation_service.py`(`create_reservation`, `list_reservations`, `list_participant_candidates`)
* `server/tests/test_reservation_service.py`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 3.3節(バリデーションルール)、4.7節(サーバー側バリデーション、重複時409)
* `docs/P003-backend-spec.md` 4.6〜4.9.2節(収容人数チェック、参加者一括保存)

### 【実装内容】

* `create_reservation(room_id, date, start_time, end_time, title, participant_user_ids, attendee_count, notes, organizer_user_id)`:
  1. `room_repository.find_by_id` で会議室取得。存在しない/無効なら `NotFoundError`。
  2. `title` 必須・最大100文字、`notes` 最大500文字、`end_time > start_time` を検証。違反時 `ValidationError`。
  3. `attendee_count` が指定されていれば1以上の整数かつ `room.capacity` 以下であることを検証(超過時 `ValidationError(fields={"attendee_count": "選択した会議室の収容人数(N名)を超えています"})`)。
  4. `begin_immediate_transaction` 内で `find_overlapping` を実行し、1件でもあれば `ReservationConflictError` を送出してロールバックする。
  5. 重複が無ければ `create` を呼び出し、参加者を保存してコミットする。
* `list_reservations(date_from, date_to, room_ids)`: `find_by_range` を呼び出すだけの薄いラッパー。
* `list_participant_candidates()`: `docs/P002-frontend-spec.md` 4.10.1節の一般ユーザー向け参加者候補一覧(有効なユーザーの `employee_id`・`name` のみ)を返す。内部実現(認可・Repository層)は `docs/P003-backend-spec.md` 4.10節参照。

### 【実装してはいけないこと】

* APIルーティング・ステータスコードのマッピングはこのタスクに含めない(U003-T3の範囲)。

### 【Unit Test内容】

* テスト対象: `reservation_service.py`
* 正常系: バリデーションを満たす予約の作成、期間指定での一覧取得、参加者候補一覧の取得
* 主要な異常系: 件名未入力、件名101文字、終了時刻が開始時刻以前、参加予定人数が収容人数超過、存在しない会議室ID、重複する時間帯での作成(`ReservationConflictError`)
* 実行するテストコマンド: `cd server && python -m pytest tests/test_reservation_service.py -v`
* 合格条件: 全件PASS

### 【実行コマンド】

* `cd server && python -m pytest tests/test_reservation_service.py -v`

### 【完了条件】

* 上記Unit TestがすべてPASSする

### 【次タスクに進む前の停止条件】

* 3回自己修正しても通らない場合は停止し、人間に報告する

---

## U003-T3: 予約作成・一覧・参加者候補APIハンドラ実装

### 【目的】

* U003-T2のService層を使い、`POST /api/reservations`, `GET /api/reservations`, `GET /api/users/directory` を実装する。

### 【作成・編集対象ファイル】

* `server/app/routers/reservations.py`(新規、`GET`/`POST` のみ。詳細取得・更新・削除・マイ予約はU004で追加する)
* `server/app/routers/users.py`(新規、`GET /api/users/directory` のみ。管理者用のユーザーCRUDはU005で追加する)
* `server/app/schemas/reservation.py`(`ReservationCreateRequest`, `ReservationListItemResponse`)
* `server/app/errors.py`(`ReservationConflictError` → 409 のマッピングを追加)
* `server/app/main.py`(ルーター登録)
* `server/tests/test_reservations_api.py`, `server/tests/test_users_directory_api.py`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 4.6〜4.7節、4.10.1節(参加者候補APIの外部契約。内部方針は `docs/P003-backend-spec.md` 4.10節)

### 【実装内容】

* `POST /api/reservations`: リクエストをパースし `reservation_service.create_reservation` を呼び出す。`organizer_user_id` は `Depends(get_current_user)` から取得する(リクエストボディには含めない)。成功時201。
* `GET /api/reservations`: `date_from`・`date_to`(必須)、`room_id`(複数可、任意)をクエリから取得し `reservation_service.list_reservations` を呼び出す。`date_from > date_to` は400。
* `GET /api/users/directory`: `Depends(get_current_user)` のみ要求(管理者限定にしない、`docs/P003-backend-spec.md` 4.10節のとおり)。

### 【実装してはいけないこと】

* `GET /api/reservations/{id}`, `PUT`, `DELETE`, `GET /api/reservations/mine` はこのタスクに含めない(U004の範囲)。

### 【Unit Test内容】

* テスト対象: `POST/GET /api/reservations`, `GET /api/users/directory`
* 正常系: 予約作成(201)、期間指定一覧取得(200、`room_name`・`organizer_name` を含み `attendee_count`/`notes` を含まないこと)、参加者候補一覧取得(200)
* 主要な異常系: 未ログインでの各APIアクセスが401、バリデーション違反が400(fields付き)、重複時間帯での作成が409、存在しない会議室での作成が404、`date_from > date_to` が400
* 実行するテストコマンド: `cd server && python -m pytest tests/test_reservations_api.py tests/test_users_directory_api.py -v`
* 合格条件: 全件PASS

### 【実行コマンド】

* `cd server && python -m pytest tests/test_reservations_api.py tests/test_users_directory_api.py -v`

### 【完了条件】

* 上記Unit TestがすべてPASSする

### 【次タスクに進む前の停止条件】

* 3回自己修正しても通らない場合は停止し、人間に報告する

---

## U003-T4: S02予約カレンダー画面実装

### 【目的】

* `docs/P002-frontend-spec.md` 3.2節にもとづき会議室×時間帯グリッドを実装する。

### 【作成・編集対象ファイル】

* `client/src/pages/CalendarPage.tsx`
* `client/src/components/RoomTimeGrid.tsx`(会議室を列、08:00-20:00を30分刻みの行としたグリッド)
* `client/src/api/reservationApi.ts`(`listReservations`, `listRooms` の呼び出しラッパー)
* `client/src/App.tsx`(ログイン後のルート `/` をこのページに差し替え、ヘッダー(マイ予約リンク、管理者のみ会議室管理リンク、ログアウトボタン)を実装する)
* `client/tests/CalendarPage.test.tsx`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 3.2節(グリッド仕様、動作)

### 【実装内容】

* 週の前後移動コントロール、会議室フィルタ(複数選択)を実装する。
* グリッド描画時に `GET /api/reservations` を呼び出し、予約済みセルに予約者名・件名を表示する(3.2節、参加予定人数は表示しない)。
* 空きセルのクリックでS03へ遷移(会議室・日時を引き継ぐ)、自分に関係する予約セルのクリックでS04へ遷移する土台(S04自体はU004で実装するため、このタスクではルーティングのみ用意する)。

### 【実装してはいけないこと】

* S03(予約作成画面)の本実装はこのタスクに含めない(U003-T5の範囲)。S04の本実装はこのタスクに含めない(U004の範囲)。

### 【Unit Test内容】

* テスト対象: `CalendarPage`, `RoomTimeGrid`
* 正常系: 予約一覧取得結果がグリッドの該当セルに表示されること、参加予定人数がセル表示に含まれないこと
* 主要な異常系: API呼び出し失敗時にエラー表示すること
* 実行するテストコマンド: `cd client && node --import tsx --test tests/CalendarPage.test.tsx`
* 合格条件: 全件PASS

### 【実行コマンド】

* `cd client && node --import tsx --test tests/CalendarPage.test.tsx`

### 【完了条件】

* 上記Unit TestがすべてPASSする

### 【次タスクに進む前の停止条件】

* 3回自己修正しても通らない場合は停止し、人間に報告する

---

## U003-T5: S03予約作成画面実装

### 【目的】

* `docs/P002-frontend-spec.md` 3.3節にもとづき予約作成フォームを実装する。

### 【作成・編集対象ファイル】

* `client/src/pages/ReservationCreatePage.tsx`
* `client/src/api/reservationApi.ts`(`createReservation`, `listParticipantCandidates` を追加)
* `client/src/App.tsx`(ルート `/reservations/new` を追加)
* `client/tests/ReservationCreatePage.test.tsx`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 3.3節(全項目のバリデーションルール、終日チェックボックスの自動入力仕様、重複エラー表示)

### 【実装内容】

* 会議室(プルダウン)、日付、開始/終了時刻、終日チェックボックス(チェック時09:00/18:00を自動入力、以後手動編集可)、件名、参加者(複数選択、`GET /api/users/directory` の結果を使用)、参加予定人数(会議室選択時に収容人数を保持しクライアント側でも即時検証)、備考を実装する。
* 送信時のクライアント側バリデーションと、サーバー側409(重複)受信時のエラー表示(3.3節「重複エラーメッセージ」)、入力内容の保持を実装する。

### 【実装してはいけないこと】

* S02からの遷移元ロジック自体はU003-T4側の範囲(このタスクでは受け取ったクエリパラメータを初期値に反映するだけ)。

### 【Unit Test内容】

* テスト対象: `ReservationCreatePage`
* 正常系: 全項目入力後の送信でAPIが正しい引数で呼ばれること、終日チェックボックスON時に開始09:00/終了18:00が自動入力されること
* 主要な異常系: 件名未入力・101文字でのエラー表示、参加予定人数が収容人数超過でのエラー表示、API側409受信時の重複エラーメッセージ表示と入力保持
* 実行するテストコマンド: `cd client && node --import tsx --test tests/ReservationCreatePage.test.tsx`
* 合格条件: 全件PASS

### 【実行コマンド】

* `cd client && node --import tsx --test tests/ReservationCreatePage.test.tsx`

### 【完了条件】

* 上記Unit TestがすべてPASSする

### 【次タスクに進む前の停止条件】

* 3回自己修正しても通らない場合は停止し、人間に報告する

---

## U003-T6: S02/S03とAPIの接続確認

### 【目的】

* 会議室選択→カレンダー表示→予約作成→カレンダーへの反映、および重複エラー表示までの一連の流れを、結合確認用の薄いタスクとして確認する(スプリント内結合テストの本体は `docs/P008-test-direction.md` で別途行う)。

### 【作成・編集対象ファイル】

* 変更対象ファイルなし(疎通確認のみ)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 3.2〜3.3節

### 【実装内容】

* `server/`・`client/` を同時起動し、「S02で空きセルをクリック→S03に遷移し会議室・日時が引き継がれている→登録→S02に戻り予約が反映されている→同じ時間帯に別の予約を試みて重複エラーが表示される」を手動確認する。

### 【実装してはいけないこと】

* このタスクで新たな機能追加は行わない。不具合発見時は該当タスク(U003-T1〜T5)に戻って修正する。

### 【Unit Test内容】

* このタスク自体はUnit Testの追加を行わない(疎通確認のみ)。

### 【実行コマンド】

* `cd server && uvicorn app.main:app --reload`
* `cd client && npm run dev`

### 【完了条件】

* 上記の一連の操作が例外・エラーなく完了し、重複エラーが正しく表示されること

### 【次タスクに進む前の停止条件】

* 疎通確認中に発見した不具合が3回試行しても解消しない場合は停止し、人間に報告する

---

## U003-T7: CR-001: オンライン会議URL — バックエンド(スキーマ・バリデーション・API)

### 【目的】

* `docs/P901-cr-direction/CR-001.md`・`docs/P903-cr-records/CR-001.md` にもとづき、`POST /api/reservations` のリクエスト/レスポンスに `meeting_url`(オンライン会議URL)項目を追加する。`docs/P003-backend-spec.md` 2.2/3章の `reservations.meeting_url` カラム(マイグレーション `003_add_reservation_meeting_url.sql`、P903内側のP002/P003で追加済み)を実際に読み書きできるようにする。

### 【作成・編集対象ファイル】

* `server/app/schemas/reservation.py`(`ReservationCreateRequest`・`ReservationDetailResponse` に `meeting_url: str | None = None` を追加)
* `server/app/repositories/reservation_repository.py`(`create`・`find_by_id` に `meeting_url` を追加)
* `server/app/services/reservation_service.py`(`_validate` に `meeting_url` のバリデーションを追加、`create_reservation` で受け取り・保存・レスポンスに反映)
* `server/app/routers/reservations.py`(`create_reservation` ハンドラで `body.meeting_url` をService層に渡す)
* `server/tests/test_reservation_repository.py`、`server/tests/test_reservation_service.py`、`server/tests/test_reservations_api.py`(追加テスト)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 3.3節(バリデーションルール: `http://`/`https://` 始まり・最大500文字)、4.7節(リクエスト/レスポンスへの `meeting_url` 追加)
* `docs/P003-backend-spec.md` 2.2節(カラム定義)、4.6〜4.9.2節(バリデーション詳細)

### 【実装内容】

* `ReservationCreateRequest`・`ReservationDetailResponse` に `meeting_url: str | None = None` を追加する(`ReservationListItemResponse`・`MyReservationListItemResponse` には追加しない。`docs/P002-frontend-spec.md` 4.6節のとおり一覧レスポンスは意図的に含めないため)。
* `reservation_service._validate` に `meeting_url: str | None` パラメータを追加し、値が空文字列・`None` でない場合のみ次を検証する。
  1. `http://` または `https://` で始まること。違反時 `fields["meeting_url"] = "オンライン会議URLは http:// または https:// で始めてください"`
  2. 500文字以内であること。違反時 `fields["meeting_url"] = "オンライン会議URLは500文字以内で入力してください"`
* `create_reservation`: `meeting_url` パラメータを受け取り、空文字列は `None` に正規化してから `_validate` に渡し、`reservation_repository.create` に渡して保存し、レスポンス辞書にも含める。
* `reservation_repository.create`・`find_by_id` の SQL に `meeting_url` カラムを追加する(`create` はINSERT列、`find_by_id` はSELECT列)。
* `get_reservation`(Service層)が返す辞書にも `reservation["meeting_url"]` を含める(`find_by_id` がカラムを返すようになるため、辞書内包表記に1行追加するだけでよい)。

### 【実装してはいけないこと】

* `GET /api/reservations`(一覧)のレスポンスに `meeting_url` を追加しない(`docs/P002-frontend-spec.md` 4.6節で意図的に除外)。
* `PUT /api/reservations/{id}`(更新)・S04関連の変更はこのタスクに含めない(U004-T6の範囲)。

### 【Unit Test内容】

* テスト対象: `reservation_repository.py`(`create`/`find_by_id`)、`reservation_service.py`(`create_reservation`)、`POST /api/reservations`
* 正常系: `meeting_url` 未入力(`null`/省略)で登録成功し `null` として保存・返却される、`https://example.com/meeting/123` のような妥当な値で登録成功しレスポンスに含まれる
* 主要な異常系: `ftp://example.com`(不正スキーム)で400・`fields.meeting_url`、`example.com`(スキームなし)で400、501文字の値で400、ちょうど500文字の値では成功(境界値)
* `GET /api/reservations`(一覧)のレスポンスに `meeting_url` キー自体が含まれないことを確認するテストを1件追加する(回帰防止)
* 実行するテストコマンド: `cd server && python -m pytest tests/test_reservation_repository.py tests/test_reservation_service.py tests/test_reservations_api.py -v`
* 合格条件: 全件PASS(U003/U004分の既存テストを含め回帰なし)

### 【実行コマンド】

* `cd server && python -m pytest tests/test_reservation_repository.py tests/test_reservation_service.py tests/test_reservations_api.py -v`

### 【完了条件】

* 上記Unit TestがすべてPASSする

### 【次タスクに進む前の停止条件】

* 3回自己修正しても通らない場合は停止し、人間に報告する

---

## U003-T8: CR-001: オンライン会議URL — S03予約作成画面

### 【目的】

* S03(予約作成画面)にオンライン会議URLの入力欄とクライアント側バリデーションを追加する。

### 【作成・編集対象ファイル】

* `client/src/validation/reservationValidation.ts`(`ReservationFormValues`・`ReservationFormErrors` に `meetingUrl` を追加、バリデーション関数に検証ロジックを追加。S04と共有するため、ここに1箇所だけ実装する)
* `client/src/api/reservationApi.ts`(`ReservationDetail`・`ReservationCreateInput` に `meeting_url: string | null` を追加)
* `client/src/pages/ReservationCreatePage.tsx`(入力欄の追加、送信ペイロードへの反映)
* `client/tests/ReservationCreatePage.test.tsx`(追加テスト)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 3.3節(オンライン会議URL入力欄のバリデーションルール・エラーメッセージ)

### 【実装内容】

* `reservationValidation.ts`: `MEETING_URL_MAX_LENGTH = 500` を追加。`values.meetingUrl` が空文字列でない場合のみ、`http://`/`https://` 始まりチェックと文字数チェックを行い、違反時にU003-T7と同じ文言の `errors.meetingUrl` を設定する。
* `ReservationCreatePage.tsx`: `FormState` に `meetingUrl: string` を追加(初期値 `''`)。他の項目と同じ配置パターンでラベル・テキスト入力欄・エラー表示を追加する。送信時、`meeting_url: form.meetingUrl.trim() === '' ? null : form.meetingUrl` を `createReservation` の引数に含める。

### 【実装してはいけないこと】

* S04(`ReservationDetailPage.tsx`)側の表示・編集ロジックの変更はこのタスクに含めない(U004-T7の範囲)。ただし共有バリデーション関数(`reservationValidation.ts`)の変更はS04にも影響するため、S04側のUnitTest(`ReservationDetailPage.test.tsx`)が既存の他項目バリデーションについて回帰していないことをU004-T7側で確認する前提とする。

### 【Unit Test内容】

* テスト対象: `ReservationCreatePage`、`validateReservationForm`
* 正常系: オンライン会議URL未入力での送信成功、妥当なURL入力での送信成功(APIに正しい値で渡ること)
* 主要な異常系: `ftp://`・スキームなしでのエラー表示、501文字でのエラー表示
* 実行するテストコマンド: `cd client && node --import tsx --test tests/ReservationCreatePage.test.tsx`
* 合格条件: 全件PASS

### 【実行コマンド】

* `cd client && node --import tsx --test tests/ReservationCreatePage.test.tsx`

### 【完了条件】

* 上記Unit TestがすべてPASSする

### 【次タスクに進む前の停止条件】

* 3回自己修正しても通らない場合は停止し、人間に報告する

---

## U003-T9: CR-001: 既存回帰修正 — マイグレーションファイル一覧アサーション更新

### 【目的】

* `docs/P903-cr-records/CR-001.md`(対処内容節)に記録済みのとおり、U003-T7で新しいマイグレーションファイル(`003_add_reservation_meeting_url.sql`、P903内側のP002/P003完了時点で既に追加済み)が `server/migrations/` に加わったことで、適用済みマイグレーション一覧をハードコードしていた既存テスト2件が想定どおり不一致でFAILする。これを実際のマイグレーション一覧に合わせて更新する(CR-001の不具合ではなく、U001由来の既存テストコードが新しいマイグレーションファイルの存在を前提にしていなかったことによるもの)。

### 【作成・編集対象ファイル】

* `server/tests/test_migration.py`(`test_apply_pending_migrations_creates_schema_and_seed_admin`・`test_apply_pending_migrations_is_idempotent` の2件)

### 【参照すべき仕様箇所】

* `docs/P903-cr-records/CR-001.md`「実行したテストと結果」節(不一致の原因説明)
* `server/migrations/003_add_reservation_meeting_url.sql`

### 【実装内容】

* 上記2テストの `applied == [...]` / `applied_versions(conn) == {...}` / `migration_count == 2` を、`003_add_reservation_meeting_url` を含む3件の一覧・件数に更新する。

### 【実装してはいけないこと】

* `app/db/migration.py`(マイグレーション実行処理本体)は変更しない。今回の不一致はテスト側のハードコードが原因であり、実装側に欠陥は無い(`docs/P903-cr-records/CR-001.md` で確認済み)。
* `test_apply_pending_migrations_rolls_back_on_syntax_error`(3件目のテスト、一時ディレクトリを使うため無関係)は変更しない。

### 【Unit Test内容】

* テスト対象: `test_migration.py`
* 正常系: 更新後の2テストがPASSすること
* 実行するテストコマンド: `cd server && python -m pytest tests/test_migration.py -v`
* 合格条件: 全件PASS

### 【実行コマンド】

* `cd server && python -m pytest tests/test_migration.py -v`

### 【完了条件】

* 上記Unit TestがすべてPASSする

### 【次タスクに進む前の停止条件】

* 3回自己修正しても通らない場合は停止し、人間に報告する

---

## 重要

* 各タスクの範囲外のファイルは編集しないでください。
* タスクの実装後、実行したテストコマンドと結果を報告してください。
* タスクが完了したら、上記「タスク一覧」の該当行を `[x]` に更新してください。
* 全タスクが完了したら、`docs/P007-impl-direction.md` の本スプリント行を `[x]` に更新してください。
* Executor Stepの停止条件に該当しない限り、次のタスクに自動的に進んでください。
