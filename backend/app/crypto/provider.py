"""Crypto provider interface and factory — encryption at rest for sensitive fields.

Sensitive profile fields (E-Verify case number, employer EIN, petition receipt number)
must never be stored in plaintext (see .kiro/steering/profile.md). All encryption flows
through this interface so the rest of the app never depends directly on AWS.

Two implementations, selected by the ``CRYPTO_PROVIDER`` env var:

* ``LocalProvider`` — Fernet symmetric encryption (default, no AWS needed).
* ``KmsProvider``   — real AWS KMS encrypt/decrypt via boto3 (production cloud integration).

Ciphertext is tagged with a provider prefix so a value encrypted by one provider is never
mis-decrypted by another. Values round-trip as opaque strings suitable for a text column.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from ..config import get_settings


class CryptoProvider(Protocol):
    """Contract every crypto backend must satisfy."""

    def encrypt(self, plaintext: str) -> str:
        """Return an opaque, storable ciphertext string for the given plaintext."""
        ...

    def decrypt(self, ciphertext: str) -> str:
        """Return the plaintext for a ciphertext produced by ``encrypt``."""
        ...


@lru_cache
def get_crypto() -> CryptoProvider:
    """Return the configured crypto provider (cached)."""
    settings = get_settings()
    if settings.crypto_provider.lower() == "kms":
        from .kms import KmsProvider

        return KmsProvider()
    from .local import LocalProvider

    return LocalProvider()
