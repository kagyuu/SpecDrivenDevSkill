"""U002-T2 単体テスト — 会議室の業務ルール(P003 6.2)。"""

import tempfile
import unittest
from pathlib import Path

from meeting_room import db
from meeting_room.errors import ApiError
from meeting_room.repositories import rooms_repo
from meeting_room.schemas import RoomRequest, validate
from meeting_room.services import room_service

ADMIN = {"user_id": "admin001", "name": "初期管理者", "role": "admin", "is_active": True}
GENERAL = {"user_id": "user001", "name": "山田 太郎", "role": "general", "is_active": True}


def room_payload(**overrides):
    data = {"name": "会議室A", "capacity": 10, "equipment": "", "description": "", "is_active": True}
    data.update(overrides)
    return validate(RoomRequest, data)


class RoomServiceTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = str(Path(self._tmp.name) / "app.db")
        db.apply_migrations(db_path=self.db_path)
        self.conn = db.connect(self.db_path)
        self.addCleanup(self.conn.close)

    # 正常系: 登録 → 一覧
    def test_create_and_list(self):
        room = room_service.create_room(self.conn, room_payload(description="窓側の大会議室"))
        self.assertIsInstance(room["room_id"], int)
        self.assertEqual(room["description"], "窓側の大会議室")
        rooms = room_service.list_rooms(self.conn, GENERAL, include_inactive=False)
        self.assertEqual([r["room_id"] for r in rooms], [room["room_id"]])

    # 正常系: 更新で値が変わり updated_at が進む
    def test_update_room(self):
        room = room_service.create_room(self.conn, room_payload())
        updated = room_service.update_room(
            self.conn, room["room_id"], room_payload(capacity=12, description="改装後")
        )
        self.assertEqual(updated["capacity"], 12)
        self.assertGreaterEqual(updated["updated_at"], updated["created_at"])

    # 正常系: 無効化は論理削除で、冪等
    def test_deactivate_is_logical_and_idempotent(self):
        room = room_service.create_room(self.conn, room_payload())
        room_service.deactivate_room(self.conn, room["room_id"])
        stored = rooms_repo.find_by_id(self.conn, room["room_id"])
        self.assertIsNotNone(stored)
        self.assertIs(stored["is_active"], False)
        room_service.deactivate_room(self.conn, room["room_id"])  # 2回目も例外にしない

    # 正常系: 管理者のみ include_inactive=true を使える
    def test_include_inactive_requires_admin(self):
        room = room_service.create_room(self.conn, room_payload())
        room_service.deactivate_room(self.conn, room["room_id"])
        self.assertEqual(len(room_service.list_rooms(self.conn, ADMIN, include_inactive=True)), 1)
        self.assertEqual(len(room_service.list_rooms(self.conn, GENERAL, include_inactive=False)), 0)
        with self.assertRaises(ApiError) as ctx:
            room_service.list_rooms(self.conn, GENERAL, include_inactive=True)
        self.assertEqual((ctx.exception.status, ctx.exception.code), (403, "FORBIDDEN"))

    # 異常系: 同名の有効な会議室は 409 DUPLICATE_KEY
    def test_duplicate_name_rejected(self):
        room_service.create_room(self.conn, room_payload())
        with self.assertRaises(ApiError) as ctx:
            room_service.create_room(self.conn, room_payload())
        self.assertEqual((ctx.exception.status, ctx.exception.code), (409, "DUPLICATE_KEY"))
        self.assertEqual(ctx.exception.message, "同じ名前の会議室がすでに登録されています。")

    # 正常系: 無効化済みの同名があっても登録できる
    def test_same_name_after_deactivation(self):
        first = room_service.create_room(self.conn, room_payload())
        room_service.deactivate_room(self.conn, first["room_id"])
        second = room_service.create_room(self.conn, room_payload())
        self.assertNotEqual(first["room_id"], second["room_id"])

    # 異常系: 更新で他の有効な同名にぶつかると 409
    def test_update_to_duplicate_name_rejected(self):
        room_service.create_room(self.conn, room_payload(name="会議室A"))
        other = room_service.create_room(self.conn, room_payload(name="会議室B"))
        with self.assertRaises(ApiError) as ctx:
            room_service.update_room(self.conn, other["room_id"], room_payload(name="会議室A"))
        self.assertEqual(ctx.exception.code, "DUPLICATE_KEY")
        # 自分自身の名前のままの更新は通る
        room_service.update_room(self.conn, other["room_id"], room_payload(name="会議室B", capacity=4))

    # 異常系: 存在しない room_id は 404
    def test_missing_room(self):
        for action in (
            lambda: room_service.update_room(self.conn, 999, room_payload()),
            lambda: room_service.deactivate_room(self.conn, 999),
        ):
            with self.assertRaises(ApiError) as ctx:
                action()
            self.assertEqual(ctx.exception.status, 404)

    # Sprint 2 時点では予約件数は常に0(U003-T2で差し替える)
    def test_count_future_reservations_is_zero_in_sprint2(self):
        self.assertEqual(room_service.count_future_reservations(self.conn, 1), 0)


if __name__ == "__main__":
    unittest.main()
