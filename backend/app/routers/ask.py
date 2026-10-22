"""Impact explainer / Ask routes (spec .kiro/specs/impact-explainer/).

Reference implementation of the design's streaming /ask Lambda on FastAPI (non-streaming
JSON here; streaming is the production target). Retrieves official docs (Bedrock KB when
configured, else the ingested NewsItem corpus), builds a derived personalization context
for logged-in users, and returns a grounded, cited answer.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai.provider import SourceCandidate, get_provider
from ..database import get_db
from ..deps import get_current_user_optional
from ..models import NewsItem, Profile, User
from ..personalization import build_personalization_context, context_to_prompt_block

router = APIRouter(prefix="/ask", tags=["impact-explainer"])

_DISCLAIMER = (
    "This is general information only — not legal advice. Always verify with your DSO "
    "or a qualified immigration attorney."
)


class AskTurn(BaseModel):
    question: str
    answer: str


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    history: list[AskTurn] = Field(default_factory=list)


class CitationOut(BaseModel):
    n: int
    title: str
    source: str
    url: str | None
    excerpt: str


class AskResponse(BaseModel):
    answer: str
    statusLabel: str
    citations: list[CitationOut]
    grounded: bool
    personalized: bool
    disclaimer: str = _DISCLAIMER


def _candidates(db: Session, limit: int = 50) -> list[SourceCandidate]:
    rows = db.execute(select(NewsItem).limit(limit)).scalars().all()
    return [SourceCandidate(title=n.title, url=n.url, text=n.summary) for n in rows]


@router.post("", response_model=AskResponse)
def ask(
    payload: AskRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
) -> AskResponse:
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Personalization: only for a logged-in user with a profile (derived facts only).
    context = ""
    personalized = False
    if user is not None:
        profile = db.get(Profile, user.id)
        if profile is not None:
            ctx = build_personalization_context(profile)
            context = context_to_prompt_block(ctx) or ""
            personalized = bool(context)

    history = [{"question": t.question, "answer": t.answer} for t in payload.history[-3:]]

    result = get_provider().answer_impact(
        payload.question, context, history, _candidates(db)
    )

    return AskResponse(
        answer=result.answer,
        statusLabel=result.status_label,
        citations=[
            CitationOut(n=c.n, title=c.title, source=c.source, url=c.url, excerpt=c.excerpt)
            for c in result.citations
        ],
        grounded=result.grounded,
        personalized=personalized,
    )
