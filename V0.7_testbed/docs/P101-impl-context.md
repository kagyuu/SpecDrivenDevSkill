# 実装コンテキスト(Executor向け)

> 本書は `spec-driven-dev` Skill フェーズP101の成果物です。
> インプット: `server/INDEX.md`、`client/INDEX.md`、`docs/ArchitectureHandbook.md`、`docs/ADR.md`、`docs/P007-impl-direction.md`
> 本書はExecutor Stepに入るたび(スプリント着手のたび)に更新する。

## 0. 現在の着手対象

| 項目 | 値 |
| --- | --- |
| 対象スプリント | ※CR-001: **U003-T5**(`docs/P007-impl-direction/U003-reservation-core.md`)→ **U004-T6**(`docs/P007-impl-direction/U004-reservation-ui.md`)。CR-001(オンライン会議URL)で追加された2タスクのみが対象 |
| スプリント進捗 | U001 `[x]` / U002 `[x]` / U003 `[~]`(T1〜T4完了・**T5未着手**) / U004 `[~]`(T1〜T5完了・**T6未着手**) |
| 実行順 | U003-T5(バックエンド)→ U004-T6(フロントエンド)。列追加とAPI応答が先に無いと画面側のテストが書けないため、この順を守る |
| 更新日時 | 2026-08-05(CR-001 のP903実行にあたりP101を更新。U001〜U004の本体は実装完了済み) |

* U001・U002 の実装済み範囲と実際のファイル構成は `server/INDEX.md` / `client/INDEX.md`(P104で更新済み)を参照する。第1章の「実装コードは未着手」という記述は U001・U002 については解消済みである。
* U003 着手時の申し送り: `server/src/meeting_room/services/room_service.py` の `count_future_reservations()` は Sprint 2 時点の暫定実装(常に0)であり、`# TODO(U003-T2)` のとおり本実装へ差し替えること(結合テストT014が対象)。
* 実装中に判明した仕様の不足・食い違い(クライアント単体テストの実行コマンド、409 `DUPLICATE_KEY` の表示文言、不足しているエラー文言、未知の `scope` の扱い)は `docs/P007-impl-direction.md` 5章「未解決事項」#6〜#9 に記載済み。
* ※CR-001 の実装コンテキスト(今回の作業で必ず守る点):
  * 追加する列は `reservations.meeting_url TEXT NOT NULL DEFAULT ''`。**`NULL` を使わない**(ADR-011)。API応答の `meeting_url` は常に文字列で、未登録は `""`。
  * マイグレーションは**新規ファイル `server/migrations/004-meeting-url.sql` のみ**に書く。`001`〜`003` を編集しない(ADR-009)。ファイルの中身は `ALTER TABLE` 1文。
  * 検証は「500文字以内」→「`http://` または `https://` で始まる」の順(P002 3.3)。空欄はエラーにしない。URLパーサを使わない(ADR-011)。
  * **S02(カレンダー)は変更しない。** `client/src/views/s02-calendar.js` / `client/src/lib/grid.js` に手を入れないこと(CR-001が明示的に対象外)。
  * S04の閲覧モードのリンクは `el()` ヘルパで `a` 要素を組み立てる。`innerHTML` による文字列連結でHTMLを作らない。
  * 既存の単体テスト(サーバー240件 / クライアント126件)を1件も壊さないこと。既存テストの期待値を書き換えて通すことは禁止(仕様変更でレスポンスにキーが増える箇所は、増えたことを確認する形でテストを追加する)。

## 1. ソースツリーの現状(`INDEX.md` の要約)

* ソースツリーは `server/`(バックエンド)と `client/`(フロントエンド)の2つ。※CR-001の時点では **U001〜U004 の実装が完了済み**であり、以下の「実装コードは未着手」以降の記述は初回実行時の状態を残したものである。現状の構成は `server/INDEX.md` / `client/INDEX.md`(P104で更新済み)を参照すること。
* `server/`: `pyproject.toml`(依存なし)、`.python-version`(3.11)、`src/meeting_room/__init__.py`(雛形)、`migrations/`(空)、`tests/`(空)。
* `client/`: `package.json`(`"type": "module"`、依存なし)、`src/lib/`・`src/views/`(空)、`tests/`(空)。
* 実装予定のファイル配置は `server/INDEX.md` / `client/INDEX.md` の「実装予定の構成(実装前)」に列挙済み。**新しいファイルを勝手な場所に作らず、この配置に従う。**

## 2. 遵守すべき技術的決定(`docs/ADR.md` の一覧)

