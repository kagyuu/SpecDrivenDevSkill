"""パスワードハッシュ化・検証 (docs/P007-impl-direction/U001-foundation-auth.md U001-2).

★deviation★ docs/P003-backend-spec.md §3 はbcrypt(cost factor 12)を指定しているが、
本サンドボックスはpypi.orgにアクセスできずbcryptパッケージをインストールできない
(docs/P101-impl-context.md参照)。標準ライブラリの hashlib.scrypt を用いて同等の
コスト付きハッシュ(CPU/メモリコストパラメータ付き)で代替する。
"""
from __future__ import annotations

import hashlib
import hmac
import os

_SCRYPT_N = 2 ** 14
_SCRYPT_R = 8
_SCRYPT_P = 1
_DKLEN = 32
_ALGO_TAG = "scrypt1"


def hash_password(plain: str) -> str:
    """平文パスワードをハッシュ化する。ログ出力・保存には平文を含めない。"""
    salt = os.urandom(16)
    derived = hashlib.scrypt(
        plain.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=_DKLEN
    )
    return f"{_ALGO_TAG}${salt.hex()}${derived.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    """平文パスワードとハッシュを比較する。"""
    try:
        algo_tag, salt_hex, derived_hex = hashed.split("$")
    except ValueError:
        return False
    if algo_tag != _ALGO_TAG:
        return False
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(derived_hex)
    actual = hashlib.scrypt(
        plain.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=_DKLEN
    )
    return hmac.compare_digest(actual, expected)
