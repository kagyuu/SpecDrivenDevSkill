# 実装計画書 — 会議室予約システム

> 本書は `spec-driven-dev` Skill フェーズP005の成果物です。`docs/P002-frontend-spec.md`・`docs/P003-backend-spec.md`・`docs/P004-traceability-matrix.md` にもとづき、実装をどのスプリントに分割するかを確定します。

## 1. スプリント分割の考え方

* コード格納先はクライアント・サーバ型のため `client/`(React+TS+Vite)、`server/`(Python+FastAPI)とする(`SKILL-P007-impl-direction.md` の規定に従う)。
* 5スプリント(U001〜U005)に分割する。ミドルウェア・計算機資源としての追加スプリントは作らない。★ACCEPTED★ データストアがSQLite(サーバプロセス内蔵、別立てDBサーバ不要)であるため、専用のインフラ構築スプリントは不要と判断した。検討した代替: 「データベース構築」専用スプリントを設ける。不採用理由: SQLiteはファイルベースでありアプリケーション起動時のマイグレーション適用(`docs/P003-backend-spec.md` 3章)のみで完結するため、専用スプリントを設けても中身がU001のごく一部の作業(スキーマファイル作成)にしかならず、分割の実益が無い。残存リスク特になし。
* 依存関係: 認証(U001)→会議室管理(U002)→予約コア機能(U003、会議室が存在しないと予約を作れないため)→予約詳細・マイ予約(U004、予約コアの上に構築)→ユーザー管理・横断強化(U005)の順とする。各スプリントは直前までのスプリントが実装済みの画面・API・データモデルにのみ依存する。
* 技術的難易度: 予約の重複チェック・排他制御(`docs/P003-backend-spec.md` 4.6〜4.9.2節、`BEGIN IMMEDIATE`によるトランザクション制御)が本アプリで最もリスクの高い実装であるため、依存関係が許す限り早いスプリント(U003、全5スプリント中3番目)に配置する。会議室が先に存在しないと予約を作れないため、これより前には置けない。
* データモデルは全テーブルをU001でまとめて作成する(`docs/P003-backend-spec.md` 2.2節の初期マイグレーション `001_initial_schema.sql` に全テーブルを含める)。以降のスプリントは新規テーブルを作らず、既存テーブルへのCRUD追加のみを行う。★FIXME★ 全テーブルを最初のマイグレーションにまとめる方針は、テーブル数が6個と少なく相互参照(外部キー)が多いため一括作成が合理的と判断したための仮定。将来CRでテーブルが大幅に増える場合はスプリントごとに段階的マイグレーションを分ける方針に切り替える必要がある。

## 2. スプリント一覧

| スプリントID | 名称(英語) | 位置づけ |
| --- | --- | --- |
| U001 | foundation-and-auth | プロジェクト基盤(client/server初期化)、全データモデル(マイグレーション)、認証(ログイン/ログアウト/自分の情報取得)、S01ログイン画面 |
| U002 | room-management | 会議室CRUD API、S06会議室管理画面(管理者用) |
| U003 | reservation-core-and-calendar | 予約の作成・一覧・重複チェック(最もリスクの高い排他制御を含む)、参加者候補API、S02予約カレンダー画面、S03予約作成画面 |
| U004 | reservation-detail-and-mylist | 予約の詳細取得・更新・取消、自分の予約一覧、S04予約詳細・編集画面、S05マイ予約一覧画面 |
| U005 | user-management-and-hardening | ユーザーCRUD API(自己無効化禁止・最後の管理者保護含む)、S07ユーザー管理画面、横断ナビゲーション結線、構造化ログ・エラーレスポンス統一の最終確認 |

## 3. 各スプリントの詳細

### U001 foundation-and-auth

