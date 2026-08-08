"""U001-T2 単体テスト — エラーレスポンス変換とアクセスログ(P002 5.2 / P003 4.4)。"""

import json
import unittest

from meeting_room import logging_middleware
from meeting_room.errors import ApiError, internal_error_response, to_response


def _body(response) -> dict:
    return json.loads(response.body.decode("utf-8"))


class ToResponseTest(unittest.TestCase):
    # 正常系: VALIDATION_ERROR は details を含む
    def test_validation_error_includes_details(self):
        err = ApiError(
            400,
            "VALIDATION_ERROR",
            "入力内容に誤りがあります。",
            details=[{"field": "user_id", "message": "ユーザーIDを入力してください。"}],
        )
        res = to_response(err)
        self.assertEqual(res.status_code, 400)
        body = _body(res)
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(body["error"]["message"], "入力内容に誤りがあります。")
        self.assertEqual(body["error"]["details"][0]["field"], "user_id")

    # 正常系: extra は error オブジェクト直下にマージされる
    def test_extra_is_merged_into_error_object(self):
        err = ApiError(
            409,
            "RESERVATION_CONFLICT",
            "選択した時間帯はすでに予約されています。",
            extra={"conflicts": [{"reservation_id": 9, "start_time": "09:30", "end_time": "10:30"}]},
        )
        res = to_response(err)
        self.assertEqual(res.status_code, 409)
        body = _body(res)
        self.assertEqual(body["error"]["conflicts"][0]["reservation_id"], 9)
        self.assertNotIn("details", body["error"])

    # 異常系: details を渡さなければ details キーは出力されない
    def test_details_key_absent_when_not_given(self):
        res = to_response(ApiError(404, "NOT_FOUND", "対象のデータが見つかりません。削除された可能性があります。"))
        body = _body(res)
        self.assertNotIn("details", body["error"])
        self.assertEqual(set(body["error"].keys()), {"code", "message"})

    # 異常系: 500 の本文に内部情報を含めない
    def test_internal_error_has_no_internal_details(self):
        res = internal_error_response()
        self.assertEqual(res.status_code, 500)
        body = _body(res)
        self.assertEqual(body["error"]["code"], "INTERNAL_ERROR")
        text = res.body.decode("utf-8")
        for leaked in ("Traceback", "SELECT", ".py", "/"):
            self.assertNotIn(leaked, text)

    # 正常系: Content-Type は P002 5.1 のとおり
    def test_media_type_is_json_utf8(self):
        res = to_response(ApiError(400, "VALIDATION_ERROR", "入力内容に誤りがあります。", details=[]))
        self.assertEqual(res.media_type, "application/json; charset=utf-8")


class LogRecordTest(unittest.TestCase):
    REQUIRED = {"ts", "level", "method", "path", "status", "duration_ms", "user_id",
                "error_code", "message"}

    # 正常系: ログ行がJSONとしてパースでき、必須項目が揃う
    def test_log_line_is_json_with_required_fields(self):
        record = logging_middleware.build_log_record("GET", "/api/me", 200, 1.234, user_id="user001")
        parsed = json.loads(logging_middleware.format_log_line(record))
        self.assertTrue(self.REQUIRED.issubset(parsed.keys()))
        self.assertEqual(parsed["level"], "INFO")
        self.assertEqual(parsed["user_id"], "user001")

    # 正常系: 未認証は user_id が "-"
    def test_unauthenticated_user_id_is_dash(self):
        record = logging_middleware.build_log_record("POST", "/api/auth/login", 401, 2.0,
                                                     error_code="AUTH_FAILED")
        self.assertEqual(record["user_id"], "-")
        self.assertEqual(record["level"], "WARN")

    # 異常系: sid・パスワード・セッションIDを出力しない
    def test_log_line_never_contains_sid(self):
        record = logging_middleware.build_log_record(
            "POST", "/api/auth/login", 200, 3.0, user_id="user001", message="ok"
        )
        line = logging_middleware.format_log_line(record)
        self.assertNotIn("sid", line)
        self.assertNotIn("password", line)
        self.assertNotIn("session_id", line)

    # 正常系: 5xx のときのみ stack を含める
    def test_stack_only_for_5xx(self):
        ok = logging_middleware.build_log_record("GET", "/api/me", 200, 1.0, stack="TRACE")
        self.assertNotIn("stack", ok)
        ng = logging_middleware.build_log_record("GET", "/api/me", 500, 1.0, stack="TRACE")
        self.assertEqual(ng["stack"], "TRACE")
        self.assertEqual(ng["level"], "ERROR")


if __name__ == "__main__":
    unittest.main()
