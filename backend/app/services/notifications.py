"""Notification generation helper.

Called synchronously from the community write sites (answers, best-answer, votes) to
record an in-app notification for the content owner. In production this would be an
EventBridge→Lambda fan-out; here it's a direct DB insert in the same transaction.

Rules (steering):
- Never leak an anonymous actor's identity — pass ``actor_is_anonymous=True`` and the
  actor is recorded as "Anonymous".
- Never notify a user about their own action (caller passes recipient != actor).
"""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from ..models import Notification

ANON = "Anonymous"


def notify(
    db: Session,
    *,
    recipient_id: int,
    actor_id: int,
    actor_name: str,
    actor_is_anonymous: bool,
    type: str,
    message: str,
    post_id: int | None = None,
    answer_id: int | None = None,
) -> Notification | None:
    """Create a notification row (not committed — the caller commits).

    Returns None (no-op) when the recipient is the actor, so users never get notified
    about their own activity.
    """
    if recipient_id == actor_id:
        return None

    actor = ANON if actor_is_anonymous else actor_name
    n = Notification(
        id=str(uuid.uuid4()),
        recipient_id=recipient_id,
        type=type,
        actor=actor,
        message=message,
        post_id=post_id,
        answer_id=answer_id,
    )
    db.add(n)
    return n
