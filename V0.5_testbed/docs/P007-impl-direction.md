# プログラム実装定義 兼 プログラミング指示書 — 目次(OKF形式)

> 本書は `spec-driven-dev` Skill フェーズP007の成果物です。インプット文書: `docs/P002-frontend-spec.md`、`docs/P003-backend-spec.md`、`docs/P005-impl-plan.md`、`docs/P006-test-plan.md`。
> コード格納先: クライアント・サーバ型のため `client/`(React+TS+Vite、npmビルド)・`server/`(Python+FastAPI、uvビルド)とする。両ディレクトリとも現時点では未作成のため、U001タスクでビルドツールの標準初期化を行う。

## 目次

- [x] U001 [foundation-auth: 基盤・認証](./P007-impl-direction/U001-foundation-auth.md) — プロジェクト初期化、全テーブルのDBスキーマ、ログイン画面、認証・セッションAPI
- [x] U002 [admin-management: 会議室・ユーザー管理](./P007-impl-direction/U002-admin-management.md) — 会議室管理画面・ユーザー管理画面、rooms/users CRUD API
- [x] U003 [reservation-core: 予約カレンダー・予約作成](./P007-impl-direction/U003-reservation-core.md) — 予約カレンダー画面・予約作成画面、GET/POST reservations API、重複チェック排他制御
- [x] U004 [reservation-detail-mine: 予約詳細・マイ予約](./P007-impl-direction/U004-reservation-detail-mine.md) — 予約詳細・編集画面・マイ予約一覧画面、reservations の参照・更新・削除API
- [x] U005 [cr-001-all-day-checkbox: 終日チェックボックス](./P007-impl-direction/U005-cr-001-all-day-checkbox.md) — CR-001対応。S03に「終日」チェックボックスを追加し、開始09:00/終了18:00を自動入力する
- [x] U006 [cr-002-room-description: 会議室説明文](./P007-impl-direction/U006-cr-002-room-description.md) — CR-002対応。S06に説明文(description)を追加し、`rooms`テーブル・GET/POST/PUT `/api/rooms`・登録編集フォーム・一覧表示に反映する

## 進捗更新ルール

* 各スプリント(U001〜U004)の実装・単体テストがすべて完了したら、ExecutorはP102の一部として該当行のチェックボックスを `[x]` に更新する。
* 全スプリントが `[x]` になるまでP007(実行対象スプリント群)は完了しない。
* U005・U006は、通常のスプリントではなくRefactor(P901〜P905)のP903でCR-001・CR-002対応としてそれぞれ追加したものである。実装・単体テストの完了後に `[x]` へ更新する点は他スプリントと同じ扱いとする。

## 未解決事項

* 特になし(P002・P003・P005・P006の内容で実装指示を記述できる状態であることを確認済み)。
