"""Creator feed routes (spec .kiro/specs/creator-feed/).

Reference implementation of the Node/DynamoDB/EventBridge/Knowledge-Base design on the
existing FastAPI stack. Routes live under ``/creator-posts`` to avoid colliding with the
community Q&A ``/posts`` routes. The source matcher runs synchronously after save here
(the design's async EventBridge→Lambda); the frontend still polls as specified.

Confidence scores are stored for debugging but NEVER returned to the client
(steering/creator-feed.md).
"""
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai.provider import SourceCandidate, get_provider
from ..creator_post_schemas import CreatorPostCreate, CreatorPostOut
from ..database import get_db
from ..deps import get_current_user
from ..models import CreatorPost, NewsItem, Profile, User

router = APIRouter(prefix="/creator-posts", tags=["creator-feed"])


def _to_out(p: CreatorPost) -> CreatorPostOut:
    """Serialize a post. Deliberately omits match_confidence_score (steering rule)."""
    return CreatorPostOut(
        id=p.id,
        creatorId=p.creator_id,
        creatorDisplayName=p.creator_display_name,
        headline=p.headline,
        body=p.body,
        visaTypeTags=json.loads(p.visa_type_tags) if p.visa_type_tags else [],
        statusLabel=p.status_label,
        sourceUrl=p.source_url,
        sourceLabel=p.source_label,
        effectiveDate=p.effective_date,
        expiryDate=p.expiry_date,
        postedAt=p.posted_at,
        updatedAt=p.updated_at,
        matchStatus=p.match_status,
        matchedDocumentTitle=p.matched_document_title,
        matchedDocumentUrl=p.matched_document_url,
    )


def _candidates(db: Session, limit: int = 100) -> list[SourceCandidate]:
    """Official documents to match against — the real NewsItems we already ingested."""
    rows = db.execute(select(NewsItem).limit(limit)).scalars().all()
    return [SourceCandidate(title=n.title, url=n.url, text=n.summary) for n in rows]


def _run_matcher(db: Session, post: CreatorPost) -> None:
    """Run the official-source matcher and persist the result on the post."""
    match = get_provider().match_post(post.headline, post.body, _candidates(db))
    post.match_confidence_score = match.score  # stored, never serialized
    if match.matched:
        post.match_status = "matched"
        post.matched_document_title = match.title
        post.matched_document_url = match.url
    else:
        post.match_status = "no_match"
        post.matched_document_title = None
        post.matched_document_url = None


def _creator_name(db: Session, user: User) -> str:
    profile = db.get(Profile, user.id)
    if profile and profile.creator_display_name:
        return profile.creator_display_name
    return user.username


def _matches_visa(tags: list[str], visa_type: str) -> bool:
    return "ALL" in tags or visa_type in tags


# ------------------------------- routes ------------------------------

@router.get("", response_model=list[CreatorPostOut])
def list_posts(
    visaType: str | None = Query(default=None),
    statusLabel: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[CreatorPostOut]:
    rows = (
        db.execute(
            select(CreatorPost)
            .where(CreatorPost.deleted.is_(False))
            .order_by(CreatorPost.posted_at.desc())
        )
        .scalars()
        .all()
    )
    out = []
    for p in rows:
        if statusLabel and p.status_label != statusLabel:
            continue
        if visaType and visaType != "ALL":
            if not _matches_visa(json.loads(p.visa_type_tags or "[]"), visaType):
                continue
        out.append(_to_out(p))
    return out


@router.get("/{post_id}", response_model=CreatorPostOut)
def get_post(post_id: str, db: Session = Depends(get_db)) -> CreatorPostOut:
    p = db.get(CreatorPost, post_id)
    if p is None or p.deleted:
        raise HTTPException(status_code=404, detail="Post not found")
    return _to_out(p)


@router.post("", response_model=CreatorPostOut, status_code=201)
def create_post(
    payload: CreatorPostCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CreatorPostOut:
    if user.role not in ("creator", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Verified Creators or Admins can post to the feed",
        )
    post = CreatorPost(
        id=str(uuid.uuid4()),
        creator_id=user.id,
        creator_display_name=_creator_name(db, user),
        headline=payload.headline,
        body=payload.body,
        visa_type_tags=json.dumps(payload.visaTypeTags),
        status_label=payload.statusLabel,
        source_url=payload.sourceUrl,
        source_label=payload.sourceLabel,
        effective_date=payload.effectiveDate,
        expiry_date=payload.expiryDate,
        match_status="pending",
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    # Run the matcher (sync here; async EventBridge→Lambda in production).
    _run_matcher(db, post)
    db.commit()
    db.refresh(post)
    return _to_out(post)


@router.put("/{post_id}", response_model=CreatorPostOut)
def update_post(
    post_id: str,
    payload: CreatorPostCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CreatorPostOut:
    post = db.get(CreatorPost, post_id)
    if post is None or post.deleted:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.creator_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="You can only edit your own posts")

    post.headline = payload.headline
    post.body = payload.body
    post.visa_type_tags = json.dumps(payload.visaTypeTags)
    post.status_label = payload.statusLabel
    post.source_url = payload.sourceUrl
    post.source_label = payload.sourceLabel
    post.effective_date = payload.effectiveDate
    post.expiry_date = payload.expiryDate
    post.match_status = "pending"
    db.commit()
    _run_matcher(db, post)  # edit re-triggers matching (REQ-7)
    db.commit()
    db.refresh(post)
    return _to_out(post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from fastapi import Response

    post = db.get(CreatorPost, post_id)
    if post is None or post.deleted:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.creator_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="You can only delete your own posts")
    post.deleted = True  # soft delete (REQ-7)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
