# システム詳細設計書 — 会議室予約システム

> 本書は `spec-driven-dev` Skill フェーズ3の成果物です(V0.3ルールで再生成)。
> インプット: `docs/01-requirement.md`, `docs/02-frontend-spec.md`

## 1. 全体アーキテクチャ

* バックエンドは Python + FastAPI(Starlette/ASGI)。エントリポイントは `server/app/main.py`。
* レイヤ構成: `router`(APIハンドラ)→ `service`(業務ロジック)→ `repository`(DBアクセス、`sqlite3`直叩き)→ SQLite(`server/data/app.db`)。
* リクエストは `router` で入力バリデーション(Pydanticモデル)→ `service` で認可・業務ルール適用→ `repository` でSQL実行、という順で処理する。

## 2. 状態管理(セッション)

> 外部から見える契約(Cookie方式であること・Cookie名`session_id`・HttpOnly・無効時401)は `docs/02-frontend-spec.md` 2章「バックエンドAPI外部仕様」冒頭の共通事項で確定済み。本章ではその内部実現を確定する。

* **スコープ**: ユーザセッション単位。
* **実現方法**: SQLite に `sessions` テーブルを追加して永続化する(プロセス内メモリのみだと再起動でログアウトされ、300名規模の社内システムとしては再起動時の影響が大きいため)。
* `session_id` は `secrets.token_urlsafe(32)` で生成し、Cookie(`session_id`, `HttpOnly`, `SameSite=Lax`)としてブラウザへ送る。
* セッション有効期限は発行から8時間。`GET /api/me` など認証必須APIの呼び出し時に期限切れなら `401` を返し、該当セッション行を削除する。
* ログアウト (`POST /api/auth/logout`) 時は該当 `session_id` 行を削除する。

### sessions テーブル(ユーザインタフェースに現れないデータモデル追加)

| カラム | 型 | 制約 |
| --- | --- | --- |
| session_id | TEXT | PK |
| user_id | INTEGER | NOT NULL, FK → users.id |
| created_at | TEXT | NOT NULL (ISO8601) |
| expires_at | TEXT | NOT NULL (ISO8601) |

`docs/02-frontend-spec.md` のデータモデル(ER図)は `sessions` を含んでいないため、本フェーズで追加する。フロントエンドが直接参照するデータではない(Cookie経由でのみ利用)ため、`docs/02-frontend-spec.md` 自体の修正は不要と判断する(2章の対象は画面の入出力に現れるデータモデルであり、`sessions` は該当しない)。

## 3. 認証・認可の内部仕様

> パスワード認証の外部契約(`POST /api/auth/login` のリクエスト/レスポンス形式、401の条件)は `docs/02-frontend-spec.md` 2章「POST /api/auth/login」に定義済み。本章ではハッシュ方式など内部実現のみを扱う。

* パスワードは `hashlib.pbkdf2_hmac("sha256", password, salt, 100_000)` でハッシュ化し、`salt:hash` の形式で `users.password_hash` に保存する。
* `POST /api/auth/login`:
  1. `employee_id` で `users` を検索。存在しない、または `is_active=0` の場合は `401`。
  2. パスワードハッシュを照合。不一致なら `401`。
  3. `sessions` に新規行を作成し、Cookie を発行して `200` を返す。
* 認証必須エンドポイントは共通の `require_login` 依存関数で `session_id` Cookie を検証し、`request.state.user` にログインユーザーを設定する。
* 管理者専用エンドポイントは `require_admin` 依存関数で `request.state.user.role == "admin"` を確認し、`403` を返す。

## 4. 各APIの内部仕様

共通: 全レスポンスは `router` 層で Pydantic モデルにシリアライズする。DBアクセスは全て `repository` 層経由(SQLインジェクション対策としてプレースホルダを使用)。

### 認証系

* `POST /api/auth/login` / `POST /api/auth/logout` / `GET /api/me`: 3章のとおり。`sessions` テーブルを使用。

### 会議室系(`rooms` テーブル)

