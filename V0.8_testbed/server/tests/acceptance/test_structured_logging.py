"""P201 acceptance test A008 (docs/P009-acceptance-direction/A008-structured-logging.md).

Uses a real subprocess (stdout captured) rather than TestClient, since the
whole point is confirming JSON Lines actually reach real stdout the way an
operator's log collector would see it - not just that a Python object gets
constructed correctly in-process.
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path

import httpx

SERVER_DIR = Path(__file__).resolve().parent.parent.parent
PYTHON_EXE = SERVER_DIR / ".venv" / "Scripts" / "python.exe"
PORT = 8733
BASE_URL = f"http://127.0.0.1:{PORT}"


def test_a_failed_login_produces_a_structured_warning_log_line(tmp_path: Path):
    db_path = tmp_path / "acceptance_logging.db"
    env = {**os.environ, "DATABASE_PATH": str(db_path), "COOKIE_SECURE": "false"}
    process = subprocess.Popen(
        [str(PYTHON_EXE), "-m", "uvicorn", "app.main:app", "--port", str(PORT)],
        cwd=str(SERVER_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                if httpx.get(f"{BASE_URL}/health", timeout=1).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.2)
        else:
            raise RuntimeError("server did not become ready")

        # 手順1
        login_response = httpx.post(
            f"{BASE_URL}/api/auth/login",
            json={"employee_id": "admin", "password": "wrong-password"},
            timeout=10,
        )
        assert login_response.status_code == 401
    finally:
        process.send_signal(signal.SIGTERM)
        try:
            stdout, _ = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, _ = process.communicate(timeout=5)

    # 手順2・3
    json_lines = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            json_lines.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    login_failed_events = [record for record in json_lines if record.get("event") == "login_failed"]

    assert login_failed_events, (
        "expected at least one JSON Lines log record with event='login_failed'; "
        f"captured stdout:\n{stdout}"
    )
    record = login_failed_events[0]
    assert record.get("level") == "WARNING"
    assert "timestamp" in record
    assert re.match(r"^\d{4}-\d{2}-\d{2}T", str(record.get("timestamp", "")))
