# client/ INDEX

> P104(実装構造修正)で更新。会議室予約システムのフロントエンド(全4スプリント U001〜U004実装済み)。CR-001対応(U005、終日チェックボックス)・CR-002対応(U006、会議室説明文)・CR-003対応(U007、予約の参加予定人数)で追加更新。

## 技術スタックと deviation

* **ビルド不要のプレーンHTML/CSS/JavaScript(ES Modules)**(ADR-001はReact 18 + TypeScript + Viteを指定しているが、本サンドボックスはregistry.npmjs.orgに接続できずnpm install/npm create viteが利用不可のため代替。詳細は `docs/P101-impl-context.md`)。
* 各画面は「DOM非依存のコントローラ関数(unit test対象)」と「実際のDOM描画関数(`mountXxxPage`、手動/結合確認用)」に分離して実装している(jsdom等のDOM実装がインストールできないため)。
* テスト: Node.js 22標準搭載の `node --test`(npmパッケージ不要)。`client/tests/` に57件、全PASS(CR-001対応で35件→38件、CR-002対応で38件→45件、CR-003対応で45件→57件)。

## ディレクトリ構成

* `index.html` — SPAのエントリポイント。`<div id="app">` に `js/app.js` をmoduleとして読み込む。
* `css/style.css` — 最小限の共通スタイル。
* `js/app.js` — 簡易ハッシュルータ(`#/calendar` `#/reservations/new` `#/reservations/{id}` `#/my-reservations` `#/rooms` `#/users`)。ログイン状態・管理者権限に応じて表示を切り替える。
* `js/api/` — バックエンドAPIのfetchラッパー(`credentials: "include"` でCookieベース認証、ADR-004に対応)。
  * `authApi.js` — login/logout/getMe。
  * `roomApi.js` — 会議室CRUD。
  * `userApi.js` — ユーザーCRUD。
  * `reservationApi.js` — 予約一覧/作成/詳細/マイ予約/更新/削除。
* `js/pages/` — 画面コンポーネント(S01〜S07)。
  * `loginPage.js` — S01ログイン画面。`validateLoginInput`/`createLoginController`(unit test対象)+ `mountLoginPage`。
  * `roomManagementPage.js` — S06会議室管理画面。`validateRoomInput`(説明文の200文字以内チェック含む、※CR-002)、`createRoomManagementController`(登録/編集/無効化。`startEdit`/`submitUpdate`/`cancelEdit`はCR-002で追加、元々編集UIが未実装だったため合わせて実装)。
  * `userManagementPage.js` — S07ユーザー管理画面。
  * `calendarPage.js` — S02予約カレンダー画面。`generateTimeSlots`(9:00-18:00 30分刻み)/`buildCalendarGrid`。
  * `reservationCreatePage.js` — S03予約作成画面。`getAllDayDefaults`(終日チェックボックスON時の開始09:00/終了18:00既定値、※CR-001により追加)。`validateReservationInput` の参加予定人数チェック・`normalizeAttendeeCount`・`reservationErrorMessage`(※CR-003により追加。`reservationErrorMessage` は409の重複メッセージと、`details[].field="attendee_count"` を伴う400の収容人数超過メッセージを振り分ける。S04からも共用する)。
  * `reservationDetailPage.js` — S04予約詳細・編集画面。`canEdit`(本人/管理者判定)。`submitUpdate` は参加予定人数を含む全量更新を送信する(※CR-003)。
  * `myReservationsPage.js` — S05マイ予約一覧画面(期間フィルタ既定`upcoming`)。
* `tests/` — `node --test` 用の単体テスト(`*.test.mjs`)。各ページのコントローラ関数(フォームバリデーション・API呼び出し・エラー表示ロジック)を対象とする。DOM描画そのもの(`mountXxxPage`)は自動テスト対象外(手動/結合確認のみ、上記deviation参照)。

## 実行方法

* 単体テスト全件: `cd client && node --test tests/*.test.mjs`(57件PASS)。
* 構文チェック(ビルド相当): `node --check js/**/*.js`(バンドラ非使用のため)。
* 手動確認: 静的ファイルサーバー(例 `npx http-server client` または `python3 -m http.server`)で `index.html` を配信し、`server/` を起動した状態でブラウザから確認する。

## 参照

* `docs/ArchitectureHandbook.md` §4(ディレクトリ構成の方針)
* `docs/P101-impl-context.md`(サンドボックス制約とdeviationの詳細)
* `docs/P002-frontend-spec.md`(画面外部仕様)