* `GET /api/rooms`: `is_active=1` の行のみ取得(`include_inactive=true` かつ管理者の場合は全件)。
* `POST /api/rooms` / `PUT /api/rooms/{id}`: `name` の重複チェックは `WHERE name = ? AND is_active = 1 AND id != ?` で行う。`capacity` は `docs/02-frontend-spec.md` 1章S06「収容人数: 必須。1以上の整数」の実現方法として、DBの `CHECK (capacity > 0)` 制約任せにせず、アプリケーション層(routerハンドラ)で `capacity < 1` の場合に明示的に `400 VALIDATION_ERROR` を返す(フェーズ8 F002での明確化。`POST`/`PUT`双方のハンドラで実施する)。
* `DELETE /api/rooms/{id}`: `UPDATE rooms SET is_active = 0 WHERE id = ?`(論理削除)。

### 予約系(`reservations` テーブル、重複チェックが中心)

* **重複判定ロジック**: 同一 `room_id` かつ同一 `date` の既存予約のうち、`NOT (end_time <= 対象.start_time OR start_time >= 対象.end_time)` を満たす行が1件でもあれば重複とみなし `409` を返す。更新時(`PUT`)は自分自身の `id` を判定対象から除外する。
* **排他制御**: SQLite の単一ファイル書き込みロックを利用する。予約の作成・更新は `BEGIN IMMEDIATE` トランザクションで「重複チェックSELECT」と「INSERT/UPDATE」を1トランザクション内に収め、SQLiteのライタロックにより同時リクエストでの二重予約を防止する(想定同時接続30程度の規模ではこの方式で十分と判断する)。
* `GET /api/reservations`: `date BETWEEN date_from AND date_to`、`room_id` 指定時は追加で絞り込み。`rooms`・`users` と JOIN して `room_name` / `created_by_name` を付与する。
* `GET /api/reservations/mine`: `created_by = ログインユーザーid`。`period=future` は `date >= 当日`、`period=past` は `date < 当日`。
* `GET /api/reservations/{id}`: 存在しなければ `404`。`reservation_participants` を JOIN して `participant_ids` を付与する。
* `POST /api/reservations`: `room_id` が存在し `is_active=1` でなければ `404`。バリデーション(時刻・文字数)は Pydantic モデルで実施。作成成功時、`created_by` はログインユーザー、`participant_ids` に本人が含まれていなければ自動追加する。`participant_ids` に指定された各IDは、有効な(`is_active=1`)`users` に実在することを事前に検証し、1件でも存在しない場合は `400 VALIDATION_ERROR` を返す(フェーズ8 F001での明確化: `docs/02-frontend-spec.md` 1章S03「参加者(社員): 有効なユーザーのみ選択可能」の実現方法として、DBの外部キー制約任せにせずアプリケーション層で明示的に検証する)。
* `PUT /api/reservations/{id}`: 認可(本人 or 管理者)確認後、`POST` と同様の重複・存在チェックを行う。
* `DELETE /api/reservations/{id}`: 認可確認後、`reservation_participants` を先に削除し、`reservations` 行を削除する(物理削除)。

### ユーザー系(`users` テーブル)

* `GET /api/users` / `POST /api/users` / `PUT /api/users/{id}` / `DELETE /api/users/{id}`: いずれも `require_admin`。`POST`/`PUT`のパスワードは3章の方式でハッシュ化して保存する。`employee_id` の一意性は `UNIQUE` 制約 + アプリ側事前チェック(重複時 `400`)の両方で担保する。

## 5. エラーハンドリング共通方針

* 未捕捉例外は `500` + `{"error": {"code": "INTERNAL_ERROR", "message": "予期しないエラーが発生しました"}}` を返し、詳細はサーバログにのみ出力する。
* Pydantic バリデーションエラーは `400` + `{"error": {"code": "VALIDATION_ERROR", "message": "..."}}` に変換する。

## 6. 未確定事項(次フェーズへの申し送り)

* 社内SSO(SAML/OIDC)連携は本バージョン対象外(`docs/01-requirement.md` のとおり)。
* 本設計は単一プロセス・単一SQLiteファイルを前提とする。将来の多拠点展開時のスケールアウトは別途検討(`docs/01-requirement.md` 非機能要件のとおり、現時点ではスコープ外)。
