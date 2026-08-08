# server/ INDEX

> 本書は `spec-driven-dev` Skill フェーズP020の成果物(INDEX形式)を、フェーズP104(実装構造修正)で更新したものです。
> `server/` ソースツリーのディレクトリ・主要ファイルの目次。
> **実装状況: Sprint 1〜4(U001〜U004)まで実装済み。** サーバー側の未実装項目は残っていない。
> **※CR-001(2026-08-05)**: 予約のオンライン会議URL(`reservations.meeting_url`)を追加済み(マイグレーション `004-meeting-url.sql`、`schemas.py`、`reservations_repo.py`、`reservation_service.py`)。

## ビルド・設定

- pyproject.toml — ビルド定義(`uv` 前提。`requires-python = ">=3.11"`、外部依存パッケージなし)
- .python-version — 使用するPythonバージョン(3.11)
- .gitignore — Python生成物・仮想環境の除外設定
- README.md — サーバー側の説明(内容はP302で整備する)

## アプリケーション本体 `src/meeting_room/`

* 層の責務は `handlers`(HTTP入出力とスキーマ検証) → `services`(業務ルール・トランザクション境界) → `repositories`(SQL実行)。`repositories` はHTTPを知らず、`handlers` はSQLを書かない(`docs/P003-backend-spec.md` 2.1)。

- `__init__.py` — パッケージ初期化
- py.typed — 型情報を同梱していることを示すマーカー
- main.py — ASGIアプリ生成(`create_app`)、ルート定義(`api_routes`)、起動時のマイグレーション+初期管理者シード実行、静的ファイル配信とMIME型、`ApiError` の例外ハンドラ
- config.py — 環境変数からの設定読み込み(`DB_PATH` / `SESSION_IDLE_SECONDS` / `SESSION_ABSOLUTE_SECONDS` / `INITIAL_ADMIN_ID` / `INITIAL_ADMIN_PASSWORD`)。モジュール読み込み時に1回だけ解決する
- db.py — sqlite3接続(`connect`)、`PRAGMA` 設定(`init_wal`)、`BEGIN IMMEDIATE` トランザクション(`transaction`)、差分適用マイグレーション(`apply_migrations`)、初期管理者シード(`seed_initial_admin`)
- errors.py — `ApiError` 例外、`to_response`、`JsonResponse`(日本語を素通しするJSON応答)、500応答の生成
- logging_middleware.py — 全リクエスト横断のアクセスログ(標準出力へJSON1行)。`sid`・パスワードを出力しない。5xxのみ `stack` を含む
- security.py — scryptによるパスワードハッシュ生成・検証、セッションID生成、**時刻取得の集約**(`now_utc` / `today_local`)
- auth.py — セッション解決と認可ヘルパ(`require_login` / `require_admin` / `require_owner_or_admin`)、リクエスト単位のDB接続(`open_conn`)
- schemas.py — Pydantic v2 のリクエストモデルと明示検証(`validate`)。`LoginRequest` / `UserResponse` / `RoomRequest` / `UserCreateRequest` / `UserUpdateRequest` / `ReservationRequest`(※CR-001: `meeting_url` の検証。500文字以内 → `http://`/`https://` の前方一致の順)、および日付・時刻の正規表現(`DATE_PATTERN` / `TIME_PATTERN`)。エラーメッセージは `docs/P002-frontend-spec.md` 3章の日本語文言

### `src/meeting_room/repositories/` — データアクセス層

- users_repo.py — `users` のCRUD。`password_hash` を返すのは `find_by_id_with_hash` のみ
- sessions_repo.py — `sessions` のCRUDと期限切れ削除・ユーザー単位の一括削除
- rooms_repo.py — `rooms` のCRUDと同名の有効な会議室の検索
- reservations_repo.py — `reservations` / `reservation_attendees` のCRUD、期間・ユーザー別の一覧、`count_future`、参加者の全置換、および **P003 5.2 の重複判定SQL(`find_conflicts`。半開区間の交差。境界一致は重複としない)**。※CR-001: 共通 `SELECT`・`to_reservation_dict`・`insert`・`update` が `meeting_url` を扱う(未登録は空文字)

