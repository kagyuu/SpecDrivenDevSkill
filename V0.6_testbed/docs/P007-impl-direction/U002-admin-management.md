あなたはExecutor(実装担当)です。このスプリント(U002: admin-management)には6個のタスク(U002-1〜U002-6)があります。**1回に1タスクだけ**実施し、完了条件を満たしたら報告し、次タスクの指示を待ってください。

前提: U001(foundation-auth)が完了し、認証・セッション・DBスキーマが利用可能であること。
参照する仕様書: `docs/P002-frontend-spec.md`、`docs/P003-backend-spec.md`、`docs/P005-impl-plan.md` §3.2、`docs/P006-test-plan.md`。

---

# 【タスクID】U002-1

## 【目的】

* 会議室・ユーザーの入力項目に対するバリデーション純粋関数を実装する。

## 【作成・編集対象ファイル】

* `server/app/core/validators.py`(既存ファイルに追記): `validate_room_name`、`validate_capacity`、`validate_user_name`、`validate_role`

## 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S06、§3 S07

## 【実装内容】

* `validate_room_name(value)`: 1〜50文字。
* `validate_capacity(value)`: 1以上の整数。
* `validate_user_name(value)`: 1〜50文字。
* `validate_role(value)`: `"general"` または `"admin"` のいずれか。

## 【実装してはいけないこと】

* DBアクセスを伴う一意性チェック(会議室名の重複チェック、社員IDの重複チェックはU002-3のService層で行う)。

## 【Unit Test内容】

* テスト対象: 上記4関数
* 正常系テスト: 仕様範囲内の値でTrue。
* 主要な異常系テスト: 51文字の会議室名/氏名、0以下の収容人数、`"manager"` のような未定義role でFalse。
* 実行するテストコマンド: `cd server && uv run pytest tests/test_validators.py -v`
* 合格条件: 全テストPASS(U001-2で追加済みのテストと合わせて全件PASSすること)。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_validators.py -v`

## 【完了条件】

* 上記テストが全てPASSする。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

---

# 【タスクID】U002-2

## 【目的】

* 会議室・ユーザーのRepository層(CRUD)を実装する。

## 【作成・編集対象ファイル】

* `server/app/repositories/room_repository.py`(`list`、`find`、`find_by_name_active`、`insert`、`update`、`set_active`)
* `server/app/repositories/user_repository.py`(既存ファイルに追記): `list`、`insert`、`update`、`set_active`

## 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §7.4〜§7.7、§7.14〜§7.17

## 【実装内容】

* `room_repository.list(include_inactive: bool)`: `include_inactive=False` の場合 `is_active=true` のみ返す。
* `room_repository.find_by_name_active(name)`: 有効な会議室のうち同名のものを検索する(重複チェック用)。
* `user_repository.list(include_inactive: bool)`: 既定 `include_inactive=True`。
* いずれも `created_at`/`updated_at` をINSERT/UPDATE時にISO8601形式で設定する。

## 【実装してはいけないこと】

* 権限チェック・一意性チェックのロジック(Service層、U002-3の責務)。

## 【Unit Test内容】

* テスト対象: `room_repository`、`user_repository` の各関数
* 正常系テスト: 登録・取得・更新・無効化が正しく反映される。
* 主要な異常系テスト: 存在しないIDでの `find`/`update` がNone/例外になる。無効化済みを除外した `list` が正しい件数を返す。
* 実行するテストコマンド: `cd server && uv run pytest tests/test_room_repository.py tests/test_user_repository.py -v`
* 合格条件: 全テストPASS。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_room_repository.py tests/test_user_repository.py -v`

## 【完了条件】

* 上記テストが全てPASSする。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

---

# 【タスクID】U002-3

## 【目的】

* 会議室・ユーザーのService層(業務ロジック: 重複チェック、一意性チェック、初期パスワード発行、自己無効化禁止)を実装する。

## 【作成・編集対象ファイル】

* `server/app/services/room_service.py`(`create`、`update`、`deactivate`)
* `server/app/services/user_service.py`(`create`、`update`、`deactivate`)

## 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §7.5(会議室名重複チェック)、§7.15(社員ID一意性チェック、初期パスワードのハッシュ化)、§7.17(自己無効化禁止)、§3(パスワード生成規則)

## 【実装内容】

* `room_service.create(data)`: `validate_room_name`/`validate_capacity` を通し、`find_by_name_active` で重複があれば `ValidationError(field="name")` を送出。無ければ `room_repository.insert`。
* `room_service.deactivate(room_id)`: 対象が無ければ `NotFoundError`。あれば `set_active(room_id, False)`。
* `user_service.create(data)`: `validate_employee_id`/`validate_user_name`/`validate_role`/`validate_password_policy` を通し、`employee_id` の重複があれば `ValidationError`。`hash_password` でハッシュ化し `user_repository.insert`。
* `user_service.deactivate(user_id, current_user_id)`: `user_id == current_user_id` の場合 `ValidationError(field="user_id", reason="self-deactivation not allowed")`。それ以外は `set_active(user_id, False)`。

## 【実装してはいけないこと】

* HTTPステータスコードの決定(Service層は例外を送出するのみ。ステータスコードへの変換はHandler層(U002-4)の責務)。

## 【Unit Test内容】

