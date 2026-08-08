"""U003-T1 単体テスト — `003-reservations.sql` の適用と `reservations` Repository。

参照: docs/P002-frontend-spec.md 6.2 / 5.3、docs/P003-backend-spec.md 3.4 / 3.5 / 5.2
重複判定の境界値(境界接触を重複としないこと)が本テストの最重要観点である。
"""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from meeting_room import db, security
from meeting_room.repositories import reservations_repo, rooms_repo, users_repo

NOW = "2026-08-05T00:00:00Z"


class ReservationsRepoTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = str(Path(self._tmp.name) / "app.db")
        db.apply_migrations(db_path=self.db_path)
        self.conn = db.connect(self.db_path)
        self.addCleanup(self.conn.close)
        with db.transaction(self.conn):
            self.room_a = rooms_repo.insert(self.conn, "会議室A", 10, "", "", True, NOW)
            self.room_b = rooms_repo.insert(self.conn, "会議室B", 4, "", "", True, NOW)
            for user_id, name in [("user001", "山田 太郎"), ("user002", "鈴木 花子")]:
                users_repo.insert(
                    self.conn, user_id, name, security.hash_password("Passw0rd!23"),
                    "general", True, NOW,
                )

    def _insert(
        self, room_id=None, user_id="user001", reserved_date="2026-08-10",
        start_time="09:00", end_time="10:00", title="定例会議",
        attendee_count=None, note="", meeting_url="",
    ):
        with db.transaction(self.conn):
            return reservations_repo.insert(
                self.conn, self.room_a if room_id is None else room_id, user_id,
                reserved_date, start_time, end_time, title, attendee_count, note, NOW,
                meeting_url=meeting_url,
            )


