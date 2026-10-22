"""Amazon SES email provider — real email delivery (production).

Requires EMAIL_PROVIDER=ses and a verified SES_FROM_EMAIL identity. Falls back to a
logged preview if SES is misconfigured, so a reminder run never crashes.
"""
from __future__ import annotations

import logging

from ..config import get_settings
from .local import LocalProvider

logger = logging.getLogger("visaroo.email")


class SesProvider:
    def __init__(self) -> None:
        import boto3  # imported lazily so the app runs without boto3 configured

        self.settings = get_settings()
        if not self.settings.ses_from_email:
            raise RuntimeError("EMAIL_PROVIDER=ses requires SES_FROM_EMAIL to be set.")
        self._client = boto3.client("ses", region_name=self.settings.aws_region)
        self._fallback = LocalProvider()

    def send(self, to: str, subject: str, body: str) -> None:
        try:
            self._client.send_email(
                Source=self.settings.ses_from_email,
                Destination={"ToAddresses": [to]},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {"Text": {"Data": body}},
                },
            )
        except Exception as exc:  # noqa: BLE001 - degrade gracefully
            logger.warning("SES send failed, logging preview instead: %s", exc)
            self._fallback.send(to, subject, body)
