"""Schemas for persistent user countdowns (deadline-tracker feature).

A countdown stores only a label + a target ISO date (optionally the source deadline id
it was pinned from). The server never computes or adjusts the date — per
steering/deadline-tracker.md, all deadline math is client-side. These schemas just
validate and carry the stored value.
"""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _require_iso(v: str) -> str:
    try:
        date.fromisoformat(v)
    except ValueError as exc:
        raise ValueError(f"targetDate must be ISO-8601 date (YYYY-MM-DD): {v}") from exc
    return v


class CountdownCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=120)
    targetDate: str = Field(min_length=1, max_length=10)
    sourceDeadlineId: str | None = Field(default=None, max_length=40)
    note: str | None = Field(default=None, max_length=300)

    @field_validator("targetDate")
    @classmethod
    def _target(cls, v: str) -> str:
        return _require_iso(v)


class CountdownOut(BaseModel):
    id: str
    title: str
    targetDate: str
    sourceDeadlineId: str | None
    note: str | None
    createdAt: datetime
    updatedAt: datetime
