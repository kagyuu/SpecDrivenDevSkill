# 実装計画書 — 会議室予約システム

> 本書は `spec-driven-dev` Skill フェーズP005の成果物です。インプット文書: `docs/P001-requirement.md`、`docs/P002-frontend-spec.md`、`docs/P003-backend-spec.md`、`docs/P004-traceability-matrix.md`(全項目OK確認済み)。

## 1. スプリント分割の方針

`SKILL-P005-impl-plan.md` の原則(コード量の均等化、依存関係の前倒し、スプリント内での単体テスト・結合テスト完結、不確実要素の前倒し)に従い、対象の規模(画面7・API17・テーブル5)を検討した結果、**4スプリント**に分割する。

* 認証・セッションはすべての画面・APIが依存する土台であり、かつ本アプリで最も不確実性が高い要素(Cookie/セッションの実現方式、SQLiteでの排他制御)を含むため、最初のスプリントに前倒しする。
* 会議室管理・ユーザー管理は、互いに依存せず、かつ他のどの機能からも参照される「マスタデータ」を扱う点で性質が近い(CRUD + 論理削除という同型の実装パターン)ため、1スプリントにまとめてコード量を稼ぐ。
* 予約機能は分量が大きい(カレンダー表示・作成・詳細編集・取消・マイ予約の5画面相当・6API)ため2スプリントに分割する。分割の軸は「新規作成に必要な最小機能(閲覧+作成)」と「参照・更新・削除系」とし、前者を先に実装することで後者のテスト(既存予約に対する更新・削除)がしやすくなるようにする。
* 単純な画面数・API数・テーブル数の合計だけでは各スプリントの実装負荷は完全には均等にならない(後述§4参照)。特にスプリント3は画面・API数が少ないが、予約重複チェックの排他制御(`docs/P003-backend-spec.md` §5)という本アプリで最も難度の高いロジックを含むため、体感の実装負荷は数字以上に大きい。この点を踏まえてスプリント3以降の見積もりでは注意を要する旨を記載する。

## 2. スプリント一覧

| # | スプリント名(英語) | 位置づけ |
| --- | --- | --- |
| 1 | `foundation-auth` | プロジェクト基盤(client/server初期化、全テーブルのスキーマ作成)+ ログイン画面 + 認証・セッションAPI |
| 2 | `admin-management` | 会議室管理・ユーザー管理(管理者専用のマスタデータCRUD) |
| 3 | `reservation-core` | 予約カレンダー表示・予約作成(閲覧+作成の最小機能、重複チェックの排他制御を含む) |
| 4 | `reservation-detail-mine` | 予約詳細・編集・取消・マイ予約一覧(参照・更新・削除系) |

## 3. 各スプリントの内容

### 3.1 `foundation-auth`(スプリント1)

* **画面**: S01 ログイン画面
* **API**: `POST /api/auth/login`、`POST /api/auth/logout`、`GET /api/me`
* **データモデル**: USERS、ROOMS、RESERVATIONS、RESERVATION_PARTICIPANTS、SESSIONS(全テーブルのスキーマをここで作成する。ROOMS・RESERVATIONS等のCRUD処理自体は後続スプリントで実装するが、テーブル定義とマイグレーションは基盤として本スプリントで用意する)
* **その他**: プロジェクトディレクトリ初期化(`client/`(React+TS+Vite)、`server/`(Python+FastAPI、uvビルド))、認証・認可ミドルウェア(`require_admin()` 等の依存関数の骨組み)、共通エラーレスポンス形式の実装、SQLite接続・マイグレーション実行の仕組み。
* 依存: なし(最初のスプリント)。

### 3.2 `admin-management`(スプリント2)

* **画面**: S06 会議室管理画面、S07 ユーザー管理画面
* **API**: `GET/POST/PUT/DELETE /api/rooms`、`GET/POST/PUT/DELETE /api/users`
* **データモデル**: 追加なし(スプリント1のROOMS・USERSスキーマを使用)
* 依存: スプリント1(認証・セッション、ROOMS・USERSテーブル)。

### 3.3 `reservation-core`(スプリント3)

* **画面**: S02 予約カレンダー画面、S03 予約作成画面
* **API**: `GET /api/reservations`、`POST /api/reservations`
* **データモデル**: 追加なし(スプリント1のRESERVATIONS・RESERVATION_PARTICIPANTSスキーマを使用)
* **主要ロジック**: `docs/P003-backend-spec.md` §5 の重複チェック・`BEGIN IMMEDIATE` による排他制御。
* 依存: スプリント1(認証)、スプリント2(会議室一覧がプルダウンに必要、ユーザー一覧が参加者選択に必要)。