### `src/meeting_room/services/` — 業務ルールとトランザクション境界

- auth_service.py — ログイン・ログアウト・セッション解決(スライディング期限と絶対期限の判定)
- room_service.py — 会議室の業務ルール(名称一意性、無効化時の今後の予約チェック。`count_future_reservations` は U003-T2 で `reservations_repo.count_future` を呼ぶ本実装に差し替え済み)
- user_service.py — ユーザーの業務ルール(社員ID重複、最後の有効な管理者の保護、自分自身の無効化拒否、権限変更・無効化時のセッション削除)
- reservation_service.py — **本システムの中核。** 予約の入力検証(30分刻み・業務時間・過去日・会議室の有効性・収容人数・参加者)、重複チェックとINSERT/UPDATEを同一 `BEGIN IMMEDIATE` トランザクションに収める排他制御、権限判定(予約者本人または管理者)、ロックタイムアウトの 500 変換(ADR-007 / P003 5)

### `src/meeting_room/handlers/` — HTTP入出力層

- auth_handlers.py — API-01〜API-03(ログイン・ログアウト・自分の情報取得)。Cookie属性の付与もここ
- room_handlers.py — API-04〜API-07(会議室)
- user_handlers.py — API-08〜API-11(ユーザー。`scope` による2経路の認可分岐を含む)
- reservation_handlers.py — API-12〜API-17(予約)。API-12のクエリ検証(必須・期間31日以内・`room_id` 繰り返し)、API-13の `period` 検証を含む

## マイグレーション `migrations/`

差分適用型。`schema_migrations` に未記録のファイルのみをファイル名昇順で適用する(ADR-009)。**適用済みファイルは編集しない。**

- 001-init.sql — `users` / `sessions` / `idx_sessions_user_id`(Sprint 1)
- 002-rooms.sql — `rooms` / `uq_rooms_name_active`(部分ユニークインデックス)(Sprint 2)
- 003-reservations.sql — `reservations` / `reservation_attendees`(ON DELETE CASCADE)/ `idx_reservations_room_date` / `idx_reservations_date` / `idx_reservations_user_date`(Sprint 3)
- 004-meeting-url.sql — `reservations.meeting_url` の追加(`ALTER TABLE ... ADD COLUMN`、`NOT NULL DEFAULT ''`)。**※CR-001**(オンライン会議URL。ADR-011)

## テスト `tests/`

* 単体テスト実行: `cd server && python3 -m unittest discover -s tests -t .`(結合テストも同時に検出される)
* 結合テスト実行(個別): `cd server && python3 -m unittest tests.integration.test_t0NN_xxx -v`
* 受け入れ結合テスト実行(P009 / P201): `cd server && python3 -m unittest discover -s tests/acceptance -t .`

