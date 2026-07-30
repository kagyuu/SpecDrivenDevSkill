import time
import unittest

from tests._server_helper import RunningServer


class TestT005PerformanceCalendar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = RunningServer()
        _, _, cls.cookie = cls.server.request(
            "POST", "/api/auth/login", {"employee_id": "admin", "password": "admin12345"}
        )
        _, rooms, _ = cls.server.request("GET", "/api/rooms", cookie=cls.cookie)
        # 会議室3室 x 直近7日間に予約を計約21件作成する
        day_base = 20991001
        count = 0
        for day_offset in range(7):
            date = f"2099-10-{day_offset + 1:02d}"
            for room in rooms:
                hour = 9 + (count % 8)
                cls.server.request(
                    "POST",
                    "/api/reservations",
                    {
                        "room_id": room["id"],
                        "date": date,
                        "start_time": f"{hour:02d}:00",
                        "end_time": f"{hour + 1:02d}:00",
                        "subject": f"性能計測用予約{count}",
                        "notes": "",
                        "participant_ids": [],
                    },
                    cookie=cls.cookie,
                )
                count += 1

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_calendar_query_average_response_time_under_1s(self):
        durations = []
        for _ in range(10):
            start = time.monotonic()
            status, body, _ = self.server.request(
                "GET", "/api/reservations?date_from=2099-10-01&date_to=2099-10-07", cookie=self.cookie
            )
            durations.append(time.monotonic() - start)
            self.assertEqual(status, 200)

        avg = sum(durations) / len(durations)
        maximum = max(durations)
        print(f"[T005] avg={avg*1000:.2f}ms max={maximum*1000:.2f}ms n={len(durations)}")
        self.assertLess(avg, 1.0, f"平均応答時間が1秒を超えています: {avg}s")


if __name__ == "__main__":
    unittest.main()
