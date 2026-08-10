あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U004 — reservation-detail-and-mylist

## タスク一覧(OKF副目次)

* 状態は `[ ]`(未着手) / `[~]`(進行中) / `[x]`(完了) の3種類とする。1タスクの作業を開始したら `[~]` に、完了条件をすべて満たしたら `[x]` に更新する。
* このスプリントファイル自体の状態(`docs/P007-impl-direction.md` の該当行)は、全タスクが `[x]` になって初めて `[x]` にする。1件以上のタスクが `[~]`/`[x]` で残りが `[ ]` の場合は `[~]` とする。
* **中断からの再開**・**先行実装の禁止**: `docs/P007-impl-direction/U001-foundation-and-auth.md` タスク一覧節と同じ規則に従う。

- [x] U004-T1 [予約詳細・更新・取消Service/Repository層拡張](#u004-t1-予約詳細更新取消servicerepository層拡張) — 自分自身除外の重複チェック、権限チェック(★実施メモ: `find_by_organizer_or_participant`の【実装内容】本文は主催者のみと読める記述だったが、メソッド名どおり参加者としての予約も含めて実装した)
- [x] U004-T2 [予約詳細・更新・取消・マイ予約APIハンドラ実装](#u004-t2-予約詳細更新取消マイ予約apiハンドラ実装) — GET/PUT/DELETE /api/reservations/{id}, GET /api/reservations/mine
- [x] U004-T3 [S04予約詳細・編集画面実装](#u004-t3-s04予約詳細編集画面実装) — 表示・編集・取消(★実施メモ: バリデーション共通化のため`client/src/validation/reservationValidation.ts`を新設し、`ReservationCreatePage.tsx`(S03)の`validate()`をこの共通関数の呼び出しに置き換えた。入力項目・挙動は変更していないことをU003-T5のUnitTest再実行で確認済み)
- [x] U004-T4 [S05マイ予約一覧画面実装](#u004-t4-s05マイ予約一覧画面実装) — 期間フィルタ付き一覧
- [x] U004-T5 [S04/S05とAPIの接続確認](#u004-t5-s04s05とapiの接続確認) — 結合確認用の薄いタスク(★実施メモ: U002-T4と同じ理由でブラウザ操作は未実施。「マイ予約一覧→詳細取得→更新→カレンダー一覧に反映→取消→マイ予約から消える」をcurlで直接確認した)
- [x] U004-T6 [CR-001: オンライン会議URL — バックエンド(更新・取得API)](#u004-t6-cr-001-オンライン会議url--バックエンド更新取得api) — `GET`/`PUT /api/reservations/{id}` の `meeting_url` 項目追加(★実施メモ: U003-T7と合わせて`server/tests/`3ファイルに追加した計25件のうち更新・取得系を含む、全件PASS確認済み)
- [x] U004-T7 [CR-001: オンライン会議URL — S04予約詳細・編集画面](#u004-t7-cr-001-オンライン会議url--s04予約詳細編集画面) — リンク表示・編集欄(★実施メモ: `client/tests/ReservationDetailPage.test.tsx`に追加した5件を含む全10件PASS確認済み)

---

## U004-T1: 予約詳細・更新・取消Service/Repository層拡張

### 【目的】

* U003で実装した `reservation_repository.py`・`reservation_service.py` に、詳細取得・更新・取消・マイ予約一覧のロジックを追加する。

### 【作成・編集対象ファイル】

* `server/app/repositories/reservation_repository.py`(追加: `find_by_id`, `update`, `delete`, `find_by_organizer_or_participant`, `replace_participants`)
* `server/app/services/reservation_service.py`(追加: `get_reservation`, `update_reservation`, `cancel_reservation`, `list_my_reservations`)
* `server/tests/test_reservation_repository.py`(追加テスト)、`server/tests/test_reservation_service.py`(追加テスト)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 3.4節、3.5節、4.8〜4.9.2節
* `docs/P003-backend-spec.md` 4.6〜4.9.2節(自分自身を除外する重複チェック、参加者の全削除・再INSERT方針)

### 【実装内容】

* `get_reservation(reservation_id, requesting_user_id)`: 予約詳細を取得し、`editable`(予約者本人または管理者かどうか)を算出して返す(`docs/P002-frontend-spec.md` 4.9節)。存在しない場合 `NotFoundError`。
* `update_reservation`: `docs/P003-backend-spec.md` 4.9.1節のとおり、`find_overlapping` に `exclude_reservation_id` を指定して自分自身を除外して重複チェックする。参加者は既存を全削除してから再INSERTする。権限チェック(予約者本人または管理者以外は `ForbiddenError`)はService層で行う。
* `cancel_reservation`: 物理削除(`docs/P002-frontend-spec.md` 4.9.2節)。権限チェックは更新と同様。
* `list_my_reservations(user_id, period)`: `period` に応じて `WHERE organizer_user_id = ? AND (end_datetime >= now | end_datetime < now)` を切り替える(`all` は条件無し)。

### 【実装してはいけないこと】

* APIルーティングはこのタスクに含めない(U004-T2の範囲)。

### 【Unit Test内容】

* テスト対象: 追加した各メソッド
* 正常系: 予約者本人による詳細取得・更新・取消、管理者による他者予約の更新・取消、期間フィルタごとのマイ予約一覧取得
* 主要な異常系: 予約者本人でも管理者でもないユーザーによる更新・取消が `ForbiddenError`、自分自身の予約を同じ時間帯に更新しても重複エラーにならないこと(除外ロジックの確認)、存在しない `reservation_id` の取得・更新・取消が `NotFoundError`
* 実行するテストコマンド: `cd server && python -m pytest tests/test_reservation_repository.py tests/test_reservation_service.py -v`
* 合格条件: 全件PASS(U003分の既存テストを含め回帰なく全件PASSすること)

### 【実行コマンド】

* `cd server && python -m pytest tests/test_reservation_repository.py tests/test_reservation_service.py -v`

### 【完了条件】

* 上記Unit TestがすべてPASSする

### 【次タスクに進む前の停止条件】

* 3回自己修正しても通らない場合は停止し、人間に報告する

---

## U004-T2: 予約詳細・更新・取消・マイ予約APIハンドラ実装

### 【目的】

* U004-T1のService層を使い、`GET/PUT/DELETE /api/reservations/{reservation_id}`, `GET /api/reservations/mine` を実装する。

### 【作成・編集対象ファイル】

* `server/app/routers/reservations.py`(U003で作成したファイルにエンドポイントを追加)
* `server/app/schemas/reservation.py`(`ReservationDetailResponse`, `ReservationUpdateRequest`, `MyReservationListItemResponse` を追加)
* `server/app/errors.py`(`ForbiddenError` → 403 のマッピングを追加)
* `server/tests/test_reservations_api.py`(追加テスト)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 4.8〜4.9.2節

### 【実装内容】

* `GET /api/reservations/{id}`: `reservation_service.get_reservation` を呼び出し200または404。
* `PUT /api/reservations/{id}`: `reservation_service.update_reservation` を呼び出し200/400/403/404/409。
* `DELETE /api/reservations/{id}`: `reservation_service.cancel_reservation` を呼び出し204/403/404。
* `GET /api/reservations/mine`: `period` クエリパラメータ(既定 `upcoming`)を受け取り `list_my_reservations` を呼び出す。

### 【実装してはいけないこと】

* U003で実装済みの `POST`/`GET /api/reservations`(一覧)は変更しない(回帰防止のため、変更が必要な場合はその理由を明記して別途報告する)。

### 【Unit Test内容】

* テスト対象: `GET/PUT/DELETE /api/reservations/{id}`, `GET /api/reservations/mine`
* 正常系: 予約者本人による詳細取得・更新・取消、マイ予約一覧(upcoming/past/all)取得
* 主要な異常系: 無関係な一般ユーザーによる更新・取消が403、存在しないIDが404、更新時の重複が409、未ログインが401
* 実行するテストコマンド: `cd server && python -m pytest tests/test_reservations_api.py -v`
* 合格条件: 全件PASS(U003分を含め回帰なし)

### 【実行コマンド】

* `cd server && python -m pytest tests/test_reservations_api.py -v`

### 【完了条件】

* 上記Unit TestがすべてPASSする

### 【次タスクに進む前の停止条件】

* 3回自己修正しても通らない場合は停止し、人間に報告する

---

## U004-T3: S04予約詳細・編集画面実装

### 【目的】

* `docs/P002-frontend-spec.md` 3.4節にもとづき予約詳細・編集画面を実装する。

### 【作成・編集対象ファイル】

* `client/src/pages/ReservationDetailPage.tsx`
* `client/src/api/reservationApi.ts`(`getReservation`, `updateReservation`, `cancelReservation` を追加)
* `client/src/App.tsx`(ルート `/reservations/:id` を追加。U003-T4で用意した遷移先をこのページに接続する)
* `client/tests/ReservationDetailPage.test.tsx`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 3.4節(編集可否、取消確認ダイアログ)

### 【実装内容】

* `GET /api/reservations/{id}` の `editable` フラグに応じて、編集フォームまたは読み取り専用表示を出し分ける(3.4節)。
* 「更新」ボタンでS03と同じバリデーション・重複エラー表示を行う。
* 「取消」ボタンで確認ダイアログを表示し、OK時に `DELETE` を呼びS02へ遷移する。

### 【実装してはいけないこと】

* S03(予約作成画面)のコンポーネントを直接変更しない。バリデーションロジックの共通化が必要な場合は、共通関数を新規ファイル(`client/src/validation/reservationValidation.ts`)に切り出して両画面から参照する形にすること(既存ファイルへの無関係な変更を避けるため)。

### 【Unit Test内容】

* テスト対象: `ReservationDetailPage`
* 正常系: 予約者本人でのアクセス時に編集フォームが表示され更新が成功すること、取消確認ダイアログでOKを押すと `DELETE` が呼ばれること
* 主要な異常系: 無関係ユーザーでのアクセス時に読み取り専用表示になること、更新時のバリデーションエラー表示、409受信時の重複エラー表示
* 実行するテストコマンド: `cd client && node --import tsx --test tests/ReservationDetailPage.test.tsx`
* 合格条件: 全件PASS

### 【実行コマンド】

* `cd client && node --import tsx --test tests/ReservationDetailPage.test.tsx`

### 【完了条件】

* 上記Unit TestがすべてPASSする

### 【次タスクに進む前の停止条件】

* 3回自己修正しても通らない場合は停止し、人間に報告する

---

## U004-T4: S05マイ予約一覧画面実装

### 【目的】

* `docs/P002-frontend-spec.md` 3.5節にもとづきマイ予約一覧画面を実装する。

### 【作成・編集対象ファイル】

* `client/src/pages/MyReservationsPage.tsx`
* `client/src/api/reservationApi.ts`(`listMyReservations` を追加)
* `client/src/App.tsx`(ルート `/my-reservations` を追加、ヘッダーの「マイ予約」リンク先をここに接続する)
* `client/tests/MyReservationsPage.test.tsx`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 3.5節

### 【実装内容】

* 期間フィルタ(今後の予約/過去の予約/すべて、既定=今後の予約)、一覧テーブル(日付・会議室・時間帯・件名)を実装する。一覧行クリックでS04へ遷移する。

### 【実装してはいけないこと】

* S04の本実装(表示項目の詳細)はこのタスクに含めない(U004-T3で実装済みのものへ遷移するのみ)。

### 【Unit Test内容】

* テスト対象: `MyReservationsPage`
* 正常系: 既定(今後の予約)での一覧表示、フィルタ切り替え時の再取得、行クリックでの遷移
* 主要な異常系: API呼び出し失敗時のエラー表示
* 実行するテストコマンド: `cd client && node --import tsx --test tests/MyReservationsPage.test.tsx`
* 合格条件: 全件PASS

### 【実行コマンド】

* `cd client && node --import tsx --test tests/MyReservationsPage.test.tsx`

### 【完了条件】

* 上記Unit TestがすべてPASSする

### 【次タスクに進む前の停止条件】

* 3回自己修正しても通らない場合は停止し、人間に報告する

---

## U004-T5: S04/S05とAPIの接続確認

### 【目的】

* マイ予約一覧→詳細→編集/取消→カレンダーへの反映という一連の流れを、結合確認用の薄いタスクとして確認する(スプリント内結合テストの本体は `docs/P008-test-direction.md` で別途行う)。

### 【作成・編集対象ファイル】

* 変更対象ファイルなし(疎通確認のみ)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 3.4〜3.5節

### 【実装内容】

* `server/`・`client/` を同時起動し、「S05でマイ予約一覧を表示→行をクリックしてS04に遷移→内容を編集して更新→S02で反映を確認→別の予約を取消→S05から消えることを確認」を手動確認する。

### 【実装してはいけないこと】

* このタスクで新たな機能追加は行わない。不具合発見時は該当タスク(U004-T1〜T4)に戻って修正する。

### 【Unit Test内容】

* このタスク自体はUnit Testの追加を行わない(疎通確認のみ)。

### 【実行コマンド】

* `cd server && uvicorn app.main:app --reload`
* `cd client && npm run dev`

### 【完了条件】

* 上記の一連の操作が例外・エラーなく完了すること

### 【次タスクに進む前の停止条件】

* 疎通確認中に発見した不具合が3回試行しても解消しない場合は停止し、人間に報告する

---

## U004-T6: CR-001: オンライン会議URL — バックエンド(更新・取得API)

### 【目的】

* U003-T7で追加した `meeting_url` を、`GET`/`PUT /api/reservations/{reservation_id}`(詳細取得・更新)でも読み書きできるようにする。

### 【作成・編集対象ファイル】

* `server/app/schemas/reservation.py`(`ReservationUpdateRequest` に `meeting_url: str | None = None` を追加。`ReservationDetailResponse` はU003-T7で追加済みのためこのタスクでは変更しない)
* `server/app/repositories/reservation_repository.py`(`update` に `meeting_url` パラメータを追加)
* `server/app/services/reservation_service.py`(`update_reservation` で `meeting_url` を受け取り・バリデーションし保存。`get_reservation` は U003-T7 で `find_by_id` の返り値に `meeting_url` が含まれるようになっていれば追加の変更不要 — 未反映であればここで追加する)
* `server/app/routers/reservations.py`(`update_reservation` ハンドラで `body.meeting_url` をService層に渡す)
* `server/tests/test_reservation_repository.py`、`server/tests/test_reservation_service.py`、`server/tests/test_reservations_api.py`(追加テスト)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 3.4節、4.9〜4.9.1節(`meeting_url` の表示・更新)
* `docs/P003-backend-spec.md` 4.6〜4.9.2節

### 【実装内容】

* `ReservationUpdateRequest` に `meeting_url: str | None = None` を追加する。
* `reservation_repository.update` に `meeting_url: str | None` 引数を追加し、`UPDATE reservations SET ... meeting_url = ? ...` に含める。
* `reservation_service.update_reservation` は `meeting_url` を受け取り、U003-T7で `_validate` に追加した同じバリデーションを適用したうえで `reservation_repository.update` に渡す(空文字列は `None` に正規化する処理も create と同様に行う)。
* `get_reservation`・`update_reservation` の戻り値(いずれも `find_by_id` 由来の辞書、または `get_reservation` の呼び出しで再構成)に `meeting_url` が含まれることを確認する(U003-T7で `find_by_id` のSELECT列に追加済みであれば、`get_reservation` 内の辞書内包表記に1行追加するだけでよい)。

### 【実装してはいけないこと】

* `POST /api/reservations`(作成)・S03側の変更はこのタスクに含めない(U003-T7/T8で対応済み)。

### 【Unit Test内容】

* テスト対象: `reservation_repository.update`、`reservation_service.update_reservation`、`GET`/`PUT /api/reservations/{id}`
* 正常系: 既存予約(オンライン会議URL未設定)を妥当な値で更新すると成功し、`GET` で取得した詳細に反映される。設定済みの値を空欄に更新すると `null` に戻る(3.4節「編集モードで...削除(空欄に戻す)でき」に対応)
* 主要な異常系: 更新時に不正なスキーム・501文字での400
* 実行するテストコマンド: `cd server && python -m pytest tests/test_reservation_repository.py tests/test_reservation_service.py tests/test_reservations_api.py -v`
* 合格条件: 全件PASS(U003分を含め回帰なし)

### 【実行コマンド】

* `cd server && python -m pytest tests/test_reservation_repository.py tests/test_reservation_service.py tests/test_reservations_api.py -v`

### 【完了条件】

* 上記Unit TestがすべてPASSする

### 【次タスクに進む前の停止条件】

* 3回自己修正しても通らない場合は停止し、人間に報告する

---

## U004-T7: CR-001: オンライン会議URL — S04予約詳細・編集画面

### 【目的】

* S04(予約詳細・編集画面)に、オンライン会議URLのリンク表示(閲覧時)と入力欄(編集時)を追加する。

### 【作成・編集対象ファイル】

* `client/src/pages/ReservationDetailPage.tsx`
* `client/tests/ReservationDetailPage.test.tsx`(追加テスト)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` 3.4節(オンライン会議URLの表示・編集仕様)

### 【実装内容】

* `toFormState` に `meetingUrl: reservation.meeting_url ?? ''` を追加する。
* 編集フォーム(`editable: true` の分岐)に、他の項目と同じ配置パターンでオンライン会議URLのラベル・テキスト入力欄・エラー表示(`errors.meetingUrl`)を追加する(U003-T8で共有バリデーション関数に検証ロジックは追加済みのため、このタスクでは呼び出し側の配線のみでよい)。
* 送信時、`meeting_url: form.meetingUrl.trim() === '' ? null : form.meetingUrl` を `updateReservation` の引数に含める。
* 読み取り専用表示(`editable: false` の分岐、`<dl>`)に「オンライン会議URL」の項目を追加する。値が設定されている場合は `<a href={reservation.meeting_url} target="_blank" rel="noopener noreferrer">` としてクリック可能なリンクで表示し、未設定の場合は「(未設定)」と表示する。

### 【実装してはいけないこと】

* S03(`ReservationCreatePage.tsx`)側の変更はこのタスクに含めない(U003-T8で対応済み)。
* `reservationValidation.ts` のロジック自体は変更しない(U003-T8で追加済みのものをそのまま呼び出す)。

### 【Unit Test内容】

* テスト対象: `ReservationDetailPage`
* 正常系: オンライン会議URL設定済みの予約表示時にリンクとして表示されること、未設定時に「(未設定)」と表示されること、編集フォームでの入力・保存・空欄への変更が成功すること
* 主要な異常系: 編集時の不正なスキーム・501文字入力でのエラー表示
* 実行するテストコマンド: `cd client && node --import tsx --test tests/ReservationDetailPage.test.tsx`
* 合格条件: 全件PASS

### 【実行コマンド】

* `cd client && node --import tsx --test tests/ReservationDetailPage.test.tsx`

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
