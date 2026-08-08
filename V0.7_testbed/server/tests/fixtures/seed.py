"""基準データセットの投入(docs/P006-test-plan.md 5章)。

`admin001` はアプリ起動時のシード(P003 3.6)で作成されるため、ここでは不足分のみ補う。
予約(`reservations`)は Sprint 3 で実装するため、本スクリプトでは投入しない。
"""

from __future__ import annotations

from meeting_room import db, security
from meeting_room.repositories import rooms_repo, users_repo

PASSWORD = "Passw0rd!23"

USERS = [
    ("admin001", "管理 太郎", "admin", True),
    ("user001", "山田 太郎", "general", True),
    ("user002", "鈴木 花子", "general", True),
    ("user003", "退職 次郎", "general", False),
]

ROOMS = [
    ("会議室A", 10, "プロジェクタ", "", True),
    ("会議室B", 4, "", "", True),
    ("会議室C", 20, "", "", False),
]


def seed_users(db_path: str) -> None:
    conn = db.connect(db_path)
    try:
        now = security.now_utc()
        for user_id, name, role, is_active in USERS:
            if users_repo.find_by_id(conn, user_id) is not None:
                continue  # 起動時シードで作成済みの admin001 はそのまま使う
            with db.transaction(conn):
                users_repo.insert(
                    conn, user_id, name, security.hash_password(PASSWORD), role, is_active, now
                )
    finally:
        conn.close()


def seed_rooms(db_path: str) -> None:
    conn = db.connect(db_path)
    try:
        now = security.now_utc()
        for name, capacity, equipment, description, is_active in ROOMS:
            with db.transaction(conn):
                rooms_repo.insert(conn, name, capacity, equipment, description, is_active, now)
    finally:
        conn.close()


def seed_all(db_path: str) -> None:
    seed_users(db_path)
    seed_rooms(db_path)
