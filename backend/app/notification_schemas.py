"""Schemas for in-app notifications.

Notifications are generated server-side at the community write sites; there is no public
create endpoint. The client only lists them and marks them read.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: str
    type: str
    actor: str
    message: str
    postId: int | None
    answerId: int | None
    read: bool
    createdAt: datetime


class UnreadCountOut(BaseModel):
    unread: int
