あなたはExecutor(実装担当)です。このスプリント(U007: cr-003-attendee-count)には2個のタスク(U007-1・U007-2)があります。このタスクを実施したら、Executor Stepの停止条件に該当しない限り自動的に次のタスクへ進んでください。

前提: U001〜U006(既存)が完了していること。
本スプリントは通常の新規スプリントではなく、変更要求 `docs/CR.md` CR-003(反映後は `docs/cr-records/CR-003.md`)に対応する差分実装である。既存のS03・S04実装・テストのうちCR-003と無関係な部分は変更しないこと。
参照する仕様書: `docs/P001-requirement.md`「S03 予約作成画面」「S04 予約詳細・編集画面」(※CR-003により追加の行)、`docs/P002-frontend-spec.md` §3 S02/S03/S04・§4.8〜§4.12(※CR-003により追記)、`docs/P003-backend-spec.md` §6.3・§6.4・§7.9〜§7.12(※CR-003により追記)、`docs/P006-test-plan.md` S02/S03/S04行・§3 運用(再起動耐性)(※CR-003により追記)。

実装するテストコードの関数名・ファイルパスは、`docs/P008-test-direction/T024-reservation-attendee-count-create-and-fetch.md`・`T025-reservation-attendee-count-update.md`・`T026-reservation-attendee-count-exceeds-capacity.md`・`T027-my-reservations-includes-attendee-count.md`・`T028-db-init-idempotency-after-restart.md` が【実行コマンド】に明記する関数名・クラス名と厳密に一致させること(P102ルール)。

---

# 【タスクID】U007-1(バックエンド)

## 【目的】

* `RESERVATIONS` テーブルに `attendee_count` カラムを追加し、`POST /api/reservations`・`PUT /api/reservations/{reservation_id}` のリクエストと、`GET /api/reservations/{reservation_id}`・`GET /api/reservations/mine` のレスポンスに `attendee_count` を含める。
* 参加予定人数が予約先会議室の収容人数(`ROOMS.capacity`)を超える場合に `400 VALIDATION_ERROR` とする。
* あわせて、マイグレーションの適用方式を「起動のたびに全件再実行」から「`SCHEMA_MIGRATIONS` テーブルによる差分適用」に切り替える(`docs/P003-backend-spec.md` §6.4)。

## 【作成・編集対象ファイル】

* `server/app/db/migrations/0003_add_reservation_attendee_count.sql`(新規): `ALTER TABLE RESERVATIONS ADD COLUMN attendee_count INTEGER`。
* `server/app/db/connection.py`(既存ファイルを修正): `init_db()` を差分適用方式に置き換える。`SCHEMA_MIGRATIONS`(`filename` TEXT PRIMARY KEY、`applied_at` TEXT)を `CREATE TABLE IF NOT EXISTS` で用意し、未記録のファイルのみを**1文ずつ**適用して記録する。CR-003以前の方式で構築済みのDB(`SCHEMA_MIGRATIONS` を持たず0001・0002が適用済み)からの移行を成立させるため、「既に適用済み」を意味するエラー(`duplicate column name` / `table ... already exists` / `index ... already exists`)のみを読み飛ばし、**後続の文の実行は継続する**。CR-002で入れた「例外を捕捉してファイルの残りを `continue` でスキップする」実装は削除する(残りの文が黙って読み飛ばされる問題があるため。`docs/P003-backend-spec.md` §6.4(3)参照)。
* `server/app/core/validators.py`(既存ファイルに追記): `validate_attendee_count(value)`(`None` を許容。それ以外は `bool` でない `int` かつ1以上)。
* `server/app/repositories/reservation_repository.py`(既存ファイルを修正): `insert_with_participants`/`update_with_participants` のSQLに `attendee_count` を追加(`data.get("attendee_count")`)。`find_with_detail` の返す辞書に `attendee_count` を追加。
* `server/app/services/reservation_service.py`(既存ファイルを修正): `_validate_common` に `validate_attendee_count` を追加。`_check_room_and_participants` で取得した会議室の `capacity` と `attendee_count` を比較する収容人数チェックを追加し、`create`・`update` の双方で通す。
* `server/app/api/reservations.py`(既存ファイルを修正): `list_mine` のレスポンス写像に `attendee_count` を追加する。`list_reservations`(`GET /api/reservations`)の写像は**変更しない**。
* `server/app/schemas/reservation.py`(既存ファイルに追記): `ReservationCreateRequest` に `attendee_count: int | None = None` を追加。
* `server/tests/test_db_init.py`(既存ファイルに追記): T028に対応する `DbInitIdempotencyTest` を追加する。

## 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §6.3・§6.4(データモデルと適用方式)、§7.9〜§7.12(API内部仕様)
* `docs/P002-frontend-spec.md` §4.8〜§4.12(API外部仕様)

## 【実装内容】

* `attendee_count` は任意項目。未入力時は `None`(DB上は `NULL`)として扱う。
* 収容人数チェックは Service 層に置く(理由は `docs/P003-backend-spec.md` §7.11の設計判断を参照)。エラーは `ValidationError`(`details[].field = "attendee_count"`)とする。
* `PUT` は全量更新のため、`attendee_count` が省略された場合は `null` で上書きする。
* 収容人数と等しい値は許容する(`attendee_count > capacity` のときのみエラー)。

