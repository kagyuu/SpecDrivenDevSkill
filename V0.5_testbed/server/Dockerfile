# server/Dockerfile — 会議室予約システム バックエンド
#
# ★P302作成★ 本サンドボックスにはDockerデーモンが存在しない(`docker info` がソケット接続エラーになる)ため、
# 本Dockerfileは `docker build`/`docker compose up` で実際にビルド・起動を検証できていない。
# `server/pyproject.toml` の依存関係(starlette / uvicorn / pydantic>=2)をもとに、pypi.orgに到達できる
# 通常の実行環境での動作を想定して作成した(本サンドボックスではpypi.orgに接続できず `pip install` 自体が
# 失敗するため未検証、`docs/P101-impl-context.md` 参照)。実行環境でのビルド・起動確認は人間が行うこと。

FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir starlette uvicorn "pydantic>=2"

COPY app ./app

ENV DATABASE_PATH=/data/app.db
# 本番相当のデプロイでは SESSION_COOKIE_SECURE は既定値(true)のまま、TLS終端(リバースプロキシ等)の
# 後段で稼働させること。TLS終端を用意できない場合のみ明示的に false を指定する
# (docs/ADR.md ADR-004備考、docs/P302-deliver.md §10参照)。

EXPOSE 8000
VOLUME ["/data"]

CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
