"""Persistent countdown routes (deadline-tracker feature).

A countdown is a user-owned, pinned deadline the user wants to keep visible across the
app. Owner-scoped CRUD, mirroring the creator-feed router conventions.

Safety: the server stores the target date verbatim and NEVER computes or adjusts it
(steering/deadline-tracker.md — all deadline math is client-side pure functions). The
"days remaining" shown to the user is derived on the client on every render.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..countdown_schemas import CountdownCreate, CountdownOut
from ..database import get_db
from ..deps import get_current_user
from ..models import Countdown, User

router = APIRouter(prefix="/countdowns", tags=["countdowns"])

# A user can't pin an unbounded number of countdowns.
MAX_COUNTDOWNS = 20


def _to_out(c: Countdown) -> CountdownOut:
    return CountdownOut(
        id=c.id,
        title=c.title,
        targetDate=c.target_date,
        sourceDeadlineId=c.source_deadline_id,
        note=c.note,
        createdAt=c.created_at,
        updatedAt=c.updated_at,
    )


def _owned(db: Session, countdown_id: str, user: User) -> Countdown:
    c = db.get(Countdown, countdown_id)
    if c is None or c.user_id != user.id:
        raise HTTPException(status_code=404, detail="Countdown not found")
    return c


@router.get("", response_model=list[CountdownOut])
def list_countdowns(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[CountdownOut]:
    """Return the current user's countdowns, soonest target date first."""
    rows = db.execute(
        select(Countdown).where(Countdown.user_id == user.id)
    ).scalars().all()
    rows.sort(key=lambda c: c.target_date)
    return [_to_out(c) for c in rows]


@router.post("", response_model=CountdownOut, status_code=status.HTTP_201_CREATED)
def create_countdown(
    payload: CountdownCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CountdownOut:
    count = db.execute(
        select(Countdown).where(Countdown.user_id == user.id)
    ).scalars().all()
    if len(count) >= MAX_COUNTDOWNS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You can pin at most {MAX_COUNTDOWNS} countdowns.",
        )
    # If this deadline is already pinned, update it instead of duplicating.
    if payload.sourceDeadlineId:
        existing = db.execute(
            select(Countdown).where(
                Countdown.user_id == user.id,
                Countdown.source_deadline_id == payload.sourceDeadlineId,
            )
        ).scalar_one_or_none()
        if existing is not None:
            existing.title = payload.title
            existing.target_date = payload.targetDate
            existing.note = payload.note
            db.commit()
            db.refresh(existing)
            return _to_out(existing)

    c = Countdown(
        id=str(uuid.uuid4()),
        user_id=user.id,
        title=payload.title,
        target_date=payload.targetDate,
        source_deadline_id=payload.sourceDeadlineId,
        note=payload.note,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return _to_out(c)


@router.put("/{countdown_id}", response_model=CountdownOut)
def update_countdown(
    countdown_id: str,
    payload: CountdownCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CountdownOut:
    c = _owned(db, countdown_id, user)
    c.title = payload.title
    c.target_date = payload.targetDate
    c.source_deadline_id = payload.sourceDeadlineId
    c.note = payload.note
    db.commit()
    db.refresh(c)
    return _to_out(c)


@router.delete("/{countdown_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_countdown(
    countdown_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    c = _owned(db, countdown_id, user)
    db.delete(c)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
