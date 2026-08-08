# 会議室予約システム — 単一イメージ(ADR-010: 1プロセスが API と静的ファイルの双方を同一オリジンで配信する)
#
# 重要: `server/src/meeting_room/main.py` の `CLIENT_DIR` は
#   Path(__file__).resolve().parents[3] / "client"
# であり、`server/` と `client/` が**同じ親ディレクトリに並んでいること**を前提にしている。
# したがって本イメージでは `/app/server` と `/app/client` の両方を同梱する。
# フロントエンドを別コンテナ・別オリジンに分けてはならない(理由は `docs/P302-deliver.md` 3章)。

FROM python:3.11-slim

# 依存パッケージを先に入れてレイヤキャッシュを効かせる
WORKDIR /app
COPY server/requirements.txt ./server/requirements.txt
RUN pip install --no-cache-dir -r ./server/requirements.txt

# アプリケーション本体(server と client を並べて配置する)
COPY server/ ./server/
COPY client/ ./client/
COPY VERSION ./VERSION

ENV PYTHONPATH=/app/server/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DB_PATH=/app/data/app.db

# SQLiteファイルの置き場(docker-compose.yml で名前付きボリュームをマウントする)
RUN mkdir -p /app/data

WORKDIR /app/server
EXPOSE 8000

# ヘルスチェック: `/` は認証不要で 200 を返す(P302 9章で実測確認済み)。
# slim イメージに curl は含まれないため Python 標準ライブラリで確認する。
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD python3 -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/', timeout=4).status==200 else 1)"

# --workers は 1 のまま(ADR-010「単一プロセス・単一SQLiteファイル」)。
# --proxy-headers は付けない(ADR-010「`X-Forwarded-Proto` は参照しない」)。
CMD ["python3", "-m", "uvicorn", "meeting_room.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
