あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F003

## 【対応する失敗テスト】A003(S04側のみ。S05側はF001参照)

## 【障害記録】

* 症状: 会議室が無効化された後、その会議室での予約をS04(予約詳細・編集画面)で開くと、編集可能なユーザー(予約者本人・管理者)には会議室名がどこにも表示されない。
* 発生条件: `client/src/pages/ReservationDetailPage.tsx`は、`reservation.editable === true`の場合に編集フォームを表示する。会議室の選択肢は`reservationApi.listRooms()`(内部で`roomApi.listRooms(false)`を呼び出し、`include_inactive`を指定しないため有効な会議室のみを返す)から構築される。予約対象の会議室が無効化されていると、その会議室に対応する`<option>`要素自体が存在しないため、`<select>`の値(`form.roomId`)が有効な選択肢のどれとも一致せず、会議室名が画面のどこにも表示されない。
  * 読み取り専用ビュー(`reservation.editable === false`の場合)は`reservation.room_name`を直接テキスト表示しているため、この問題の影響を受けない。
* 原因区分: **アプリケーションコードの欠陥**

## 【参照ファイル】

* `client/src/pages/ReservationDetailPage.tsx`(179〜191行目付近の`<select id="detail-room">`)
* `client/src/api/roomApi.ts`(`listRooms`関数、`include_inactive`パラメータ)
* `docs/P002-frontend-spec.md` 3.6節(「無効化された会議室は...既存の予約データ...には引き続き会議室名を表示する」)
* `docs/test-records/20260809-1900-test-record.md` A003の詳細な原因分析

## 【調査方針】

* S03(`ReservationCreatePage.tsx`)は新規作成のみを扱うため有効な会議室のみでよいが、S04(編集)は既存予約が無効化済みの会議室を参照しているケースがあるため、両者で必要なデータが異なることを確認する。
* `reservationApi.listRooms()`を`include_inactive=true`で呼び出すよう変更した場合、無効な会議室が選択肢に含まれることになるが、これは「表示上は見える」だけであり、実際に無効な会議室で更新を試みた場合にサーバー側バリデーションで拒否されるか(`reservation_service.update_reservation`は`room_repository.find_by_id`で`is_active`をチェックしている)を確認する。

## 【修正方針】

* `client/src/pages/ReservationDetailPage.tsx`の会議室取得を`reservationApi.listRooms()`(有効のみ)から、無効な会議室も含めて取得する方式に変更する。ただし`reservationApi.listRooms()`自体はS02(カレンダーの会議室フィルタ)等でも使われる共有関数のため、シグネチャを不用意に変更しない。
  * 候補案A: 予約詳細取得時のレスポンス(`GET /api/reservations/{id}`)に含まれる`room_id`・`room_name`を使い、現在選択されている会議室が`rooms`一覧に無い場合はその1件だけを選択肢に追加で差し込む(表示上のワークアラウンド、サーバー側の追加呼び出し不要)。
  * 候補案B: `reservationApi`に`listAllRoomsIncludingInactive()`のような新規関数を追加し、S04専用に呼び出す(バックエンドの`GET /api/rooms?include_inactive=true`は現状「管理者のみ有効」であるため、一般ユーザーの予約者本人がこの画面を開いた場合に403になる懸念がある。`docs/P002-frontend-spec.md` 4.4節を確認し、この案が実装可能か判断する)。
  * 候補Bは認可の制約(`include_inactive=true`が管理者専用)に抵触する可能性が高いため、候補Aを優先して検討する。
* 選定した方針をこのファイルの「修正内容」として記録し、実装する。

## 【試行錯誤してよい範囲】

* `client/src/pages/ReservationDetailPage.tsx`が主たる変更対象。
* バックエンドAPIの認可要件(`GET /api/rooms?include_inactive=true`が管理者専用)は変更しない(仕様変更を伴うため、変更が必要と判断した場合はP204に回す)。

## 【修正成功時に更新するdocs】

