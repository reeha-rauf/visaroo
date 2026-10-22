"""Response builders that enforce the anonymity rule in one place.

Author identity must never leak for anonymous posts/answers. These helpers are the
single source of truth for turning ORM objects into response schemas.
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Answer, Post, Vote
from .schemas import AnswerOut, PostDetailOut, PostOut

ANON = "Anonymous"


def _score(db: Session, target_type: str, target_id: int) -> int:
    total = db.execute(
        select(func.coalesce(func.sum(Vote.value), 0)).where(
            Vote.target_type == target_type, Vote.target_id == target_id
        )
    ).scalar_one()
    return int(total)


def answer_to_schema(db: Session, answer: Answer) -> AnswerOut:
    return AnswerOut(
        id=answer.id,
        body=answer.body,
        author=ANON if answer.is_anonymous else answer.author.username,
        is_best=answer.is_best,
        score=_score(db, "answer", answer.id),
        created_at=answer.created_at,
    )


def post_to_schema(db: Session, post: Post) -> PostOut:
    return PostOut(
        id=post.id,
        title=post.title,
        body=post.body,
        visa_category=post.visa_category,
        author=ANON if post.is_anonymous else post.author.username,
        gatekeeper_flag=post.gatekeeper_flag,
        score=_score(db, "post", post.id),
        answer_count=len(post.answers),
        created_at=post.created_at,
    )


def post_detail_to_schema(db: Session, post: Post) -> PostDetailOut:
    base = post_to_schema(db, post)
    answers = sorted(
        post.answers, key=lambda a: (not a.is_best, -_score(db, "answer", a.id))
    )
    return PostDetailOut(
        **base.model_dump(),
        answers=[answer_to_schema(db, a) for a in answers],
    )
