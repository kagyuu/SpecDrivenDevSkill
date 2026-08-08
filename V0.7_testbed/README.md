# 会議室予約システム

社内向けの会議室予約システム。7画面(S01〜S07)と17本のREST API、SQLite単一ファイルのデータストアからなる。
**1つのプロセスがAPIとフロントエンドの静的ファイルの双方を同一オリジンで配信する**(`docs/ADR.md` ADR-010)。

* バージョン: [`VERSION`](./VERSION)(1.1.0)
* プロジェクト全体の目次: [`INDEX.md`](./INDEX.md)
* 納品物一覧・配布手順・リリース判定: [`docs/P302-deliver.md`](./docs/P302-deliver.md) ← **配布・運用前に必ず読む**

## 最短の起動手順(Docker Compose)

```bash
cp .env.example .env
# .env の INITIAL_ADMIN_PASSWORD を必ず変更する
docker compose build
docker compose up -d
docker compose ps          # app が healthy になるのを待つ
open http://localhost:8000/
```

> ⚠️ 上記のDocker Compose手順は**ビルド・起動の実機確認ができていない**(検証環境にDockerデーモンが無いため)。
> 詳細と根拠は `docs/P302-deliver.md` 9章・11章を参照する。

> ⚠️ セッションCookieには `Secure` 属性が付く(ADR-005 / ADR-010)。`http://localhost` はブラウザが例外的に
> 安全なオリジンとして扱うためログインできるが、**`localhost` 以外のホストに平文HTTPでアクセスするとログインできない**。
> 本番相当の環境では TLS終端リバースプロキシ(`docker compose --profile tls up -d`)を併用する。

## Docker を使わない起動(開発・検証用)

```bash
pip install -r server/requirements.txt
cd server
PYTHONPATH=src DB_PATH=./data/app.db python3 -m uvicorn meeting_room.main:app --host 0.0.0.0 --port 8000
```

## テスト

```bash
# バックエンド(単体 + 結合 + 受け入れ、240件)
cd server && python3 -m unittest discover -s tests -t .

# フロントエンド(単体126 / 結合41 / 受け入れ31)
cd client && npm test && npm run test:integration && npm run test:acceptance
```

## ディレクトリ

| パス | 内容 |
| --- | --- |
| `server/` | バックエンド。目次は [`server/INDEX.md`](./server/INDEX.md) |
| `client/` | フロントエンド。目次は [`client/INDEX.md`](./client/INDEX.md) |
| `docs/` | 要件定義から納品までの全ドキュメント。目次は [`INDEX.md`](./INDEX.md) |
| `deploy/` | TLS終端リバースプロキシの設定例 |
