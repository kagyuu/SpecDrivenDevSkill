"""API結合テスト用のTestClientフィクスチャ。テストごとに独立した一時DBファイルを使う。"""

from __future__ import annotations

import sqlite3
import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = tmp_path / f"test-{uuid.uuid4().hex}.db"
    monkeypatch.setenv("DATABASE_PATH", str(path))
    return path


@pytest.fixture
def client(db_path):
    # main は import 時ではなく、DATABASE_PATH 設定後に読み込む必要があるため遅延import する。
    from app.main import app

    # login のSet-Cookieは Secure 属性付きのため(docs/P002-frontend-spec.md §1)、
    # https スキームのbase_urlでないとテストクライアントのCookie jarに保持されない。
    # 実TLSハンドシェイクは発生しない(ASGIトランスポート内で完結する)。
    with TestClient(app, base_url="https://testserver") as test_client:
        yield test_client


def insert_room(db_path, name="会議室A", capacity=10, is_active=True) -> int:
    """テストデータ準備用: 会議室登録APIが無いスプリント範囲では直接SQLでシードする。"""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute(
        """
        INSERT INTO rooms (name, capacity, equipment_json, description, is_active, created_at, updated_at)
        VALUES (?, ?, '[]', NULL, ?, '2026-08-11T00:00:00+00:00', '2026-08-11T00:00:00+00:00')
        """,
        (name, capacity, 1 if is_active else 0),
    )
    conn.commit()
    room_id = cursor.lastrowid
    conn.close()
    return room_id


def insert_reservation(
    db_path,
    room_id: int,
    employee_id: str,
    date: str,
    start_time: str,
    end_time: str,
    title: str,
) -> int:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    user_row = conn.execute("SELECT id FROM users WHERE employee_id = ?", (employee_id,)).fetchone()
    cursor = conn.execute(
        """
        INSERT INTO reservations (room_id, user_id, date, start_time, end_time, title, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, '2026-08-11T00:00:00+00:00', '2026-08-11T00:00:00+00:00')
        """,
        (room_id, user_row["id"], date, start_time, end_time, title),
    )
    conn.commit()
    reservation_id = cursor.lastrowid
    conn.close()
    return reservation_id
