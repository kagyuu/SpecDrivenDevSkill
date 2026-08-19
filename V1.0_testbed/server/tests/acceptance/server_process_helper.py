"""A005・A009向け: 実サーバー(uvicorn)をサブプロセスとして起動・停止するヘルパー。

TestClient(in-process, 単一スレッド同期実行)ではなく、実際に `uvicorn` を別プロセスとして
起動することで、起動時マイグレーション・複数ワーカースレッドなど「本当のサーバー」でしか
再現しない挙動を確認できるようにする。
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SERVER_ROOT = Path(__file__).resolve().parents[2]


def _venv_python() -> str:
    if os.name == "nt":
        candidate = SERVER_ROOT / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = SERVER_ROOT / ".venv" / "bin" / "python"
    return str(candidate) if candidate.exists() else sys.executable


def start_server(database_path: Path, port: int, log_path: Path):
    env = os.environ.copy()
    env["DATABASE_PATH"] = str(database_path)

    log_file = open(log_path, "a", encoding="utf-8")
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    process = subprocess.Popen(
        [_venv_python(), "-m", "uvicorn", "app.main:app", "--port", str(port)],
        cwd=str(SERVER_ROOT),
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        creationflags=creationflags,
    )

    base_url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 20
    last_error: Exception | None = None
    while time.time() < deadline:
        if process.poll() is not None:
            log_file.close()
            raise RuntimeError(
                f"サーバープロセスが起動直後に終了した(終了コード {process.returncode})。ログ: {log_path}"
            )
        try:
            urllib.request.urlopen(f"{base_url}/openapi.json", timeout=1)
            return process, log_file, base_url
        except (urllib.error.URLError, ConnectionError) as exc:
            last_error = exc
            time.sleep(0.3)

    process.terminate()
    log_file.close()
    raise TimeoutError(f"サーバーが起動しなかった: {last_error}")


def stop_server(process: subprocess.Popen, log_file) -> None:
    if os.name == "nt":
        # Windows にはPOSIX SIGTERMの直接的な等価物が無いため、terminate() (TerminateProcess) を使う。
        # uvicornはこれをプロセス強制終了として扱うが、通常のCtrl+C相当のGraceful Shutdownは
        # SIGINTで行われるため、まずSIGINTを試みる。
        try:
            process.send_signal(signal.CTRL_BREAK_EVENT)  # type: ignore[attr-defined]
        except Exception:
            process.terminate()
    else:
        process.send_signal(signal.SIGTERM)

    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
    finally:
        log_file.close()
