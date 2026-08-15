# 会議室予約システム

社内の会議室予約を一元管理するWebアプリケーション。React + TypeScript + Vite(フロントエンド)と Python + FastAPI + SQLite(バックエンド)で構成される。詳細な要件は `docs/P001-requirement.md`、技術スタックの選定理由は `docs/ADR.md` を参照。

このリポジトリは `spec-driven-dev` Skillにより、要件定義から設計・実装・テスト・修正・納品準備までを一気通貫で作成した(`./INDEX.md` が全体の目次)。

## バージョン

現在のバージョン: `1.0.0`(`VERSION` ファイル参照)。ビルド履歴は `BUILD_HISTORY.md` を参照。

## クイックスタート(Docker Compose)

```
docker compose up --build
```

起動後、`http://localhost:8080` にアクセスする(初回起動時にバックエンドがマイグレーションを自動実行する)。

**注意**: 本ビルド環境ではDocker CLI自体が利用できず、この手順は未検証である。詳細・既知の制約(TLS未終端によりログインCookieが保存されない等)は `docs/P302-deliver.md` を参照。

## 開発環境での起動

```
# バックエンド
cd server
uv sync
uv run uvicorn app.main:app --reload --port 8000

# フロントエンド(別ターミナル)
cd client
npm install
npm run dev
```

`http://localhost:5173` にアクセスする(Viteの開発サーバーが `/api` をバックエンドへプロキシする、`client/vite.config.ts` 参照)。

## テスト

```
# バックエンド単体・結合・受け入れテスト
cd server && uv run python -m pytest tests/ -v

# フロントエンド単体テスト
cd client && npx vitest run

# フロントエンドE2E(結合・受け入れ結合)
cd client && npx playwright install --with-deps chromium   # 初回のみ
cd client && npx playwright test tests/integration/
cd client && npx playwright test tests/acceptance/
```

## ドキュメント

* 全体の目次: `./INDEX.md`
* 要件定義: `docs/P001-requirement.md`
* 納品物まとめ・リリース判定: `docs/P302-deliver.md`