* **画面**: S01(ログイン画面)
* **API**: `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/me`
* **データモデル**: `users`, `rooms`, `reservations`, `reservation_participants`, `sessions`, `schema_migrations`(全テーブル、`docs/P003-backend-spec.md` 2.2節のDDL一式)
* **基盤作業**: `server/`(FastAPIプロジェクト、uvicorn起動、`sqlite3`接続初期化、マイグレーション実行処理)、`client/`(Vite+React+TSプロジェクト初期化、APIクライアントの土台、ルーティングの土台)
* **シードデータ**: 初期マイグレーションに、動作確認用の初期管理者アカウント(`user_id=admin`)を1件含める。★FIXME★ 初期パスワードの具体的な値・配布方法(環境変数で注入する/固定値をドキュメントに記載する等)はP001に明記が無いため、実装時(P007)に開発・テスト用の固定値を仮設定し、本番投入前に変更が必要な旨をREADME相当の記載に残す方針とする(`docs/P003-backend-spec.md`のパスワードハッシュ方式でハッシュ化して格納する)。
* **技術的難易度**: 中(プロジェクト基盤構築の初期コストはあるが、業務ロジック自体は単純)

### U002 room-management

* **画面**: S06(会議室管理画面)
* **API**: `GET /api/rooms`, `POST /api/rooms`, `PUT /api/rooms/{room_id}`, `DELETE /api/rooms/{room_id}`
* **依存**: U001(認証・管理者権限チェックの仕組み)
* **技術的難易度**: 低(定型的なCRUD、論理削除のみやや注意)

### U003 reservation-core-and-calendar

* **画面**: S02(予約カレンダー画面)、S03(予約作成画面)
* **API**: `GET /api/reservations`, `POST /api/reservations`, `GET /api/users/directory`(参加者候補、`docs/P002-frontend-spec.md` 4.10.1節)
* **依存**: U001(認証)、U002(会議室が存在しないと予約を作成できない)
* **技術的難易度**: 高(重複チェックの排他制御 `BEGIN IMMEDIATE`、収容人数チェック、カレンダーグリッド表示のUIロジック)。このスプリントの完遂を最優先事項とし、後続スプリントより手厚くタスク分割する(P007で反映)。
* **CR-001対応(※P903内側のP005再実行で追記)**: S03(オンライン会議URL入力欄・バリデーション)、`POST /api/reservations`(リクエストへの`meeting_url`追加)にオンライン会議URL関連の項目が追加される。スプリント構成・依存関係・技術的難易度の判断に変更は無い(既存の入力項目パターン(備考欄)と同種の追加項目であり、新たな技術的リスクを持ち込まない)。`GET /api/reservations`(一覧)は`meeting_url`を含めない設計を維持するため変更なし。

### U004 reservation-detail-and-mylist

* **画面**: S04(予約詳細・編集画面)、S05(マイ予約一覧画面)
* **API**: `GET /api/reservations/{reservation_id}`, `PUT /api/reservations/{reservation_id}`, `DELETE /api/reservations/{reservation_id}`, `GET /api/reservations/mine`
* **依存**: U003(予約コアのデータモデル・重複チェックロジックを再利用するため)
* **技術的難易度**: 中(更新時の「自分自身を重複判定から除外する」分岐、編集権限チェック)
* **CR-001対応(※P903内側のP005再実行で追記)**: S04(オンライン会議URLのリンク表示・編集)、`GET /api/reservations/{reservation_id}`・`PUT /api/reservations/{reservation_id}`(レスポンス/リクエストへの`meeting_url`追加)が対象。スプリント構成・依存関係・技術的難易度の判断に変更は無い。`GET /api/reservations/mine`(S05)は`meeting_url`を表示項目としないため変更なし。

### U005 user-management-and-hardening

* **画面**: S07(ユーザー管理画面)
* **API**: `GET /api/users`, `POST /api/users`, `PUT /api/users/{user_id}`, `DELETE /api/users/{user_id}`
* **依存**: U001(認証・パスワードハッシュ方式の再利用)
* **横断作業**: 全画面のヘッダーナビゲーション結線(マイ予約・会議室管理・ユーザー管理へのリンク出し分け、ログアウト動線)、構造化ログ出力の最終確認(`docs/P003-backend-spec.md` 6章)、エラーレスポンス形式の全API横断的な確認(`docs/P002-frontend-spec.md` 4章の共通エラー形式に全APIが準拠しているかの最終チェック)
* **技術的難易度**: 中(CRUD自体は低いが、自己無効化禁止・最後の管理者保護のロジックと、横断的な結線作業がある)

