"""U001-T3 単体テスト — パスワードハッシュ・セッションID・時刻(P003 4.3 / ADR-003)。"""

import re
import unittest

from meeting_room import security


class HashPasswordTest(unittest.TestCase):
    # 正常系: 正しいパスワードで検証が真になる
    def test_verify_correct_password(self):
        stored = security.hash_password("Passw0rd!23")
        self.assertTrue(security.verify_password("Passw0rd!23", stored))

    # 正常系: 格納形式が ADR-003 のとおり
    def test_stored_format(self):
        stored = security.hash_password("Passw0rd!23")
        parts = stored.split("$")
        self.assertEqual(len(parts), 6)
        self.assertEqual(parts[0], "scrypt")
        self.assertEqual((parts[1], parts[2], parts[3]), ("16384", "8", "1"))

    # 正常系: 同じパスワードでもソルトが異なるため文字列が変わる
    def test_same_password_hashes_differ(self):
        self.assertNotEqual(security.hash_password("Passw0rd!23"), security.hash_password("Passw0rd!23"))

    # 異常系: 誤ったパスワードは偽
    def test_verify_wrong_password(self):
        stored = security.hash_password("Passw0rd!23")
        self.assertFalse(security.verify_password("WrongPass123", stored))

    # 異常系: 壊れた格納文字列でも例外を投げず偽を返す
    def test_verify_broken_stored_value(self):
        for broken in ("garbage", "", "scrypt$x$y$z$aa$bb", "bcrypt$1$2$3$aa$bb"):
            with self.subTest(broken=broken):
                self.assertFalse(security.verify_password("Passw0rd!23", broken))


class SessionIdTest(unittest.TestCase):
    # 正常系: URLセーフで十分な長さがあり、毎回異なる
    def test_new_session_id(self):
        a, b = security.new_session_id(), security.new_session_id()
        self.assertNotEqual(a, b)
        self.assertGreaterEqual(len(a), 43)
        self.assertRegex(a, r"^[A-Za-z0-9_-]+$")


class ClockTest(unittest.TestCase):
    # 正常系: 時刻取得はこの2関数に集約する(P006 6章)
    def test_now_utc_format(self):
        self.assertRegex(security.now_utc(), r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    def test_today_local_format(self):
        self.assertRegex(security.today_local(), r"^\d{4}-\d{2}-\d{2}$")

    # 他モジュールで datetime.now() を直書きしていないこと(P006 6章)
    def test_no_direct_datetime_now_outside_security(self):
        import pathlib

        root = pathlib.Path(security.__file__).resolve().parent
        offenders = []
        for path in root.rglob("*.py"):
            if path.name == "security.py":
                continue
            text = path.read_text(encoding="utf-8")
            if re.search(r"datetime\.now\(|date\.today\(", text):
                offenders.append(path.name)
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
