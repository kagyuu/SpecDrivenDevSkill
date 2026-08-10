"""Password hashing (U001-T3, docs/P007-impl-direction/U001-foundation-and-auth.md).

Implements docs/P003-backend-spec.md 1.2節: hashlib.scrypt(n=2**14, r=8, p=1),
a per-user random 16-byte salt, stored as "scrypt$<salt_hex>$<hash_hex>".

Unit tested by server/tests/test_password.py (U001-T3, all cases PASS).
"""

from __future__ import annotations

import hashlib
import hmac
import os

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SALT_BYTES = 16


def hash_password(plain: str) -> str:
    """Hash a plaintext password for storage in users.password_hash."""
    salt = os.urandom(_SALT_BYTES)
    digest = hashlib.scrypt(
        plain.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P
    )
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a users.password_hash value.

    Uses hmac.compare_digest for the final comparison (constant-time) to
    avoid leaking timing information about how much of the hash matched.
    """
    try:
        algo, salt_hex, digest_hex = hashed.split("$")
    except ValueError:
        return False
    if algo != "scrypt":
        return False
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(digest_hex)
    actual = hashlib.scrypt(
        plain.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P
    )
    return hmac.compare_digest(actual, expected)
