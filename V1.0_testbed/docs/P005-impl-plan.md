# 実装計画書 — 会議室予約システム

> 本書は `spec-driven-dev` Skill フェーズP005の成果物。`docs/P002-frontend-spec.md`・`docs/P003-backend-spec.md`・`docs/P004-traceability-matrix.md` にもとづき、実装をスプリントに分割する。

## 1. スプリント分割の考え方

* 全体を4スプリントに分割する。各スプリントは画面数・API数・データモデル数がおおむね均等になるようにしつつ、技術的リスク(重複チェックロジックなど)の高いスプリントは軽めの画面数で相殺した。
* 依存関係: 認証(U001)がすべての後続スプリントの前提。予約の基本CRUD(U002)は会議室の参照(読み取りのみ、U001で先行実装)に依存するが、会議室の管理者向けCRUD(U003)には依存しない(会議室データはシード投入または最小限のAPIで用意する。§4参照)。
* インフラ・ミドルウェア専用のスプリントは設けない。`docs/P003-backend-spec.md` §7のとおり、可用性・スケーラビリティ・TLS終端等のインフラ構成は `docs/P302-deliver.md`(Closing)側で決定するため、実装スプリントの対象外である。

## 2. スプリント一覧

| スプリント | 名称(英語) | 位置づけ |
| --- | --- | --- |
| 1 | `U001-foundation-and-auth` | 全スプリントの土台。DBスキーマ・マイグレーション基盤、認証(ログイン/ログアウト/自分情報取得)、S01、会議室の読み取り専用API。技術的不確定要素(マイグレーションの冪等性、セッション管理)が大きいため最初に実施する。 |
| 2 | `U002-reservation-core` | 予約の中核機能。予約の新規作成・一覧取得(重複チェック・収容人数チェックを含む)、S02、S03、S05。本アプリで最もロジックが複雑な重複判定を含むため、画面数はU003より少なくしてバランスを取る。 |
| 3 | `U003-reservation-management-and-rooms` | 予約の更新・取消(自分自身の枠を除いた重複チェック)、S04、および会議室管理者機能(会議室CRUD)、S06。 |
| 4 | `U004-user-administration` | ユーザー管理者機能(ユーザーCRUD)、S07、および横断的な認可の最終確認(管理者専用画面/APIガードの総仕上げ)。 |

## 3. 各スプリントの内容

### U001-foundation-and-auth

* **画面**: S01(ログイン画面)
* **API**: `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/me`, `GET /api/rooms`(読み取りのみ)
* **データモデル**: `users`, `sessions`, `schema_migrations`, `rooms`(読み取り専用として先行実装。書き込みAPIはU003)
* **その他**: マイグレーション基盤(`server/migrations/`, `schema_migrations` テーブル)、パスワードハッシュ(bcrypt)、認証ミドルウェア。開発用の初期管理者ユーザーをシードするマイグレーション(`002_seed_admin_user.sql` 等)を含める。

### U002-reservation-core

* **画面**: S02(予約カレンダー画面)、S03(予約作成画面)、S05(マイ予約一覧画面)
* **API**: `GET /api/reservations`, `GET /api/reservations/mine`, `GET /api/reservations/{id}`, `POST /api/reservations`
* **データモデル**: `reservations`, `reservation_participants`
* **その他**: 重複判定ロジック(`docs/P003-backend-spec.md` §5.9)、収容人数チェック、Repository層の時刻引数ルール(§6)をここで初めて適用する。

### U003-reservation-management-and-rooms

* **画面**: S04(予約詳細・編集画面)、S06(会議室管理画面)
* **API**: `PUT /api/reservations/{id}`, `DELETE /api/reservations/{id}`, `POST /api/rooms`, `PUT /api/rooms/{id}`, `DELETE /api/rooms/{id}`
* **データモデル**: 追加なし(既存テーブルへの書き込み経路を追加)
* **その他**: 予約編集時の自己除外重複チェック、会議室の論理削除、管理者権限ガードの初適用。

### U004-user-administration

* **画面**: S07(ユーザー管理画面)
* **API**: `GET /api/users`, `POST /api/users`, `PUT /api/users/{id}`, `DELETE /api/users/{id}`
* **データモデル**: 追加なし
* **その他**: 社員ID一意制約違反のハンドリング、自己無効化禁止ロジック、全管理者専用画面・APIを対象にした横断的な認可の最終確認タスク(結合確認用の薄いタスク)。

## 4. 全スプリント × 画面・API・データモデル対応表(実装漏れ検証)

| 画面/API/データモデル | 実装スプリント |
| --- | --- |
| S01 ログイン画面 | U001 |
| S02 予約カレンダー画面 | U002 |
| S03 予約作成画面 | U002 |
| S04 予約詳細・編集画面 | U003 |
| S05 マイ予約一覧画面 | U002 |
| S06 会議室管理画面 | U003 |
| S07 ユーザー管理画面 | U004 |
| POST /api/auth/login | U001 |
| POST /api/auth/logout | U001 |
| GET /api/me | U001 |
| GET /api/rooms | U001 |
| POST /api/rooms | U003 |
| PUT /api/rooms/{room_id} | U003 |
| DELETE /api/rooms/{room_id} | U003 |
| GET /api/reservations | U002 |
| GET /api/reservations/mine | U002 |
| GET /api/reservations/{reservation_id} | U002 |
| POST /api/reservations | U002 |
| PUT /api/reservations/{reservation_id} | U003 |
| DELETE /api/reservations/{reservation_id} | U003 |
| GET /api/users | U004 |
| POST /api/users | U004 |
| PUT /api/users/{user_id} | U004 |
| DELETE /api/users/{user_id} | U004 |
| users テーブル | U001 |
| sessions テーブル | U001 |
| schema_migrations テーブル | U001 |
| rooms テーブル | U001(読み取り)/ U003(書き込み) |
| reservations テーブル | U002 |
| reservation_participants テーブル | U002 |

全画面(7)・全API(17)・全データモデル(6)がいずれかのスプリントに割り当てられており、実装漏れは無い。

## 5. コード格納先

* クライアント・サーバ型構成のため、`client/`(React + TypeScript + Vite)と `server/`(Python + FastAPI)を作成する。
* 各スプリントの実装指示(`docs/P007-impl-direction/U00N-*.md`)には、どちらのアプリの何を変更・作成するかを明記する。

## 6. CR-001対応(Refactor経由の追加タスク)

`docs/P901-cr-direction/CR-001.md`(「備考(社内向けメモ)」欄追加)は、既存のスプリント構成に新規スプリントを追加するほどの規模ではない(新規画面・新規APIエンドポイントを伴わず、既存の予約作成・更新APIへの項目追加にとどまる)ため、既存スプリントへの追加タスクとして組み込む。

* **U002-reservation-core**: マイグレーション追加・スキーマ拡張・作成系API(`POST /api/reservations`)・S03への項目追加を担当(新規タスク U002-T7)。
* **U003-reservation-management-and-rooms**: 更新系API(`PUT /api/reservations/{id}`)・詳細取得API(`GET /api/reservations/{id}`)・一覧API(`GET /api/reservations`)のマスキングロジック・S04への項目追加を担当(新規タスク U003-T7)。

依存関係: U002-T7(列追加・作成時の保存)が完了してから、U003-T7(更新・閲覧時のマスキング)に着手する(既存のU002→U003の依存順序と整合する)。
