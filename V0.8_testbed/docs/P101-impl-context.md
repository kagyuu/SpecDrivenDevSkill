# 実装コンテキスト — 会議室予約システム(P101)

> 本書は `spec-driven-dev` Skill フェーズP101の成果物です。Executorは、詳細仕様(`docs/P002-frontend-spec.md`等)をすべて読む前に、まずこの文書と実行対象の `docs/P007-impl-direction/U0NN-{sprint-name}.md` を読めば着手できます。
>
> **CR-001対応(※P903内側のP101再実行で追記)**: 本書1〜4章は初回納品時点(U001着手前)のスナップショットのまま残す(当時の記録として)。CR-001(オンライン会議URL追加)の着手にあたって必要な最新情報は本追記(5章)を参照すること。

## 1. 現在のソースツリーの状態(初回納品時点の記録)

* `client/INDEX.md`・`server/INDEX.md`(P020作成)は、いずれも「(実装前)」のプレースホルダのみ。両ディレクトリとも今回のP102実行で初めてコードを持つ。
* コード格納先: `client/`(フロントエンド)、`server/`(バックエンド)。P007 U001-T1で標準ビルドツールにより初期化する(フロントエンドはnpm、バックエンドはuv相当のpyproject.toml構成。★実行環境に`uv`コマンドが存在しないことを確認したため、`pip`+venv+`pyproject.toml`で同等の構成を実現する。プロジェクト構造(pyproject.tomlベース)自体はuv init相当のまま変更しない)。

## 2. 遵守すべき技術的決定(`docs/ADR.md` より転記)

| ADR | タイトル | 状態 |
| --- | --- | --- |
| ADR-001 | フロントエンド技術スタック(React 18 + TypeScript + Vite) | 採用 |
| ADR-002 | バックエンド技術スタック・データストア(FastAPI + SQLite) | 採用 |
| ADR-003 | 認証方式(Cookieベースサーバーサイドセッション) | 採用 |
| ADR-004 | マイグレーション方式(バージョン管理テーブルによる差分適用) | 採用 |

* 状態管理はReact標準のみ(Redux等は使わない、ADR-001)。
* パスワードハッシュは`hashlib.scrypt`、セッションはCookie(`session_id`、HttpOnly/SameSite=Lax/8時間固定)+ `sessions`テーブル(ADR-003)。
* マイグレーションは`migrations/*.sql`を起動時に`schema_migrations`テーブルと突き合わせ、未適用分のみ適用する(ADR-004)。

## 3. これから着手するスプリント(初回納品時点の記録)

* `docs/P007-impl-direction.md` の目次で最初の未完了(`[ ]`)スプリントは **U001 foundation-and-auth**(`docs/P007-impl-direction/U001-foundation-and-auth.md`)。
* U001は5タスク(U001-T1〜T5)から成る。プロジェクト基盤構築→データモデル・マイグレーション→認証Repository/Service層→認証APIハンドラ→S01ログイン画面、の順。

## 5. CR-001対応時点の状態(※P903内側のP101再実行で追記)

* `client/`・`server/` はいずれもU001〜U005まで実装済み(全テスト当時PASS)。今回追加で着手するのは、`docs/P007-impl-direction/U003-reservation-core-and-calendar.md` の **U003-T7・U003-T8・U003-T9**、および `docs/P007-impl-direction/U004-reservation-detail-and-mylist.md` の **U004-T6・U004-T7**(いずれも`[ ]`、CR-001: オンライン会議URL追加)のみ。他のタスク・他スプリントは対象外(`docs/P903-cr-records/CR-001.md` スコープ決定節参照)。
* 実行順序: U003-T7(バックエンド: スキーマ・バリデーション・API)→U003-T8(S03フロントエンド)→U003-T9(既存回帰: `test_migration.py`)→U004-T6(バックエンド: 更新・取得API)→U004-T7(S04フロントエンド)。U003-T7/T9はU004-T6より先に完了させること(U004-T6は `find_by_id`/`create` へのカラム追加が既に済んでいることを前提にしている)。
* 変更対象は「`reservations`テーブルへの1カラム追加とその読み書き」のみであり、U001(認証)・U002(会議室管理)・U005(ユーザー管理)のコードは変更しない(`docs/P903-cr-records/CR-001.md` 対象外フェーズ節参照)。
* マイグレーションファイル(`server/migrations/003_add_reservation_meeting_url.sql`)は既に追加済み・冪等性確認済み(P903内側のP003完了時点)。U003-T7ではこのファイルを新規作成する必要は無い。

## 4. 迷ったときに参照する詳細仕様の場所

| トピック | 参照先 |
| --- | --- |
| 認証の外部契約(Cookie仕様等) | `docs/P002-frontend-spec.md` 2章 |
| 認証の内部実現(ハッシュ方式、セッションストア) | `docs/P003-backend-spec.md` 1.2節 |
| データモデル全体(DDL) | `docs/P003-backend-spec.md` 2.2節 |
| マイグレーション方式 | `docs/P003-backend-spec.md` 3章 |
| S01ログイン画面の仕様 | `docs/P002-frontend-spec.md` 3.1節 |
| 認証APIの外部仕様 | `docs/P002-frontend-spec.md` 4.1〜4.3節 |
| 認証APIの内部仕様 | `docs/P003-backend-spec.md` 4.1〜4.3節 |
| U001関連の結合テスト(T001〜T003、参考。実行自体はP103) | `docs/P008-test-direction/T001-login-success-session.md`〜`T003-logout-session-invalidation.md` |
