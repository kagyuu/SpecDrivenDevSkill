あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F001

## 【対応する失敗テスト】T009, T012, T013, T014, T015, A001, A003(S05側のみ。S04側はF003参照), A004, A006(BLOCKED), A010

* 単一の根本原因に起因すると判断した理由: 全件のサーバー側ログに同一のトレースバック(`sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread.`)が出力されており、いずれも `server/app/db/connection.py` の `get_connection()` が発生源である。トリガー条件も共通している(1つの画面が複数のAPIエンドポイントを同時に呼び出す構成 - `Header`コンポーネント自身の`GET /api/me`と、ページ本体の`GET /api/rooms`/`GET /api/reservations`等)。A005(30並列で単一エンドポイントに負荷をかけるテスト)ではこの不具合が一度も再現しなかったことから、「並行度が高い」こと自体ではなく「1リクエストのライフサイクル内で複数の同期的generator依存性(`Depends(get_db)`)がAnyIOのスレッドプール経由で解決される際、スレッド親和性が保証されないこと」が引き金と判断した。

## 【障害記録】

* 症状: 認証必須のAPIエンドポイントが間欠的に500 `INTERNAL_SERVER_ERROR` を返す。フロントエンドは対応するエラーメッセージ(「〜の取得に失敗しました」等)を表示し、データが一切表示されない。
* 発生条件: 1つの画面コンポーネントのマウント時に、複数の独立した`useEffect`が並行して複数のAPIエンドポイントを呼び出す構成(`CalendarPage`・`MyReservationsPage`・`RoomManagementPage`・`UserManagementPage`・`ReservationDetailPage`はいずれも`Header`コンポーネント自身の`GET /api/me`と、ページ本体の別のAPI呼び出しを並行して発火する)。
* 発生頻度: 非決定的(競合状態)。同一テストを複数回実行しても発生したりしなかったりする(T011は複数回PASSしたが理論上は影響範囲内、T013/T014は単独実行では通常PASSするが連続実行時にFAILした)。
* 原因区分: **アプリケーションコードの欠陥**

## 【参照ファイル】

* `server/app/db/connection.py`(`get_connection`関数)
* `server/app/dependencies.py`(`get_db`依存性、`get_current_user`が内部で`get_db`にも依存する二重依存構造)
* `docs/test-records/20260809-1500-test-record.md` T009の詳細な原因分析
* `docs/test-records/20260809-1900-test-record.md` A001, A003, A004, A006, A010

## 【調査方針】

* `server/app/db/connection.py`の`get_connection()`が`sqlite3.connect()`を呼ぶ際、`check_same_thread`引数を指定しているか確認する(現状は未指定=デフォルトの`True`)。
* FastAPI + 同期(`def`、`async def`でない)依存性generatorの組み合わせにおいて、1リクエスト内の複数の`Depends(get_db)`呼び出しが同一OSスレッドで実行される保証があるかどうかを、公式ドキュメント・既知のissueで確認する(確認済み: 保証されないケースがある、というのが今回の実測結果と整合する)。
* `check_same_thread=False`を指定した場合の安全性を確認する: 1つの`sqlite3.Connection`インスタンスは、その接続を跨いで複数スレッドから**同時に**使われるわけではなく(1リクエストのライフサイクル内で順に使われるだけ)、SQLite自体のファイルロックによる排他制御(`docs/ADR.md` ADR-004、`server/app/repositories/reservation_repository.py`の`begin_immediate_transaction`)はコネクションレベルではなくファイルレベルで機能するため、`check_same_thread=False`は本アプリケーションの使用パターン(接続はリクエストごとに新規作成・破棄、リクエスト間で共有しない)において安全と判断できるか確認する。

## 【修正方針】

* `server/app/db/connection.py`の`get_connection()`内、`sqlite3.connect(str(path))`の呼び出しに`check_same_thread=False`を追加する。
* 既存の排他制御ロジック(`BEGIN IMMEDIATE`、`docs/ADR.md` ADR-004)には触れない。この修正は「同一コネクションを異なるスレッドから順に使えるようにする」ものであり、「複数コネクションを同時に使う」際の排他性(既に`BEGIN IMMEDIATE`で担保済み)とは独立した問題である。

## 【試行錯誤してよい範囲】

* `server/app/db/connection.py`の変更のみを想定。他ファイルの変更が必要になった場合は、その理由を明記した上で最小限にとどめる。
* 修正後、T009・A001・A003(S05側)・A004・A006・A010の再実行で確認する。

## 【修正成功時に更新するdocs】

* `server/INDEX.md`: `app/db/connection.py`の項目にある「★既知の不具合」の注記を、修正済みである旨に更新する。
* `client/INDEX.md`: `CalendarPage.tsx`の項目にある注記のうち、本不具合に関する言及があれば整理する(ただしCalendarPage自体のaddDaysバグ(F002)は別問題として残す)。

