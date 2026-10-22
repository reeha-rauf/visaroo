"""News feed routes: personalized feed + manual refresh (ingest trigger)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import VISA_CATEGORIES
from ..database import get_db
from ..deps import get_current_user_optional
from ..models import NewsItem, User
from ..schemas import NewsOut
from ..services.news_ingest import ingest

router = APIRouter(prefix="/news", tags=["news"])


@router.get("", response_model=list[NewsOut])
def get_news(
    category: str | None = Query(default=None),
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> list[NewsItem]:
    """Return news, ranked so the user's visa category appears first.

    An explicit ``category`` query param overrides the user's profile category.
    """
    preferred = category or (user.visa_category if user else None)
    items = db.execute(
        select(NewsItem).order_by(NewsItem.published_at.desc().nullslast())
    ).scalars().all()

    if preferred and preferred in VISA_CATEGORIES:
        items = sorted(items, key=lambda n: n.visa_category != preferred)
    return items


@router.post("/refresh")
def refresh_news(db: Session = Depends(get_db)) -> dict:
    """Trigger ingestion. Called by the Kiro hook / EventBridge, or manually in demos."""
    return ingest(db)
