# server — 会議室予約システム バックエンド

Python 3.11 + Starlette + Pydantic v2(明示検証)+ 標準 `sqlite3`。
**このプロセスがAPI(`/api/*`)と `client/` の静的ファイルの双方を同一オリジンで配信する**(`docs/ADR.md` ADR-010)。

* ソースツリーの目次: [`INDEX.md`](./INDEX.md)
* 技術選定の理由: `docs/ADR.md`(ADR-002 バックエンド / ADR-003 パスワードハッシュ / ADR-004 データストア / ADR-009 マイグレーション / ADR-010 実行トポロジ)
* 詳細設計: `docs/P003-backend-spec.md`。**API契約の単一の正は `docs/P002-frontend-spec.md` 第5章**(ADR-002)
* 配布・起動の正式手順: `docs/P302-deliver.md`

## 依存パッケージ

| パッケージ | 用途 |
| --- | --- |
| starlette | ASGIアプリケーション層(ルーティング・リクエスト/レスポンス・ミドルウェア) |
| pydantic | リクエストの検証(ハンドラ内で明示的に呼び出す。FastAPIの自動バインドは使わない) |
| uvicorn | ASGIサーバー(実行時) |

配布用のピン留めは [`requirements.txt`](./requirements.txt)、パッケージメタデータは [`pyproject.toml`](./pyproject.toml)。

## 起動

```bash
pip install -r requirements.txt
PYTHONPATH=src DB_PATH=./data/app.db python3 -m uvicorn meeting_room.main:app --host 0.0.0.0 --port 8000
```

* `client/` は `server/` と**同じ親ディレクトリに並んでいる必要がある**(`main.py` の `CLIENT_DIR` が `parents[3]/client` を参照する)。
* 起動時に、未適用のマイグレーションの差分適用(`migrations/*.sql`)と、有効な管理者が0人のときだけの初期管理者シードを実行する。**いずれも冪等**であり、同じDBファイルに対して何度起動してもよい(P006 V-O-01 / V-O-02、`docs/P009-acceptance-direction/A007-restart-resilience.md`)。

## 環境変数

| 変数 | 既定値 | 意味 |
| --- | --- | --- |
| `DB_PATH` | `./data/app.db` | SQLiteファイルのパス |
| `SESSION_IDLE_SECONDS` | `28800` | 無操作タイムアウト(秒) |
| `SESSION_ABSOLUTE_SECONDS` | `86400` | セッションの絶対有効期限(秒) |
| `INITIAL_ADMIN_ID` | `admin001` | 初期管理者の社員ID |
| `INITIAL_ADMIN_PASSWORD` | `Passw0rd!23` | 初期管理者のパスワード。**本番では必ず上書きする** |

読み込み箇所は `src/meeting_room/config.py`(モジュール読み込み時に1回だけ解決する)。

## テスト

```bash
python3 -m unittest discover -s tests -t .             # 単体 + 結合 + 受け入れ(240件)
python3 -m unittest discover -s tests/integration -t . # 結合のみ(13件)
python3 -m unittest discover -s tests/acceptance -t .  # 受け入れのみ(14件)
```

## 運用上の注意

* ログは標準出力に1リクエスト1行のJSONで出力する。転送・監視の設定はアプリの責務外(ADR-010)。
* TLS終端はプロセスの外側(リバースプロキシ)で行う前提。アプリはHTTPで待ち受け、`X-Forwarded-Proto` は参照しない。
* SQLiteはWALモード・ロックタイムアウト5秒。ワーカー数は1のまま運用する(ADR-010)。
