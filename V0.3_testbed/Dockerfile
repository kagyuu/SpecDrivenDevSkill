FROM python:3.11-slim

WORKDIR /app
COPY server/ /app/server/
COPY client/ /app/client/

RUN pip install --no-cache-dir fastapi uvicorn pydantic starlette

WORKDIR /app/server
ENV APP_DB_PATH=/app/server/data/app.db
EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
