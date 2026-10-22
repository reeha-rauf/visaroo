"""Local email provider — logs a preview instead of sending (default)."""
from __future__ import annotations

import logging

logger = logging.getLogger("visaroo.email")


class LocalProvider:
    def send(self, to: str, subject: str, body: str) -> None:
        logger.info(
            "[email preview] to=%s subject=%s\n%s\n", to, subject, body
        )
        # Also print so it's visible when running the reminder script directly.
        print(f"\n--- EMAIL PREVIEW ---\nTo: {to}\nSubject: {subject}\n\n{body}\n---------------------\n")
