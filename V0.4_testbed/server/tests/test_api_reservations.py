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


if __name__ == "__main__":
    unittest.main()