## 【実装してはいけないこと】

* `GET /api/reservations`(S02カレンダー用の一覧API)のレスポンスに `attendee_count` を追加すること(`docs/CR.md` CR-003「影響が想定される範囲」のとおりスコープ外)。
* `attendee_count` をAPIの必須項目にすること。
* 参加者(`participant_ids`)の件数と `attendee_count` を連動させること(`docs/P002-frontend-spec.md` §3 S03の★FIXME★のとおり、両者は独立した項目とする)。

## 【Unit Test内容】

* テスト対象: `validate_attendee_count`(`server/tests/test_validators.py`)、`reservation_repository` の `attendee_count` 永続化(`server/tests/test_reservation_repository.py`)、`reservation_service` の収容人数チェック(`server/tests/test_reservation_service.py`)、`init_db` の冪等性(`server/tests/test_db_init.py`)
* 正常系テスト: `None`・1以上の整数が許容される。`insert_with_participants` で渡した `attendee_count` が `find_with_detail` で読み出せる。収容人数と等しい値が許容される。同一DBに `init_db()` を2回実行しても成功する。
* 主要な異常系テスト: `0`・`-1`・`"8"`(文字列)・`True`(bool)で `False`。収容人数超過で `ValidationError`。
* 実行するテストコマンド: `cd server && python3 -m unittest tests.test_validators tests.test_reservation_repository tests.test_reservation_service tests.test_db_init -v`
* 合格条件: 全テストPASS。

## 【実行コマンド】

* `cd server && python3 -m unittest discover -s tests -v`(既存134件に回帰がないことも合わせて確認する)

## 【完了条件】

* 上記テストが全てPASSする。

---

# 【タスクID】U007-2(フロントエンド)

## 【目的】

* S03(予約作成画面)・S04(予約詳細・編集画面)に参加予定人数の入力欄を追加し、登録・編集できるようにする。S02(予約カレンダー画面)は変更しない。

## 【作成・編集対象ファイル】

* `client/js/pages/reservationCreatePage.js`(既存ファイルを修正): `validateReservationInput` に `attendeeCount` の検証を追加(未入力(`null`/空文字/`undefined`)は許容。指定時は1以上の整数)。`createReservationCreateController.submit` が `attendee_count` をリクエストボディに含める。`mountReservationCreatePage` のフォームに参加予定人数の入力欄(`type=number`)を追加し、409だけでなく400(`field=attendee_count`)のエラーメッセージも表示する。
* `client/js/pages/reservationDetailPage.js`(既存ファイルを修正): `submitUpdate` が `attendee_count` を含める。`mountReservationDetailPage` の表示・編集フォームに参加予定人数の入力欄を追加する。
* `client/tests/reservationCreatePage.test.mjs`・`client/tests/reservationDetailPage.test.mjs`(既存ファイルに追記)

## 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S03・S04(※CR-003により追記)、§4.11・§4.12

## 【実装内容】

* `validateReservationInput({..., attendeeCount})`: 未入力は許容。1未満・非整数の場合 `"参加予定人数は1以上の整数で入力してください"` を返す。収容人数との比較はクライアント側では行わず、サーバーの400レスポンスを表示する(会議室の収容人数はS03のプルダウンが保持していないため。★FIXME★ 将来的にプルダウンへ収容人数を持たせてクライアント側でも事前チェックする案があるが、CR-003のスコープ外とした)。
* `createReservationCreateController.submit` / `createReservationDetailController.submitUpdate`: `attendee_count` を数値または `null` に正規化して送信する。
* 400エラー時のメッセージ: サーバーの `details[].field === "attendee_count"` の場合は `"参加予定人数が会議室の収容人数を超えています"` を表示する。

## 【実装してはいけないこと】

* S02(`client/js/pages/calendarPage.js`)の予約サマリ表示の変更(CR-003のとおりスコープ外)。

## 【Unit Test内容】

* テスト対象: `validateReservationInput`(参加予定人数)、`createReservationCreateController.submit`、`createReservationDetailController.submitUpdate`
* 正常系テスト: 参加予定人数を指定した場合・未指定の場合の双方でバリデーションを通過し、`attendee_count` が正しくAPIへ渡る(未指定時は `null`)。
* 主要な異常系テスト: `0`・`-1`・`1.5` でエラーメッセージが返る。サーバーが `field=attendee_count` の400を返したときに収容人数超過のメッセージが表示される。
* 実行するテストコマンド: `cd client && node --test tests/reservationCreatePage.test.mjs tests/reservationDetailPage.test.mjs`
* 合格条件: 全テストPASS。

## 【実行コマンド】

* `cd client && node --test tests/*.test.mjs`(既存の他画面のテストに回帰がないことも合わせて確認する)

## 【完了条件】

* 上記テストが全てPASSする。

## 【次タスクに進む前の停止条件】(U007-1・U007-2共通)

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

## 重要

* 実装が完了したら、Executor Stepの停止条件に該当しない限り自動的に次のタスクへ進んでください。
