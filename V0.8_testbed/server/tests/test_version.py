"""Test for the GET /version endpoint added during P302 (docs/P302-deliver.md
5章: "実行モジュールからもバージョンを確認できるようにする").

This is a minor, additive endpoint (not part of docs/P003-backend-spec.md's
original API list) permitted by SKILL-P302-deliver.md's explicit allowance
for "最終仕上げとして軽微な追加". It does not change /health's existing
{"status": "ok"} contract (see test_health.py), so that test is untouched.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_version_returns_a_version_string():
    response = client.get("/version")
    assert response.status_code == 200
    body = response.json()
    assert "version" in body
    assert isinstance(body["version"], str)
    assert body["version"] != ""
