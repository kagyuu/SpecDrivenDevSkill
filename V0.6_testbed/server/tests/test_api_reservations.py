import os
import tempfile
import unittest
from datetime import date, timedelta

from starlette.testclient import TestClient

from app.db.connection import get_connection, init_db
from app.main import create_app
from tests.helpers import seed_room, seed_user

TOMORROW = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")


def _make_client(db_path: str) -> TestClient:
    app = create_app(db_path=db_path)
    return TestClient(app, base_url="https://testserver")


class ReservationsApiTestBase(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(self.db_path)
        init_db(self.db_path)

        conn = get_connection(self.db_path)
        self.room_id = seed_room(conn, "会議室A")
        # CR-003(T024〜T027): 収容人数10名の会議室
        self.room_cap10_id = seed_room(conn, "会議室C10", capacity=10)
        seed_user(conn, "E0001", "Passw0rd1", name="山田太郎", role="general")
        seed_user(conn, "E0002", "Passw0rd2", name="鈴木花子", role="general")
        conn.close()

        self.client_e1 = _make_client(self.db_path)
        self.client_e1.post("/api/auth/login", json={"employee_id": "E0001", "password": "Passw0rd1"})
        self.client_e2 = _make_client(self.db_path)
        self.client_e2.post("/api/auth/login", json={"employee_id": "E0002", "password": "Passw0rd2"})

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _reservation_payload(self, **overrides):
        base = {
            "room_id": self.room_id, "date": TOMORROW, "start_time": "10:00", "end_time": "11:00",
            "title": "定例MTG", "participant_ids": [], "notes": None,
        }
        base.update(overrides)
        return base


class ReservationsApiTest(ReservationsApiTestBase):
    def test_create_and_list(self):
        r1 = self.client_e1.post("/api/reservations", json=self._reservation_payload())
        self.assertEqual(r1.status_code, 201, r1.text)
        r2 = self.client_e1.get(f"/api/reservations?date_from={TOMORROW}&date_to={TOMORROW}")
        self.assertEqual(r2.status_code, 200)
        ids = [res["id"] for res in r2.json()["reservations"]]
        self.assertIn(r1.json()["id"], ids)

    def test_overlap_conflict_and_boundary(self):
        self.client_e1.post("/api/reservations", json=self._reservation_payload())
        r1 = self.client_e1.post("/api/reservations", json=self._reservation_payload(
            start_time="10:30", end_time="11:30"))
        self.assertEqual(r1.status_code, 409)
        self.assertEqual(r1.json()["error"]["code"], "RESERVATION_CONFLICT")

        r2 = self.client_e1.post("/api/reservations", json=self._reservation_payload(
            start_time="11:00", end_time="12:00"))
        self.assertEqual(r2.status_code, 201, r2.text)

    def test_invalid_time_range(self):
        r1 = self.client_e1.post("/api/reservations", json=self._reservation_payload(
            start_time="11:00", end_time="10:00"))
        self.assertEqual(r1.status_code, 400)
        r2 = self.client_e1.post("/api/reservations", json=self._reservation_payload(
            start_time="10:00", end_time="10:00"))
        self.assertEqual(r2.status_code, 400)

    def test_room_not_found(self):
        r = self.client_e1.post("/api/reservations", json=self._reservation_payload(room_id=99999))
        self.assertEqual(r.status_code, 404)

    def test_get_detail(self):
        create = self.client_e1.post("/api/reservations", json=self._reservation_payload(notes="資料は事前配布"))
        reservation_id = create.json()["id"]
        r = self.client_e1.get(f"/api/reservations/{reservation_id}")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["notes"], "資料は事前配布")
        self.assertIn("created_by", body)
        self.assertIn("participants", body)

    def test_update_by_owner(self):
        create = self.client_e1.post("/api/reservations", json=self._reservation_payload())
        reservation_id = create.json()["id"]
        r1 = self.client_e1.put(f"/api/reservations/{reservation_id}",
                                 json=self._reservation_payload(title="定例MTG(変更後)"))
        self.assertEqual(r1.status_code, 200, r1.text)
        r2 = self.client_e1.get(f"/api/reservations/{reservation_id}")
        self.assertEqual(r2.json()["title"], "定例MTG(変更後)")

    def test_update_delete_forbidden_for_others(self):
        create = self.client_e1.post("/api/reservations", json=self._reservation_payload())
        reservation_id = create.json()["id"]
        r1 = self.client_e2.put(f"/api/reservations/{reservation_id}",
                                 json=self._reservation_payload(title="改ざん"))
        r2 = self.client_e2.delete(f"/api/reservations/{reservation_id}")
        self.assertEqual(r1.status_code, 403)
        self.assertEqual(r2.status_code, 403)
        detail = self.client_e1.get(f"/api/reservations/{reservation_id}").json()
        self.assertEqual(detail["title"], "定例MTG")

    def test_delete_cascades_participants(self):
        conn = get_connection(self.db_path)
        participant_id = conn.execute("SELECT id FROM USERS WHERE employee_id='E0002'").fetchone()["id"]
        conn.close()
        create = self.client_e1.post("/api/reservations",
                                      json=self._reservation_payload(participant_ids=[participant_id]))
        reservation_id = create.json()["id"]
        r1 = self.client_e1.delete(f"/api/reservations/{reservation_id}")
        self.assertEqual(r1.status_code, 200)
        r2 = self.client_e1.get(f"/api/reservations/{reservation_id}")
        self.assertEqual(r2.status_code, 404)
        conn = get_connection(self.db_path)
        remaining = conn.execute(
            "SELECT * FROM RESERVATION_PARTICIPANTS WHERE reservation_id = ?", (reservation_id,)
        ).fetchall()
        conn.close()
        self.assertEqual(len(remaining), 0)

    def test_mine_period_filter(self):
        past_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        self.client_e1.post("/api/reservations", json=self._reservation_payload())
        conn = get_connection(self.db_path)
        e1_id = conn.execute("SELECT id FROM USERS WHERE employee_id='E0001'").fetchone()["id"]
        conn.execute(
            "INSERT INTO RESERVATIONS (room_id, date, start_time, end_time, title, notes, created_by, "
            "created_at, updated_at) VALUES (?, ?, '09:00','09:30','過去MTG',NULL,?, '2020-01-01T00:00:00Z', "
            "'2020-01-01T00:00:00Z')",
            (self.room_id, past_date, e1_id),
        )
        conn.close()
        self.client_e2.post("/api/reservations", json=self._reservation_payload(
            start_time="15:00", end_time="16:00"))

        r1 = self.client_e1.get("/api/reservations/mine")
        titles_upcoming = [res["title"] for res in r1.json()["reservations"]]
        self.assertIn("定例MTG", titles_upcoming)
        self.assertNotIn("過去MTG", titles_upcoming)

        r2 = self.client_e1.get("/api/reservations/mine?period=past")
        titles_past = [res["title"] for res in r2.json()["reservations"]]
        self.assertEqual(titles_past, ["過去MTG"])

    def test_update_overlap_self_excluded(self):
        x = self.client_e1.post("/api/reservations", json=self._reservation_payload(
            start_time="10:00", end_time="11:00", title="予約X")).json()
        self.client_e1.post("/api/reservations", json=self._reservation_payload(
            start_time="13:00", end_time="14:00", title="予約Y"))

        r1 = self.client_e1.put(f"/api/reservations/{x['id']}", json=self._reservation_payload(
            start_time="10:00", end_time="11:00", title="予約X(変更後)"))
        self.assertEqual(r1.status_code, 200, r1.text)

        r2 = self.client_e1.put(f"/api/reservations/{x['id']}", json=self._reservation_payload(
            start_time="13:00", end_time="14:00", title="予約X"))
        self.assertEqual(r2.status_code, 409)


    # --- CR-003(U007-1): 参加予定人数 attendee_count ---

    def test_create_reservation_with_attendee_count_then_fetch(self):
        """T024: 参加予定人数つき予約の作成と詳細取得(未入力時はnull)。"""
        r1 = self.client_e1.post("/api/reservations", json=self._reservation_payload(
            room_id=self.room_cap10_id, attendee_count=8))
        self.assertEqual(r1.status_code, 201, r1.text)
        self.assertEqual(r1.json()["attendee_count"], 8)

        r2 = self.client_e1.get(f"/api/reservations/{r1.json()['id']}")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["attendee_count"], 8)

        # attendee_count を送らない場合は null
        r3 = self.client_e1.post("/api/reservations", json=self._reservation_payload(
            room_id=self.room_cap10_id, start_time="13:00", end_time="14:00"))
        self.assertEqual(r3.status_code, 201, r3.text)
        self.assertIn("attendee_count", r3.json())
        self.assertIsNone(r3.json()["attendee_count"])

        r4 = self.client_e1.get(f"/api/reservations/{r3.json()['id']}")
        self.assertIsNone(r4.json()["attendee_count"])

    def test_update_reservation_attendee_count_then_fetch(self):
        """T025: 参加予定人数の更新と他項目の保持。"""
        created = self.client_e1.post("/api/reservations", json=self._reservation_payload(
            room_id=self.room_cap10_id, attendee_count=4, notes="資料は事前配布")).json()
        reservation_id = created["id"]

        r1 = self.client_e1.put(f"/api/reservations/{reservation_id}", json=self._reservation_payload(
            room_id=self.room_cap10_id, attendee_count=9, notes="資料は事前配布"))
        self.assertEqual(r1.status_code, 200, r1.text)
        self.assertEqual(r1.json()["attendee_count"], 9)

        r2 = self.client_e1.get(f"/api/reservations/{reservation_id}")
        body = r2.json()
        self.assertEqual(body["attendee_count"], 9)
        self.assertEqual(body["title"], "定例MTG")
        self.assertEqual(body["notes"], "資料は事前配布")

    def test_attendee_count_exceeding_room_capacity_is_rejected(self):
        """T026: 収容人数超過の拒否(作成・更新)と境界値(等値は許容)。"""
        r1 = self.client_e1.post("/api/reservations", json=self._reservation_payload(
            room_id=self.room_cap10_id, attendee_count=11))
        self.assertEqual(r1.status_code, 400, r1.text)
        self.assertEqual(r1.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("attendee_count",
                      [d.get("field") for d in r1.json()["error"].get("details", [])])

        r2 = self.client_e1.post("/api/reservations", json=self._reservation_payload(
            room_id=self.room_cap10_id, attendee_count=10))
        self.assertEqual(r2.status_code, 201, r2.text)

        r3 = self.client_e1.put(f"/api/reservations/{r2.json()['id']}",
                                 json=self._reservation_payload(
                                     room_id=self.room_cap10_id, attendee_count=11))
        self.assertEqual(r3.status_code, 400, r3.text)
        self.assertEqual(r3.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("attendee_count",
                      [d.get("field") for d in r3.json()["error"].get("details", [])])

    def test_my_reservations_includes_attendee_count(self):
        """T027: マイ予約一覧には含み、カレンダー用一覧には含まない。"""
        self.client_e1.post("/api/reservations", json=self._reservation_payload(
            room_id=self.room_cap10_id, attendee_count=6))

        r1 = self.client_e1.get("/api/reservations/mine?period=upcoming")
        self.assertEqual(r1.status_code, 200)
        items = r1.json()["reservations"]
        self.assertTrue(items)
        self.assertEqual(items[0]["attendee_count"], 6)

        r2 = self.client_e1.get(f"/api/reservations?date_from={TOMORROW}&date_to={TOMORROW}")
        self.assertEqual(r2.status_code, 200)
        for item in r2.json()["reservations"]:
            self.assertNotIn("attendee_count", item)


if __name__ == "__main__":
    unittest.main()
