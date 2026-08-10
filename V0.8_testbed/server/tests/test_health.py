"""Unit test for U001-T1 (docs/P007-impl-direction/U001-foundation-and-auth.md).

Target: GET /health
Positive case: returns 200 and {"status": "ok"}.
There is no negative case for this endpoint (see U001-T1 Unit Test spec).
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
