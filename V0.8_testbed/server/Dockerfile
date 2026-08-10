# P302 (docs/P302-deliver.md 6章): distribution asset for the backend
# service of the "サービス提供型システム" (docker-compose) topology.
#
# NOTE (docs/P302-deliver.md 実行前チェック item 6 / 9章): this Dockerfile was
# authored and reviewed for correctness, but its build/run has NOT been
# verified in this sandbox because the Docker CLI/daemon is not installed
# here (`docker --version` -> "command not found"). Do not treat it as
# build-verified until it has actually been built and started somewhere
# Docker is available.

FROM python:3.11-slim AS runtime

WORKDIR /app

# Install dependencies first (better layer caching): copy only the metadata
# files needed to resolve deps before copying the rest of the source tree.
COPY pyproject.toml ./
COPY app ./app
COPY migrations ./migrations

# Editable install so importlib.metadata.version(...) in app/main.py's
# GET /version (P302 5章) can resolve the package version at runtime, same
# as in the local dev venv (server/.venv) this app was developed against.
RUN pip install --no-cache-dir -e .

# DATABASE_PATH (app/db/connection.py) defaults to "data/app.db", relative
# to the working directory - /app/data here. Mounted as a named volume in
# docker-compose.yml so reservation data survives container recreation.
ENV DATABASE_PATH=/app/data/app.db
# Must be "false" unless a TLS-terminating reverse proxy sits in front of
# this whole stack (see docs/P302-deliver.md 10章: this compose setup does
# not include TLS termination, so Secure cookies would silently break
# login over plain HTTP - app/routers/auth.py's cookie_secure() helper).
ENV COOKIE_SECURE=false

EXPOSE 8000

# The FastAPI lifespan hook (app/main.py) already applies pending
# migrations on startup (server/app/db/migration.py), idempotently
# (verified by server/tests/acceptance/test_restart_resilience.py) - no
# separate init step is required before `uvicorn` starts.
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
