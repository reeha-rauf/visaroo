"""Domain constants and Pydantic schemas for the webinars feature."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Visa type tags a webinar can target (includes the catch-all "ALL").
VISA_TYPE_TAGS = ["F-1", "OPT", "STEM_OPT", "H-1B", "H-4", "J-1", "ALL"]
HOST_TYPES = ["official", "verified_creator", "community"]


class WebinarCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=300)
    hostName: str = Field(min_length=1, max_length=200)
    hostType: str = "community"
    startDateUtc: str  # ISO 8601 UTC
    durationMinutes: int | None = Field(default=None, ge=1, le=1440)
    visaTypeTags: list[str] = Field(min_length=1)
    description: str = Field(max_length=280)
    registrationUrl: str = Field(min_length=1, max_length=800)
    speakerBio: str | None = None
    relatedResources: list[str] | None = None

    @field_validator("hostType")
    @classmethod
    def _host_type(cls, v: str) -> str:
        if v not in HOST_TYPES:
            raise ValueError(f"hostType must be one of {HOST_TYPES}")
        return v

    @field_validator("visaTypeTags")
    @classmethod
    def _tags(cls, v: list[str]) -> list[str]:
        bad = [t for t in v if t not in VISA_TYPE_TAGS]
        if bad:
            raise ValueError(f"invalid visa type tags {bad}; allowed: {VISA_TYPE_TAGS}")
        return v

    @field_validator("startDateUtc")
    @classmethod
    def _start(cls, v: str) -> str:
        # Accept ISO 8601; normalize a trailing Z to +00:00 for parsing.
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("startDateUtc must be an ISO 8601 datetime") from exc
        return v


class WebinarOut(BaseModel):
    id: str
    title: str
    hostName: str
    hostType: str
    postedBy: int | None
    startDateUtc: str
    durationMinutes: int | None
    visaTypeTags: list[str]
    description: str
    registrationUrl: str
    speakerBio: str | None
    relatedResources: list[str] | None
    createdAt: datetime
    updatedAt: datetime
