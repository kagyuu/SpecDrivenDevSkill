"""結合テスト用: サブプロセスでuvicornサーバーを起動するヘルパー。"""
import http.client
import json
import os
import socket
import subprocess
import sys
import tempfile
import time


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class RunningServer:
    def __init__(self):
        self.port = find_free_port()
        self.db_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.db_dir, "test.db")
        env = os.environ.copy()
        env["APP_DB_PATH"] = self.db_path
        server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(self.port),
                "--log-level",
                "warning",
            ],
            cwd=server_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        self._wait_ready()

    def _wait_ready(self, timeout=15):
        deadline = time.time() + timeout
        last_err = None
        while time.time() < deadline:
            try:
                conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=1)
                conn.request("GET", "/health")
                res = conn.getresponse()
                if res.status == 200:
                    conn.close()
                    return
                conn.close()
            except Exception as e:
                last_err = e
            time.sleep(0.2)
        raise RuntimeError(f"server did not become ready: {last_err}")

    def request(self, method, path, body=None, cookie=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        headers = {}
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if cookie:
            headers["Cookie"] = cookie
        conn.request(method, path, body=data, headers=headers)
        res = conn.getresponse()
        raw = res.read()
        parsed = None
        if raw:
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = raw.decode("utf-8", errors="replace")
        set_cookie = res.getheader("Set-Cookie")
        session_cookie = None
        if set_cookie:
            session_cookie = set_cookie.split(";")[0]
        conn.close()
        return res.status, parsed, session_cookie

    def stop(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
