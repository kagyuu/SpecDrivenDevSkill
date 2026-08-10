"""Unit test for U005-T5 (docs/P007-impl-direction/U005-user-management-and-hardening.md).

Confirms that an unhandled exception raised inside a request handler
results in a 500 response in the common error envelope, AND a structured
JSON Lines log line with event="unhandled_exception" on stdout
(docs/P003-backend-spec.md 6章). Triggered by deliberately breaking a
Repository call via monkeypatch, per this task's own 実装内容
("意図的に例外を発生させるテストで確認する").
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories import room_repository


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("COOKIE_SECURE", "false")
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_unhandled_exception_returns_500_and_logs_structured_event(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    login_response = client.post(
        "/api/auth/login", json={"employee_id": "admin", "password": "ChangeMe123!"}
    )
    assert login_response.status_code == 200

    def _boom(*_args: object, **_kwargs: object):
        raise RuntimeError("boom - intentional failure injected by this test")

    monkeypatch.setattr(room_repository, "find_all", _boom)

    response = client.get("/api/rooms")

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"

    captured = capsys.readouterr()
    log_lines = [line for line in captured.out.splitlines() if line.strip()]
    assert log_lines, "expected at least one structured log line on stdout"
    record = json.loads(log_lines[-1])
    assert record["level"] == "ERROR"
    assert record["event"] == "unhandled_exception"
    assert "timestamp" in record
    assert record["path"] == "/api/rooms"
