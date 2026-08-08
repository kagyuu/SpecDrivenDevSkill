"""パスワードハッシュ・セッションID生成・時刻取得(P003 4.3、ADR-003)。

時刻取得は本モジュールの `now_utc()` / `today_local()` に集約する。
他のモジュールで `datetime.now()` を直書きしないこと(P006 6章)。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timezone

#: scrypt のコストパラメータ(ADR-003)
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 32
SALT_BYTES = 16


def now_utc() -> str:
    """現在時刻(UTC)を ISO 8601 の `YYYY-MM-DDTHH:MM:SSZ` で返す。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_local() -> str:
    """サーバーのローカル日付(JST想定)を `YYYY-MM-DD` で返す(P003 6.4 の「本日」)。"""
    return datetime.now().strftime("%Y-%m-%d")


def _b64e(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _b64d(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


def hash_password(password: str) -> str:
    """`scrypt$<n>$<r>$<p>$<b64(salt)>$<b64(dk)>` 形式の文字列を返す(ADR-003)。"""
    salt = secrets.token_bytes(SALT_BYTES)
    dk = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_DKLEN,
    )
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${_b64e(salt)}${_b64e(dk)}"


def verify_password(password: str, stored: str) -> bool:
    """格納文字列からパラメータとソルトを復元して再計算し、定数時間比較する。

    形式が不正な場合は例外を投げず False を返す。
    """
    try:
        scheme, n_s, r_s, p_s, salt_s, dk_s = stored.split("$")
        if scheme != "scrypt":
            return False
        n, r, p = int(n_s), int(r_s), int(p_s)
        salt = _b64d(salt_s)
        expected = _b64d(dk_s)
        actual = hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=len(expected)
        )
    except Exception:
        return False
    return hmac.compare_digest(actual, expected)


#: ユーザーが存在しない場合の応答時間差を減らすためのダミーハッシュ(P003 6.1 API-01)
DUMMY_PASSWORD_HASH = hash_password("dummy-password-for-timing-equalization")


def new_session_id() -> str:
    """不透明なセッションID(ADR-005)。"""
    return secrets.token_urlsafe(32)
