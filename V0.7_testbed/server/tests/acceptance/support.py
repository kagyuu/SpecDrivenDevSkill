"""受け入れ結合テスト(P009)共通の実行基盤。

`docs/P009-acceptance-direction.md` 3章は「システムレベル/受入レベルの確認」を求めており、
A007(再起動耐性)・A009(同時接続)・A012(運用者視点)は **実プロセスの停止・再起動・
同時接続** を確認対象に含む。そのため結合テスト(P008)で使った Starlette の `TestClient`
(同一プロセス内呼び出し)では要件を満たせない。本モジュールは

* `uvicorn` を **別プロセス** として起動・停止する `ServerProcess`
* 標準ライブラリ `urllib.request` を使う **実HTTPクライアント** `HttpClient`

を提供する(`docs/P006-test-plan.md` 1.1 の「サーバープロセスを起動して urllib.request で叩く」方式)。

Cookie は `Secure` 付きで発行されるため `http.cookiejar` では平文HTTPに送出されない。
ブラウザ相当の保持を模すため、Cookie は自前の辞書で保持する
(`client/tests/helpers/server.js` の `makeFetch` と同じ方針)。
"""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = SERVER_DIR / "src"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class Response:
    """`urllib` の応答を、テストが扱いやすい形にまとめたもの。"""

    def __init__(self, status: int, headers, body: bytes):
        self.status = status
        self.headers = headers
        self.body = body

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    def json(self):
        return json.loads(self.text) if self.body else None

    @property
    def set_cookies(self) -> list[str]:
        return self.headers.get_all("Set-Cookie") or []

    def error_code(self):
        try:
            return self.json()["error"]["code"]
        except Exception:  # noqa: BLE001 — エラー本文でない場合は None
            return None


class HttpClient:
    """1ブラウザ相当のセッション(Cookieを1つ保持する実HTTPクライアント)。"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.cookie = ""

    def clear_cookies(self) -> None:
        self.cookie = ""

    def request(self, method: str, path: str, body=None, *, headers=None, cookie=None) -> Response:
        data = None
        request_headers = dict(headers or {})
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")
        jar = self.cookie if cookie is None else cookie
        if jar:
            request_headers["Cookie"] = jar
        req = urllib.request.Request(
            f"{self.base_url}{path}", data=data, method=method, headers=request_headers
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as raw:
                response = Response(raw.status, raw.headers, raw.read())
        except urllib.error.HTTPError as exc:  # 4xx/5xx も応答として扱う
            response = Response(exc.code, exc.headers, exc.read())
        if cookie is None:
            self._store_cookies(response)
        return response

    def _store_cookies(self, response: Response) -> None:
        for raw in response.set_cookies:
            pair = raw.split(";")[0]
            name, _, value = pair.partition("=")
            self.cookie = "" if value == "" else f"{name}={value}"

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, body=None, **kw):
        return self.request("POST", path, body, **kw)

    def put(self, path, body=None, **kw):
        return self.request("PUT", path, body, **kw)

    def delete(self, path, **kw):
        return self.request("DELETE", path, **kw)

    def login(self, user_id: str, password: str = "Passw0rd!23") -> Response:
        self.clear_cookies()
        return self.post("/api/auth/login", {"user_id": user_id, "password": password})


class ServerProcess:
    """`uvicorn` を別プロセスとして起動する。停止・再起動を明示的に扱える。"""

    def __init__(self, db_path: str, env_extra: dict | None = None, log_path: str | None = None):
        self.db_path = db_path
        self.env_extra = dict(env_extra or {})
        self.log_path = log_path
        self.port: int | None = None
        self.proc: subprocess.Popen | None = None
        self._log_file = None

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def env(self) -> dict:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SRC_DIR)
        env["PYTHONUNBUFFERED"] = "1"
        env["DB_PATH"] = self.db_path
        env.setdefault("INITIAL_ADMIN_ID", "admin001")
        env.setdefault("INITIAL_ADMIN_PASSWORD", "Passw0rd!23")
        env.update(self.env_extra)
        return env

    def start(self, wait: bool = True, timeout: float = 30.0) -> "ServerProcess":
        self.port = free_port()
        if self.log_path:
            self._log_file = open(self.log_path, "ab")
            stdout = stderr = self._log_file
        else:
            stdout = stderr = subprocess.PIPE
        self.proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "meeting_room.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(self.port),
                "--log-level",
                "warning",
            ],
            cwd=str(SERVER_DIR),
            env=self.env(),
            stdout=stdout,
            stderr=stderr,
        )
        if wait:
            self.wait_ready(timeout)
        return self

    def wait_ready(self, timeout: float = 30.0) -> None:
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(f"サーバーが起動直後に終了した (rc={self.proc.returncode})")
            try:
                with urllib.request.urlopen(f"{self.base_url}/", timeout=2) as raw:
                    if raw.status == 200:
                        return
            except Exception as exc:  # noqa: BLE001 — 起動待ちのリトライ
                last = exc
            time.sleep(0.15)
        raise RuntimeError(f"サーバーの起動待ちがタイムアウトした: {last}")

    def stop(self, sig=signal.SIGTERM, timeout: float = 15.0) -> int | None:
        if self.proc is None:
            return None
        if self.proc.poll() is None:
            self.proc.send_signal(sig)
            try:
                self.proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=timeout)
        rc = self.proc.returncode
        for stream in (self.proc.stdout, self.proc.stderr):
            if stream is not None and not stream.closed:
                stream.close()
        if self._log_file:
            self._log_file.flush()
            self._log_file.close()
            self._log_file = None
        self.proc = None
        return rc

    def client(self) -> HttpClient:
        return HttpClient(self.base_url)
