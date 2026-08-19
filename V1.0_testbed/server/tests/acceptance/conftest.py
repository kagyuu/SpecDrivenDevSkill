"""tests/api/conftest.py のフィクスチャ(client, db_path)をtests/acceptance/配下でも使えるようにする。"""

from tests.api.conftest import client, db_path  # noqa: F401