| ADR | 決定 | 実装上の要点 |
| --- | --- | --- |
| ADR-001 | フロントエンドはビルドツールなしの素のHTML/CSS + ESモジュール | React/TS/Viteを使わない。`client/index.html` + ハッシュルーティング。テストは `node --test` |
| ADR-002 | バックエンドは Starlette + Pydantic v2(明示検証)、テストは `unittest` | FastAPIの自動バインドは使えない。ハンドラ内でPydanticモデルを明示的に呼ぶ。OpenAPIは生成しない(API契約は P002 5章が正) |
| ADR-003 | パスワードハッシュは `hashlib.scrypt` | `scrypt$<n>$<r>$<p>$<b64(salt)>$<b64(dk)>` の1カラム文字列。`n=2**14, r=8, p=1, dklen=32`、salt 16バイト。検証は `hmac.compare_digest` |
| ADR-004 | SQLite + 標準 `sqlite3`(ORMなし) | `timeout=5.0`、`isolation_level=None`、接続直後に `PRAGMA foreign_keys = ON`、起動時に `PRAGMA journal_mode = WAL`。SQLは `repositories/` に直書き |
| ADR-005 | 認証はセッションCookie `sid`(JWTを使わない) | `HttpOnly; SameSite=Lax; Secure; Path=/`。無操作8時間(スライディング)+ 絶対24時間 |
| ADR-006 | セッションはSQLiteの `sessions` テーブルに永続化 | プロセス内メモリに持たない。認証のたびに `last_accessed_at` 更新 |
| ADR-007 | 重複判定は半開区間の交差 + `BEGIN IMMEDIATE` | `A.start < B.end AND B.start < A.end`。境界一致は重複でない。検査と更新を同一トランザクションに入れる |
| ADR-008 | 会議室・ユーザーは論理削除(`is_active`)、予約は物理削除 | 会議室名は `uq_rooms_name_active`(`WHERE is_active = 1` の部分ユニークインデックス) |
| ADR-009 | 差分適用型マイグレーション + `schema_migrations` | ファイル名昇順、未適用のみ適用。1ファイル1トランザクション。**`executescript()` を使わない**。適用済みファイルは編集しない |
| ADR-010 | 単一プロセスでAPIと静的ファイルを配信 | CORS設定なし。TLS終端・ログ集約はプロセス外。ログは標準出力に1行1JSON |
| ADR-011 ※CR-001 | 予約の任意テキスト項目は `NOT NULL DEFAULT ''`、URL検証はスキーム前方一致のみ | `meeting_url` に `NULL` を使わない。`http://` / `https://` の前方一致のみ検証(URLパーサ・ホワイトリストを使わない)。S04でのみリンク表示、S02には表示しない |

* **外部パッケージを新たに追加しない**(レジストリに到達できない)。標準ライブラリ + 既に利用可能な Starlette / Pydantic v2 のみを使う。

## 3. 実装・テストの実行コマンド

| 対象 | コマンド |
| --- | --- |
| バックエンド単体テスト | `cd server && python3 -m unittest discover -s tests -t .` |
| フロントエンド単体テスト | `cd client && node --test tests` |
| バックエンド結合テスト(P103) | `cd server && python3 -m unittest tests.integration.test_t0NN_xxx -v` |
| フロントエンド結合テスト(P103) | `cd client && node --test tests/integration/test_t0NN_xxx.js` |

* **P008の `T0NN-*.md` が指定するテストモジュール名・ファイル名に厳密に一致させること**(P103がその実行コマンドをそのまま実行するため)。結合テストの配置は `server/tests/integration/` と `client/tests/integration/` とする(T001・T003の★FIXME★をこの値で確定する)。

## 4. 迷ったときに参照する詳細仕様の場所

| 知りたいこと | 参照先 |
| --- | --- |
| 画面の入力項目・バリデーション・エラー文言 | `docs/P002-frontend-spec.md` 3章(S01=3.1 / S02=3.2 / S03=3.3 / S04=3.4 / S05=3.5 / S06=3.6 / S07=3.7) |
| ルーティング表・認証ガード・共通エラー表示 | `docs/P002-frontend-spec.md` 2.2 / 2.3 / 2.4 |
| API契約(パス・ステータス・レスポンス形式)**単一の正** | `docs/P002-frontend-spec.md` 5章(5.2 エラーコード / 5.4 認証 / 5.5 会議室 / 5.6 ユーザー / 5.7 予約) |
| テーブル定義 | `docs/P002-frontend-spec.md` 6.2(4テーブル)、`docs/P003-backend-spec.md` 3.2・3.3(`sessions` / `schema_migrations`)、3.4(インデックス) |
| 層構成・共通処理(検証・認証・エラー・ログ・トランザクション) | `docs/P003-backend-spec.md` 2.1 / 4.1〜4.5 |
| マイグレーション方式と冪等性 | `docs/P003-backend-spec.md` 3.5、ADR-009 |
| 重複チェックと排他制御(中核) | `docs/P003-backend-spec.md` 5章、ADR-007 |
| エンドポイントごとの内部処理手順 | `docs/P003-backend-spec.md` 6.1〜6.4 |
| 静的ファイル配信・MIME型 | `docs/P003-backend-spec.md` 7章 |
| 基準データセット・モック方針 | `docs/P006-test-plan.md` 5章 / 6章 |

## 5. Executorが守る禁止事項(P007共通指示の再掲)

* `docs/P002-frontend-spec.md` / `docs/P003-backend-spec.md` にない画面・API・DB項目・業務ルールを追加しない。
* 対象スプリントの範囲外のファイルを編集しない。
* 矛盾・不足に気づいたら実装を進めず `docs/P007-impl-direction.md` の「5. 未解決事項」に追記する。
* 単体テストが3回自己修正しても合格しない場合は処理を停止して人間に報告する(Executor Stepの停止条件)。
