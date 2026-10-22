"""AI Search: semantic ranking of community posts + summary-first response."""
import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai.provider import PostLite, get_provider
from ..database import get_db
from ..deps import get_current_user_optional
from ..models import Post, Profile, User
from ..personalization import build_personalization_context, context_to_prompt_block
from ..schemas import SearchRequest, SearchResponse, SearchResultPost
from ..serializers import _score

router = APIRouter(tags=["search"])

_DISCLAIMER = (
    "This is general information from community members, not legal advice. "
    "Verify with your DSO or an immigration attorney."
)
_TOP_K = 5
_MIN_SIMILARITY = 0.05


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


@router.post("/search", response_model=SearchResponse)
def search(
    payload: SearchRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
) -> SearchResponse:
    provider = get_provider()
    query_vec = provider.embed_text(payload.query)

    posts = db.execute(select(Post)).scalars().all()
    scored: list[tuple[float, Post]] = []
    for post in posts:
        if not post.embedding:
            continue
        sim = _cosine(query_vec, json.loads(post.embedding))
        if sim >= _MIN_SIMILARITY:
            scored.append((sim, post))

    scored.sort(key=lambda t: t[0], reverse=True)
    top = scored[:_TOP_K]

    # Build a derived, non-identifying personalization block for logged-in users with a
    # profile. Only counts/booleans/enums are included (see steering/profile.md).
    personalization: str | None = None
    if user is not None:
        profile = db.get(Profile, user.id)
        if profile is not None:
            ctx = build_personalization_context(profile)
            personalization = context_to_prompt_block(ctx) or None

    summary_obj = provider.summarize_search(
        payload.query,
        [PostLite(id=p.id, title=p.title, body=p.body) for _, p in top],
        personalization,
    )

    results = [
        SearchResultPost(
            id=p.id,
            title=p.title,
            snippet=(p.body[:200] + "...") if len(p.body) > 200 else p.body,
            visa_category=p.visa_category,
            score=_score(db, "post", p.id),
            similarity=round(sim, 3),
        )
        for sim, p in top
    ]

    return SearchResponse(
        query=payload.query,
        summary=summary_obj.summary,
        grounded=summary_obj.grounded,
        used_post_ids=summary_obj.used_post_ids,
        results=results,
        disclaimer=_DISCLAIMER,
        personalized=personalization is not None,
    )
