"""Current-user content routes: the authenticated user's own posts and answers.

Used by the "My posts" view under the profile. Everything is scoped to the token user
via ``get_current_user`` — a client-supplied id is never trusted.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Answer, Post, User, Vote
from ..schemas import MyAnswerOut, MyPostOut

router = APIRouter(prefix="/me", tags=["me"])


def _score(db: Session, target_type: str, target_id: int) -> int:
    total = db.execute(
        select(func.coalesce(func.sum(Vote.value), 0)).where(
            Vote.target_type == target_type, Vote.target_id == target_id
        )
    ).scalar_one()
    return int(total)


@router.get("/posts", response_model=list[MyPostOut])
def my_posts(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[MyPostOut]:
    """The current user's questions, newest first."""
    rows = db.execute(
        select(Post)
        .where(Post.author_id == user.id)
        .order_by(Post.created_at.desc())
    ).scalars().all()
    return [
        MyPostOut(
            id=p.id,
            title=p.title,
            visa_category=p.visa_category,
            is_anonymous=p.is_anonymous,
            score=_score(db, "post", p.id),
            answer_count=len(p.answers),
            created_at=p.created_at,
        )
        for p in rows
    ]


@router.get("/answers", response_model=list[MyAnswerOut])
def my_answers(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[MyAnswerOut]:
    """The current user's answers, newest first, each linked to its parent question."""
    rows = db.execute(
        select(Answer)
        .where(Answer.author_id == user.id)
        .order_by(Answer.created_at.desc())
    ).scalars().all()
    return [
        MyAnswerOut(
            id=a.id,
            body=a.body,
            is_anonymous=a.is_anonymous,
            is_best=a.is_best,
            score=_score(db, "answer", a.id),
            created_at=a.created_at,
            post_id=a.post_id,
            post_title=a.post.title,
        )
        for a in rows
    ]
