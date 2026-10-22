"""Schemas for the creator feed (spec .kiro/specs/creator-feed/).

The confidence score is intentionally absent from ``CreatorPostOut`` — it is stored for
debugging but never returned to the client (steering/creator-feed.md).
"""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

VISA_TYPE_TAGS = ["F-1", "OPT", "STEM_OPT", "H-1B", "H-4", "J-1", "ALL"]
POST_STATUS_LABELS = ["rumor_reported", "proposed", "final", "in_effect"]

MATCH_THRESHOLD = 0.75  # hardcoded per steering/creator-feed.md


def _opt_iso(v: str | None) -> str | None:
    if v is None or v == "":
        return None
    try:
        date.fromisoformat(v)
    except ValueError as exc:
        raise ValueError(f"must be ISO-8601 date (YYYY-MM-DD): {v}") from exc
    return v


class CreatorPostCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    headline: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1, max_length=1000)
    visaTypeTags: list[str] = Field(min_length=1)
    statusLabel: str
    sourceUrl: str = Field(min_length=1, max_length=800)
    sourceLabel: str = Field(min_length=1, max_length=120)
    effectiveDate: str | None = None
    expiryDate: str | None = None

    @field_validator("visaTypeTags")
    @classmethod
    def _tags(cls, v: list[str]) -> list[str]:
        bad = [t for t in v if t not in VISA_TYPE_TAGS]
        if bad:
            raise ValueError(f"invalid visa type tags {bad}; allowed: {VISA_TYPE_TAGS}")
        return v

    @field_validator("statusLabel")
    @classmethod
    def _status(cls, v: str) -> str:
        if v not in POST_STATUS_LABELS:
            raise ValueError(f"statusLabel must be one of {POST_STATUS_LABELS}")
        return v

    @field_validator("effectiveDate", "expiryDate")
    @classmethod
    def _dates(cls, v: str | None) -> str | None:
        return _opt_iso(v)


class CreatorPostOut(BaseModel):
    id: str
    creatorId: int
    creatorDisplayName: str
    headline: str
    body: str
    visaTypeTags: list[str]
    statusLabel: str
    sourceUrl: str
    sourceLabel: str
    effectiveDate: str | None
    expiryDate: str | None
    postedAt: datetime
    updatedAt: datetime
    matchStatus: str
    matchedDocumentTitle: str | None
    matchedDocumentUrl: str | None
    # NOTE: matchConfidenceScore is deliberately NOT included (steering rule).
