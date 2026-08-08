あなたはExecutor(実装担当)です。以下は Sprint 2 `master-management` の作業範囲と完了条件を、タスク単位に分けて定義したものです。各タスクを記載順に実施し、実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P007-impl-direction.md` のWBSに従って自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# スプリント U002 — master-management(マスタ管理)

* 位置づけ: 会議室マスタとユーザーマスタのCRUDと、管理者向け2画面。`docs/P005-impl-plan.md` 2.2 を参照。
* 実装対象: `rooms`、API-04〜API-07(会議室)、API-08〜API-11(ユーザー)、S06、S07。
* 前提: Sprint 1(U001)が完了していること(DB基盤・認証・共通基盤・共通レイアウト)。
* このスプリント全体の共通の禁止事項: 予約(`reservations`)に関するテーブル・API・画面を作らないこと(Sprint 3・4の担当)。

---

# 【タスクID】U002-T1 — `rooms` マイグレーションと Repository

## 【目的】

* 会議室マスタのテーブルとデータアクセス層を用意する。無効化した会議室と同名の会議室を再登録できる一意制約(部分ユニークインデックス)をここで確立する。

## 【作成・編集対象ファイル】

* `server/migrations/002-rooms.sql`(新規)
* `server/src/meeting_room/repositories/rooms_repo.py`(新規)
* `server/tests/test_rooms_repo.py`(新規)

## 【参照すべき仕様箇所】

* P002 6.2(`rooms` のテーブル定義)
* P003 3.4(`uq_rooms_name_active` 部分ユニークインデックス)、3.5(マイグレーションの作法)

## 【実装内容】

* `002-rooms.sql`: `rooms` テーブル(`room_id` INTEGER PRIMARY KEY AUTOINCREMENT、`name` NOT NULL、`capacity` INTEGER NOT NULL CHECK(1〜500)、`equipment` NOT NULL DEFAULT ''、`description` NOT NULL DEFAULT ''、`is_active` INTEGER NOT NULL DEFAULT 1、`created_at`、`updated_at`)と、`CREATE UNIQUE INDEX uq_rooms_name_active ON rooms(name) WHERE is_active = 1` を作成する。
* **既存の `001-init.sql` は編集しない**(P003 3.5「一度コミットしたマイグレーションファイルは編集しない」)。
* `rooms_repo.py`: `find_by_id` / `list_rooms(include_inactive)` / `find_active_by_name(name, exclude_room_id=None)` / `insert` / `update` / `set_active`。

## 【実装してはいけないこと】

* `rooms.name` に全行ユニークな制約を付けること(無効化した会議室と同名の再登録ができなくなる)。
* `001-init.sql` の書き換え。

## 【Unit Test内容】

* テスト対象: `002-rooms.sql` の適用、`rooms_repo`
* 正常系: 空DBに全マイグレーションを適用 → `rooms` が作られ、`schema_migrations` に `001-init.sql` と `002-rooms.sql` の2行がある。**再適用しても行数が増えない。** `insert` → `find_by_id` で一致。`set_active(False)` 後、`list_rooms(include_inactive=False)` に現れず `True` では現れる。
* 異常系: 有効な同名会議室を2件INSERT → `sqlite3.IntegrityError`。**片方を無効化してから同名をINSERT → 成功する。** `capacity=0` / `capacity=501` → CHECK制約違反。
* 実行コマンド: `cd server && python3 -m unittest discover -s tests -t .`
* 合格条件: 上記すべてPASS。

## 【実行コマンド】

* `cd server && python3 -m unittest discover -s tests -t .`

## 【完了条件】

* 単体テストが全件PASS。既存DBに対する再起動(マイグレーション再実行)が成功すること。

## 【次タスクに進む前の停止条件】

* 単体テストが3回自己修正しても合格しない場合は、処理を停止して人間に報告する。

---

# 【タスクID】U002-T2 — 会議室API(API-04〜API-07)

## 【目的】

* 会議室の一覧・登録・更新・無効化のAPIを、認可と業務制約を含めて完成させる。

## 【作成・編集対象ファイル】

* `server/src/meeting_room/schemas.py`(編集: `RoomRequest` / `RoomResponse` を追加)
* `server/src/meeting_room/services/room_service.py`(新規)
* `server/src/meeting_room/handlers/room_handlers.py`(新規)
* `server/src/meeting_room/main.py`(編集: ルート登録)
* `server/tests/test_room_service.py` / `server/tests/test_room_handlers.py`(新規)

## 【参照すべき仕様箇所】

* P002 3.6(S06の入力ルールとエラー文言)、5.2(エラーコード)、**5.5(API-04〜07の外部契約)**、5.3(`Room` の表現)
* P003 6.2(API-04〜07の内部処理)、4.3(`require_admin`)

## 【実装内容】

* `schemas.py`: `RoomRequest`(`name` 1〜50文字必須、`capacity` 1〜500の整数必須、`equipment` 0〜200文字、`description` 0〜200文字、`is_active` 既定 `true`)。エラーメッセージはP002 3.6の文言。
* `room_service.py`:
  * `list_rooms(user, include_inactive)`: `include_inactive=true` かつ非管理者は `ApiError(403, "FORBIDDEN", ...)`。
  * `create_room` / `update_room`: `BEGIN IMMEDIATE` → 同名の有効な会議室の確認(更新時は自分を除外)→ 重複なら `ApiError(409, "DUPLICATE_KEY", "同じ名前の会議室がすでに登録されています。")` → INSERT/UPDATE。更新対象が無ければ `ApiError(404, "NOT_FOUND", ...)`。
  * `deactivate_room`: `BEGIN IMMEDIATE` → 対象取得(なければ404)→ 既に `is_active=0` なら何もせず正常終了(冪等)→ **`count_future_reservations(room_id)` を呼び、1件以上なら `ApiError(409, "CONSTRAINT_VIOLATION", f"この会議室には今後の予約が{n}件あります。先に予約を取り消してください。")`** → `is_active=0` に更新。
  * `count_future_reservations(room_id) -> int` は本タスクでは **`reservations` テーブルがまだ存在しないため常に 0 を返す関数として `room_service.py` 内に切り出し、`# TODO(U003-T2): Sprint 3 で本実装に差し替える` のコメントを付ける**(`docs/P005-impl-plan.md` 2.2・5章 リスク#5)。