* テスト対象: `room_service`、`user_service` の各関数
* 正常系テスト: 正しい入力で登録・更新・無効化が成功する。
* 主要な異常系テスト: 同名会議室での登録が `ValidationError`。重複する社員IDでの登録が `ValidationError`。自分自身を無効化しようとして `ValidationError`。存在しないIDで `NotFoundError`。
* 実行するテストコマンド: `cd server && uv run pytest tests/test_room_service.py tests/test_user_service.py -v`
* 合格条件: 全テストPASS。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_room_service.py tests/test_user_service.py -v`

## 【完了条件】

* 上記テストが全てPASSする。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

---

# 【タスクID】U002-4

## 【目的】

* 会議室・ユーザーのAPI Handler層(8エンドポイント)を実装し、管理者権限チェックを適用する。

## 【作成・編集対象ファイル】

* `server/app/api/rooms.py`(`GET/POST/PUT/DELETE /api/rooms`)
* `server/app/api/users.py`(`GET/POST/PUT/DELETE /api/users`)
* `server/app/main.py`(ルーター登録)

## 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §4.4〜§4.7、§4.14〜§4.17

## 【実装内容】

* `GET /api/rooms` は `require_auth` のみ(全ユーザー閲覧可)。`include_inactive=true` は `role=="admin"` のときのみ有効、それ以外は無視して `false` 扱い。
* `POST/PUT/DELETE /api/rooms`、`GET/POST/PUT/DELETE /api/users` は `require_admin` を課す。
* 各エンドポイントは対応するService層の例外(`ValidationError`→400、`NotFoundError`→404)を `docs/P002-frontend-spec.md` §2の形式に変換する(U001-4で実装済みの例外ハンドラを利用する)。

## 【実装してはいけないこと】

* `docs/P002-frontend-spec.md` にないクエリパラメータ・レスポンスフィールドの追加。

## 【Unit Test内容】

* テスト対象: rooms/users の8エンドポイント(`TestClient`)
* 正常系テスト: 管理者ログイン状態での一覧・登録・更新・削除が成功する。
* 主要な異常系テスト: 未ログインで401。一般ユーザーで403。存在しないIDで404。同名会議室・重複社員IDで400。
* 実行するテストコマンド: `cd server && uv run pytest tests/test_api_rooms.py tests/test_api_users.py -v`
* 合格条件: 全テストPASS。

## 【実行コマンド】

* `cd server && uv run pytest tests/test_api_rooms.py tests/test_api_users.py -v`

## 【完了条件】

* 上記テストが全てPASSする。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

---

# 【タスクID】U002-5

## 【目的】

* S06会議室管理画面・S07ユーザー管理画面のフロントエンドコンポーネントを実装する。

## 【作成・編集対象ファイル】

* `client/src/pages/RoomManagementPage.tsx`
* `client/src/pages/UserManagementPage.tsx`
* `client/src/api/roomApi.ts`、`client/src/api/userApi.ts`

## 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S06、§3 S07、§4.4〜§4.7、§4.14〜§4.17

## 【実装内容】

* 一覧表示(無効化済みも状態列付きで表示)、新規登録フォーム、編集フォーム、削除(無効化)ボタンをそれぞれ実装する。
* ユーザー管理画面には初期パスワード入力欄(新規登録時必須)を含める。

## 【実装してはいけないこと】

* API接続部分(U002-6で実施。本タスクではモックデータでコンポーネントの表示・フォームの入力保持のみ確認する)。

## 【Unit Test内容】

* テスト対象: `RoomManagementPage`、`UserManagementPage` のフォームバリデーション・表示ロジック
* 正常系テスト: モックデータが一覧に表示される。フォーム入力値が保持される。
* 主要な異常系テスト: 必須項目未入力で送信ボタンが無効化される、またはエラー表示される。
* 実行するテストコマンド: `cd client && npm run test -- RoomManagementPage UserManagementPage`
* 合格条件: 全テストPASS。

## 【実行コマンド】

* `cd client && npm run test -- RoomManagementPage UserManagementPage`
* `cd client && npm run build`

## 【完了条件】

* 上記テストがPASSし、ビルドが成功する。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。

---

# 【タスクID】U002-6(結合確認用の薄いタスク)

## 【目的】

* U002-1〜U002-5の画面とAPIを接続し、会議室・ユーザーそれぞれの登録→一覧反映→編集→無効化の一連動作が実際に繋がることを確認する。

## 【作成・編集対象ファイル】

* `client/src/pages/RoomManagementPage.tsx`、`client/src/pages/UserManagementPage.tsx`(モックからAPI接続への切り替え)
* `client/src/App.tsx`(ルーティングにS06/S07を追加。管理者ログイン時のみ表示)

## 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S06、§3 S07

## 【実装内容】

* `roomApi`/`userApi` を呼び出すよう画面を接続する。

## 【実装してはいけないこと】

* S02〜S05(予約関連画面)の実装(U003・U004の範囲)。

## 【Unit Test内容】

* テスト対象: 画面とAPIの結線(モックした `roomApi`/`userApi` を使用)
* 正常系テスト: 登録操作で `roomApi.create`/`userApi.create` が呼ばれ、成功後に一覧が再取得される。
* 主要な異常系テスト: APIがエラーを返した場合に画面上にエラーが表示され、一覧が意図せず更新されない。
* 実行するテストコマンド: `cd client && npm run test -- RoomManagementPage UserManagementPage`
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
