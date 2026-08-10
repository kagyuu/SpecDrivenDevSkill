あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T016(CR-001対応)

## 【目的】

* `docs/P901-cr-direction/CR-001.md` にもとづき追加したオンライン会議URL項目が、S03(作成)→S04(表示・編集)→DBまで一貫して連携することを確認する(画面+API+DBの結合)。

## 【参照テスト計画】

* `docs/P006-test-plan.md` 2.1〜2.4節「CR-001対応」

## 【対象モジュール】

* `client/src/pages/ReservationCreatePage.tsx`, `client/src/pages/ReservationDetailPage.tsx`, `client/src/validation/reservationValidation.ts`, `server/app/routers/reservations.py`, `server/app/services/reservation_service.py`, `server/app/repositories/reservation_repository.py`, SQLite(`reservations.meeting_url`)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* U003-T7/T8、U004-T6/T7(`docs/P007-impl-direction/U003-reservation-core-and-calendar.md`、`docs/P007-impl-direction/U004-reservation-detail-and-mylist.md`)が完了していること。会議室「第一会議室」(収容人数8)が登録済みであること。

## 【使用するテストデータ】

* 会議室: 第一会議室、日付: 翌営業日、時間帯: 13:00-14:00、件名: 「CR-001確認用会議」、オンライン会議URL(作成時): `https://example.com/meeting/cr001`
* 更新後のオンライン会議URL: `https://example.com/meeting/cr001-updated`

## 【事前準備】

* 一般ユーザーでログインし、S03(予約作成画面)を開く

## 【実行手順】

1. テストデータでフォームを入力し(オンライン会議URLに `https://example.com/meeting/cr001` を入力)登録する
2. SQLiteを直接クエリし `reservations.meeting_url` に登録した値が保存されていることを確認する
3. S02カレンダー画面が呼ぶ `GET /api/reservations` のレスポンスに `meeting_url` キーが含まれないことを確認する(3.2/4.6節、意図的な除外の回帰確認)
4. 作成した予約のS04(詳細画面)を開き、オンライン会議URLがクリック可能なリンク(`https://example.com/meeting/cr001`)として表示されることを確認する
5. S04の編集フォームでオンライン会議URLを `https://example.com/meeting/cr001-updated` に変更して更新する
6. 再度S04を開き、更新後のURLがリンク表示されていることを確認する
7. S04の編集フォームでオンライン会議URLを空欄にして更新する
8. 再度S04を開き、「(未設定)」と表示され、DBの `meeting_url` が `NULL` であることを確認する

## 【実行コマンド】

* `cd client && node --import tsx --test tests/integration/reservationMeetingUrl.test.tsx`

## 【期待結果】

* 手順1: 201
* 手順2: `meeting_url = 'https://example.com/meeting/cr001'`
* 手順3: レスポンスの各要素に `meeting_url` キーが存在しない
* 手順4: `<a href="https://example.com/meeting/cr001">` 相当の要素が表示される
* 手順5: 200
* 手順6: 更新後URLでリンク表示される
* 手順7: 200
* 手順8: 画面に「(未設定)」表示、DBは `NULL`

## 【合否判定基準】

* 上記すべてを満たせばPASS

## 【失敗時に記録する内容】

* 実際のレスポンス、画面表示内容、DBの内容

## 【修正禁止事項】

* アプリケーションコードを修正しない。テストコードをその場で都合よく変更しない。失敗したテストをスキップしない。期待値を変更して成功扱いにしない。同じ失敗に対して場当たり的な再テストを繰り返さない。

## 【次タスクへ進む条件】

* 結果を記録したら本スプリントのテストタスクは完了(T016が最終タスク)

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Executor Stepの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。