* `room_handlers.py`: 4本のハンドラ。GET以外は `require_admin`。GETは `require_login`。ステータスコードは P002 5.5 のとおり(POSTは201、DELETEは204)。
* `main.py`: `/api/rooms` と `/api/rooms/{room_id}` を登録する。

## 【実装してはいけないこと】

* `reservations` テーブルの作成・参照(Sprint 3の担当)。
* 会議室の物理削除(仕様は論理削除)。

## 【Unit Test内容】

* テスト対象: `room_service`、`room_handlers`
* 正常系: 管理者で登録 → 201 とレスポンス形状(`room_id` 採番、`created_at`/`updated_at` あり)。更新 → 200 で値が変わり `updated_at` が進む。無効化 → 204 で `is_active=0`。一般ユーザーの `GET /api/rooms` は有効な会議室のみを `room_id` 昇順で返す。管理者の `include_inactive=true` は無効分も返す。
* 異常系: `name` 空 / 51文字、`capacity` 0 / 501 / 小数、`description` 201文字 → 400 `VALIDATION_ERROR`(`details[].field` が該当項目)。一般ユーザーのPOST/PUT/DELETE → 403 `FORBIDDEN`。一般ユーザーの `include_inactive=true` → 403。同名登録 → 409 `DUPLICATE_KEY`。存在しない `room_id` の更新・削除 → 404。既に無効な会議室の削除 → 204(冪等)。未認証 → 401。
* 実行コマンド: `cd server && python3 -m unittest discover -s tests -t .`
* 合格条件: 上記すべてPASS。

## 【実行コマンド】

* `cd server && python3 -m unittest discover -s tests -t .`

## 【完了条件】

* 単体テストが全件PASS。API-04〜07がP002 5.5の契約どおり応答すること。

## 【次タスクに進む前の停止条件】

* 単体テストが3回自己修正しても合格しない場合は、処理を停止して人間に報告する。

---

# 【タスクID】U002-T3 — ユーザーAPI(API-08〜API-11)

## 【目的】

* ユーザーの一覧・登録・更新・無効化のAPIを、`scope` による2つの利用モードと業務制約(最後の管理者の保護)を含めて完成させる。

## 【作成・編集対象ファイル】

* `server/src/meeting_room/schemas.py`(編集: `UserCreateRequest` / `UserUpdateRequest` を追加)
* `server/src/meeting_room/services/user_service.py`(新規)
* `server/src/meeting_room/handlers/user_handlers.py`(新規)
* `server/src/meeting_room/main.py`(編集: ルート登録)
* `server/tests/test_user_service.py` / `server/tests/test_user_handlers.py`(新規)

## 【参照すべき仕様箇所】

* P002 3.7(S07の入力ルール)、**5.6(API-08〜11の外部契約と `scope` の定義)**
* P003 6.3(API-08〜11の内部処理)、4.3(権限変更・無効化時のセッション削除)

## 【実装内容】

