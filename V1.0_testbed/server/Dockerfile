# server/Dockerfile — バックエンド(FastAPI + uvicorn)。ADR-002, ADR-003参照。
# docs/P302-deliver.md 作成時点ではDocker CLI自体がビルド環境に存在せず、実際のビルド・起動確認は
# できていない(docs/P302-deliver.md §9「最終確認結果」参照)。

FROM python:3.13-slim AS base

WORKDIR /app

# uvをインストール(パッケージマネージャ、docs/P007-impl-direction.md「コード格納先」参照)
RUN pip install --no-cache-dir uv==0.12.3

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app
COPY migrations ./migrations

# データベースファイルの永続化先(docker-compose.yml でボリュームをマウントする想定)
RUN mkdir -p /app/data
ENV DATABASE_PATH=/app/data/app.db
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/openapi.json', timeout=2)" || exit 1

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
