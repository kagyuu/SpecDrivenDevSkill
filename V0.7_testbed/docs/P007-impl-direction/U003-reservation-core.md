あなたはExecutor(実装担当)です。以下は Sprint 3 `reservation-core` の作業範囲と完了条件を、タスク単位に分けて定義したものです。各タスクを記載順に実施し、実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P007-impl-direction.md` のWBSに従って自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# スプリント U003 — reservation-core(予約コア)

* 位置づけ: 本システムの中核。予約のデータモデルと6本のAPI、重複チェックと排他制御。`docs/P005-impl-plan.md` 2.3 を参照。
* 実装対象: `reservations` / `reservation_attendees`、API-12〜API-17。**画面はこのスプリントでは実装しない**(Sprint 4の担当)。
* 前提: Sprint 1・2(U001・U002)が完了していること。
* このスプリント全体の共通の禁止事項: 画面ファイル(`client/src/views/s02〜s05`)を作らないこと。P002・P003にない業務ルール(例: 予約可能な最大日数、1人あたりの予約上限)を追加しないこと。

---

# 【タスクID】U003-T1 — `reservations` / `reservation_attendees` のマイグレーションと Repository

## 【目的】

* 予約のデータモデルを作成し、カレンダー表示・重複チェックに必要なインデックスを用意する。

## 【作成・編集対象ファイル】

* `server/migrations/003-reservations.sql`(新規)
* `server/src/meeting_room/repositories/reservations_repo.py`(新規)
* `server/tests/test_reservations_repo.py`(新規)

## 【参照すべき仕様箇所】

* P002 6.2(`reservations` / `reservation_attendees` のテーブル定義)、5.3(`Reservation` の表現)
* P003 3.4(インデックス)、3.5(マイグレーションの作法)、5.2(判定SQL)

## 【実装内容】

* `003-reservations.sql`:
  * `reservations`(`reservation_id` INTEGER PK AUTOINCREMENT、`room_id` NOT NULL REFERENCES `rooms`、`user_id` NOT NULL REFERENCES `users`、`reserved_date` NOT NULL、`start_time` NOT NULL、`end_time` NOT NULL CHECK(`end_time` > `start_time`)、`title` NOT NULL、`attendee_count` INTEGER NULL CHECK(`attendee_count` IS NULL OR (`attendee_count` BETWEEN 1 AND 9999))、`note` NOT NULL DEFAULT ''、`created_at`、`updated_at`)。
  * `reservation_attendees`(`reservation_id` REFERENCES `reservations` **ON DELETE CASCADE**、`user_id` REFERENCES `users`、複合主キー)。
  * インデックス `idx_reservations_room_date` / `idx_reservations_date` / `idx_reservations_user_date`。
* **既存のマイグレーションファイルは編集しない。**
* `reservations_repo.py`:
  * `find_by_id(conn, reservation_id)`(`rooms`・`users` と JOIN して `room_name` / `user_name` を含める)
  * `list_by_period(conn, date_from, date_to, room_ids=None)`(同上JOIN、並びは `reserved_date, start_time, room_id`)
  * `list_by_user(conn, user_id, period)`(`upcoming` は `reserved_date >= :today` 昇順、`past` は `< :today` 降順)
  * `find_conflicts(conn, room_id, reserved_date, start_time, end_time, exclude_reservation_id=None)` — **P003 5.2 のSQLをそのまま用いる**
  * `count_future(conn, room_id, today)`(`reserved_date >= today` の件数)
  * `insert` / `update` / `delete`
  * `replace_attendees(conn, reservation_id, user_ids)` / `list_attendees(conn, reservation_id)`(`users` と JOIN して `user_id` と `name` を返す)

## 【実装してはいけないこと】

* 予約の論理削除(仕様は物理削除。P002 5.7 API-17)。
* 重複チェックのSQLをP003 5.2と異なる条件で書くこと(境界一致を重複と誤判定する `<=` を使わない)。

## 【Unit Test内容】

* テスト対象: `003-reservations.sql` の適用、`reservations_repo`
* 正常系: 全マイグレーション適用後に `reservations` / `reservation_attendees` が存在し、再適用しても `schema_migrations` の行数が増えない。`insert` → `find_by_id` が `room_name`・`user_name` を含んで返る。`replace_attendees` で2件→1件に置き換わる。`delete` で参加者行も消える(CASCADE)。`list_by_period` の並び順。`list_by_user('upcoming')` に過去日が含まれない。
* 異常系(**重複判定の境界値。最重要**): 既存予約 09:00-10:00 に対し `find_conflicts` が、
  * 09:00-10:00(完全一致)→ 1件
  * 09:30-10:30(後方部分重複)→ 1件
  * 08:30-09:30(前方部分重複)→ 1件
  * 09:15-09:45(内包)→ 1件 ※30分刻み制約は上位層の責務なので、Repository単体では任意の時刻で検証してよい
  * 08:00-11:00(被内包)→ 1件
  * **10:00-11:00(境界接触・後)→ 0件**
  * **08:00-09:00(境界接触・前)→ 0件**
  * 別の `room_id` → 0件 / 別の `reserved_date` → 0件
  * `exclude_reservation_id` に自身を指定 → 0件
  * `end_time <= start_time` の行のINSERT → CHECK制約違反
* 実行コマンド: `cd server && python3 -m unittest discover -s tests -t .`
* 合格条件: 上記すべてPASS(特に境界接触の2件が0件になること)。

## 【実行コマンド】

* `cd server && python3 -m unittest discover -s tests -t .`

## 【完了条件】

* 単体テストが全件PASS。既存DBに対する再起動でマイグレーションが差分適用されること。

## 【次タスクに進む前の停止条件】

* 単体テストが3回自己修正しても合格しない場合は、処理を停止して人間に報告する。

---

# 【タスクID】U003-T2 — 予約Service(検証・重複チェック・排他制御)

## 【目的】

* 予約の登録・更新・取消に必要な業務ルールを1か所に集約し、同時リクエストでも重複を通さないようにする。

## 【作成・編集対象ファイル】

* `server/src/meeting_room/schemas.py`(編集: `ReservationRequest` を追加)
* `server/src/meeting_room/services/reservation_service.py`(新規)
* `server/tests/test_reservation_service.py`(新規)

## 【参照すべき仕様箇所】

* P002 3.3(S03の入力ルール。30分刻み、業務時間08:00〜20:00、本日以降)、3.4(S04の編集ルール)、5.2(エラーコード)、5.7(API-15/16/17の外部契約)
* P003 **5(重複チェックと排他制御の全体)**、6.4(API-15/16/17の内部処理)、4.5(トランザクション)

## 【実装内容】

* `schemas.py` に `ReservationRequest`: `room_id`(整数必須)、`reserved_date`(`^\d{4}-\d{2}-\d{2}$`)、`start_time` / `end_time`(`^([01]\d|2[0-3]):[0-5]\d$`)、`title`(1〜100文字)、`attendee_user_ids`(既定 `[]`、最大50、重複不可)、`attendee_count`(NULL可、1〜9999)、`note`(0〜500文字)。エラーメッセージはP002 3.3の文言。
* `reservation_service.py`:
  * `_validate_business(conn, req, today)`: 次を順に検証する。
    1. 時刻が30分刻み(分が `00` または `30`)、`08:00 <= start < end <= 20:00` → 違反は 400 `VALIDATION_ERROR`。
    2. `reserved_date >= today` → 過去日は 400 `VALIDATION_ERROR`(`field="reserved_date"`、「過去の日付には予約できません。」)。
    3. `room_id` が存在し `is_active=1` → 不成立は 400 `VALIDATION_ERROR`(`field="room_id"`)。
    4. `attendee_count` が指定されていて会議室の `capacity` を超える → **400 `CAPACITY_EXCEEDED`**(メッセージにcapacityを含める)。
    5. `attendee_user_ids` が全て存在し `is_active=1` → 不成立は 400 `VALIDATION_ERROR`(`field="attendee_user_ids"`)。
  * `create(conn, actor, req)`: `BEGIN IMMEDIATE` の中で `_validate_business` → `find_conflicts`(1件以上なら `ApiError(409, "RESERVATION_CONFLICT", "選択した時間帯はすでに予約されています。", extra={"conflicts": [最大5件]})`)→ INSERT → `replace_attendees` → 詳細を返す。予約者は必ず `actor.user_id`(リクエスト値を信用しない)。
  * `update(conn, actor, reservation_id, req)`: `BEGIN IMMEDIATE` → 対象取得(なければ404)→ **予約者本人でも管理者でもなければ 403 `FORBIDDEN`** → 対象の `reserved_date` が過去日なら 409 `CONSTRAINT_VIOLATION`(「過去の予約は編集できません。」)→ `_validate_business` → `find_conflicts(exclude_reservation_id=reservation_id)` → UPDATE → `replace_attendees`。
  * `delete(conn, actor, reservation_id)`: `BEGIN IMMEDIATE` → 対象取得(なければ404)→ 権限判定(403)→ 過去日なら 409 → 参加者を削除 → 予約を削除。
  * `sqlite3.OperationalError`(`database is locked`)を捕捉し、`ApiError(500, "INTERNAL_ERROR", ...)` に変換してログに `error_code=DB_LOCK_TIMEOUT` を残す(P003 5.3)。
* `room_service.count_future_reservations` を `reservations_repo.count_future` を呼ぶ**本実装に差し替え**、TODOコメントを削除する(`docs/P005-impl-plan.md` 5章 リスク#5)。

## 【実装してはいけないこと】

* 重複チェックとINSERTを別トランザクションに分けること(TOCTOUになる)。
* Pythonの `threading.Lock` による直列化(P003 5.3 が明確に否定している)。
* 重複時に既存予約を上書きする、あるいは自動的に別の時間帯を提案すること。

## 【Unit Test内容】

* テスト対象: `ReservationRequest`、`reservation_service`
* 正常系: 登録 → 予約が作られ、`user_id` がリクエストではなくセッションのユーザーになる。参加者が保存される。更新で同じ時間帯のまま件名だけ変更できる(自己除外)。取消で行と参加者行が消える。管理者は他人の予約を更新・取消できる。
* 異常系:
  * 件名101文字 / 空、備考501文字、参加者51件、参加者重複 → 400 `VALIDATION_ERROR`。
  * `start_time="09:15"`(30分刻み違反)、`start_time="07:30"` / `end_time="20:30"`(業務時間外)、`end_time <= start_time` → 400。
  * 昨日の日付 → 400(`field="reserved_date"`)。
  * 存在しない `room_id` / 無効な会議室 → 400(`field="room_id"`)。
  * `attendee_count` が `capacity`+1 → **400 `CAPACITY_EXCEEDED`**、`capacity` ちょうど → 成功。
  * 無効ユーザーを参加者に指定 → 400。
  * 重複する時間帯 → 409 `RESERVATION_CONFLICT` かつ `extra.conflicts` に既存予約が含まれる。境界接触(10:00-11:00)→ 成功。
  * 第三者(予約者でも管理者でもない)による更新・取消 → 403 `FORBIDDEN`。
  * 存在しない `reservation_id` → 404。
  * 過去日の予約の更新・取消 → 409 `CONSTRAINT_VIOLATION`。
* 同時実行: 同じ会議室・同じ時間帯への `create` を2スレッドから同時に実行し、**必ず一方だけが成功し、他方が 409 になること**(片方が500 `INTERNAL_ERROR`(ロックタイムアウト)になった場合もFAILとする)。
* 実行コマンド: `cd server && python3 -m unittest discover -s tests -t .`
* 合格条件: 上記すべてPASS。

## 【実行コマンド】

* `cd server && python3 -m unittest discover -s tests -t .`

## 【完了条件】

* 単体テストが全件PASS。
* `room_service.count_future_reservations` のTODOが解消されていること。

## 【次タスクに進む前の停止条件】

* 単体テストが3回自己修正しても合格しない場合は、処理を停止して人間に報告する。

---

# 【タスクID】U003-T3 — 予約の参照系API(API-12・API-13・API-14)

## 【目的】

* カレンダー・マイ予約・詳細のためのGET系APIを完成させる。ルーティングの順序に起因する不具合をここで防ぐ。

## 【作成・編集対象ファイル】

* `server/src/meeting_room/handlers/reservation_handlers.py`(新規)
* `server/src/meeting_room/main.py`(編集: ルート登録)
* `server/tests/test_reservation_read_handlers.py`(新規)

## 【参照すべき仕様箇所】

* P002 5.7(API-12/13/14の外部契約。クエリパラメータと並び順)、5.3(`Reservation` の表現)
* P003 6.4(内部処理。**ルーティング順序の注意**)

## 【実装内容】

* API-12 `GET /api/reservations`: `date_from` / `date_to` 必須、`date_to >= date_from`、期間は最大31日(超過は 400 `VALIDATION_ERROR`)。`room_id` は繰り返し可(未指定なら全件)。`attendees` は**空配列**を返す(一覧の軽量化。P002 5.7)。
* API-13 `GET /api/reservations/mine`: `period` は `upcoming`(既定)/ `past` のみ。それ以外は 400。
* API-14 `GET /api/reservations/{reservation_id}`: `attendees` を含めて返す。閲覧は全ログインユーザーに許可(権限による制限をかけない)。存在しなければ 404。
* `main.py`: **`/api/reservations/mine` を `/api/reservations/{reservation_id}` より先に登録する**(P003 6.4)。
* すべて `require_login`。

## 【実装してはいけないこと】

* API-14に予約者・管理者限定の制限をかけること(閲覧は全員可)。
* API-12で予約ごとに追加クエリを発行すること(N+1。P003 8章の性能前提に反する)。

## 【Unit Test内容】

* テスト対象: 3本のハンドラ
* 正常系: 期間指定で該当予約のみが `reserved_date, start_time, room_id` 昇順で返る。`room_id` 指定で絞られる。`mine?period=upcoming` が本日以降のみを昇順で、`past` が本日より前のみを降順で返す。`GET /api/reservations/mine` が**予約IDとして解釈されず**正しく一覧を返す(ルーティング順序の確認)。API-14が `attendees` と `room_name` / `user_name` を含む。他人の予約もAPI-14で閲覧できる。
* 異常系: `date_from` 欠落 / `date_to < date_from` / 32日間 → 400。`period=future` → 400。存在しない予約ID → 404。未認証 → 401。
* 実行コマンド: `cd server && python3 -m unittest discover -s tests -t .`
* 合格条件: 上記すべてPASS。

## 【実行コマンド】

* `cd server && python3 -m unittest discover -s tests -t .`

## 【完了条件】

* 単体テストが全件PASS。

## 【次タスクに進む前の停止条件】

* 単体テストが3回自己修正しても合格しない場合は、処理を停止して人間に報告する。

---

# 【タスクID】U003-T4 — 予約の更新系API(API-15・API-16・API-17)

## 【目的】

* 予約の登録・更新・取消のHTTP層を完成させ、Sprint 3 を閉じる。

## 【作成・編集対象ファイル】

* `server/src/meeting_room/handlers/reservation_handlers.py`(編集)
* `server/src/meeting_room/main.py`(編集: ルート登録)
* `server/tests/test_reservation_write_handlers.py`(新規)

## 【参照すべき仕様箇所】

* P002 5.7(API-15/16/17。ステータスコードと409の応答形式)、5.2
* P003 6.4

## 【実装内容】

* API-15 `POST /api/reservations` → 成功時 **201** + `{"reservation": ...}`。
* API-16 `PUT /api/reservations/{reservation_id}` → 成功時 200。
* API-17 `DELETE /api/reservations/{reservation_id}` → 成功時 **204**(本文なし)。
* 409 `RESERVATION_CONFLICT` の本文に `conflicts`(`reservation_id` / `start_time` / `end_time`)を含める(P002 5.7)。
* すべて `require_login`。権限判定(予約者本人または管理者)は `reservation_service` 側で行う。

## 【実装してはいけないこと】

* リクエストボディの `user_id` を予約者として採用すること(必ずセッションのユーザー)。
* 部分更新(PATCH相当)の実装(仕様は全置換更新)。

## 【Unit Test内容】

* テスト対象: 3本のハンドラ
* 正常系: 登録が201でLocationに依存しないレスポンス形状、更新が200、取消が204で本文が空。取消後にAPI-14が404。
* 異常系: 重複登録 → 409 かつ本文に `error.conflicts` が含まれ、各要素が `reservation_id` / `start_time` / `end_time` を持つ。`attendee_count` 超過 → 400 `CAPACITY_EXCEEDED`。第三者の更新・取消 → 403。存在しないID → 404。未認証 → 401。
* 実行コマンド: `cd server && python3 -m unittest discover -s tests -t .`
* 合格条件: 上記すべてPASS。

## 【実行コマンド】

* `cd server && python3 -m unittest discover -s tests -t .`
* `cd client && node --test tests`(退行がないことの確認)

## 【完了条件】

* 単体テストが全件PASS。
* API-12〜API-17の6本がP002 5.7の契約どおり応答すること。
* Sprint 3 の全タスク(T1〜T4)が完了したら、`docs/P007-impl-direction.md` の `U003` 行のチェックボックスを `[x]` に更新する。

## 【次タスクに進む前の停止条件】

* 単体テストが3回自己修正しても合格しない場合は、処理を停止して人間に報告する。

# 【タスクID】U003-T5 — ※CR-001 オンライン会議URL(`meeting_url`)の列追加とAPI反映

## 【目的】

* CR-001(`docs/P901-cr-direction/CR-001.md`)にもとづき、予約にオンライン会議URLを任意項目として保持できるようにする。バックエンド側(マイグレーション・スキーマ検証・Repository・API-12〜API-16の応答)を対象とする。

## 【作成・編集対象ファイル】

* `server/migrations/004-meeting-url.sql`(新規)
* `server/src/meeting_room/schemas.py`(`ReservationRequest` に `meeting_url` を追加)
* `server/src/meeting_room/repositories/reservations_repo.py`(`_SELECT` / `to_reservation_dict` / `insert` / `update`)
* `server/src/meeting_room/services/reservation_service.py`(`insert` / `update` への受け渡しのみ)
* `server/tests/test_reservations_repo.py`・`server/tests/test_reservation_service.py`・`server/tests/test_reservation_write_handlers.py`・`server/tests/test_reservation_read_handlers.py`・`server/tests/test_db_migration.py`(単体テストの追加)

## 【参照すべき仕様箇所】

* P002 3.3(オンライン会議URLの入力ルールと検証仕様)、3.4(S04の表示)、5.3(`Reservation` の `meeting_url`)、5.7 API-15/API-16、6.2(`reservations` の列定義)
* P003 3.5(マイグレーションの作法・`004-meeting-url.sql`)、4.2(スキーマ検証)、6.4(API-15/16の内部処理)

## 【実装内容】

* `004-meeting-url.sql`: `ALTER TABLE reservations ADD COLUMN meeting_url TEXT NOT NULL DEFAULT '';` の1文のみ。
* `schemas.ReservationRequest` に `meeting_url: Any = ""` を追加し、`field_validator` で次を検証する。
  * `None` / 空文字 / キー欠落 → `""`(エラーとしない)
  * 500文字超 → 「オンライン会議URLは500文字以内で入力してください。」
  * `http://` `https://` のいずれでも始まらない → 「オンライン会議URLは http:// または https:// で始まるURLを入力してください。」
  * 検証順序は **P002 3.3 の規定に従い「文字数 → スキーム」の順**とする(両方に違反する場合は文字数のメッセージを返す。P012による明文化)
