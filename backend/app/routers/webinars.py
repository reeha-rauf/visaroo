"""Webinars feature routes (spec .kiro/specs/webinars/).

Reference implementation of the design's Node/DynamoDB/Cognito webinar handler on the
existing FastAPI stack. Verified-Creator/Admin "Cognito groups" are represented by the
``User.role`` field (``creator`` | ``admin``). GET routes are public; POST/DELETE require
the right role.
"""
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User, Webinar
from ..webinar_schemas import WebinarCreate, WebinarOut

router = APIRouter(prefix="/webinars", tags=["webinars"])


# ------------------------------ helpers ------------------------------

def _to_out(w: Webinar) -> WebinarOut:
    return WebinarOut(
        id=w.id,
        title=w.title,
        hostName=w.host_name,
        hostType=w.host_type,
        postedBy=w.posted_by,
        startDateUtc=w.start_date_utc,
        durationMinutes=w.duration_minutes,
        visaTypeTags=json.loads(w.visa_type_tags) if w.visa_type_tags else [],
        description=w.description,
        registrationUrl=w.registration_url,
        speakerBio=w.speaker_bio,
        relatedResources=json.loads(w.related_resources) if w.related_resources else None,
        createdAt=w.created_at,
        updatedAt=w.updated_at,
    )


def _parse_utc(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def _matches_visa(tags: list[str], visa_type: str) -> bool:
    """A webinar matches when it carries the visa type or the catch-all ALL tag."""
    return "ALL" in tags or visa_type in tags


def _load_filtered(
    db: Session, visa_type: str | None, include_past: bool
) -> list[Webinar]:
    now = datetime.now(timezone.utc)
    rows = db.execute(select(Webinar)).scalars().all()
    out: list[Webinar] = []
    for w in rows:
        start = _parse_utc(w.start_date_utc)
        is_past = start < now
        if is_past and not include_past:
            continue
        if visa_type and visa_type != "ALL":
            if not _matches_visa(json.loads(w.visa_type_tags or "[]"), visa_type):
                continue
        out.append(w)
    # Upcoming ascending; past descending (REQ-1).
    out.sort(key=lambda w: w.start_date_utc, reverse=include_past)
    return out


# ------------------------------- routes ------------------------------

@router.get("", response_model=list[WebinarOut])
def list_webinars(
    visaType: str | None = Query(default=None),
    includePast: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[WebinarOut]:
    return [_to_out(w) for w in _load_filtered(db, visaType, includePast)]


@router.get("/{webinar_id}", response_model=WebinarOut)
def get_webinar(webinar_id: str, db: Session = Depends(get_db)) -> WebinarOut:
    w = db.get(Webinar, webinar_id)
    if w is None:
        raise HTTPException(status_code=404, detail="Webinar not found")
    return _to_out(w)


@router.post("", response_model=WebinarOut, status_code=201)
def create_webinar(
    payload: WebinarCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WebinarOut:
    if user.role not in ("creator", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Verified Creators or Admins can post webinars",
        )
    w = Webinar(
        id=str(uuid.uuid4()),
        title=payload.title,
        host_name=payload.hostName,
        host_type=payload.hostType,
        posted_by=user.id,
        start_date_utc=payload.startDateUtc,
        duration_minutes=payload.durationMinutes,
        visa_type_tags=json.dumps(payload.visaTypeTags),
        description=payload.description,
        registration_url=payload.registrationUrl,
        speaker_bio=payload.speakerBio,
        related_resources=json.dumps(payload.relatedResources) if payload.relatedResources else None,
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return _to_out(w)


@router.delete("/{webinar_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webinar(
    webinar_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    w = db.get(Webinar, webinar_id)
    if w is None:
        raise HTTPException(status_code=404, detail="Webinar not found")
    if user.role != "admin" and w.posted_by != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own webinars",
        )
    db.delete(w)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
