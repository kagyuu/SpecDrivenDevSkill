あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U004 — user-administration

## タスク一覧(OKF副目次)

* 状態は `[ ]`(未着手) / `[~]`(進行中) / `[x]`(完了) の3種類とする。
* このスプリントファイル自体の状態(`docs/P007-impl-direction.md` の該当行)は、全タスクが `[x]` になって初めて `[x]` にする。
* **中断からの再開**・**先行実装の禁止** のルールは `docs/P007-impl-direction/U001-foundation-and-auth.md` 冒頭の注記と同一。

- [x] U004-T1 [ユーザーCRUDのスキーマ](#u004-t1-ユーザーcrudのスキーマ) — UserCreateRequest(初期パスワード含む)等
- [x] U004-T2 [Repository層(users 書き込み)](#u004-t2-repository層users-書き込み) — 一意制約違反ハンドリング・自己無効化判定の土台
- [x] U004-T3 [Service層・APIハンドラ(GET/POST/PUT/DELETE users)](#u004-t3-service層apiハンドラgetpostputdelete-users) — 重複ID変換・自己無効化禁止
- [x] U004-T4 [フロントエンド S07ユーザー管理画面](#u004-t4-フロントエンド-s07ユーザー管理画面) — 一覧・登録・編集・削除
- [x] U004-T5 [結合確認用の薄いタスク: 管理者専用画面・APIの横断的認可確認](#u004-t5-結合確認用の薄いタスク-管理者専用画面apiの横断的認可確認) — 全管理者専用エンドポイント/画面のガード総点検

---

## U004-T1: ユーザーCRUDのスキーマ

### 【目的】

* ユーザー管理API(`docs/P002-frontend-spec.md` §3 S07)の入出力スキーマを定義する。

### 【作成・編集対象ファイル】

* `server/app/schemas/user.py`(新規)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S07

### 【実装内容】

* `UserCreateRequest`(employee_id必須20文字以内、name必須50文字以内、role必須"general"|"admin"、is_active既定true、initial_password必須8文字以上)。
* `UserUpdateRequest`(employee_idを含まない。name/role/is_activeのみ、全置換)。
* `UserResponse`(password_hashを含めないこと)。

### 【実装してはいけないこと】

* レスポンススキーマに `password_hash` フィールドを含めること(`docs/P002-frontend-spec.md` の非機能要件「パスワードはハッシュ化して保存」の趣旨を損なう、レスポンスに含めてよい理由はない)。

### 【Unit Test内容】

* テスト対象: 各Pydanticスキーマ
* 正常系/異常系: `UserCreateRequest` に `initial_password="short"`(7文字)を渡すとバリデーションエラーになること。`role="owner"`(許可されていない値)でエラーになること。
* 実行コマンド: `cd server && uv run python -m pytest tests/schemas/test_user_schema.py -v`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/schemas/test_user_schema.py -v`

### 【完了条件】

* 上記Unit Testがすべて成功する。

### 【次タスクに進む前の停止条件】

* Unit Testが3回の自己修正を経ても成功しない場合、処理を停止し人間に報告する。

---

## U004-T2: Repository層(users 書き込み)

### 【目的】

* ユーザーの一覧・作成・更新・論理削除のデータアクセス関数を追加する。

### 【作成・編集対象ファイル】

* `server/app/repositories/users.py`(編集、書き込み関数を追加)
* `server/tests/repositories/test_users_repo.py`(編集)

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §5.11、§6

### 【実装内容】

* `list_users(conn) -> list[User]`(`is_active` に関わらず全件、管理画面は無効ユーザーも一覧表示するため)。
* `create_user(conn, data, password_hash, created_at) -> int`。`employee_id` の一意制約違反時はsqlite3の `IntegrityError` をそのまま送出し、Service層で捕捉・変換する(Repository層ではエラーコードへの変換を行わない)。
* `update_user(conn, user_id, data, updated_at) -> None`。
* `deactivate_user(conn, user_id, updated_at) -> None`(`is_active=0` のみ、物理削除しない)。

### 【実装してはいけないこと】

* `employee_id` の重複を事前に `SELECT` で確認してからガードする実装(競合状態を避けるため、DBのUNIQUE制約への違反を捕捉する方式に統一する。事前チェックと制約の二重実装はしない)。
* 自己無効化の判定ロジック(これはService層が「操作者と対象が同一か」を判定する業務ロジックであり、Repository層は指定されたIDをそのまま無効化するだけの役割に留める)。

### 【Unit Test内容】

* テスト対象: 上記各関数
* 正常系: `create_user` で作成したユーザーが `list_users` に含まれること。
* 異常系: 既存の `employee_id` で `create_user` を呼ぶと `sqlite3.IntegrityError` が送出されること。
* 正常系: `deactivate_user` 後、対象ユーザーの `is_active` が0になること(行自体は残ること)。
* 実行コマンド: `cd server && uv run python -m pytest tests/repositories/test_users_repo.py -v`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/repositories/test_users_repo.py -v`

### 【完了条件】

* 上記Unit Testがすべて成功する。

### 【次タスクに進む前の停止条件】

* Unit Testが3回の自己修正を経ても成功しない場合、処理を停止し人間に報告する。

---

## U004-T3: Service層・APIハンドラ(GET/POST/PUT/DELETE users)

### 【目的】

* `GET /api/users`、`POST /api/users`、`PUT /api/users/{id}`、`DELETE /api/users/{id}` を実装する。

### 【作成・編集対象ファイル】

* `server/app/services/users.py`(新規)
* `server/app/api/routers/users.py`(新規)
* `server/app/main.py`(編集、ルーター登録)
* `server/tests/api/test_users_api.py`(新規)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S07
* `docs/P003-backend-spec.md` §5.11

### 【実装内容】

* 4エンドポイントとも `require_admin` 依存を必須にする。
* `POST /api/users`: `create_user` 呼び出し時の `sqlite3.IntegrityError` を捕捉し、409 `DUPLICATE_EMPLOYEE_ID`(メッセージ「この社員IDは既に登録されています」)に変換する。
* `DELETE /api/users/{id}`: パスパラメータの `id` が `current_user.id`(認証ミドルウェアが解決した操作者自身)と一致する場合、400 `CANNOT_DEACTIVATE_SELF`(メッセージ「自分自身のアカウントは無効化できません」)を返す。一致しなければ `deactivate_user` を呼び204。

### 【実装してはいけないこと】

* パスワード再発行・変更用のエンドポイント追加(`docs/P002-frontend-spec.md` §3 S07・§8のとおりスコープ外、★FIXME★として記録済み)。

### 【Unit Test内容】

* テスト対象: 4エンドポイント
* 正常系: 管理者が新規ユーザーを登録→201、レスポンスに `password_hash` が含まれないこと。
* 異常系: 既存の `employee_id` で登録→409 `DUPLICATE_EMPLOYEE_ID`。
* 異常系: 管理者が自分自身のIDに対して `DELETE`→400 `CANNOT_DEACTIVATE_SELF`。
* 正常系: 管理者が他の管理者・一般ユーザーを無効化→204。
* 異常系: 一般ユーザーがこれら4エンドポイントのいずれかを呼ぶと403 `FORBIDDEN`。
* 実行コマンド: `cd server && uv run python -m pytest tests/api/test_users_api.py -v`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/api/test_users_api.py -v`

### 【完了条件】

* 上記Unit Testがすべて成功する。

### 【次タスクに進む前の停止条件】

* Unit Testが3回の自己修正を経ても成功しない場合、処理を停止し人間に報告する。

---

## U004-T4: フロントエンド S07ユーザー管理画面

### 【目的】

* `docs/P002-frontend-spec.md` §3 S07を実装する。

### 【作成・編集対象ファイル】

* `client/src/pages/UserAdminPage.tsx`(新規)
* `client/src/router.tsx`(編集、S07を管理者専用ルートとして追加)
* `client/src/tests/UserAdminPage.test.tsx`(新規)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S07

### 【実装内容】

* ユーザー一覧(社員ID/氏名/権限/有効・無効)、新規登録フォーム(社員ID・氏名・権限・初期パスワード)、編集フォーム(氏名・権限・有効フラグ、社員IDは読み取り専用表示)、削除ボタン(自分自身の行では無効化した状態でボタンを表示し、押下できないようにする。`docs/P002-frontend-spec.md` §3 S07のとおり)。
* `RoomAdminPage`(U003-T6)と同様、`role !== "admin"` の場合はコンポーネントをレンダリングしない。

### 【実装してはいけないこと】

* パスワード再発行用のUI(スコープ外)。

### 【Unit Test内容】

* テスト対象: `UserAdminPage`
* 正常系: 管理者としてアクセスするとユーザー一覧・フォームが表示されること。
* 正常系: 自分自身の行の削除ボタンが無効化されていること。
* 異常系: 一般ユーザーとしてアクセスすると権限不足の案内が表示され、フォームがDOMに存在しないこと。
* 実行コマンド: `cd client && npm run test -- src/tests/UserAdminPage.test.tsx`
* 合格条件: 全テストPASS。

### 【実行コマンド】

* `cd client && npm run test -- src/tests/UserAdminPage.test.tsx`
* `cd client && npm run build`

### 【完了条件】

* 上記Unit Testがすべて成功し、`npm run build` が成功する。

### 【次タスクに進む前の停止条件】

* Unit Testが3回の自己修正を経ても成功しない場合、処理を停止し人間に報告する。

---

## U004-T5: 結合確認用の薄いタスク: 管理者専用画面・APIの横断的認可確認

### 【目的】

* U001〜U004で実装した管理者専用API(`POST/PUT/DELETE /api/rooms/*`、`GET/POST/PUT/DELETE /api/users/*`)すべてについて、一般ユーザーが呼び出すと一貫して403 `FORBIDDEN` になることを、個別タスクの単体テストとは別に横断的に確認する。個々のAPIの単体テストは各タスクで既にカバーしているため、本タスクはそれらを1つの一覧として再確認する薄い確認作業であり、新しい業務ロジックは実装しない。

### 【作成・編集対象ファイル】

* `server/tests/api/test_admin_authorization_matrix.py`(新規)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §6(認可の外部契約表)

### 【実装内容】

* `docs/P002-frontend-spec.md` §6の表に列挙された管理者専用操作(会議室CRUD・ユーザーCRUD・他人の予約の編集/取消)を1つのパラメータ化テスト(`pytest.mark.parametrize`)としてまとめ、一般ユーザーでの呼び出しがすべて403になることを1本のテストファイルで確認する。

### 【実装してはいけないこと】

* 個別APIの実装変更(既存実装が仕様どおりであることの確認のみを行う。もし本タスクで403にならないケースが見つかった場合は、その場で実装を修正せず、`docs/P007-impl-direction.md` の「未解決事項」に記録して人間の判断を仰ぐ)。

### 【Unit Test内容】

* テスト対象: §6の認可表に列挙された全操作
* 正常系: すべての組み合わせで一般ユーザーが403 `FORBIDDEN` を受け取ること。
* 実行コマンド: `cd server && uv run python -m pytest tests/api/test_admin_authorization_matrix.py -v`
* 合格条件: PASS。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/api/test_admin_authorization_matrix.py -v`

### 【完了条件】

* 上記テストがPASSする。

### 【次タスクに進む前の停止条件】

* 該当なし(本スプリントの最終タスク、かつP007全体の最終タスク)。全タスク完了後、`docs/P007-impl-direction.md` のU004行を `[x]` に更新する。

## 重要

* 各タスクの範囲外のファイルは編集しないでください。
* タスクの実装後、実行したテストコマンドと結果を報告してください。
* タスクが完了したら、上記「タスク一覧」の該当行を `[x]` に更新してください。
* 全タスクが完了したら、`docs/P007-impl-direction.md` の本スプリント行を `[x]` に更新してください。
* Executor Stepの停止条件(`SKILL.md` 参照)に該当しない限り、次のタスクに自動的に進んでください。1タスクごとに人間の指示を待つ必要はありません。