## 4. 全スプリント × 画面・API・データモデル対応表(実装漏れ検証)

### 4.1 画面

| 画面ID | スプリント |
| --- | --- |
| S01 | U001 |
| S02 | U003 |
| S03 | U003 |
| S04 | U004 |
| S05 | U004 |
| S06 | U002 |
| S07 | U005 |

全7画面(`docs/P001-requirement.md` 画面一覧)がいずれか1スプリントに割り当てられており、漏れは無い。

### 4.2 API

| API | スプリント |
| --- | --- |
| POST /api/auth/login | U001 |
| POST /api/auth/logout | U001 |
| GET /api/me | U001 |
| GET /api/rooms | U002 |
| POST /api/rooms | U002 |
| PUT /api/rooms/{room_id} | U002 |
| DELETE /api/rooms/{room_id} | U002 |
| GET /api/reservations | U003 |
| POST /api/reservations | U003 |
| GET /api/users/directory | U003 |
| GET /api/reservations/{reservation_id} | U004 |
| PUT /api/reservations/{reservation_id} | U004 |
| DELETE /api/reservations/{reservation_id} | U004 |
| GET /api/reservations/mine | U004 |
| GET /api/users | U005 |
| POST /api/users | U005 |
| PUT /api/users/{user_id} | U005 |
| DELETE /api/users/{user_id} | U005 |

`docs/P001-requirement.md` の17APIおよび`docs/P002-frontend-spec.md` 4.10.1節で追加された`GET /api/users/directory`の計18APIすべてが割り当てられており、漏れは無い。

### 4.3 データモデル

| テーブル | 作成スプリント |
| --- | --- |
| users | U001 |
| rooms | U001 |
| reservations | U001 |
| reservation_participants | U001 |
| sessions | U001 |
| schema_migrations | U001 |

全6テーブル(`docs/P003-backend-spec.md` 2.2節)がU001で作成される。以降のスプリントは既存テーブルへのCRUD追加のみ。

**CR-001対応(※P903内側のP005再実行で追記)**: `reservations` テーブルに `meeting_url` カラムを追加する(`server/migrations/003_add_reservation_meeting_url.sql`、`docs/P003-backend-spec.md` 2.2/3章)。新規テーブルの追加ではなく既存テーブルへのカラム追加のため、本表の「作成スプリント」列(テーブル新規作成の割り当て)自体は変更しない。カラム追加はU003(予約作成、`POST /api/reservations`)・U004(予約詳細・編集、`GET`/`PUT /api/reservations/{reservation_id}`)の担当範囲で実施する。

## 5. コード量・難易度バランスの確認

| スプリント | 画面数 | API数 | 新規テーブル数 | 難易度 |
| --- | --- | --- | --- | --- |
| U001 | 1 | 3 | 6 | 中(基盤構築コストを含む) |
| U002 | 1 | 4 | 0 | 低 |
| U003 | 2 | 3 | 0 | 高(排他制御) |
| U004 | 2 | 4 | 0 | 中 |
| U005 | 1 | 4 | 0 | 中(横断作業込み) |

機械的な量(画面数+API数)はU002〜U005でおおむね均等(5前後)。U001はテーブル数が多いが定型的なDDLでありロジック的な複雑さは小さいため、見かけの量ほど重くない。U003は量としては他スプリントと同程度だが、技術的リスク(排他制御)を理由に「実装・デバッグに時間がかかりやすい要素を含むスプリントは重いものとして扱ってよい」という原則にもとづき、P007でのタスク数を他スプリントより手厚くする(6章参照は不要、P007側で対応)。