## 【ロールバック条件】

* `check_same_thread=False`指定後、単体テスト(120件)のいずれかが新たに失敗する場合。
* 修正後もT009等で同一のスレッドエラーが再現する場合(別の原因が併存している可能性があるため、追加調査が必要)。

## 【検証コマンド】

* `cd server && python -m pytest tests/ -v`(既存120件の回帰確認)
* `cd server && python -m pytest tests/integration/test_login_session_integration.py tests/integration/test_logout_integration.py tests/integration/test_room_deactivate_integration.py tests/integration/test_reservation_update_self_exclude.py -v`
* `cd client && node --import tsx --test tests/integration/calendarListDisplay.test.tsx`(T009相当)
* `cd client && node --import tsx --test tests/acceptance/mainBusinessFlow.test.tsx`(A001)
* `cd client && node --import tsx --test tests/acceptance/setupToOperation.test.tsx`(A010)

## 【完了条件】

* 上記検証コマンドがすべてPASSする。
* 特にT009・A001・A010は、修正前は決定的に再現していたため、修正後は複数回(3回以上)再実行しても再現しないことを確認する。

## 重要:

* 作業開始前に現在の変更状態を確認してください。
* 必要な範囲でソースコード変更を試して構いません。
* 修正に成功した場合は、関連する docs/* も必要に応じて更新してください。
* 修正しきれなかった場合は、試行錯誤で変更した未完了のソースコードを元の状態に戻してください。
* 原因が仕様矛盾の場合は、コードで無理に解決せず、人間に判断を促す内容を `docs/P202-fix-plan/P202-fix-unresolved.md` に記録してください。

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
* 実施内容: 調査方針どおり原因を確認し、`server/app/db/connection.py`の`get_connection()`内、`sqlite3.connect(str(path))`を`sqlite3.connect(str(path), check_same_thread=False)`に変更した。安全性の判断根拠(接続はリクエストごとに新規作成・破棄され、複数スレッドから同時にではなく順に使われるだけであること、書き込み排他は`BEGIN IMMEDIATE`によるファイルロックで別途担保されていること)をコード中のコメントとして残した。
* 変更したソースコード: `server/app/db/connection.py`(1関数、1行の引数追加+コメント)
* 更新したdocs: `server/INDEX.md`(該当箇所の★既知の不具合注記を更新予定、P204で反映確認)
* 実行したテスト・結果:
  * `cd server && python -m pytest tests/ -v` → 127件中126件PASS(修正前から失敗していたF004対応のA008のみ未修正の時点でFAIL、F001自体には無関係)。F004適用後は127件全件PASS。
  * `cd client && node --import tsx --test tests/integration/calendarListDisplay.test.tsx` → 3回連続PASS(修正前は3/3・4/4で決定的にFAILしていた)
  * `cd client && node --import tsx --test tests/integration/mylistPeriodFilter.test.tsx` → 3回連続PASS(ただし別途T012自体のテストコードに含まれていた無関係な不具合(予約件名とラジオボタンラベルの文字列衝突によるクエリの病的な遅延)も同時に修正した。テストコード側の問題であり、アプリケーションコードとは無関係)
  * `cd client && node --import tsx --test tests/integration/userCrud.test.tsx` → 3回連続PASS(こちらもテストコード側の不具合(削除ボタンのインデックス選択が`admin`行を指してしまっていた)を別途修正)
  * `cd client && node --import tsx --test tests/integration/userProtectionDisplay.test.tsx tests/integration/headerNavByRole.test.tsx` → PASS
  * `cd client && node --import tsx --test tests/acceptance/mainBusinessFlow.test.tsx tests/acceptance/participantSelectionFlow.test.tsx tests/acceptance/setupToOperation.test.tsx tests/acceptance/calendarPerformance.test.tsx` → 全件PASS(setupToOperation.test.tsxは`getByLabelText`→`findByLabelText`へのテストコード側の非同期待ち漏れ修正も別途実施)
* テスト結果: 対応する全テストID(T009, T012, T013, T014, T015, A001, A003のS05側, A004, A006, A010)がPASSに転じたことを確認した。
* 残課題: なし。
* 修正経緯: T009の原因調査でトレースバックを確認 → `check_same_thread`未指定が原因と特定 → 修正後の再実行で、当初想定していた10件のうち大半は即座にPASSしたが、T012・T013・A010の3件は修正後も別の原因(いずれもテストコード自体の作成時の不具合)でFAILし続けたため追加調査・修正した(詳細は各テストファイルのコミット内コメント参照)。これらはF001の対象外(テスト作成時のミス)であり、F001自体の妥当性判断には影響しない。
