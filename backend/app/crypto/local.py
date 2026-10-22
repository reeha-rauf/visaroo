"""Local Fernet-based crypto provider (default, no AWS required).

Used for development and demos so sensitive fields are still encrypted at rest without
needing an AWS KMS key. In production, set CRYPTO_PROVIDER=kms.
"""
from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet

from ..config import get_settings

_PREFIX = "local:"


def _derive_key(secret: str) -> bytes:
    """Derive a urlsafe-base64 32-byte Fernet key from an arbitrary secret string."""
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


class LocalProvider:
    """Fernet symmetric encryption. Key comes from FERNET_KEY or is derived from
    SECRET_KEY so the app runs out of the box in development."""

    def __init__(self) -> None:
        settings = get_settings()
        if settings.fernet_key:
            key = settings.fernet_key.encode("utf-8")
        else:
            key = _derive_key(settings.secret_key)
        self._fernet = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        token = self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")
        return _PREFIX + token

    def decrypt(self, ciphertext: str) -> str:
        token = ciphertext[len(_PREFIX):] if ciphertext.startswith(_PREFIX) else ciphertext
        return self._fernet.decrypt(token.encode("utf-8")).decode("utf-8")
