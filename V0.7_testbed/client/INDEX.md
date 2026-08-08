# client/ INDEX

> 本書は `spec-driven-dev` Skill フェーズP020の成果物(INDEX形式)を、フェーズP104(実装構造修正)で更新したものです。
> `client/` ソースツリーのディレクトリ・主要ファイルの目次。
> **実装状況: Sprint 1〜4(U001〜U004)まで実装済み。** P002 2.2 の7画面すべてが実装されており、未実装項目は残っていない。
> **※CR-001(2026-08-05)**: S03・S04にオンライン会議URLの入力欄を追加し、S04の閲覧モードでリンク表示するようにした(`validation.js`、`reservation-form.js`、`s04-reservation-detail.js`)。**S02は変更していない**(CR-001が明示的に対象外)。
> ビルドツールを使わず、ブラウザが `client/index.html` から ES モジュールを直接読む構成。単一HTMLシェル + ハッシュルーティングのSPA(`docs/P002-frontend-spec.md` 2.2、ADR-001)。静的ファイルはサーバープロセスが同一オリジンで配信する(ADR-010)。

## ルート直下

- package.json — npmメタデータ(`"type": "module"`)。**依存パッケージを持たない**(ADR-001)
- index.html — 単一HTMLシェル(入口)。`#header` / `#app` を持ち、`/src/main.js` をESモジュールとして読み込む

## `src/`

- main.js — エントリポイント。`router.defineDefaultRoutes()` でルート表を登録し、ルーターを起動する
- styles.css — 全画面共通のスタイル(無効行の `is-inactive`、フィールドエラー、画面上部メッセージ)、S02カレンダーのグリッド(`td.cell` / 自分の予約の `is-mine`)、予約フォームと詳細行、S05の一覧

### `src/lib/` — 画面から独立した共通ロジック

- router.js — ハッシュルーティング。**ルート表 `ROUTES`(P002 2.2 の7ルート。`/reservations/new` を `/reservations/{reservation_id}` より先に置く)** と `register` / `resolve` / `navigate` / `start` / `parseQuery`。`#/...?key=value` のクエリは描画関数のパラメータに合流する。未知のハッシュは `#/calendar` へ
- api.js — APIクライアント(`get` / `post` / `put` / `del`)。`credentials: 'same-origin'`、2xxはJSON(204は `null`)、それ以外は `{status, code, message, details, extra}` を throw。401 `UNAUTHENTICATED` のときのみ `#/login` へ遷移しセッション切れメッセージを残す。`runtime`(fetch / navigate)はテストから差し替え可能
- validation.js — P002 3章の入力ルールを純粋関数として実装(`validateUserId` / `validatePassword` / `validateTitle` / `validateTimeRange` / `validateAttendeeCount` / `validateRoomName` / `validateCapacity` / `validateNote` / **`validateMeetingUrl`(※CR-001)** ほか)。戻り値は `null` またはエラーメッセージ文字列
- dom.js — 要素生成(`el`)、フィールド単位のエラー表示、画面上部メッセージ、P002 2.4 の対応表をまとめた `showApiError`、送信中のボタン非活性化
- datetime.js — 週の開始日(月曜)算出、日付加減算、`YYYY-MM-DD` / `HH:MM` の整形、30分刻みの時刻リスト(08:00〜20:00の25要素)、`addMinutes`
- grid.js — S02の「(日付, 会議室, スロット) → 予約」占有マップ構築(純粋関数)。**予約の終了時刻のスロットは占有しない**(09:00-10:00 は 09:00 と 09:30 のみ)。会議室フィルタとセル表示文言も担当

### `src/components/` — 画面をまたいで再利用する部品

- header.js — 共通ヘッダー。管理者のときのみ「会議室管理」「ユーザー管理」リンクを描画し、ログアウトを行う(S01では描画しない)
- reservation-form.js — S03とS04の編集モードで共用する予約入力フォーム。組み立て・値の読み書き・終日チェック(09:00/18:00の自動入力)・クライアント側検証・重複/収容人数超過エラー領域への表示・送信ボディ生成。※CR-001: オンライン会議URL(`data-role="meeting_url"`。参加予定人数と備考の間)を含む

### `src/views/` — 画面ごとの描画モジュール(1画面 = 1モジュール)

- s01-login.js — S01 ログイン画面(`#/login`)。クライアント側バリデーション、401時のエラー表示、成功時の `#/calendar` 遷移
- s02-calendar.js — S02 予約カレンダー画面(`#/calendar`)。月曜起点7日分の「会議室=列 / 時間帯=行」グリッド、前週・翌週・今日・日付選択、**クライアント側の会議室フィルタ(再取得しない)**、空きセル→S03 / 予約済みセル→S04 の遷移、過去日セルのメッセージ。S03・S04の完了メッセージを受け取る `setFlash` / `takeFlash` も持つ
- s03-reservation-new.js — S03 予約作成画面(`#/reservations/new`)。S02から引き継いだクエリを初期値にし、`POST /api/reservations` を呼ぶ。409は重複エラー領域、400 `CAPACITY_EXCEEDED` は収容人数超過エラー領域へ表示
- s04-reservation-detail.js — S04 予約詳細・編集画面(`#/reservations/{reservation_id}`)。閲覧項目の表示、権限と過去日による編集・取消ボタンの出し分け、`reservation-form.js` を再利用した編集、確認ダイアログ付きの取消。※CR-001: `meetingUrlRow()` がオンライン会議URLを `a` 要素(別タブ)として描画し、未登録なら「-」を表示する
- s05-my-reservations.js — S05 マイ予約一覧画面(`#/my-reservations`)。期間フィルタ(`upcoming` / `past`)、APIの返却順のままの4列一覧、0件表示、行クリックでS04へ
- s06-room-admin.js — S06 会議室管理画面(`#/admin/rooms`、管理者のみ)。一覧・モーダルフォーム・無効化の確認ダイアログ・権限による表示制御
- s07-user-admin.js — S07 ユーザー管理画面(`#/admin/users`、管理者のみ)。一覧・新規/編集フォーム(編集時は社員ID非活性・パスワード空欄なら変更しない)・無効化