class MigrationTest(ReservationsRepoTestBase):
    # 正常系: 003 適用で2テーブルと3インデックスが作られる
    def test_tables_and_indexes_created(self):
        tables = {
            r["name"]
            for r in self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        self.assertIn("reservations", tables)
        self.assertIn("reservation_attendees", tables)
        indexes = {
            r["name"]
            for r in self.conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        }
        self.assertIn("idx_reservations_room_date", indexes)
        self.assertIn("idx_reservations_date", indexes)
        self.assertIn("idx_reservations_user_date", indexes)

    # 正常系: 再適用しても schema_migrations の行数が増えない(ADR-009)
    def test_reapply_does_not_add_rows(self):
        before = self.conn.execute("SELECT COUNT(*) AS c FROM schema_migrations").fetchone()["c"]
        self.assertEqual(db.apply_migrations(db_path=self.db_path), [])
        after = self.conn.execute("SELECT COUNT(*) AS c FROM schema_migrations").fetchone()["c"]
        self.assertEqual(after, before)
        self.assertIn(
            "003-reservations.sql",
            [r["version"] for r in self.conn.execute("SELECT version FROM schema_migrations")],
        )

    # 異常系: end_time <= start_time は CHECK 制約違反
    def test_check_constraint_end_after_start(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self._insert(start_time="10:00", end_time="10:00")
        with self.assertRaises(sqlite3.IntegrityError):
            self._insert(start_time="10:00", end_time="09:30")

    # 異常系: attendee_count が範囲外は CHECK 制約違反(NULLは許可)
    def test_check_constraint_attendee_count(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self._insert(attendee_count=0)
        self.assertIsInstance(self._insert(attendee_count=None), int)


class CrudTest(ReservationsRepoTestBase):
    # 正常系: insert → find_by_id が room_name / user_name を含んで返る
    def test_find_by_id_includes_joined_names(self):
        reservation_id = self._insert(attendee_count=8, note="資料は事前配布")
        found = reservations_repo.find_by_id(self.conn, reservation_id)
        self.assertEqual(found["room_name"], "会議室A")
        self.assertEqual(found["user_name"], "山田 太郎")
        self.assertEqual(found["attendee_count"], 8)
        self.assertEqual(found["note"], "資料は事前配布")
        self.assertEqual(found["attendees"], [])

    def test_find_by_id_missing(self):
        self.assertIsNone(reservations_repo.find_by_id(self.conn, 999))

    # 正常系: replace_attendees で 2件 → 1件 に置き換わる
    def test_replace_attendees(self):
        reservation_id = self._insert()
        with db.transaction(self.conn):
            reservations_repo.replace_attendees(
                self.conn, reservation_id, ["user001", "user002"]
            )
        self.assertEqual(len(reservations_repo.list_attendees(self.conn, reservation_id)), 2)
        with db.transaction(self.conn):
            reservations_repo.replace_attendees(self.conn, reservation_id, ["user002"])
        attendees = reservations_repo.list_attendees(self.conn, reservation_id)
        self.assertEqual(attendees, [{"user_id": "user002", "name": "鈴木 花子"}])

    # 正常系: delete で参加者行も消える(ON DELETE CASCADE)
    def test_delete_cascades_attendees(self):
        reservation_id = self._insert()
        with db.transaction(self.conn):
            reservations_repo.replace_attendees(self.conn, reservation_id, ["user002"])
        with db.transaction(self.conn):
            reservations_repo.delete(self.conn, reservation_id)
        self.assertIsNone(reservations_repo.find_by_id(self.conn, reservation_id))
        rows = self.conn.execute("SELECT COUNT(*) AS c FROM reservation_attendees").fetchone()
        self.assertEqual(rows["c"], 0)

    # 正常系: update で全項目が置き換わる
    def test_update_replaces_all_columns(self):
        reservation_id = self._insert()
        with db.transaction(self.conn):
            reservations_repo.update(
                self.conn, reservation_id, self.room_b, "2026-08-11", "13:00", "14:00",
                "臨時会議", 3, "備考", "2026-08-06T00:00:00Z",
            )
        found = reservations_repo.find_by_id(self.conn, reservation_id)
        self.assertEqual(found["room_id"], self.room_b)
        self.assertEqual(found["reserved_date"], "2026-08-11")
        self.assertEqual(found["title"], "臨時会議")
        self.assertEqual(found["user_id"], "user001")  # 予約者は変わらない
        self.assertEqual(found["updated_at"], "2026-08-06T00:00:00Z")


class ListTest(ReservationsRepoTestBase):
    # 正常系: list_by_period の並びは reserved_date, start_time, room_id
    def test_list_by_period_order(self):
        self._insert(reserved_date="2026-08-11", start_time="09:00", end_time="10:00")
        self._insert(reserved_date="2026-08-10", start_time="11:00", end_time="12:00")
        self._insert(
            room_id=self.room_b, reserved_date="2026-08-10", start_time="09:00", end_time="10:00"
        )
        self._insert(reserved_date="2026-08-10", start_time="09:00", end_time="10:00")
        rows = reservations_repo.list_by_period(self.conn, "2026-08-10", "2026-08-11")
        self.assertEqual(
            [(r["reserved_date"], r["start_time"], r["room_id"]) for r in rows],
            [
                ("2026-08-10", "09:00", self.room_a),
                ("2026-08-10", "09:00", self.room_b),
                ("2026-08-10", "11:00", self.room_a),
                ("2026-08-11", "09:00", self.room_a),
            ],
        )

    def test_list_by_period_excludes_outside_range(self):
        self._insert(reserved_date="2026-08-09")
        self._insert(reserved_date="2026-08-12")
        rows = reservations_repo.list_by_period(self.conn, "2026-08-10", "2026-08-11")
        self.assertEqual(rows, [])

    def test_list_by_period_filters_room_ids(self):
        self._insert(reserved_date="2026-08-10")
        self._insert(room_id=self.room_b, reserved_date="2026-08-10")
        rows = reservations_repo.list_by_period(
            self.conn, "2026-08-10", "2026-08-10", room_ids=[self.room_b]
        )
        self.assertEqual([r["room_id"] for r in rows], [self.room_b])

    # 正常系: list_by_user('upcoming') に過去日が含まれない / 'past' は降順
    def test_list_by_user_periods(self):
        self._insert(reserved_date="2026-08-10")
        self._insert(reserved_date="2026-08-12")
        self._insert(reserved_date="2026-08-01")
        self._insert(reserved_date="2026-08-03")
        self._insert(user_id="user002", reserved_date="2026-08-11")
        upcoming = reservations_repo.list_by_user(self.conn, "user001", "upcoming", "2026-08-10")
        self.assertEqual([r["reserved_date"] for r in upcoming], ["2026-08-10", "2026-08-12"])
        past = reservations_repo.list_by_user(self.conn, "user001", "past", "2026-08-10")
        self.assertEqual([r["reserved_date"] for r in past], ["2026-08-03", "2026-08-01"])

    # 正常系: count_future は reserved_date >= today のみ数える
    def test_count_future(self):
        self._insert(reserved_date="2026-08-10")
        self._insert(reserved_date="2026-08-11")
        self._insert(reserved_date="2026-08-01")
        self._insert(room_id=self.room_b, reserved_date="2026-08-11")
        self.assertEqual(reservations_repo.count_future(self.conn, self.room_a, "2026-08-10"), 2)
        self.assertEqual(reservations_repo.count_future(self.conn, self.room_b, "2026-08-10"), 1)


class FindConflictsTest(ReservationsRepoTestBase):
    """P003 5.2 の判定SQLの境界値(最重要)。既存予約は 09:00-10:00。"""

    def setUp(self):
        super().setUp()
        self.existing = self._insert(
            reserved_date="2026-08-10", start_time="09:00", end_time="10:00"
        )

    def _conflicts(self, start, end, room_id=None, date="2026-08-10", exclude=None):
        return reservations_repo.find_conflicts(
            self.conn,
            self.room_a if room_id is None else room_id,
            date, start, end, exclude_reservation_id=exclude,
        )

    def test_exact_match_conflicts(self):
        self.assertEqual(len(self._conflicts("09:00", "10:00")), 1)

    def test_overlap_tail_conflicts(self):
        self.assertEqual(len(self._conflicts("09:30", "10:30")), 1)

    def test_overlap_head_conflicts(self):
        self.assertEqual(len(self._conflicts("08:30", "09:30")), 1)

    def test_contained_conflicts(self):
        # 30分刻み制約は上位層の責務のため Repository 単体では任意の時刻で検証してよい
        self.assertEqual(len(self._conflicts("09:15", "09:45")), 1)

    def test_containing_conflicts(self):
        self.assertEqual(len(self._conflicts("08:00", "11:00")), 1)

    # 最重要: 境界接触は重複ではない
    def test_touching_after_is_not_conflict(self):
        self.assertEqual(self._conflicts("10:00", "11:00"), [])

    def test_touching_before_is_not_conflict(self):
        self.assertEqual(self._conflicts("08:00", "09:00"), [])

    def test_other_room_is_not_conflict(self):
        self.assertEqual(self._conflicts("09:00", "10:00", room_id=self.room_b), [])

    def test_other_date_is_not_conflict(self):
        self.assertEqual(self._conflicts("09:00", "10:00", date="2026-08-11"), [])

    def test_exclude_self(self):
        self.assertEqual(self._conflicts("09:00", "10:00", exclude=self.existing), [])

    def test_conflict_payload_shape(self):
        conflicts = self._conflicts("09:30", "10:30")
        self.assertEqual(
            conflicts[0],
            {"reservation_id": self.existing, "start_time": "09:00", "end_time": "10:00"},
        )


class MeetingUrlRepoTest(ReservationsRepoTestBase):
    """※CR-001 `meeting_url` の往復と全置換更新(P002 5.3 / 6.2、ADR-011)。"""

    URL = "https://example.com/meet/abc"

    # 正常系: insert で渡した値が find_by_id で返る
    def test_insert_and_read_meeting_url(self):
        rid = self._insert(meeting_url=self.URL)
        row = reservations_repo.find_by_id(self.conn, rid)
        self.assertEqual(row["meeting_url"], self.URL)

    # 正常系: 未指定なら空文字(NULL にしない)
    def test_default_is_empty_string(self):
        rid = self._insert()
        row = reservations_repo.find_by_id(self.conn, rid)
        self.assertEqual(row["meeting_url"], "")
        self.assertIsNotNone(row["meeting_url"])

    # 正常系: update は全置換であり、空文字で消える
    def test_update_replaces_meeting_url(self):
        rid = self._insert(meeting_url=self.URL)
        with db.transaction(self.conn):
            reservations_repo.update(
                self.conn, rid, self.room_a, "2026-08-10", "09:00", "10:00",
                "定例会議", None, "", NOW, meeting_url="http://example.com/x",
            )
        self.assertEqual(
            reservations_repo.find_by_id(self.conn, rid)["meeting_url"],
            "http://example.com/x",
        )
        with db.transaction(self.conn):
            reservations_repo.update(
                self.conn, rid, self.room_a, "2026-08-10", "09:00", "10:00",
                "定例会議", None, "", NOW, meeting_url="",
            )
        self.assertEqual(reservations_repo.find_by_id(self.conn, rid)["meeting_url"], "")

    # 正常系: 一覧APIが使う SELECT にも meeting_url が含まれる
    def test_list_by_period_includes_meeting_url(self):
        self._insert(meeting_url=self.URL)
        rows = reservations_repo.list_by_period(self.conn, "2026-08-01", "2026-08-31")
        self.assertEqual(len(rows), 1)
        self.assertIn("meeting_url", rows[0])
        self.assertEqual(rows[0]["meeting_url"], self.URL)

    def test_list_by_user_includes_meeting_url(self):
        self._insert(meeting_url=self.URL)
        rows = reservations_repo.list_by_user(self.conn, "user001", "upcoming", "2026-08-01")
        self.assertEqual(rows[0]["meeting_url"], self.URL)

    # 正常系: 500文字ちょうどが保存できる(DB側に長さ制約は置かない。検証はスキーマ層)
    def test_500_chars_can_be_stored(self):
        url = "https://" + ("a" * 492)
        self.assertEqual(len(url), 500)
        rid = self._insert(meeting_url=url)
        self.assertEqual(reservations_repo.find_by_id(self.conn, rid)["meeting_url"], url)


if __name__ == "__main__":
    unittest.main()
