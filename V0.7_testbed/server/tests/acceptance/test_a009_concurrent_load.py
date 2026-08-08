"""A009 — 同時接続の負荷(V-N-02。同時30接続相当)。

docs/P009-acceptance-direction/A009-concurrent-load.md
"""

from __future__ import annotations

import json
import os
import statistics
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta

from meeting_room import db as db_module
from meeting_room import security
from meeting_room.repositories import rooms_repo, users_repo
from tests.acceptance.support import ServerProcess

ROOM_COUNT = 10
USER_COUNT = 10
CONCURRENCY = 30
READS_PER_THREAD = 3
PASSWORD = "Passw0rd!23"
PRELOAD_SLOTS = [("09:00", "10:00"), ("10:00", "11:00")]
WRITE_SLOTS = [("14:00", "15:00"), ("15:00", "16:00"), ("16:00", "17:00")]


class A009ConcurrentLoadTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = os.path.join(self._tmp.name, "app.db")
        self.log_path = os.path.join(self._tmp.name, "server.log")
        self.server = ServerProcess(self.db_path, log_path=self.log_path)
        self.server.start()
        self.addCleanup(self.server.stop)
        self._generate_data()
        # 事前準備2: 10名分のセッションCookieを取得しておく
        self.clients = []
        for index in range(1, USER_COUNT + 1):
            client = self.server.client()
            res = client.login(f"user{index:03d}", PASSWORD)
            self.assertEqual(res.status, 200, res.text)
            self.clients.append(client)

    def _generate_data(self):
        monday = datetime.now() - timedelta(days=datetime.now().weekday()) + timedelta(days=7)
        self.dates = [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]
        self.date_from = self.dates[0]
        self.date_to = (monday + timedelta(days=6)).strftime("%Y-%m-%d")
        # 更新系は「さらに翌週の月曜」に対して行う(既存予約と重ならない)
        self.write_date = (monday + timedelta(days=7)).strftime("%Y-%m-%d")

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
            self.room_ids = []
            for index in range(1, ROOM_COUNT + 1):
                with db_module.transaction(conn):
                    self.room_ids.append(
                        rooms_repo.insert(conn, f"会議室{index:02d}", 20, "", "", True, now)
                    )
            count = 0
            with db_module.transaction(conn):
                for reserved_date in self.dates:
                    for room_id in self.room_ids:
                        for start, end in PRELOAD_SLOTS:
                            if count >= 100:
                                break
                            conn.execute(
                                "INSERT INTO reservations(room_id, user_id, reserved_date,"
                                " start_time, end_time, title, attendee_count, note,"
                                " created_at, updated_at)"
                                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (
                                    room_id,
                                    f"user{((count % USER_COUNT) + 1):03d}",
                                    reserved_date,
                                    start,
                                    end,
                                    f"既存{count}",
                                    None,
                                    "",
                                    now,
                                    now,
                                ),
                            )
                            count += 1
            self.preloaded = count
        finally:
            conn.close()

    def _reservation_count(self) -> int:
        conn = db_module.connect(self.db_path)
        try:
            return conn.execute("SELECT COUNT(*) AS c FROM reservations").fetchone()["c"]
        finally:
            conn.close()

    def _run_concurrently(self, worker, count):
        barrier = threading.Barrier(count)
        results = [None] * count
        threads = []
        for index in range(count):
            thread = threading.Thread(target=worker, args=(index, barrier, results))
            threads.append(thread)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=120)
        return results

    def test_concurrent_load(self):
        self.assertEqual(self.preloaded, 100, "投入した既存予約")
        path = f"/api/reservations?date_from={self.date_from}&date_to={self.date_to}"

        # 手順1・2: 30スレッド × 3回 = 90リクエストの参照系
        def read_worker(index, barrier, results):
            client = self.server.client()
            client.cookie = self.clients[index % USER_COUNT].cookie
            statuses = []
            durations = []
            barrier.wait()
            for _ in range(READS_PER_THREAD):
                started = time.perf_counter()
                res = client.get(path)
                durations.append((time.perf_counter() - started) * 1000)
                statuses.append(res.status)
            results[index] = (statuses, durations)

        results = self._run_concurrently(read_worker, CONCURRENCY)
        self.assertTrue(all(r is not None for r in results), "参照系スレッドが完了していない")
        statuses = [s for r in results for s in r[0]]
        durations = [d for r in results for d in r[1]]
        self.assertEqual(len(statuses), CONCURRENCY * READS_PER_THREAD)
        self.assertEqual(
            [s for s in statuses if s >= 500], [], f"5xxが発生した: {sorted(set(statuses))}"
        )
        self.assertEqual(set(statuses), {200}, f"200以外の応答: {sorted(set(statuses))}")
        read_stats = {
            "requests": len(statuses),
            "median_ms": round(statistics.median(durations), 1),
            "max_ms": round(max(durations), 1),
        }

        # 手順3・4: 30スレッドから互いに重ならない会議室・時間帯へ同時に POST
        before = self._reservation_count()
        combos = [
            (room_id, slot)
            for slot in WRITE_SLOTS
            for room_id in self.room_ids
        ][:CONCURRENCY]
        self.assertEqual(len(combos), CONCURRENCY)

        def write_worker(index, barrier, results):
            room_id, (start, end) = combos[index]
            client = self.server.client()
            client.cookie = self.clients[index % USER_COUNT].cookie
            body = {
                "room_id": room_id,
                "reserved_date": self.write_date,
                "start_time": start,
                "end_time": end,
                "title": f"同時登録{index}",
                "attendee_user_ids": [],
                "attendee_count": None,
                "note": "",
            }
            barrier.wait()
            res = client.post("/api/reservations", body)
            results[index] = (res.status, res.error_code(), res.text[:200])

        write_results = self._run_concurrently(write_worker, CONCURRENCY)
        self.assertTrue(all(r is not None for r in write_results), "更新系スレッドが完了していない")
        write_statuses = [r[0] for r in write_results]
        self.assertEqual(
            [s for s in write_statuses if s >= 500],
            [],
            f"5xxが発生した: {[r for r in write_results if r[0] >= 500]}",
        )
        self.assertEqual(
            write_statuses.count(201),
            CONCURRENCY,
            f"201が30件でない: {sorted(set(write_statuses))} / {[r for r in write_results if r[0] != 201]}",
        )
        self.assertEqual(self._reservation_count(), before + CONCURRENCY)

        # 手順5: サーバーログに DB_LOCK_TIMEOUT が出ていない
        with open(self.log_path, "r", encoding="utf-8", errors="replace") as handle:
            log = handle.read()
        self.assertNotIn("DB_LOCK_TIMEOUT", log, "DB_LOCK_TIMEOUT が記録されている")
        records = [
            json.loads(line) for line in log.splitlines() if line.strip().startswith("{")
        ]
        self.assertEqual(
            [r for r in records if r["status"] >= 500], [], "5xxのアクセスログがある"
        )
        print(
            "[A009 計測] "
            + json.dumps(
                {
                    "read": read_stats,
                    "write_201": write_statuses.count(201),
                    "cpu_count": os.cpu_count(),
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    unittest.main()
