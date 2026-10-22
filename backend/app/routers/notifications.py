"""In-app notification routes: list, unread count, and mark-read.

Read-only + mark-read for the authenticated recipient. Notifications are created
server-side at the community write sites (see services/notifications.py).
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Notification, User
from ..notification_schemas import NotificationOut, UnreadCountOut

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Cap how many we return / retain per user in the list view.
LIST_LIMIT = 50


def _to_out(n: Notification) -> NotificationOut:
    return NotificationOut(
        id=n.id,
        type=n.type,
        actor=n.actor,
        message=n.message,
        postId=n.post_id,
        answerId=n.answer_id,
        read=n.read,
        createdAt=n.created_at,
    )


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    unread: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[NotificationOut]:
    """Return the user's notifications, newest first. ``?unread=true`` filters to unread."""
    stmt = (
        select(Notification)
        .where(Notification.recipient_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(LIST_LIMIT)
    )
    if unread:
        stmt = stmt.where(Notification.read.is_(False))
    rows = db.execute(stmt).scalars().all()
    return [_to_out(n) for n in rows]


@router.get("/unread-count", response_model=UnreadCountOut)
def unread_count(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> UnreadCountOut:
    total = db.execute(
        select(func.count(Notification.id)).where(
            Notification.recipient_id == user.id, Notification.read.is_(False)
        )
    ).scalar_one()
    return UnreadCountOut(unread=int(total))


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationOut:
    n = db.get(Notification, notification_id)
    if n is None or n.recipient_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.read = True
    db.commit()
    db.refresh(n)
    return _to_out(n)


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_read(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    rows = db.execute(
        select(Notification).where(
            Notification.recipient_id == user.id, Notification.read.is_(False)
        )
    ).scalars().all()
    for n in rows:
        n.read = True
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
