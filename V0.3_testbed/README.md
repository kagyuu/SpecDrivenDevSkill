# 会議室予約システム

`spec-driven-dev` Skill(V0.3)フェーズ1〜9で実装した会議室予約システム。仕様は `docs/` 配下を参照。

## ローカル直接起動

```bash
cd server
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

ブラウザで `http://localhost:8000/` を開く。初期ユーザー: `admin`/`admin12345`(管理者)、`u001`/`password1`・`u002`/`password2`(一般)。

バージョン確認: `curl http://localhost:8000/health`

## テスト実行

```bash
cd server
python3 -m unittest discover -s tests -p "test_*.py"
```

## Docker Compose 起動(手順のみ、本検証環境では未実地検証)

```bash
cp .env.example .env
docker compose build
docker compose up -d
curl http://localhost:8000/health
```

詳細は `docs/09-deliver.md` を参照。