## `tests/`

* 単体テスト実行: `cd client && node --test 'tests/*.js'`
  * **注意**: `docs/P007-impl-direction.md` が指定する `node --test tests`(ディレクトリ指定)は Node.js v22.22.2 では動作しない(`docs/P007-impl-direction.md` 5章 未解決事項#6)。
* 結合テスト実行: `cd client && node --test tests/integration/test_t0NN_xxx.js`
* 受け入れ結合テスト実行(P009 / P201): `cd client && node --test 'tests/acceptance/test_*.js'`

- test_validation.js — U001-T5: 各バリデーション関数の境界値
- test_datetime.js — U001-T5: 週開始日・日付加減算・時刻リスト
- test_api.js — U001-T5: 400/401/403/404/409/500 のエラー変換(`fetch` を差し替え)
- test_s01_login.js — U001-T6: S01の描画と送信ハンドラ
- test_s06_room_admin.js — U002-T4: S06の描画・登録/編集/削除・権限・エラー表示
- test_s07_user_admin.js — U002-T5: S07の描画・登録/編集/削除・権限・エラー表示
- test_grid.js — U004-T1: 占有マップの構築(終了スロットを占有しないこと、フィルタ、セル表示文言)
- test_s02_calendar.js — U004-T1: S02の描画・API呼び出し回数・フィルタ・週送り・セルクリックの遷移・過去日メッセージ
- test_reservation_form.js — U004-T2: 予約フォームの構成・終日チェック・値の読み書き・検証・エラー領域
- test_s03_reservation_new.js — U004-T2: S03の初期値引き継ぎ・送信ボディ・409/400の表示・送信中の非活性
- test_s04_reservation_detail.js — U004-T3: S04の表示項目・権限による出し分け・編集/取消・404表示
- test_s05_my_reservations.js — U004-T4: S05の一覧・期間フィルタ・0件表示・行クリック
- test_router.js — U004-T5: 7ルートの登録と解決、クエリの受け渡し、ヘッダーのリンクとログアウト、401時の `#/login` 遷移
- helpers/dom-env.js — テスト用の最小DOM実装(jsdomを取得できないため。ADR-001)
- helpers/server.js — 実サーバープロセス(uvicorn)の起動/停止と、Cookieを保持する `fetch`
- acceptance/support.js — 受け入れ結合テストの共通下準備(サーバー起動 + 実APIによる基準データセット投入、独立セッションの払い出し)
- acceptance/test_a001_business_flow.js — A001: ログイン→カレンダー→作成→詳細→編集→取消の業務フロー全体(10手順)
- acceptance/test_a003_role_separation_ui.js — A003(画面側): 一般ユーザーのヘッダーに管理メニューが出ないこと、S06/S07を直接開いても一覧を取得しないこと
- acceptance/test_a004_room_master_impact_ui.js — A004(画面側): 収容人数変更後のS03検証、無効化後にS03のプルダウン・S02の列から消えること
- acceptance/test_a005_consistency.js — A005: S02とS05の整合、他人の予約・過去予約の混入がないこと
- acceptance/test_a006_session_ui.js — A006(画面側): セッション消失時の `#/login` 遷移とメッセージ
- acceptance/test_a008_calendar_render.js — A008(画面側): 10室×200件でのS02描画時間・表示完了までの時間の計測
- acceptance/test_a011_user_acceptance.js — A011: 利用者視点の受け入れシナリオ(手順1〜6。手順7の実ブラウザ目視確認は NOT RUN)
- helpers/dom-env.js — **テスト用の最小DOM実装**(外部パッケージを取得できずjsdomを使えないため。`document` / 要素 / セレクタ / イベントの必要最小限)
- helpers/server.js — 結合テスト用に実サーバー(`uvicorn`)を起動し、Cookieを保持する `fetch` を提供する
- integration/test_t003_s01_login_api.js — 結合テストT003(S01↔ログインAPI。実サーバーに対して実行)
- integration/test_t010_master_screens_api.js — 結合テストT010(S06・S07↔マスタAPI。実サーバーに対して実行)
- integration/test_t015_calendar_grid_api.js — 結合テストT015(S02↔`GET /api/rooms` / `GET /api/reservations`)
- integration/test_t016_create_flow.js — 結合テストT016(S02→S03の引き継ぎと登録完了。手順7の期待結果はF001で修正済み・PASS。※CR-001で手順9・10(オンライン会議URL)を追加)
- integration/test_t017_detail_edit_cancel.js — 結合テストT017(S04の編集・取消と権限による表示制御。※CR-001で手順8〜10(オンライン会議URLのリンク表示・編集)を追加)
- integration/test_t018_my_reservations_filter.js — 結合テストT018(S05の期間フィルタ。過去日の予約はRepository経由で直接INSERT)

## 関連ドキュメント

* 画面仕様・ルート定義: `docs/P002-frontend-spec.md` 2.2 / 3章
* 各ファイルの実装指示: `docs/P007-impl-direction.md` および `docs/P007-impl-direction/U001-foundation-auth.md`(共通基盤・S01)、`U002-master-management.md`(S06・S07)、`U004-reservation-ui.md`(S02〜S05)
* 技術選定の理由: `docs/ADR.md`(ADR-001 フロントエンド)
* 技術的側面の概観: `docs/ArchitectureHandbook.md`
* 結合テストの実行記録: `docs/test-records/`