* `client/INDEX.md`: `ReservationDetailPage.tsx`があれば、その項目に修正内容を反映する(現状INDEX.mdには個別ページの不具合注記はまだ無いため、新規追加は不要な場合はそのままでよい)。

## 【ロールバック条件】

* 修正後、既存のReservationDetailPage関連の単体テスト(`client/tests/ReservationDetailPage.test.tsx`)のいずれかが新たに失敗する場合。
* 修正が一般ユーザー(予約者本人、非管理者)に対して403エラーを新たに引き起こす場合。

## 【検証コマンド】

* `cd client && node --import tsx --test tests/ReservationDetailPage.test.tsx`(既存単体テストの回帰確認)
* `cd client && node --import tsx --test tests/acceptance/inactiveRoomHistory.test.tsx`(A003相当。ただしS05側の並行アクセス不具合(F001)が先に解消されている必要がある)

## 【完了条件】

* 上記検証コマンドがすべてPASSする。
* 無効化済み会議室に紐づく予約を、予約者本人(一般ユーザー)としてS04で開いた場合に、403にならず会議室名が表示される。

## 重要:

* 作業開始前に現在の変更状態を確認してください。
* 必要な範囲でソースコード変更を試して構いません。
* 修正に成功した場合は、関連する docs/* も必要に応じて更新してください。
* 修正しきれなかった場合は、試行錯誤で変更した未完了のソースコードを元の状態に戻してください。

## 完了条件:

* 全モジュールビルド成功
* すべての Unit Test 成功
* すべての結合テスト成功(P008・P009)
* `docs/P202-fix-plan/P202-fix-resolved.md` に全修正結果が記録されている
* 未解決障害がない、または `docs/P202-fix-plan/P202-fix-unresolved.md` に未解決なしと明記されている

## 未解決時の記録方法:

* 修正しきれなかった障害が1件でもある場合、`TEMPLATE-P202-fix-unresolved.md` の構成に従って `docs/P202-fix-plan/P202-fix-unresolved.md` を作成または更新するよう指示する。

---

## 【修正結果(P203実施)】

* 修正日: 2026-08-09
* 実施内容: 【調査方針】で検討した候補案Aを採用した。`reservationApi.listRooms()`(有効な会議室のみ)の結果に、現在の予約が参照する`room_id`が含まれていない場合は、予約詳細レスポンス自身の`room_id`/`room_name`から合成した1件をリストの先頭に追加する`roomOptions`という派生値を新設し、`<select>`の選択肢と、収容人数バリデーションに使う`selectedRoom`の両方をこの`roomOptions`ベースに変更した。合成エントリの`capacity`は実際の値が取得できないため`Number.POSITIVE_INFINITY`とし(`0`にすると収容人数バリデーションが常にエラーになってしまうため)、この合成エントリのままでは実際に更新を保存できない(サーバー側`update_reservation`が無効化済み会議室を拒否するため)ことをコメントに明記した。バックエンドAPIの認可要件(`include_inactive=true`が管理者専用)は変更していない。
* 変更したソースコード: `client/src/pages/ReservationDetailPage.tsx`(`roomOptions`の追加、`selectedRoom`・`<select>`の参照先変更)
* 更新したdocs: なし
* 実行したテスト・結果:
  * `cd client && node --import tsx --test tests/ReservationDetailPage.test.tsx` → 5件PASS(回帰なし)
  * `cd client && node --import tsx --test tests/acceptance/inactiveRoomHistory.test.tsx` → 3回連続で3件ともPASS(修正前はS04側のみ決定的にFAILしていた)
* テスト結果: A003(S04側)がPASSに転じたことを確認した。
* 残課題: なし。合成エントリを実際に選択した状態のまま更新を試みた場合にサーバー側で404になる、という残存挙動はあるが、これは意図した設計(無効化済み会議室では更新できない)であり不具合ではない。
* 修正経緯: 候補案Aを一発で実装し、追加の試行錯誤は不要だった。
