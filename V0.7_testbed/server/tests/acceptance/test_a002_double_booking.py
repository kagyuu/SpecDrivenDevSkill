"""A002 — 二重予約の防止(docs/P009-acceptance-direction/A002-double-booking-prevention.md)。

実プロセス + 実HTTPクライアントで、逐次・並行の両方を確認する。
"""

from __future__ import annotations

import threading
import unittest

from tests.acceptance.base import AcceptanceTestCase, day


class A002DoubleBookingTest(AcceptanceTestCase):
    def setUp(self):
        super().setUp()
        self.room_a = self.room_ids()["会議室A"]
        self.date = day(1)
        # 事前準備2: user001 / user002 の両方でログインし、それぞれのCookieを保持する
        self.c1 = self.new_client()
        self.c2 = self.new_client()
        self.assertEqual(self.c1.login("user001").status, 200)
        self.assertEqual(self.c2.login("user002").status, 200)

    def _body(self, start, end):
        return self.reservation_body(self.room_a, self.date, start, end)

    def _count(self) -> int:
        return self.db().execute("SELECT COUNT(*) AS c FROM reservations").fetchone()["c"]

    def _clear_reservations(self):
        conn = self.db()
        conn.execute("DELETE FROM reservation_attendees")
        conn.execute("DELETE FROM reservations")
        self.assertEqual(self._count(), 0)

    def _parallel_post(self, clients):
        """送信タイミングを揃えて同時に POST /api/reservations する。"""
        barrier = threading.Barrier(len(clients))
        results: list = [None] * len(clients)

        def worker(index, client):
            barrier.wait()
            res = client.post("/api/reservations", self._body("10:00", "11:00"))
            results[index] = (res.status, res.error_code())

        threads = [
            threading.Thread(target=worker, args=(i, c)) for i, c in enumerate(clients)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)
        return results

    def test_double_booking_is_prevented(self):
        # 手順1: user001 で 10:00-11:00 を登録 → 201
        res = self.c1.post("/api/reservations", self._body("10:00", "11:00"))
        self.assertEqual(res.status, 201, res.text)

        # 手順2: user002 で 10:30-11:30(重なる) → 409 RESERVATION_CONFLICT
        res = self.c2.post("/api/reservations", self._body("10:30", "11:30"))
        self.assertEqual(res.status, 409, res.text)
        self.assertEqual(res.error_code(), "RESERVATION_CONFLICT")

        # 手順3: DBは1件
        self.assertEqual(self._count(), 1)

        # 手順4: 予約0件に戻す
        self._clear_reservations()

        # 手順5・6: 2本同時 → 一方が201、他方が409。DBは1件。500は許容しない
        results = self._parallel_post([self.c1, self.c2])
        statuses = sorted(status for status, _ in results)
        self.assertEqual(statuses, [201, 409], f"同時2本の応答: {results}")
        self.assertEqual(self._count(), 1, f"同時2本後の件数: {results}")
        for status, code in results:
            if status == 409:
                self.assertEqual(code, "RESERVATION_CONFLICT")

        # 手順7: 同時実行数5 → ちょうど1本が201、残り4本が409。DBは1件
        self._clear_reservations()
        clients = []
        for user_id in ("user001", "user002", "admin001", "user001", "user002"):
            client = self.new_client()
            self.assertEqual(client.login(user_id).status, 200)
            clients.append(client)
        results = self._parallel_post(clients)
        created = [r for r in results if r[0] == 201]
        conflicted = [r for r in results if r[0] == 409]
        self.assertEqual(len(created), 1, f"同時5本の応答: {results}")
        self.assertEqual(len(conflicted), 4, f"同時5本の応答: {results}")
        self.assertEqual(self._count(), 1, f"同時5本後の件数: {results}")


if __name__ == "__main__":
    unittest.main()
