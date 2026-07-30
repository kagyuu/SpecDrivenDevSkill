import threading
import unittest

from tests._server_helper import RunningServer


class TestT003ConcurrentBooking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = RunningServer()
        _, _, cls.cookie = cls.server.request(
            "POST", "/api/auth/login", {"employee_id": "u001", "password": "password1"}
        )
        _, rooms, _ = cls.server.request("GET", "/api/rooms", cookie=cls.cookie)
        cls.room_id = rooms[0]["id"]

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_only_one_of_two_simultaneous_requests_succeeds(self):
        results = [None, None]
        payload = {
            "room_id": self.room_id,
            "date": "2099-09-01",
            "start_time": "15:00",
            "end_time": "16:00",
            "subject": "同時実行テスト",
            "notes": "",
            "participant_ids": [],
        }

        def worker(idx):
            status, _, _ = self.server.request("POST", "/api/reservations", payload, cookie=self.cookie)
            results[idx] = status

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(sorted(results), [201, 409], f"期待: [201, 409]、実際: {results}")


if __name__ == "__main__":
    unittest.main()
