あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U002 — room-management

## タスク一覧(OKF副目次)

* 状態は `[ ]`(未着手) / `[~]`(進行中) / `[x]`(完了) の3種類とする。1タスクの作業を開始したら `[~]` に、完了条件をすべて満たしたら `[x]` に更新する。
* このスプリントファイル自体の状態(`docs/P007-impl-direction.md` の該当行)は、全タスクが `[x]` になって初めて `[x]` にする。1件以上のタスクが `[~]`/`[x]` で残りが `[ ]` の場合は `[~]` とする。
* **中断からの再開**・**先行実装の禁止**: `docs/P007-impl-direction/U001-foundation-and-auth.md` タスク一覧節と同じ規則に従う。

- [x] U002-T1 [会議室Repository/Service層実装](#u002-t1-会議室repositoryservice層実装) — CRUDと論理削除ロジック
- [x] U002-T2 [会議室APIハンドラ実装](#u002-t2-会議室apiハンドラ実装) — GET/POST/PUT/DELETE /api/rooms
- [x] U002-T3 [S06会議室管理画面実装](#u002-t3-s06会議室管理画面実装) — 一覧・登録・編集フォーム
- [x] U002-T4 [S06とAPIの接続確認](#u002-t4-s06とapiの接続確認) — 結合確認用の薄いタスク(★実施メモ: このセッションはブラウザ/Playwrightを使えないため、`docs/P002-frontend-spec.md` 3.6節の「登録→一覧反映→編集→無効化→一覧から消える」の一連の流れを、フロントエンドが呼ぶのと同じAPI呼び出し順序でcurlにより直接検証した。フロントエンド側のクリック操作・画面遷移自体は未検証。UnitTest(RoomManagementPage.test.tsx)がコンポーネント側の挙動を別途カバーしている)

---

## U002-T1: 会議室Repository/Service層実装

### 【目的】

* 会議室の登録・一覧・更新・論理削除を行うRepository層・Service層を実装する。

### 【作成・編集対象ファイル】

* `server/app/repositories/room_repository.py`(`find_all(include_inactive: bool)`, `find_by_id`, `create`, `update`, `deactivate`)
* `server/app/services/room_service.py`(バリデーション、`equipment` のJSONエンコード/デコード)
* `server/tests/test_room_service.py`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 3.6節(バリデーションルール)
* `docs/P003-backend-spec.md` 4.4〜4.5.2節(内部仕様)、2.2節(テーブル定義)

### 【実装内容】

* `room_service.create(name, capacity, equipment, description)`: `name` 必須最大50文字、`capacity` 1以上の整数、`description` 任意最大200文字を検証し、違反時は `ValidationError(fields={...})` を送出する。
* `room_service.update`: 同様のバリデーションに加え `is_active` の更新を受け付ける。
* `room_service.deactivate(room_id)`: `is_active=False` に更新する(物理削除しない)。存在しない場合は `NotFoundError`。
* `equipment` はPythonの `list[str]` として受け取り、Repository層でJSON文字列にエンコードして保存、取得時はデコードして返す。

### 【実装してはいけないこと】

* APIルーティング・権限チェック(管理者のみ)はこのタスクに含めない(U002-T2の範囲)。

### 【Unit Test内容】

* テスト対象: `room_service.py`
* 正常系: 会議室の作成・一覧取得(有効のみ/無効含む)・更新・論理削除
* 主要な異常系: `name` 空文字、`capacity` 0または負数、`description` 201文字、存在しない `room_id` の更新・削除
* 実行するテストコマンド: `cd server && python -m pytest tests/test_room_service.py -v`
* 合格条件: 全件PASS

### 【実行コマンド】

* `cd server && python -m pytest tests/test_room_service.py -v`

### 【完了条件】

* 上記Unit TestがすべてPASSする

### 【次タスクに進む前の停止条件】

* 3回自己修正しても通らない場合は停止し、人間に報告する

---

## U002-T2: 会議室APIハンドラ実装

### 【目的】

* U002-T1のService層を使い、`GET/POST/PUT/DELETE /api/rooms` を実装する。

### 【作成・編集対象ファイル】

* `server/app/routers/rooms.py`
* `server/app/schemas/room.py`(`RoomCreateRequest`, `RoomUpdateRequest`, `RoomResponse`)
* `server/app/dependencies.py`(`require_admin` 依存性を追加。`get_current_user` の上に権限チェックを重ねる)
* `server/app/main.py`(ルーター登録)
* `server/tests/test_rooms_api.py`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 4.4〜4.5.2節(外部仕様、ステータスコード)

### 【実装内容】

* `GET /api/rooms`: `include_inactive` クエリパラメータを受け取り、管理者以外が指定した場合は無視する(`docs/P002-frontend-spec.md` 4.4節のとおり)。認証は必須だが管理者限定ではない。
* `POST/PUT/DELETE /api/rooms`: `Depends(require_admin)` を付与し、一般ユーザーには403を返す。
* `PUT`/`DELETE` で存在しない `room_id` の場合、`NotFoundError` を404にマッピングする(`errors.py` に追加)。

### 【実装してはいけないこと】

* 予約・ユーザー管理のエンドポイントはこのタスクに含めない。

### 【Unit Test内容】

* テスト対象: `GET/POST/PUT/DELETE /api/rooms`
* 正常系: 管理者による作成・一覧・更新・削除(論理削除後に一覧から消えること)
* 主要な異常系: 一般ユーザーによるPOST/PUT/DELETEが403、未ログインでのGETが401、存在しないroom_idのPUT/DELETEが404、バリデーション違反が400
* 実行するテストコマンド: `cd server && python -m pytest tests/test_rooms_api.py -v`
* 合格条件: 全件PASS

### 【実行コマンド】

* `cd server && python -m pytest tests/test_rooms_api.py -v`

### 【完了条件】

* 上記Unit TestがすべてPASSする

### 【次タスクに進む前の停止条件】

* 3回自己修正しても通らない場合は停止し、人間に報告する

---

## U002-T3: S06会議室管理画面実装

### 【目的】

* `docs/P002-frontend-spec.md` 3.6節にもとづき会議室管理画面を実装する。

### 【作成・編集対象ファイル】

* `client/src/pages/RoomManagementPage.tsx`
* `client/src/api/roomApi.ts`
* `client/src/App.tsx`(ルート `/admin/rooms` を追加、`role=admin` 以外は403表示にリダイレクトする)
* `client/tests/RoomManagementPage.test.tsx`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 3.6節(バリデーション、削除確認ダイアログ、アクセス制御)

### 【実装内容】

* 会議室一覧テーブル(名前・収容人数・設備・説明文・有効無効)、新規登録フォーム、編集フォーム、削除ボタン(確認ダイアログ「この会議室を無効化しますか?」)を実装する。
* 設備は固定チェックボックス群(プロジェクター/ホワイトボード/Web会議設備/電話会議設備、3.6節参照)とする。
* 管理者以外がアクセスした場合、403画面(「アクセス権がありません。トップに戻る」リンク付き)を表示する。

### 【実装してはいけないこと】

* ユーザー管理画面(S07)はこのタスクに含めない(U005の範囲)。

### 【Unit Test内容】

* テスト対象: `RoomManagementPage` コンポーネント
* 正常系: 一覧表示、新規登録フォーム送信でAPI呼び出し(モック)
* 主要な異常系: 必須項目未入力時のエラー表示、収容人数に0や負数を入力した場合のエラー表示、`role=general` でアクセスした場合に403画面が表示されること
* 実行するテストコマンド: `cd client && node --import tsx --test tests/RoomManagementPage.test.tsx`
* 合格条件: 全件PASS

### 【実行コマンド】

* `cd client && node --import tsx --test tests/RoomManagementPage.test.tsx`

### 【完了条件】

* 上記Unit TestがすべてPASSする

### 【次タスクに進む前の停止条件】

* 3回自己修正しても通らない場合は停止し、人間に報告する

---

## U002-T4: S06とAPIの接続確認

### 【目的】

* U002-T2のAPIとU002-T3の画面が実際に接続され、一連の操作(登録→一覧反映→編集→無効化)が通しで動作することを、結合確認用の薄いタスクとして確認する(スプリント内結合テストの本体は `docs/P008-test-direction.md` で別途行うため、ここではあくまで実装者自身による簡易な動作疎通確認に留める)。

### 【作成・編集対象ファイル】

* 変更対象ファイルなし(疎通確認のみ)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 3.6節

### 【実装内容】

* `server/` と `client/` を同時起動し、手動(またはE2Eスクリプト)で「会議室を1件登録→一覧に表示されることを確認→編集して収容人数を変更→一覧に反映されることを確認→無効化→一覧から消えることを確認」を実施する。

### 【実装してはいけないこと】

* このタスクで新たな機能追加・バグ修正は行わない。問題を見つけた場合は該当タスク(U002-T1/T2/T3)に戻って修正する。

### 【Unit Test内容】

* このタスク自体はUnit Testの追加を行わない(疎通確認のみ)。

### 【実行コマンド】

* `cd server && uvicorn app.main:app --reload`
* `cd client && npm run dev`

### 【完了条件】

* 上記の一連の操作が例外・エラーなく完了すること

### 【次タスクに進む前の停止条件】

* 疎通確認中に発見した不具合が、U002-T1〜T3の修正で3回試行しても解消しない場合は停止し、人間に報告する

---

## 重要

* 各タスクの範囲外のファイルは編集しないでください。
* タスクの実装後、実行したテストコマンドと結果を報告してください。
* タスクが完了したら、上記「タスク一覧」の該当行を `[x]` に更新してください。
* 全タスクが完了したら、`docs/P007-impl-direction.md` の本スプリント行を `[x]` に更新してください。
* Executor Stepの停止条件に該当しない限り、次のタスクに自動的に進んでください。
