from __future__ import annotations

import hashlib
import hmac
import os
from base64 import urlsafe_b64decode, urlsafe_b64encode

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SALT_BYTES = 16
KEY_BYTES = 32


def hash_password(password: str) -> str:
    """Hash a password with scrypt and return a self-contained verifier.

    Format: `scrypt$<n>$<r>$<p>$<salt_b64>$<hash_b64>`. Salt is freshly drawn
    per call; everything needed to verify is stored in the returned string.
    """
    salt = os.urandom(SALT_BYTES)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=KEY_BYTES,
    )
    return (
        f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}"
        f"${urlsafe_b64encode(salt).decode()}${urlsafe_b64encode(derived).decode()}"
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n_str, r_str, p_str, salt_b64, hash_b64 = stored.split("$")
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    salt = urlsafe_b64decode(salt_b64)
    expected = urlsafe_b64decode(hash_b64)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=int(n_str),
        r=int(r_str),
        p=int(p_str),
        dklen=len(expected),
    )
    return hmac.compare_digest(derived, expected)
