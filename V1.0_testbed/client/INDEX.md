# client/ INDEX

React 18 + TypeScript + Vite(ADR-001)によるフロントエンド。CR-001対応(P903、`internal_memo`欄追加)にて最新の実装内容で更新した。

* ※既知の課題(ローカル実行環境固有): `npm run build`(`vite build`)がこの環境(Node.js v24.12.0/Windows)ではソース内容によらずネイティブクラッシュする。`tsc -b`・`npx vitest run`・`npx playwright test`はすべて正常。詳細は `docs/test-records/20260811-CR001-test-record.md` 参照。

- `package.json` — 依存関係定義(react, react-dom, react-router-dom / devDependencies: vitest, testing-library, @playwright/test 等)
- `vite.config.ts` — Vite設定。開発サーバーの `/api` プロキシ(`http://localhost:8000`へ転送。フロントエンド・バックエンドを同一オリジンに見せるための設定、理由はファイル内コメント参照)、Vitestのjsdom設定(`test.include` を `src/tests/**` に限定し、Playwright専用の `tests/` 配下を誤って収集しないようにしている)
- `playwright.config.ts` — E2E結合テスト用設定。バックエンド(uvicorn, port 8000)・フロントエンド(vite, port 5173)を自動起動する
- `index.html` — エントリHTML
- `src/main.tsx` — Reactアプリのマウント、`RouterProvider`
- `src/router.tsx` — ルーティング定義(S01〜S07すべて実ルート)
- `src/index.css` — 全体スタイル
- `src/api/` — APIクライアント
  - `client.ts` — 共通`apiFetch`ラッパー、`ApiError`
  - `rooms.ts` — 会議室API(一覧取得、CRUD)
  - `reservations.ts` — 予約API(一覧・詳細・CRUD)。`Reservation`/`ReservationInput`に`internal_memo`を含む(※CR-001により追加)
  - `users.ts` — ユーザーAPI(一覧・登録・無効化)
- `src/components/RoomTimeGrid.tsx` — S02の会議室×時間帯グリッド
- `src/pages/` — 画面コンポーネント
  - `LoginPage.tsx` — S01 ログイン画面
  - `CalendarPage.tsx` — S02 予約カレンダー画面。ログインユーザー名の表示・ログアウトボタンを実装済み(P202 F001)。日付計算はローカルタイムゾーン基準(P202 F002、`toDateString`のコメント参照)
  - `ReservationCreatePage.tsx` — S03 予約作成画面(参加者選択は未実装。`docs/P007-impl-direction.md` 未解決事項を参照)。「備考(社内向けメモ)」欄を追加済み(※CR-001により追加)
  - `ReservationDetailPage.tsx` — S04 予約詳細・編集画面。`canEdit`(所有者・管理者)ブロック内に「備考(社内向けメモ)」欄を追加済み(※CR-001により追加、閲覧条件と編集条件が一致するため同じ分岐を利用)
  - `MyReservationsPage.tsx` — S05 マイ予約一覧画面
  - `RoomAdminPage.tsx` — S06 会議室管理画面(管理者用)
  - `UserAdminPage.tsx` — S07 ユーザー管理画面(管理者用)
- `src/tests/` — 単体テスト(Vitest + Testing Library、25件PASS。`docs/P007-impl-direction/U00N-*.md` 対応分。CR-001対応で`internal_memo`関連テストを追加)
- `tests/integration/` — E2E結合テスト(Playwright、`docs/P008-test-direction/T0NN-*.md` 対応分。9件全PASS)
  - `helpers.ts` — ログイン・API経由データ準備・日付計算の共通ヘルパー
  - `t001_login_flow.spec.ts` 〜 `t010_reservation_internal_memo_masking.spec.ts`(T002は`server/tests/integration/`側、T010は※CR-001により追加)
- `tests/acceptance/` — E2E受け入れ結合テスト(Playwright、`docs/P009-acceptance-direction/A0NN-*.md` 対応分。5件全PASS。A003・A005・A008・A009は`server/tests/acceptance/`側)
  - `a001_general_user_journey.spec.ts` 〜 `a007_performance_calendar.spec.ts`
