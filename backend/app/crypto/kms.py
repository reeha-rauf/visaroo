"""AWS KMS crypto provider — real cloud encryption at rest for sensitive fields.

Uses the KMS Encrypt/Decrypt APIs directly. Sensitive profile fields (E-Verify number,
EIN, petition receipt number) are short, well under the 4KB KMS plaintext limit, so a
direct KMS call per field is appropriate (no envelope key needed at this size).

Ciphertext blobs are base64-encoded and prefixed so they store cleanly in a text column
and are never confused with locally-encrypted values.
"""
from __future__ import annotations

import base64
import logging

from ..config import get_settings

logger = logging.getLogger("visaroo.kms")

_PREFIX = "kms:"


class KmsProvider:
    """Encrypt/decrypt via AWS KMS. Requires CRYPTO_PROVIDER=kms and a valid KMS_KEY_ID."""

    def __init__(self) -> None:
        import boto3  # imported lazily so the app runs without boto3 configured

        self.settings = get_settings()
        if not self.settings.kms_key_id:
            raise RuntimeError(
                "CRYPTO_PROVIDER=kms requires KMS_KEY_ID to be set (key id, ARN, or alias)."
            )
        self._client = boto3.client("kms", region_name=self.settings.aws_region)

    def encrypt(self, plaintext: str) -> str:
        resp = self._client.encrypt(
            KeyId=self.settings.kms_key_id,
            Plaintext=plaintext.encode("utf-8"),
        )
        blob = base64.b64encode(resp["CiphertextBlob"]).decode("utf-8")
        return _PREFIX + blob

    def decrypt(self, ciphertext: str) -> str:
        blob = ciphertext[len(_PREFIX):] if ciphertext.startswith(_PREFIX) else ciphertext
        resp = self._client.decrypt(
            CiphertextBlob=base64.b64decode(blob),
            KeyId=self.settings.kms_key_id,
        )
        return resp["Plaintext"].decode("utf-8")