### 3.4 `reservation-detail-mine`(スプリント4)

* **画面**: S04 予約詳細・編集画面、S05 マイ予約一覧画面
* **API**: `GET /api/reservations/mine`、`GET /api/reservations/{reservation_id}`、`PUT /api/reservations/{reservation_id}`、`DELETE /api/reservations/{reservation_id}`
* **データモデル**: 追加なし
* 依存: スプリント3(予約作成ができないと編集・取消・詳細表示・一覧のテストデータが作れない)。

## 4. 対応表(全スプリント × 全画面・API・データモデル)

実装漏れがないことを検証する。

| 画面 | 実装スプリント |
| --- | --- |
| S01 ログイン画面 | 1 |
| S02 予約カレンダー画面 | 3 |
| S03 予約作成画面 | 3 |
| S04 予約詳細・編集画面 | 4 |
| S05 マイ予約一覧画面 | 4 |
| S06 会議室管理画面 | 2 |
| S07 ユーザー管理画面 | 2 |

| API | 実装スプリント |
| --- | --- |
| POST /api/auth/login | 1 |
| POST /api/auth/logout | 1 |
| GET /api/me | 1 |
| GET /api/rooms | 2 |
| POST /api/rooms | 2 |
| PUT /api/rooms/{room_id} | 2 |
| DELETE /api/rooms/{room_id} | 2 |
| GET /api/users | 2 |
| POST /api/users | 2 |
| PUT /api/users/{user_id} | 2 |
| DELETE /api/users/{user_id} | 2 |
| GET /api/reservations | 3 |
| POST /api/reservations | 3 |
| GET /api/reservations/mine | 4 |
| GET /api/reservations/{reservation_id} | 4 |
| PUT /api/reservations/{reservation_id} | 4 |
| DELETE /api/reservations/{reservation_id} | 4 |

画面7件・API17件すべてがいずれか1つのスプリントに割り当てられており、実装漏れはない。

| データモデル(テーブル) | スキーマ作成スプリント | 主なCRUD実装スプリント |
| --- | --- | --- |
| USERS | 1 | 2(管理)、1(認証時の参照) |
| ROOMS | 1 | 2 |
| RESERVATIONS | 1 | 3(作成)、4(参照・更新・削除) |
| RESERVATION_PARTICIPANTS | 1 | 3(作成)、4(更新・削除) |
| SESSIONS | 1 | 1 |

## 5. 計算機・ミドルウェア・データベースの要否

* データベース: SQLite(ファイルベース)。`server/` 配下にファイルを配置する。追加のミドルウェア(Redis等のキャッシュ、メッセージキュー)は本要件の規模(同時30接続、単一サーバー)では不要と判断する。
* 上記の理由により、インフラ専用のスプリントは設けない。プロジェクト初期化・DBスキーマ作成はスプリント1に含める。

## 6. 未解決事項

* 特になし。

## 7. CR対応履歴(P903で追記)

* **CR-002**(2026-08-03、S06に説明文(description)を追加): 既存スプリント2(`admin-management`)の対象範囲内の差分実装として、新規タスクU006(既存スプリント構成には含めず、CR専用の差分スプリントとしてP007目次に追加)で対応した。新規のスプリント構成変更・アーキテクチャ上の計画変更は不要と判断した(CR-001と同様の判断)。§4の対応表(S06=スプリント2、ROOMS=スプリント1でスキーマ作成・スプリント2でCRUD)自体に変更はない(descriptionカラムの追加はスキーマの拡張であり、担当スプリントの変更を伴わない)。

* **CR-003**(2026-08-04、予約に参加予定人数(attendee_count)を追加): 既存スプリント3(`reservation-core`、予約作成)・スプリント4(`reservation-detail-mine`、予約詳細・編集)の対象範囲にまたがる差分実装として、新規タスクU007(CR専用の差分スプリントとしてP007目次に追加)で対応した。§4の対応表(S03=スプリント3、S04=スプリント4、RESERVATIONS=スプリント1でスキーマ作成)自体に変更はない。
  * ただしCR-003では、データモデル変更に伴いマイグレーションの適用方式そのものを「起動のたびに全件再実行」から「`SCHEMA_MIGRATIONS` テーブルによる差分適用」に変更している(`docs/P003-backend-spec.md` §6.4)。これはスプリント1(プロジェクト初期化・DBスキーマ作成)で作った基盤に対する変更であり、CR-003のスコープに含めた。判断理由は `docs/cr-records/CR-003.md` を参照。