* `reservations_repo`: `_SELECT` に `r.meeting_url` を追加、`to_reservation_dict` の戻り値に `"meeting_url"` を追加、`insert` / `update` の列と引数に `meeting_url` を追加する。
* `reservation_service`: `create` / `update` から `req.meeting_url` を Repository に渡す。**業務判定(DBの状態に依存する検証)は追加しない**(P003 6.4 ※CR-001)。

## 【実装してはいけないこと】

* 適用済みの `001-init.sql` / `002-rooms.sql` / `003-reservations.sql` を編集すること。
* URLのホスト名妥当性・到達性の検証、ドメインのホワイトリスト(P002 3.3 の★ACCEPTED★のとおり前方一致のみ)。
* S02(カレンダー)の応答からの `meeting_url` の除去。`Reservation` 表現は共通であり、一覧APIにも含まれてよい(画面側で表示しないだけ)。

## 【Unit Test内容】

* テスト対象: `004-meeting-url.sql` の適用、`schemas.ReservationRequest`、`reservations_repo`、`reservation_service`、予約系ハンドラ
* 正常系: 未指定・空文字・`http://...`・`https://...`・500文字ちょうど(`https://` + 492文字)が通ること。`insert` → `find_by_id` で値が往復すること。API-15の201応答とAPI-14の200応答に `meeting_url` が含まれること。API-16で空文字を送るとURLが消えること。
* 異常系: 501文字 → 400 `VALIDATION_ERROR`(`field="meeting_url"`)。`example.com/meet`(スキームなし)→ 400。`ftp://example.com` → 400。`HTTP://example.com`(大文字スキーム)→ 400(★FIXME★ 大文字スキームの扱いはCR-001・P002 3.3に指定がないため、前方一致の文字どおりの解釈として**エラー**とした)。
* マイグレーション: 全4ファイル適用後に `reservations` に `meeting_url` 列が存在すること。**同一DBに対して `apply_migrations()` を2回呼んでも2回目が成功し、`schema_migrations` が4行のままであること**(`ADD COLUMN` は `IF NOT EXISTS` を持たないため、この確認は必須。P006 3.3 V-O-01/V-O-02)。
* 既存行の互換性: `004` 適用前に投入した予約行が、適用後に `meeting_url = ''` として読めること。
* 実行コマンド: `cd server && python3 -m unittest discover -s tests -t .`
* 合格条件: 上記すべてPASS。既存の240件の単体テストが1件も退行しないこと。

## 【実行コマンド】

* `cd server && python3 -m unittest discover -s tests -t .`

## 【完了条件】

* 単体テストが全件PASS。
* API-14/15/16 の応答に `meeting_url` が含まれ、検証ルールがP002 3.3と一致すること。

## 【次タスクに進む前の停止条件】

* 単体テストが3回自己修正しても合格しない場合は、処理を停止して人間に報告する。

---

---

## 重要

* このスプリントの範囲外のファイルは編集しないでください。
* 実装後、実行したテストコマンドと結果を報告してください。
* このスプリントが完了したら、Executor Stepの停止条件に該当しない限り、次のスプリント(`U004-reservation-ui.md`)に自動的に進んでください。1タスクごとに人間の指示を待つ必要はありません。
