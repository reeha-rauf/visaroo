"""Server-side deadline computation for the .ics export and reminder checker.

Mirrors the pure formulas in frontend/src/utils/deadlineCalculations.ts and the
definitions in deadlineDefinitions.ts. Per steering/deadline-tracker.md, these are
plain deterministic functions — no LLM. The frontend remains the primary calculator for
the UI (REQ-NF-3); this exists so the server can emit calendars and reminder emails.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta

from .models import Profile

# deadlineId -> (label, applicable visa types, official url)
_META = {
    "opt_window_open": ("OPT application window opens", {"F-1"}),
    "opt_deadline": ("OPT application deadline", {"F-1"}),
    "ead_expiry": ("EAD card expiry", {"OPT", "STEM_OPT"}),
    "stem_window_open": ("STEM OPT filing window opens", {"OPT", "STEM_OPT"}),
    "stem_deadline": ("STEM OPT filing deadline", {"OPT", "STEM_OPT"}),
    "i20_expiry": ("I-20 expiry", {"F-1", "OPT", "STEM_OPT"}),
    "grace_period_end": ("Grace period end", {"F-1", "OPT", "STEM_OPT"}),
    "sevp_reporting": ("SEVP reporting deadline", {"F-1", "OPT", "STEM_OPT"}),
    "i94_expiry": ("I-94 expiry", {"H-1B"}),
    "h1b_petition_expiry": ("H-1B petition expiry", {"H-1B"}),
    "cap_gap_end": ("Cap-gap coverage end", {"H-1B"}),
    "visa_stamp_expiry": ("Visa stamp expiry", {"F-1", "OPT", "STEM_OPT", "H-1B", "H-4", "J-1", "Other"}),
    "passport_expiry": ("Passport expiry", {"F-1", "OPT", "STEM_OPT", "H-1B", "H-4", "J-1", "Other"}),
    "renewal_reminder": ("Renewal reminder", {"F-1", "OPT", "STEM_OPT", "H-1B", "H-4", "J-1", "Other"}),
}


@dataclass
class ServerDeadline:
    id: str
    label: str
    date: date
    days_remaining: int


def _parse(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _shift(value: str | None, days: int) -> date | None:
    d = _parse(value)
    return d + timedelta(days=days) if d else None


def _raw_date(profile: Profile, deadline_id: str) -> date | None:
    """Compute a single deadline's date from the profile (no overrides applied)."""
    p = profile
    if deadline_id == "opt_window_open":
        return _shift(p.program_end_date, -90)
    if deadline_id == "opt_deadline":
        return _shift(p.program_end_date, -60)
    if deadline_id == "ead_expiry":
        return _parse(p.ead_end_date)
    if deadline_id == "stem_window_open":
        return _shift(p.ead_end_date, -90)
    if deadline_id == "stem_deadline":
        return _shift(p.ead_end_date, -60)
    if deadline_id == "i20_expiry":
        return _parse(p.i20_expiry_date)
    if deadline_id == "grace_period_end":
        if p.grace_period_end_date:
            return _parse(p.grace_period_end_date)
        if p.visa_type == "STEM_OPT":
            return _shift(p.ead_end_date, 60)
        return _shift(p.program_end_date, 60)
    if deadline_id == "sevp_reporting":
        return _shift(p.last_reportable_event_date, 10)
    if deadline_id == "i94_expiry":
        return _parse(p.i94_expiry_date)
    if deadline_id == "h1b_petition_expiry":
        return _parse(p.h1b_petition_expiry)
    if deadline_id == "cap_gap_end":
        return _parse(p.cap_gap_end)
    if deadline_id == "visa_stamp_expiry":
        return _parse(p.visa_stamp_expiry)
    if deadline_id == "passport_expiry":
        return _parse(p.passport_expiry)
    if deadline_id == "renewal_reminder":
        return _parse(p.next_renewal_reminder)
    return None


def compute_server_deadlines(
    profile: Profile, today: date | None = None
) -> list[ServerDeadline]:
    """Return applicable, non-null, non-expired deadlines for the profile.

    Overrides in ``profile.deadline_overrides`` win over computed values (REQ-7).
    Expired and not-applicable deadlines are excluded (used for .ics + reminders).
    """
    today = today or date.today()
    overrides: dict[str, str] = {}
    if profile.deadline_overrides:
        try:
            overrides = json.loads(profile.deadline_overrides)
        except (ValueError, TypeError):
            overrides = {}

    out: list[ServerDeadline] = []
    for deadline_id, (label, visa_types) in _META.items():
        if profile.visa_type not in visa_types:
            continue
        d = _parse(overrides.get(deadline_id)) or _raw_date(profile, deadline_id)
        if d is None:
            continue
        days = (d - today).days
        if days < 0:
            continue  # exclude expired from calendar/reminders
        out.append(ServerDeadline(id=deadline_id, label=label, date=d, days_remaining=days))

    out.sort(key=lambda x: x.date)
    return out
