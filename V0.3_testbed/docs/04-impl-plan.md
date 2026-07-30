# 実装計画書 — 会議室予約システム

> 本書は `spec-driven-dev` Skill フェーズ4の成果物です(V0.3ルールで再生成)。
> インプット: `docs/01-requirement.md`, `docs/02-frontend-spec.md`, `docs/03-backend-spec.md`

## 1. スプリント方針

全4スプリントに分割する。不確定要素が大きい認証・セッション基盤を最初のスプリントに置き、以降は「読み取り系(カレンダー閲覧)」→「予約の作成・変更(重複チェックという最も業務ロジックが複雑な部分)」→「管理者機能・横断的な仕上げ」の順に進める。各スプリントは、それに先立つスプリントで実装済みのAPI・データモデルにのみ依存する。追加の計算機・ミドルウェアは不要(単一プロセス+SQLiteファイルのみ)。

「各スプリントのコード量を同じにする」の目安として、画面数・API数・データモデル数の合計(機械的に数えられる指標)を採用する。厳密な行数の均等化は求めない。

## 2. スプリント一覧

| スプリント | 名称(英語) | 位置づけ | コード量目安(画面数+API数+新規データモデル数) |
| --- | --- | --- | --- |
| 1 | `foundation` | DBスキーマ、認証・セッション基盤、ログイン画面。以降全スプリントが依存する土台。 | 1画面 + 3API + 5モデル = 9 |
| 2 | `rooms-and-calendar-read` | 会議室CRUD、予約の参照系API、カレンダー閲覧・マイ予約一覧・会議室管理画面。 | 3画面 + 7API + 0モデル = 10 |
| 3 | `reservation-write` | 予約の作成・更新・取消(重複チェック中心)、予約作成/詳細編集画面。 | 2画面 + 3API + 0モデル = 5 |
| 4 | `user-admin-and-hardening` | ユーザー管理機能、横断的なエラーハンドリング/認可の仕上げ。 | 1画面 + 4API + 0モデル = 5 |

スプリント1・2がやや大きい(9・10)のは、スプリント1が全スプリントの土台(データモデル一式)を含むため、スプリント2が読み取り系APIをまとめて持つためであり、意図的な配分である(不確定要素の大きい基盤を先に厚めに倒す方針、本書1章のとおり)。3・4は概ね均等(5・5)。

## 3. 各スプリントで実装する画面・API・データモデル

### スプリント1: `foundation`

* 画面: S01 ログイン画面
* API: `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/me`
* データモデル: `users`, `rooms`, `reservations`, `reservation_participants`, `sessions`(全テーブルのスキーマ作成、初期データ投入)

### スプリント2: `rooms-and-calendar-read`

* 画面: S02 予約カレンダー画面, S05 マイ予約一覧画面, S06 会議室管理画面
* API: `GET /api/rooms`, `POST /api/rooms`, `PUT /api/rooms/{room_id}`, `DELETE /api/rooms/{room_id}`, `GET /api/reservations`, `GET /api/reservations/mine`, `GET /api/reservations/{reservation_id}`
* データモデル: 追加なし(スプリント1のスキーマを使用)

### スプリント3: `reservation-write`

* 画面: S03 予約作成画面, S04 予約詳細・編集画面
* API: `POST /api/reservations`, `PUT /api/reservations/{reservation_id}`, `DELETE /api/reservations/{reservation_id}`
* データモデル: 追加なし

### スプリント4: `user-admin-and-hardening`

* 画面: S07 ユーザー管理画面(+ 各画面の管理者専用ナビゲーションの出し分け仕上げ)
* API: `GET /api/users`, `POST /api/users`, `PUT /api/users/{user_id}`, `DELETE /api/users/{user_id}`
* データモデル: 追加なし
* 横断: エラーハンドリング共通化、認可(403/401)の一貫性確認

## 4. 対応表(全スプリント × 全画面・API・データモデル)

| 種別 | 項目 | 実装スプリント |
| --- | --- | --- |
| 画面 | S01 ログイン | 1 |
| 画面 | S02 予約カレンダー | 2 |
| 画面 | S03 予約作成 | 3 |
| 画面 | S04 予約詳細・編集 | 3 |
| 画面 | S05 マイ予約一覧 | 2 |
| 画面 | S06 会議室管理 | 2 |
| 画面 | S07 ユーザー管理 | 4 |
| API | POST /api/auth/login | 1 |
| API | POST /api/auth/logout | 1 |
| API | GET /api/me | 1 |
| API | GET /api/rooms | 2 |
| API | POST /api/rooms | 2 |
| API | PUT /api/rooms/{room_id} | 2 |
| API | DELETE /api/rooms/{room_id} | 2 |
| API | GET /api/reservations | 2 |
| API | GET /api/reservations/mine | 2 |
| API | GET /api/reservations/{id} | 2 |
| API | POST /api/reservations | 3 |
| API | PUT /api/reservations/{id} | 3 |
| API | DELETE /api/reservations/{id} | 3 |
| API | GET /api/users | 4 |
| API | POST /api/users | 4 |
| API | PUT /api/users/{id} | 4 |
| API | DELETE /api/users/{id} | 4 |
| データモデル | users | 1 |
| データモデル | rooms | 1 |
| データモデル | reservations | 1 |
| データモデル | reservation_participants | 1 |
| データモデル | sessions | 1 |

上記の通り、`docs/01-requirement.md` の全7画面・全17API、および `docs/03-backend-spec.md` の全5テーブルが、いずれかのスプリントに漏れなく対応している。実装漏れなし。

## 5. コード格納先

* クライアント・サーバ型のため `server/`(Python + FastAPI, uv でビルド)、`client/`(静的HTML/TS、後続フェーズで詳細を確定)を用いる。
