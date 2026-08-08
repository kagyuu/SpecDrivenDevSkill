"""T014 — 今後の予約がある会議室の無効化拒否(docs/P008-test-direction/T014-room-deactivate-blocked.md)。

Sprint 2 の暫定実装(`count_future_reservations` が常に0)が Sprint 3 で本実装に
差し替えられていることを確認する。
"""

import unittest
from datetime import datetime, timedelta
from pathlib import Path

from meeting_room import db, security
from meeting_room.repositories import reservations_repo
from tests.integration.support import IntegrationTestCase

SERVER_SRC = Path(__file__).resolve().parents[2] / "src"


def _date(offset_days: int) -> str:
    return (datetime.now() + timedelta(days=offset_days)).strftime("%Y-%m-%d")


class T014RoomDeactivateBlockedTest(IntegrationTestCase):
    seed_rooms = True

    def setUp(self):
        super().setUp()
        self.assertEqual(self.login("admin001").status_code, 200)
        rooms = self.client.get("/api/rooms?include_inactive=true").json()["rooms"]
        self.room_a = next(r["room_id"] for r in rooms if r["name"] == "会議室A")
        self.room_b = next(r["room_id"] for r in rooms if r["name"] == "会議室B")
        # 会議室D(予約なし)を追加する
        res = self.client.post("/api/rooms", json={"name": "会議室D", "capacity": 6})
        self.assertEqual(res.status_code, 201, res.text)
        self.room_d = res.json()["room"]["room_id"]

        # 事前準備2: user001 で会議室Aに「本日+1日」の予約を1件登録する
        self.assertEqual(self.login("user001").status_code, 200)
        res = self.client.post(
            "/api/reservations",
            json={
                "room_id": self.room_a,
                "reserved_date": _date(1),
                "start_time": "10:00",
                "end_time": "11:00",
                "title": "定例会議",
                "attendee_user_ids": [],
                "attendee_count": None,
                "note": "",
            },
        )
        self.assertEqual(res.status_code, 201, res.text)
        self.future_reservation_id = res.json()["reservation"]["reservation_id"]

        # 事前準備3: 会議室Bに「本日-3日」の予約をリポジトリ経由で直接INSERTする
        conn = self.db()
        with db.transaction(conn):
            reservations_repo.insert(
                conn, self.room_b, "user001", _date(-3), "10:00", "11:00",
                "過去の会議", None, "", security.now_utc(),
            )

        # 事前準備4: admin001 でログインする
        self.assertEqual(self.login("admin001").status_code, 200)

    def test_deactivate_blocked_by_future_reservation(self):
        # 手順1: 今後の予約がある会議室Aの無効化は 409
        res = self.client.delete(f"/api/rooms/{self.room_a}")
        self.assertEqual(res.status_code, 409, res.text)
        error = res.json()["error"]
        self.assertEqual(error["code"], "CONSTRAINT_VIOLATION")
        self.assertIn("1", error["message"])
        row = self.db().execute(
            "SELECT is_active FROM rooms WHERE room_id = ?", (self.room_a,)
        ).fetchone()
        self.assertEqual(row["is_active"], 1, "会議室Aは is_active=1 のまま")

        # 手順2: 予約を取り消してから無効化 → 204
        self.assertEqual(self.login("user001").status_code, 200)
        self.assertEqual(
            self.client.delete(f"/api/reservations/{self.future_reservation_id}").status_code,
            204,
        )
        self.assertEqual(self.login("admin001").status_code, 200)
        self.assertEqual(self.client.delete(f"/api/rooms/{self.room_a}").status_code, 204)

        # 手順3: 過去の予約のみの会議室Bは無効化できる
        self.assertEqual(self.client.delete(f"/api/rooms/{self.room_b}").status_code, 204)

        # 手順4: 予約のない会議室Dは無効化できる
        self.assertEqual(self.client.delete(f"/api/rooms/{self.room_d}").status_code, 204)

    def test_todo_marker_removed(self):
        # 手順5: `TODO(U003-T2)` が残っていないこと
        hits = [
            str(path)
            for path in SERVER_SRC.rglob("*.py")
            if "TODO(U003-T2)" in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(hits, [], "暫定実装のTODOが残っている")


if __name__ == "__main__":
    unittest.main()
