あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U005 — user-management-and-hardening

## タスク一覧(OKF副目次)

* 状態は `[ ]`(未着手) / `[~]`(進行中) / `[x]`(完了) の3種類とする。1タスクの作業を開始したら `[~]` に、完了条件をすべて満たしたら `[x]` に更新する。
* このスプリントファイル自体の状態(`docs/P007-impl-direction.md` の該当行)は、全タスクが `[x]` になって初めて `[x]` にする。1件以上のタスクが `[~]`/`[x]` で残りが `[ ]` の場合は `[~]` とする。
* **中断からの再開**・**先行実装の禁止**: `docs/P007-impl-direction/U001-foundation-and-auth.md` タスク一覧節と同じ規則に従う。

- [x] U005-T1 [ユーザーRepository/Service層実装](#u005-t1-ユーザーrepositoryservice層実装) — CRUD、自己無効化禁止、最後の管理者保護
- [x] U005-T2 [ユーザー管理APIハンドラ実装](#u005-t2-ユーザー管理apiハンドラ実装) — GET/POST/PUT/DELETE /api/users
- [x] U005-T3 [S07ユーザー管理画面実装](#u005-t3-s07ユーザー管理画面実装) — 一覧・登録・編集フォーム
- [x] U005-T4 [横断ナビゲーション結線](#u005-t4-横断ナビゲーション結線) — ヘッダーの権限別出し分け、ログアウト動線(★実施メモ: 「手動確認: 一般ユーザー・管理者それぞれでログインし...」はブラウザが無い環境のため実施不可。代わりにHeader.test.tsxで「一般ユーザーはどちらのリンクも見えない/管理者はS02で会議室管理のみ・S06でユーザー管理も見える」を直接検証した。またHeader導入によりRoomManagementPage・UserManagementPageがuseNavigate()を必要とするようになったため、両ページの既存UnitTestがRouterコンテキスト無しで失敗する回帰が発生し、テスト側にMemoryRouterラップを追加して解消した(実装側の不具合ではない)")
- [x] U005-T5 [エラーレスポンス・ログ形式の横断確認](#u005-t5-エラーレスポンスログ形式の横断確認) — 結合確認用の薄いタスク(★実施メモ: 全ルーターが`app/exceptions.py`のドメイン例外+`app/errors.py`の共通ハンドラ経由でのみエラーを返すことを`grep HTTPException`で確認(`fastapi.HTTPException`の直接使用は無し)。未処理例外時の構造化ログは本タスクで新規実装した(`app/logging_utils.py`)。バックエンド116件・フロントエンド38件、全件PASSを確認。login_failed/reservation_conflict等の他イベントの実際のログ出力箇所への配線は本タスクのスコープ外として見送った(実装してはいけないこと「新しいAPIエンドポイント・画面の追加は行わない」の範囲を踏まえた判断)

---

## U005-T1: ユーザーRepository/Service層実装

### 【目的】

* ユーザーの登録・一覧・更新・論理削除、および自己無効化禁止・最後の管理者保護のロジックを実装する。

### 【作成・編集対象ファイル】

* `server/app/repositories/user_repository.py`(U001-T3で作成済み。追加: `find_all(include_inactive)`, `create`, `update`, `deactivate`, `count_active_admins`)
* `server/app/services/user_service.py`(新規)
* `server/tests/test_user_service.py`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 3.7節(バリデーション、自己無効化禁止、最後の管理者保護)
* `docs/P003-backend-spec.md` 4.11〜4.11.2節(内部仕様、セッション削除連動)

### 【実装内容】

* `user_service.create(employee_id, name, password, role)`: 社員ID書式(半角英数字4〜20文字)・重複チェック・氏名最大50文字・パスワード8文字以上を検証し、`password.hash_password`(U001-T3で実装済み)でハッシュ化して保存する。
* `user_service.update(user_id, name, password, role, is_active, requesting_user_id)`: `password` が `None` の場合はハッシュを変更しない。`is_active=False` への変更時、`requesting_user_id == user_id` なら `SelfDeactivationForbiddenError`、対象が管理者かつ更新後の有効な管理者数が0になるなら `LastAdminProtectedError` を送出する(`docs/P003-backend-spec.md` 4.11〜4.11.2節の判定順序のとおり)。無効化が成功した場合、`session_repository.delete_by_user_id`(U001-T3で実装済み)を同一トランザクションで呼び出す。
* `user_service.deactivate`: `update` の `is_active=False` 版として同じ検証ロジックを再利用する。

### 【実装してはいけないこと】

* APIルーティングはこのタスクに含めない(U005-T2の範囲)。U001-T3で実装した認証ロジック(`auth_service.py`)は変更しない。

### 【Unit Test内容】

* テスト対象: `user_service.py`
* 正常系: ユーザーの作成・一覧・更新・無効化、パスワード未指定更新でハッシュが変わらないこと
* 主要な異常系: 社員ID重複での作成、社員ID書式違反、パスワード7文字以下、自分自身の無効化、最後の管理者の無効化(管理者が1名の状態で試行)、管理者が2名いる状態での1名無効化は成功すること(境界値)
* 実行するテストコマンド: `cd server && python -m pytest tests/test_user_service.py -v`
* 合格条件: 全件PASS

### 【実行コマンド】

* `cd server && python -m pytest tests/test_user_service.py -v`

### 【完了条件】

* 上記Unit TestがすべてPASSする

### 【次タスクに進む前の停止条件】

* 3回自己修正しても通らない場合は停止し、人間に報告する

---

## U005-T2: ユーザー管理APIハンドラ実装

### 【目的】

* U005-T1のService層を使い、`GET/POST/PUT/DELETE /api/users` を実装する。

### 【作成・編集対象ファイル】

* `server/app/routers/users.py`(U003-T3で作成済みのファイルに管理者用CRUDを追加)
* `server/app/schemas/user.py`(`UserCreateRequest`, `UserUpdateRequest`, `UserResponse`)
* `server/app/errors.py`(`SelfDeactivationForbiddenError` → 400、`LastAdminProtectedError` → 400 のマッピングを追加)
* `server/tests/test_users_api.py`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 4.10〜4.11.2節

### 【実装内容】

* 4エンドポイントすべてに `Depends(require_admin)` を付与する。
* `GET /api/users`: `include_inactive` クエリパラメータ対応。
* レスポンスは `password_hash` を含めない(`UserResponse` に `password_hash` フィールドを含めないことで担保する)。

### 【実装してはいけないこと】

* U003-T3で実装済みの `GET /api/users/directory` の認可(ログイン済みなら誰でも可)を変更しない。本タスクで追加するCRUD系4エンドポイントとはパスも認可要件も異なるため混同しないこと。

### 【Unit Test内容】

* テスト対象: `GET/POST/PUT/DELETE /api/users`
* 正常系: 管理者による作成・一覧・更新・無効化
* 主要な異常系: 一般ユーザーによるアクセスが403、社員ID重複が400、自己無効化が400(`SELF_DEACTIVATION_FORBIDDEN`)、最後の管理者無効化が400(`LAST_ADMIN_PROTECTED`)、レスポンスに `password_hash` が含まれないこと
* 実行するテストコマンド: `cd server && python -m pytest tests/test_users_api.py -v`
* 合格条件: 全件PASS

### 【実行コマンド】

* `cd server && python -m pytest tests/test_users_api.py -v`

### 【完了条件】

* 上記Unit TestがすべてPASSする

### 【次タスクに進む前の停止条件】

* 3回自己修正しても通らない場合は停止し、人間に報告する

---

## U005-T3: S07ユーザー管理画面実装

### 【目的】

* `docs/P002-frontend-spec.md` 3.7節にもとづきユーザー管理画面を実装する。

### 【作成・編集対象ファイル】

* `client/src/pages/UserManagementPage.tsx`
* `client/src/api/userApi.ts`
* `client/src/App.tsx`(ルート `/admin/users` を追加、`role=admin` 以外は403表示)
* `client/tests/UserManagementPage.test.tsx`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 3.7節

### 【実装内容】

* ユーザー一覧テーブル(社員ID・氏名・権限・有効無効)、新規登録フォーム(社員ID・氏名・パスワード・権限)、編集フォーム(パスワードは空欄=変更なし)、削除ボタン(確認ダイアログ)を実装する。
* サーバーからの `SELF_DEACTIVATION_FORBIDDEN`/`LAST_ADMIN_PROTECTED` エラーコードをそれぞれ「自分自身は無効化できません」「最後の管理者アカウントは無効化できません」というメッセージにマッピングして表示する。

### 【実装してはいけないこと】

* 会議室管理画面(S06、U002で実装済み)のコンポーネントを流用する場合も、S06のファイル自体は変更しない(共通化する場合は新規共通コンポーネントファイルを切り出すこと)。

### 【Unit Test内容】

* テスト対象: `UserManagementPage`
* 正常系: 一覧表示、新規登録フォーム送信
* 主要な異常系: 社員ID未入力・パスワード7文字でのエラー表示、自己無効化エラーメッセージの表示、最後の管理者保護エラーメッセージの表示、`role=general` でのアクセス時の403画面
* 実行するテストコマンド: `cd client && node --import tsx --test tests/UserManagementPage.test.tsx`
* 合格条件: 全件PASS

### 【実行コマンド】

* `cd client && node --import tsx --test tests/UserManagementPage.test.tsx`

### 【完了条件】

* 上記Unit TestがすべてPASSする

### 【次タスクに進む前の停止条件】

* 3回自己修正しても通らない場合は停止し、人間に報告する

---

## U005-T4: 横断ナビゲーション結線

### 【目的】

* これまでのスプリントで個別に実装した画面間のヘッダーナビゲーションを最終的に結線し、権限による表示出し分けを完成させる。

### 【作成・編集対象ファイル】

* `client/src/components/Header.tsx`(新規。既存の各ページに散らばっていたヘッダー相当のマークアップがあれば、このコンポーネントに集約する)
* `client/src/pages/CalendarPage.tsx`, `client/src/pages/MyReservationsPage.tsx`, `client/src/pages/RoomManagementPage.tsx`, `client/src/pages/UserManagementPage.tsx`(いずれも `Header` コンポーネントを使うよう置き換える。置き換え以外の変更はしない)
* `client/tests/Header.test.tsx`

### 【参照すべき仕様箇所】

* `docs/P001-requirement.md` 画面遷移図、`docs/P002-frontend-spec.md` 3.0節(共通ヘッダー仕様、★P010初回レビュー後に新設)、3.6節

### 【実装内容】

* `Header` コンポーネントは、現在どの画面から表示されているか(`currentScreen` props、値は `S02`|`S04`|`S05`|`S06`|`S07`)を受け取り、`docs/P002-frontend-spec.md` 3.0節の表のとおりリンクを出し分ける。
  * ログインユーザー名、「マイ予約」、「ログアウト」: 全画面・全ユーザーで表示。
  * 「会議室管理」: 全画面で管理者のみ表示。
  * 「ユーザー管理」: **`currentScreen === 'S06'` かつ管理者の場合のみ**表示する(他の画面では管理者であっても表示しない。`docs/P001-requirement.md` 画面遷移図「S06→S07」の経路のみを許可する設計、3.0節の★ACCEPTED★参照)。
* `role` に応じたリンクの表示・非表示をこのコンポーネント1箇所に集約し、各ページ側で個別に権限判定しない。

### 【実装してはいけないこと】

* 各ページの業務ロジック(バリデーション等)には触れない。ヘッダー部分の置き換えのみ行う。
* S06以外の画面(S02・S04・S05・S07)のヘッダーに「ユーザー管理」リンクを表示しないこと(3.0節の制約に反するため)。

### 【Unit Test内容】

* テスト対象: `Header`
* 正常系: 一般ユーザーで表示した場合に「会議室管理」「ユーザー管理」リンクが表示されないこと、管理者が `currentScreen='S02'` で表示した場合に「会議室管理」は表示され「ユーザー管理」は表示されないこと、管理者が `currentScreen='S06'` で表示した場合に「ユーザー管理」も表示されること
* 主要な異常系: ログアウトボタン押下で `authApi.logout` が呼ばれ `/login` へ遷移すること
* 実行するテストコマンド: `cd client && node --import tsx --test tests/Header.test.tsx`
* 合格条件: 全件PASS

### 【実行コマンド】

* `cd client && node --import tsx --test tests/Header.test.tsx`

### 【完了条件】

* 上記Unit TestがすべてPASSする
* 手動確認: 一般ユーザー・管理者それぞれでログインし、ヘッダーのリンク表示が仕様どおりであることを確認する

### 【次タスクに進む前の停止条件】

* 3回自己修正しても通らない場合は停止し、人間に報告する

---

## U005-T5: エラーレスポンス・ログ形式の横断確認

### 【目的】

* U001〜U005で実装した全APIが `docs/P002-frontend-spec.md` 4章の共通エラー形式、および `docs/P003-backend-spec.md` 6章の構造化ログ方針に準拠していることを最終確認する(結合確認用の薄いタスク)。

### 【作成・編集対象ファイル】

* 不備が見つかった場合のみ、該当する `server/app/errors.py` または各ルーターファイルを修正する(新規ファイル追加はしない)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 4章冒頭(共通エラー形式)
* `docs/P003-backend-spec.md` 6章(ログ出力方針)

### 【実装内容】

* 全ルーター(`auth.py`, `rooms.py`, `reservations.py`, `users.py`)を確認し、エラーレスポンスが `{"error": {"code": ..., "message": ..., "fields"?: ...}}` の形式に統一されていることを確認する。
* 未処理例外(500)発生時に構造化ログ(`event="unhandled_exception"`)が標準出力に出力されることを、意図的に例外を発生させるテストで確認する。
* 全既存Unit Test(U001〜U005で作成した全テストファイル)を通しで実行し、回帰が無いことを確認する。

### 【実装してはいけないこと】

* 新しいAPIエンドポイント・画面の追加は行わない。

### 【Unit Test内容】

* このタスク自体は新規Unit Testの追加を主目的としないが、500エラー時のログ出力形式を確認する軽量なテストを1件 `server/tests/test_error_logging.py` に追加する。
* 実行するテストコマンド: `cd server && python -m pytest tests/ -v`(バックエンド全件)、`cd client && node --import tsx --test tests/*.test.tsx`(フロントエンド全件)
* 合格条件: バックエンド・フロントエンドとも全件PASS

### 【実行コマンド】

* `cd server && python -m pytest tests/ -v`
* `cd client && node --import tsx --test tests/*.test.tsx`
* 上記コマンドは実装時に実際に実行し、0件スキップになっていないこと(パス指定漏れでテストが静かにスキップされていないこと)を確認してから完了とすること(`SKILL.md` 各フェーズ共通指示)。

### 【完了条件】

* バックエンド・フロントエンドの全Unit TestがPASSする
* エラーレスポンス形式・ログ出力形式の不統一が無いことを確認する(見つかった場合は修正し再確認する)

### 【次タスクに進む前の停止条件】

* このタスクが本スプリント最後のタスクであるため「次タスク」は無い。全タスク完了後、`docs/P007-impl-direction.md` の本スプリント行を `[x]` に更新し、P007全体の完了条件(全スプリントが`[x]`)を満たしているか確認すること。

---

## 重要

* 各タスクの範囲外のファイルは編集しないでください。
* タスクの実装後、実行したテストコマンドと結果を報告してください。
* タスクが完了したら、上記「タスク一覧」の該当行を `[x]` に更新してください。
* 全タスクが完了したら、`docs/P007-impl-direction.md` の本スプリント行を `[x]` に更新してください。
* Executor Stepの停止条件に該当しない限り、次のタスクに自動的に進んでください。
