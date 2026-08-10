# client/ INDEX

React + TypeScript + Vite(`docs/ADR.md` ADR-001)。ルーティングは `react-router-dom`。

- `package.json` — 依存関係定義(react, react-dom, react-router-dom / dev: @testing-library/react, jsdom, tsx, typescript, vite)
- `index.html` / `vite.config.ts` / `tsconfig.json` — Vite標準構成
- `src/main.tsx` — Reactエントリポイント
- `src/App.tsx` — ルーティング定義(`/login`, `/`, `/reservations/new`, `/reservations/:id`, `/my-reservations`, `/admin/rooms`, `/admin/users`)
- `src/pages/` — 画面コンポーネント(1画面=1ファイル、P002の画面番号に対応)
  - `LoginPage.tsx` — S01 ログイン画面
  - `CalendarPage.tsx` — S02 予約カレンダー画面(トップ)。日付ナビゲーション(`addDays`)はUTC基準で計算する(P202 F002。タイムゾーン依存で無効になっていた不具合を修正済み。`docs/P202-fix-plan/fixed/F002-calendar-adddays-timezone.md`参照)
  - `ReservationCreatePage.tsx` — S03 予約作成画面
  - `ReservationDetailPage.tsx` — S04 予約詳細・編集画面
  - `MyReservationsPage.tsx` — S05 マイ予約一覧画面
  - `RoomManagementPage.tsx` — S06 会議室管理画面(管理者用)
  - `UserManagementPage.tsx` — S07 ユーザー管理画面(管理者用)
- `src/components/` — 複数画面から使う共通コンポーネント
  - `Header.tsx` — 共通ヘッダー(権限・画面別のリンク出し分け、ログアウト動線)。S02/S05/S06/S07で使用(S04は未対応、`docs/P007-impl-direction/U005-user-management-and-hardening.md` U005-T4の実施メモ参照)
  - `RoomTimeGrid.tsx` — 会議室×時間帯グリッド(S02で使用)
- `src/api/` — バックエンドAPIのfetchラッパー(モジュールごとに `export const xxxApi = {...}` という可変オブジェクトで公開し、単体テストからのモック差し替えを可能にしている)
  - `authApi.ts` — 認証API
  - `roomApi.ts` — 会議室API
  - `reservationApi.ts` — 予約API
  - `userApi.ts` — ユーザー管理API
- `src/validation/reservationValidation.ts` — 予約フォームの共通バリデーション(S03/S04両方から参照)
- `tests/` — Unit Test(`*.test.tsx`、`node --import tsx --test tests/*.test.tsx`)
  - `setupJsdom.ts` — jsdomグローバルのセットアップ(各テストファイルの先頭でimportする)
  - `integration/` — P103結合テスト(実サーバーに対して実行。`realServer.ts`が共有ヘルパー)
