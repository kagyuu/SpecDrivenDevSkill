あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F002

## 【対応する失敗テスト】T006

## 【障害記録】

* 症状: S02(`CalendarPage`)の「前へ」「次へ」ボタンを押しても、実行時刻・タイムゾーンによっては表示日付が変化しないことがある。
* 発生条件: `client/src/pages/CalendarPage.tsx`の`addDays()`が、日付文字列(`YYYY-MM-DD`)を`new Date(isoDate + 'T00:00:00')`でDateオブジェクト化している。この構文はローカルタイムゾーンの午前0時として解釈される。その後`date.toISOString().slice(0, 10)`でUTC基準の日付文字列に変換して返す。`todayIsoDate()`も同様にUTC基準(`new Date().toISOString().slice(0, 10)`)で「今日」を計算している。UTCから離れたタイムゾーン(日本を含む、UTC+9)では、実行時刻によって「ローカル午前0時をUTC変換した結果の日付」と「本来加算したい暦日」がずれ、`addDays(today, 1)`が`today`と同じ文字列を返すことがある(実測: 2026-08-08T18:23 UTC時点で`addDays("2026-08-08", 1)` → `"2026-08-08"`、変化なし)。
* Reactの`useState`は同一の文字列値でstateを更新した場合、値としては変化していないと判定するため、依存する`useEffect`(`[date, selectedRoomIds]`)が再実行されず、日付ナビゲーションが実質的に無効化される。
* 原因区分: **アプリケーションコードの欠陥**

## 【参照ファイル】

* `client/src/pages/CalendarPage.tsx`(`todayIsoDate`・`addDays`関数)
* `docs/test-records/20260809-1500-test-record.md` T006の詳細な原因分析(再現コマンド含む)

## 【調査方針】

* `addDays`・`todayIsoDate`のいずれもUTC基準かローカル基準かが混在している点を洗い出す。
* 修正方針として、(a) すべてUTC基準に統一する(`Date.UTC(...)`を使って構築する)、または (b) 日付文字列を直接文字列/数値演算で加減算し、Dateオブジェクトのタイムゾーン解釈を経由しない、の2案を比較する。

## 【修正方針】

* `addDays`を、`Date`オブジェクトのローカルタイムゾーン解釈を経由しない実装に置き換える。例:
  ```ts
  function addDays(isoDate: string, days: number): string {
    const [year, month, day] = isoDate.split('-').map(Number)
    const utcDate = new Date(Date.UTC(year, month - 1, day))
    utcDate.setUTCDate(utcDate.getUTCDate() + days)
    return utcDate.toISOString().slice(0, 10)
  }
  ```
  `Date.UTC(...)`で明示的にUTCとして構築し、`setUTCDate`で加減算することで、ローカルタイムゾーンの影響を受けなくなる。
* `todayIsoDate()`自体は既にUTC基準(`toISOString()`)で一貫しているため、変更は不要と見込むが、`addDays`の入力・出力と整合していることを確認する。

## 【試行錯誤してよい範囲】

* `client/src/pages/CalendarPage.tsx`の`addDays`関数のみを想定。呼び出し側(「前へ」「次へ」ボタンのonClick)は変更しない。

## 【修正成功時に更新するdocs】

* `client/INDEX.md`: `CalendarPage.tsx`の項目にある「★既知の不具合」の注記を、修正済みである旨に更新する。

## 【ロールバック条件】

* 修正後、既存のCalendarPage関連の単体テスト(`client/tests/CalendarPage.test.tsx`)のいずれかが新たに失敗する場合。

## 【検証コマンド】

* `cd client && node --import tsx --test tests/CalendarPage.test.tsx`(既存単体テストの回帰確認)
* `cd client && node --import tsx --test tests/integration/reservationCreateSuccess.test.tsx`(T006相当)
* 追加確認: 修正した`addDays`関数を、タイムゾーンをまたぐ複数の時刻(UTC日付境界付近を含む)で単体的に検証する小さなNodeスクリプトを実行し、`addDays(X, 1)`が常に`X`と異なる値を返すことを確認する。

## 【完了条件】

* 上記検証コマンドがすべてPASSする。
* T006の完了条件(S02の「次へ」クリックで翌営業日のセルに予約が表示される)を満たす。

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
* 実施内容: 【修正方針】に記載した案のとおり、`addDays`を`Date.UTC(...)`で明示的にUTCとして構築し`setUTCDate`で加減算する実装に置き換えた。`todayIsoDate()`は変更不要と確認したとおり変更しなかった。
* 変更したソースコード: `client/src/pages/CalendarPage.tsx`(`addDays`関数、約8行)
* 更新したdocs: なし(`client/INDEX.md`は当初「★既知の不具合」を個別ページ単位では記載していなかったため追加更新は不要と判断)
* 実行したテスト・結果:
  * 単体的な検証スクリプト(`addDays`をUTC境界をまたぐ複数の基準時刻で実行) → 常に`addDays(X, 1) !== X`を確認
  * `cd client && node --import tsx --test tests/CalendarPage.test.tsx` → 4件PASS(回帰なし)
  * `cd client && node --import tsx --test tests/integration/reservationCreateSuccess.test.tsx` → 3回連続PASS(修正前は決定的にFAILしていた)
* テスト結果: T006がPASSに転じたことを確認した。
* 残課題: なし。
* 修正経緯: 一発で修正が成功し、追加の試行錯誤は不要だった。