* `schemas.py`: `UserCreateRequest`(`user_id` `^[A-Za-z0-9]{4,20}$`、`name` 1〜50、`role` `general|admin`、`password` 8〜64、`is_active` 既定 `true`)、`UserUpdateRequest`(`user_id` を含まない。`password` は省略可)。
* `user_service.py`:
  * `list_users(user, scope, include_inactive)`: `scope="management"`(既定)は `require_admin` 済みを前提に全項目を返す。`scope="attendee_candidates"` はログイン済みなら誰でも呼べ、**`user_id` と `name` だけ**を有効ユーザーについて返す(`role`・`is_active` を含めない)。
  * `create_user`: `BEGIN IMMEDIATE` → `user_id` の存在確認(**無効化済みも重複として扱う**)→ 409 `DUPLICATE_KEY` → パスワードをハッシュ化して INSERT。
  * `update_user`: 対象取得(なければ404)→ 「最後の有効な管理者」判定(対象が有効な管理者で、他に有効な管理者が0人のとき、`role` を `general` にする / `is_active=false` にする操作は 409 `CONSTRAINT_VIOLATION`)→ UPDATE(`password` 指定時のみハッシュ更新)→ 権限変更または無効化があれば当該ユーザーの `sessions` を全削除。
  * `deactivate_user(actor, target_id)`: 自分自身なら 409 `CONSTRAINT_VIOLATION`(「自分自身を無効化することはできません。」)→ 最後の有効な管理者なら 409 → `is_active=0` + `sessions` 全削除。既に無効なら 204(冪等)。
* `user_handlers.py`: 4本。`scope=attendee_candidates` の GET のみ `require_login`、それ以外はすべて `require_admin`。

## 【実装してはいけないこと】

* `password_hash` をレスポンスに含めること。
* `scope=attendee_candidates` で `role` や `is_active` を返すこと(**SELECT句のレベルで含めない**)。
* ユーザーの物理削除。

## 【Unit Test内容】

* テスト対象: `user_service`、`user_handlers`
* 正常系: 管理者で登録 → 201、`password` がレスポンスに無い。DBの `password_hash` が `scrypt$` で始まる。更新で氏名・権限が変わる。`password` を指定した更新後、新しいパスワードでログインできる。無効化 → 204 かつ当該ユーザーのセッションが消える。`scope=attendee_candidates` を一般ユーザーのセッションで呼ぶと200で、返る各要素のキーが `user_id` と `name` の2つだけ、かつ無効ユーザーを含まない。
* 異常系: `user_id` 3文字 / 記号入り、`name` 51文字、`role` に `owner` → 400。既存IDでの登録(有効・無効の両方)→ 409 `DUPLICATE_KEY`。最後の有効な管理者を `general` に変更 / 無効化 → 409 `CONSTRAINT_VIOLATION`。自分自身のDELETE → 409。一般ユーザーの `scope=management` GET・POST・PUT・DELETE → 403。存在しない `user_id` の更新・削除 → 404。
* 実行コマンド: `cd server && python3 -m unittest discover -s tests -t .`
* 合格条件: 上記すべてPASS。

## 【実行コマンド】

* `cd server && python3 -m unittest discover -s tests -t .`

## 【完了条件】

* 単体テストが全件PASS。API-08〜11がP002 5.6の契約どおり応答すること。

## 【次タスクに進む前の停止条件】

* 単体テストが3回自己修正しても合格しない場合は、処理を停止して人間に報告する。

---

# 【タスクID】U002-T4 — S06 会議室管理画面

## 【目的】

* 管理者が会議室を一覧・登録・編集・無効化できる画面を実装する。

## 【作成・編集対象ファイル】

* `client/src/views/s06-room-admin.js`(新規)
* `client/src/lib/router.js`(編集: `#/admin/rooms` の登録)
* `client/tests/test_s06_room_admin.js`(新規)

## 【参照すべき仕様箇所】

* P002 2.3(権限による表示制御)、2.4(エラー表示)、**3.6(S06の項目・バリデーション・確認ダイアログ・エラー文言)**、5.5

## 【実装内容】

* 一覧: `GET /api/rooms?include_inactive=true` の結果を「会議室名 / 収容人数 / 設備 / 説明文 / 有効・無効 / 操作」の表で描画する。無効な行はグレー表示(CSSクラス `is-inactive`)。
* 新規登録・編集: モーダルフォーム(会議室名・収容人数・設備・説明文・有効フラグ)。送信前に `validation.js` で検証し、違反はフィールド直下に表示する。
* 削除: 「この会議室を無効化します。よろしいですか?」の確認後に `DELETE`。409 `CONSTRAINT_VIOLATION` のときはAPIの `message` を画面上部に表示する。
* 権限: `GET /api/me` の `role` が `admin` でなければ、本体を描画せず「この画面を表示する権限がありません。」と「カレンダーへ戻る」リンクのみを表示する。
* 「ユーザー管理」への遷移リンクを画面内に置く(P002 4章の `S06 → S07`)。

