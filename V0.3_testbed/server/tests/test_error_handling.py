import unittest

from starlette.testclient import TestClient

from app.main import create_app


class TestErrorHandling(unittest.TestCase):
    def setUp(self):
        self.app = create_app(":memory:")
        self.client = TestClient(self.app)

    def test_not_found_path_returns_404_common_format(self):
        res = self.client.get("/api/does-not-exist")
        self.assertEqual(res.status_code, 404)
        self.assertIn("error", res.json())

    def test_validation_error_returns_400_common_format(self):
        self.client.post("/api/auth/login", json={"employee_id": "admin", "password": "admin12345"})
        res = self.client.post("/api/reservations", json={"room_id": 1})
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.json())

    def test_health_returns_200_with_version(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertIn("version", res.json())


if __name__ == "__main__":
    unittest.main()
