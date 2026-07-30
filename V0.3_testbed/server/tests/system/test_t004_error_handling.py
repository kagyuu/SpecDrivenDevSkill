import unittest

from tests._server_helper import RunningServer


class TestT004ErrorHandling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = RunningServer()
        _, _, cls.admin_cookie = cls.server.request(
            "POST", "/api/auth/login", {"employee_id": "admin", "password": "admin12345"}
        )
        _, rooms, _ = cls.server.request("GET", "/api/rooms", cookie=cls.admin_cookie)
        cls.room_id = rooms[0]["id"]

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_step1_nonexistent_path_404(self):
        status, body, _ = self.server.request("GET", "/api/does-not-exist", cookie=self.admin_cookie)
        self.assertEqual(status, 404)
        self.assertIn("error", body)

    def test_step2_malformed_json_returns_common_error_format(self):
        import http.client

        conn = http.client.HTTPConnection("127.0.0.1", self.server.port, timeout=5)
        conn.request(
            "POST",
            "/api/auth/login",
            body=b"{not valid json",
            headers={"Content-Type": "application/json"},
        )
        res = conn.getresponse()
        raw = res.read()
        conn.close()
        # 500になること自体は仕様範囲内(docs/03-backend-spec.md 5章)。共通形式が維持されるかを確認する。
        self.assertIn(b'"error"', raw)

    def test_step3_nonexistent_reservation_404(self):
        status, _, _ = self.server.request("GET", "/api/reservations/999999", cookie=self.admin_cookie)
        self.assertEqual(status, 404)

    def test_step4_missing_required_field_400(self):
        status, body, _ = self.server.request(
            "POST", "/api/reservations", {"room_id": self.room_id}, cookie=self.admin_cookie
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")

    def test_step5_nonexistent_participant_id_400_not_500(self):
        # V0.2でFAILしていたケース。今回のコードは修正を最初から含むため400が期待される。
        status, body, _ = self.server.request(
            "POST",
            "/api/reservations",
            {
                "room_id": self.room_id,
                "date": "2099-10-01",
                "start_time": "10:00",
                "end_time": "11:00",
                "subject": "T004参加者不正",
                "notes": "",
                "participant_ids": [999999],
            },
            cookie=self.admin_cookie,
        )
        self.assertEqual(status, 400, f"期待: 400, 実際: {status} body={body}")
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")

    def test_step6_invalid_room_capacity_400_not_500(self):
        # 確認観点2・3の実地検証のため意図的に仕込んだバグ(docs/07-test-direction/T004-error-handling.md 補足参照)。
        status, body, _ = self.server.request(
            "POST",
            "/api/rooms",
            {"name": "T004容量不正室", "capacity": 0, "equipment": None},
            cookie=self.admin_cookie,
        )
        self.assertEqual(status, 400, f"期待: 400, 実際: {status} body={body}")
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")


if __name__ == "__main__":
    unittest.main()
