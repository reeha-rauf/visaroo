"""Community Q&A: posts, the gatekeeper preview, answers, and best-answer."""
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai.provider import get_provider
from ..config import VISA_CATEGORIES
from ..database import get_db
from ..deps import get_current_user
from ..models import Answer, Post, User
from ..schemas import (
    AnswerCreate,
    AnswerOut,
    ModerationOut,
    PostCreate,
    PostDetailOut,
    PostOut,
)
from ..serializers import (
    answer_to_schema,
    post_detail_to_schema,
    post_to_schema,
)
from ..services.notifications import notify

router = APIRouter(tags=["community"])


def _moderation_to_warning(result) -> str | None:
    """Build a soft-warn message (or None). Never blocks posting."""
    if result.harmful:
        return (
            "Heads up: this looks like it may touch on visa fraud or something not "
            "allowed. Please keep questions within the law. For official guidance, "
            "check with your DSO or an immigration attorney. You can still post."
        )
    if not result.relevant:
        return (
            "This doesn't look like it's about visas or immigration. You can still "
            "post, but you'll reach more people on-topic."
        )
    return None


def _flag(result) -> str | None:
    if result.harmful:
        return "harmful"
    if not result.relevant:
        return "off_topic"
    return None


def _truncate(text: str, limit: int = 60) -> str:
    """Shorten a title for use inside a notification message."""
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


@router.post("/posts/moderate", response_model=ModerationOut)
def preview_moderation(
    payload: PostCreate, _: User = Depends(get_current_user)
) -> ModerationOut:
    """Run the gatekeeper WITHOUT saving, so the UI can show suggestions (soft-warn)."""
    result = get_provider().moderate_post(payload.title, payload.body)
    return ModerationOut(
        relevant=result.relevant,
        reason=result.reason,
        suggested_category=result.suggested_category,
        suggested_title=result.suggested_title,
        harmful=result.harmful,
        warning=_moderation_to_warning(result),
    )


@router.post("/posts", response_model=PostOut, status_code=201)
def create_post(
    payload: PostCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostOut:
    provider = get_provider()
    result = provider.moderate_post(payload.title, payload.body)

    category = payload.visa_category
    if category not in VISA_CATEGORIES:
        category = result.suggested_category

    embedding = provider.embed_text(f"{payload.title}\n{payload.body}")

    post = Post(
        author_id=user.id,
        title=payload.title,
        body=payload.body,
        visa_category=category,
        is_anonymous=payload.is_anonymous,
        gatekeeper_flag=_flag(result),
        embedding=json.dumps(embedding),
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post_to_schema(db, post)


@router.get("/posts", response_model=list[PostOut])
def list_posts(
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[PostOut]:
    stmt = select(Post).order_by(Post.created_at.desc())
    if category and category in VISA_CATEGORIES:
        stmt = stmt.where(Post.visa_category == category)
    posts = db.execute(stmt).scalars().all()
    return [post_to_schema(db, p) for p in posts]


@router.get("/posts/{post_id}", response_model=PostDetailOut)
def get_post(post_id: int, db: Session = Depends(get_db)) -> PostDetailOut:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post_detail_to_schema(db, post)


@router.post("/posts/{post_id}/answers", response_model=AnswerOut, status_code=201)
def create_answer(
    post_id: int,
    payload: AnswerCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnswerOut:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    answer = Answer(
        post_id=post_id,
        author_id=user.id,
        body=payload.body,
        is_anonymous=payload.is_anonymous,
    )
    db.add(answer)
    db.flush()  # assign answer.id before building the notification

    # Notify the question's author that they got a new answer (skips self-answers).
    notify(
        db,
        recipient_id=post.author_id,
        actor_id=user.id,
        actor_name=user.username,
        actor_is_anonymous=payload.is_anonymous,
        type="new_answer",
        message=f'answered your question "{_truncate(post.title)}"',
        post_id=post.id,
        answer_id=answer.id,
    )

    db.commit()
    db.refresh(answer)
    return answer_to_schema(db, answer)


@router.post("/answers/{answer_id}/best", response_model=AnswerOut)
def mark_best(
    answer_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnswerOut:
    answer = db.get(Answer, answer_id)
    if answer is None:
        raise HTTPException(status_code=404, detail="Answer not found")
    post = db.get(Post, answer.post_id)
    if post.author_id != user.id:
        raise HTTPException(
            status_code=403, detail="Only the post author can mark a best answer"
        )
    # Exactly one best answer per post.
    for other in post.answers:
        other.is_best = other.id == answer_id

    # Notify the answer's author that their answer was marked best (skips self-mark).
    notify(
        db,
        recipient_id=answer.author_id,
        actor_id=user.id,
        actor_name=user.username,
        actor_is_anonymous=False,  # the post owner acts as themselves here
        type="best_answer",
        message=f'marked your answer as the best answer on "{_truncate(post.title)}"',
        post_id=post.id,
        answer_id=answer.id,
    )

    db.commit()
    db.refresh(answer)
    return answer_to_schema(db, answer)