## 【実装してはいけないこと】

* 一覧の絞り込み・並べ替え・ページングなど、P002にない機能の追加。
* 会議室の物理削除ボタン。

## 【Unit Test内容】

* テスト対象: `s06-room-admin.js` の描画関数とイベントハンドラ
* 正常系: 会議室3件(うち1件無効)を渡すと3行描画され、無効行に `is-inactive` クラスが付く。説明文の列が存在する。フォーム送信で `POST /api/rooms` が正しいボディで呼ばれる。編集で `PUT` が呼ばれる。削除確認でOKを選ぶと `DELETE` が呼ばれ、キャンセルを選ぶと呼ばれない。
* 異常系: 一般ユーザーの `me` を渡すと表が描画されず権限メッセージのみになる。409 `DUPLICATE_KEY` で会議室名欄の直下にメッセージが出る。409 `CONSTRAINT_VIOLATION` で画面上部にAPIの `message` が出る。収容人数に 0 を入れて送信 → APIが呼ばれずエラー表示。
* 実行コマンド: `cd client && node --test tests`
* 合格条件: 上記すべてPASS。

## 【実行コマンド】

* `cd client && node --test tests`

## 【完了条件】

* 単体テストが全件PASS。

## 【次タスクに進む前の停止条件】

* 単体テストが3回自己修正しても合格しない場合は、処理を停止して人間に報告する。

---

# 【タスクID】U002-T5 — S07 ユーザー管理画面

## 【目的】

* 管理者がユーザーを一覧・登録・編集・無効化できる画面を実装する。

## 【作成・編集対象ファイル】

* `client/src/views/s07-user-admin.js`(新規)
* `client/src/lib/router.js`(編集: `#/admin/users` の登録)
* `client/tests/test_s07_user_admin.js`(新規)

## 【参照すべき仕様箇所】

* P002 2.3、2.4、**3.7(S07の項目・バリデーション。パスワード欄の扱いを含む)**、5.6

## 【実装内容】

* 一覧: `GET /api/users`(既定 `scope=management`, `include_inactive=true`)の結果を「社員ID / 氏名 / 権限 / 有効・無効 / 操作」で描画する。無効行はグレー表示。
* 新規登録: 社員ID・氏名・権限・パスワード・有効フラグ。編集: 社員IDは表示のみ(入力不可)、パスワードは**空欄なら変更しない**旨をラベルに明記する。
* 削除: 確認ダイアログの後に `DELETE`。409 `CONSTRAINT_VIOLATION`(自分自身・最後の管理者)は画面上部にAPIの `message` をそのまま表示する。
* 「戻る」リンクでS06へ遷移する(P002 4章の `S07 → S06`)。
* 権限: S06と同じ制御。

## 【実装してはいけないこと】

* パスワードの画面表示・ログ出力・ローカル保存。
* 社員IDの変更機能(P002 5.6 で `user_id` は変更不可)。

## 【Unit Test内容】

* テスト対象: `s07-user-admin.js`
* 正常系: 4件(うち1件無効)を渡すと4行描画。新規フォーム送信で `POST /api/users` が呼ばれ、ボディに `password` が含まれる。編集フォームでパスワード空欄のまま送信すると、ボディに `password` キーが**含まれない**。社員ID欄が編集時は非活性。
* 異常系: 一般ユーザーでは権限メッセージのみ。パスワード7文字 → APIが呼ばれずエラー表示。409 `DUPLICATE_KEY` → 社員ID欄の直下にメッセージ。409 `CONSTRAINT_VIOLATION` → 画面上部にメッセージ。
* 実行コマンド: `cd client && node --test tests`
* 合格条件: 上記すべてPASS。

## 【実行コマンド】

* `cd client && node --test tests`
* `cd server && python3 -m unittest discover -s tests -t .`(退行がないことの確認)

## 【完了条件】

* クライアント・サーバー双方の単体テストが全件PASS。
* Sprint 2 の全タスク(T1〜T5)が完了したら、`docs/P007-impl-direction.md` の `U002` 行のチェックボックスを `[x]` に更新する。

## 【次タスクに進む前の停止条件】

* 単体テストが3回自己修正しても合格しない場合は、処理を停止して人間に報告する。

---

## 重要

* このスプリントの範囲外のファイルは編集しないでください。
* 実装後、実行したテストコマンドと結果を報告してください。
* このスプリントが完了したら、Executor Stepの停止条件に該当しない限り、次のスプリント(`U003-reservation-core.md`)に自動的に進んでください。1タスクごとに人間の指示を待つ必要はありません。
