"""A008 — カレンダー表示の性能(V-N-01)。

docs/P009-acceptance-direction/A008-calendar-performance.md
手順3(S02の描画時間)は `client/tests/acceptance/test_a008_calendar_render.js` が計測し、
本テストはAPI側の計測と、N+1になっていないことの確認を行う。
"""

from __future__ import annotations

import json
import os
import statistics
import sqlite3
import tempfile
import time
import unittest
from datetime import datetime, timedelta

from meeting_room import db as db_module
from meeting_room import security
from meeting_room.repositories import rooms_repo, users_repo
from tests.acceptance.support import ServerProcess

ROOM_COUNT = 10
USER_COUNT = 10
WEEKDAYS = 5
PER_ROOM_PER_DAY = 4  # 10室 × 5日 × 4件 = 200件
PASSWORD = "Passw0rd!23"
SLOTS = [("09:00", "10:00"), ("11:00", "12:00"), ("13:00", "14:00"), ("15:00", "16:00")]
#: 計測結果を人間が読めるようにテスト記録へ転記するための出力先
MEASUREMENT_FILE = os.environ.get("A008_MEASUREMENT_FILE")


def _week_start(base: datetime) -> datetime:
    """基準日を含む週の月曜日。"""
    return base - timedelta(days=base.weekday())


class A008CalendarPerformanceTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = os.path.join(self._tmp.name, "app.db")
        self.log_path = os.path.join(self._tmp.name, "server.log")
        self.server = ServerProcess(self.db_path, log_path=self.log_path)
        self.server.start()
        self.addCleanup(self.server.stop)
        self._generate_data()
        self.client = self.server.client()
        self.assertEqual(self.client.login("user001", PASSWORD).status, 200)
        # 手順3(事前準備): ウォームアップ
        self.client.get("/api/rooms")
        self.client.get(
            f"/api/reservations?date_from={self.date_from}&date_to={self.date_to}"
        )

    def _generate_data(self):
        """会議室10室・ユーザー10名・1週間分の予約200件を投入する。"""
        # 予約日は「翌週の月曜〜金曜」にして過去日にならないようにする
        monday = _week_start(datetime.now()) + timedelta(days=7)
        self.dates = [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(WEEKDAYS)]
        self.date_from = self.dates[0]
        self.date_to = (monday + timedelta(days=6)).strftime("%Y-%m-%d")

        conn = db_module.connect(self.db_path)
        try:
            now = security.now_utc()
            hashed = security.hash_password(PASSWORD)
            for index in range(1, USER_COUNT + 1):
                user_id = f"user{index:03d}"
                if users_repo.find_by_id(conn, user_id) is None:
                    with db_module.transaction(conn):
                        users_repo.insert(
                            conn, user_id, f"利用者{index:02d}", hashed, "general", True, now
                        )
            room_ids = []
            for index in range(1, ROOM_COUNT + 1):
                with db_module.transaction(conn):
                    room_ids.append(
                        rooms_repo.insert(conn, f"会議室{index:02d}", 20, "", "", True, now)
                    )
            self.room_ids = room_ids
            count = 0
            with db_module.transaction(conn):
                for day_index, reserved_date in enumerate(self.dates):
                    for room_index, room_id in enumerate(room_ids):
                        for slot_index in range(PER_ROOM_PER_DAY):
                            start, end = SLOTS[slot_index]
                            owner = f"user{((count % USER_COUNT) + 1):03d}"
                            conn.execute(
                                "INSERT INTO reservations(room_id, user_id, reserved_date,"
                                " start_time, end_time, title, attendee_count, note,"
                                " created_at, updated_at)"
                                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (
                                    room_id,
                                    owner,
                                    reserved_date,
                                    start,
                                    end,
                                    f"会議{day_index}-{room_index}-{slot_index}",
                                    5,
                                    "",
                                    now,
                                    now,
                                ),
                            )
                            count += 1
            self.reservation_count = count
        finally:
            conn.close()

    def _measure(self, path, times=5):
        durations = []
        for _ in range(times):
            started = time.perf_counter()
            res = self.client.get(path)
            durations.append((time.perf_counter() - started) * 1000)
            self.assertEqual(res.status, 200, res.text)
        return durations, res

    def test_calendar_performance(self):
        self.assertEqual(self.reservation_count, 200, "生成した予約件数")

        # 手順1: GET /api/rooms を5回計測
        rooms_durations, rooms_res = self._measure("/api/rooms")
        self.assertEqual(len(rooms_res.json()["rooms"]), ROOM_COUNT)

        # 手順2: GET /api/reservations(1週間分)を5回計測 → 中央値1秒以内
        path = f"/api/reservations?date_from={self.date_from}&date_to={self.date_to}"
        list_durations, list_res = self._measure(path)
        self.assertEqual(len(list_res.json()["reservations"]), 200)
        list_median = statistics.median(list_durations)
        self.assertLess(
            list_median,
            1000.0,
            f"API-12 の中央値が1秒を超えた: {list_median:.1f}ms (全計測 {list_durations})",
        )

        # 手順4: 合計(rooms + reservations の中央値の和)が3秒以内
        # 画面描画時間はクライアント側テストで計測する(本テストではAPI合計を判定する)
        rooms_median = statistics.median(rooms_durations)
        total_median = rooms_median + list_median
        self.assertLess(
            total_median,
            3000.0,
            f"API合計の中央値が3秒を超えた: {total_median:.1f}ms",
        )

        # 手順5: サーバーログの duration_ms を確認する
        with open(self.log_path, "r", encoding="utf-8", errors="replace") as handle:
            records = [
                json.loads(line)
                for line in handle.read().splitlines()
                if line.strip().startswith("{")
            ]
        api12 = [r for r in records if r["path"] == "/api/reservations" and r["method"] == "GET"]
        self.assertTrue(api12, "API-12 のアクセスログがない")
        server_median = statistics.median(r["duration_ms"] for r in api12)
        self.assertLess(server_median, 1000.0, f"サーバー側 duration_ms 中央値: {server_median}")

        # 手順6: API-12 の1リクエストで予約取得SQLが1回だけ(N+1でない)
        sql_log: list[str] = []
        conn = db_module.connect(self.db_path)
        try:
            conn.set_trace_callback(sql_log.append)
            from meeting_room.services import reservation_service

            rows = reservation_service.list_by_period(conn, self.date_from, self.date_to, None)
        finally:
            conn.set_trace_callback(None)
            conn.close()
        self.assertEqual(len(rows), 200)
        selects = [s for s in sql_log if s.strip().upper().startswith("SELECT")]
        self.assertEqual(
            len(selects), 1, f"API-12 の予約取得SQLが1回でない: {len(selects)}回\n{selects}"
        )

        measurement = {
            "rooms_ms": [round(d, 1) for d in rooms_durations],
            "reservations_ms": [round(d, 1) for d in list_durations],
            "rooms_median_ms": round(rooms_median, 1),
            "reservations_median_ms": round(list_median, 1),
            "api_total_median_ms": round(total_median, 1),
            "server_duration_ms_median": server_median,
            "select_count_api12": len(selects),
            "rooms": ROOM_COUNT,
            "reservations": self.reservation_count,
            "cpu_count": os.cpu_count(),
        }
        print(f"[A008 計測] {json.dumps(measurement, ensure_ascii=False)}")
        if MEASUREMENT_FILE:
            with open(MEASUREMENT_FILE, "w", encoding="utf-8") as handle:
                json.dump(measurement, handle, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    unittest.main()