- `__init__.py` — テストパッケージ初期化
- test_db_migration.py — U001-T1: 差分適用マイグレーションの冪等性・ロールバック
- test_errors.py — U001-T2: エラーレスポンス変換とアクセスログの項目
- test_security.py — U001-T3: scryptハッシュ・セッションID・時刻取得の集約
- test_users_repo.py — U001-T3: `users` Repository と初期管理者シードの冪等性
- test_auth_service.py — U001-T4: ログイン・セッション有効性判定
- test_auth_handlers.py — U001-T4: 認証API3本と `require_*` ヘルパ、アクセスログの `user_id`
- test_rooms_repo.py — U002-T1: `002-rooms.sql` の適用と `rooms` Repository・部分ユニーク制約
- test_room_service.py / test_room_handlers.py — U002-T2: 会議室の業務ルールとAPI-04〜07
- test_user_service.py / test_user_handlers.py — U002-T3: ユーザーの業務ルールとAPI-08〜11
- test_reservations_repo.py — U003-T1: `003-reservations.sql` の適用と `reservations` Repository。**重複判定の境界値(境界接触が0件になること)を含む**
- test_reservation_service.py — U003-T2: `ReservationRequest` と予約の業務ルール、および**2スレッド同時 `create` で必ず一方だけが成功することの検証**
- test_reservation_read_handlers.py — U003-T3: API-12〜API-14(`/mine` がIDとして解釈されないルーティング順序の確認を含む)
- test_reservation_write_handlers.py — U003-T4: API-15〜API-17(409の `error.conflicts` の形状、403、204の本文なしを含む)
- fixtures/seed.py — 結合テスト用の基準データセット投入(`docs/P006-test-plan.md` 5章)
- integration/support.py — 結合テストの共通基底(DB作り直し・アプリ起動・ログイン補助)
- integration/test_t001_login_session.py 〜 test_t014_room_deactivate_blocked.py — 結合テスト T001・T002・T004〜T009・T011〜T014(T003・T010・T015〜T018 はクライアント側 `client/tests/integration/`)
- integration/test_t019_meeting_url.py — 結合テストT019(**※CR-001** オンライン会議URLのAPI契約と `004-meeting-url.sql` の差分適用。手順12で実プロセスを2回目として起動する)
- acceptance/support.py — 受け入れ結合テストの実行基盤。**uvicorn を別プロセスで起動・停止**する `ServerProcess` と、標準ライブラリ `urllib.request` による実HTTPクライアント `HttpClient`(A007・A009・A012 は実プロセスでないと確認できないため)
- acceptance/base.py — 受け入れ結合テストの共通 TestCase(DB作り直し・基準データセット投入・ログイン補助・サーバーログ検査)
- acceptance/test_a002_double_booking.py — A002: 逐次・同時2本・同時5本の二重予約防止
- acceptance/test_a003_role_separation.py — A003(API側): 管理者専用API8本の403/401、他人の予約のPUT/DELETE
- acceptance/test_a004_room_master_impact.py — A004(API側): 無効化の業務制約409、収容人数変更の既存予約・新規予約への波及
- acceptance/test_a006_session_lifecycle.py — A006(API側): Cookie属性・スライディング期限・絶対期限・無効化/権限変更/ログアウトによる失効
- acceptance/test_a007_restart_resilience.py — A007: **同一DBファイルで4回起動**し、`schema_migrations` が増えないこと・データが残ること・WAL残存下でも起動できることを確認(運用観点 V-O-01 / V-O-02)
- acceptance/test_a008_calendar_performance.py — A008(API側): 10室×200件での応答時間計測と、API-12がN+1でないことのSQL回数検証
- acceptance/test_a009_concurrent_load.py — A009: 30スレッド同時の参照90本・更新30本で5xxと `DB_LOCK_TIMEOUT` が0件であること
- acceptance/test_a010_security.py — A010: パスワードハッシュ・応答本文/ログの秘密混入・Cookie属性・403・500応答からの情報漏えい
- acceptance/test_a012_operator_acceptance.py — A012: 環境変数指定の初期管理者・ログ形式・停止/再起動・不正 `DB_PATH` での起動失敗

## 関連ドキュメント

* ディレクトリ構成の根拠: `docs/P003-backend-spec.md` 2.1
* 各ファイルの実装指示: `docs/P007-impl-direction.md` および `docs/P007-impl-direction/U001〜U004-*.md`
* 技術選定の理由: `docs/ADR.md`(ADR-002 バックエンド、ADR-003 パスワードハッシュ、ADR-004 データストア、ADR-009 マイグレーション)
* 技術的側面の概観: `docs/ArchitectureHandbook.md`
* 結合テストの実行記録: `docs/test-records/`
