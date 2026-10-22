"""Voting on posts and answers (one vote per user per item; re-voting updates)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Answer, Post, User, Vote
from ..schemas import VoteRequest
from ..services.notifications import notify

router = APIRouter(tags=["votes"])


@router.post("/votes")
def cast_vote(
    payload: VoteRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if payload.target_type not in ("post", "answer"):
        raise HTTPException(status_code=400, detail="Invalid target_type")
    if payload.value not in (-1, 1):
        raise HTTPException(status_code=400, detail="Vote value must be +1 or -1")

    target_model = Post if payload.target_type == "post" else Answer
    target = db.get(target_model, payload.target_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Target not found")

    existing = db.execute(
        select(Vote).where(
            Vote.user_id == user.id,
            Vote.target_type == payload.target_type,
            Vote.target_id == payload.target_id,
        )
    ).scalar_one_or_none()

    is_new_upvote = existing is None and payload.value == 1

    if existing is None:
        db.add(
            Vote(
                user_id=user.id,
                target_type=payload.target_type,
                target_id=payload.target_id,
                value=payload.value,
            )
        )
    elif existing.value == payload.value:
        # Toggling the same vote removes it.
        db.delete(existing)
    else:
        existing.value = payload.value

    # Notify the target's author only on a brand-new upvote (not toggles/downvotes),
    # and never for self-votes. Votes are anonymous, so the actor stays "Someone".
    if is_new_upvote:
        post_id = target.id if payload.target_type == "post" else target.post_id
        if payload.target_type == "post":
            message = f'upvoted your question "{_truncate(target.title)}"'
        else:
            message = "upvoted your answer"
        notify(
            db,
            recipient_id=target.author_id,
            actor_id=user.id,
            actor_name="Someone",
            actor_is_anonymous=False,
            type=f"{payload.target_type}_upvote",
            message=message,
            post_id=post_id,
            answer_id=target.id if payload.target_type == "answer" else None,
        )

    db.commit()
    return {"ok": True}


def _truncate(text: str, limit: int = 60) -> str:
    """Shorten a title for a notification message."""
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"
