"""Email provider interface and factory.

Reminder emails flow through this interface so the app never depends directly on AWS.
Two implementations, selected by the ``EMAIL_PROVIDER`` env var:

* ``LocalProvider`` — prints a preview to the log (default, no AWS, safe for demos).
* ``SesProvider``   — real Amazon SES ``send_email`` via boto3 (production).
"""
from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from ..config import get_settings


class EmailProvider(Protocol):
    def send(self, to: str, subject: str, body: str) -> None:
        """Send (or preview) a plain-text email."""
        ...


@lru_cache
def get_email_provider() -> EmailProvider:
    settings = get_settings()
    if settings.email_provider.lower() == "ses":
        from .ses import SesProvider

        return SesProvider()
    from .local import LocalProvider

    return LocalProvider()
