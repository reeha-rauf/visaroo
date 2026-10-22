"""Computed deadline estimates derived from a profile's stored base dates.

Formulas from .kiro/specs/profile/design.md ("Computed Dates"). These are ESTIMATES
labelled as computed in the UI, never persisted (avoids drift — see steering/profile.md).

Cap note: design.md's table lists "OPT days remaining = 365 − used", but that contradicts
REQ-3 ("0–150 ... days remaining against the applicable cap") and the OPT unemployment
rule. We follow the requirements: OPT cap = 90, STEM OPT cap = 150.
"""
from __future__ import annotations

from datetime import date, timedelta

from .profile_domain import OPT_UNEMPLOYMENT_CAP, STEM_OPT_UNEMPLOYMENT_CAP
from .profile_schemas import ComputedDates


def _parse(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _shift(d: date | None, days: int) -> str | None:
    return (d + timedelta(days=days)).isoformat() if d else None


def compute_dates(
    *,
    visa_type: str,
    program_end_date: str | None,
    ead_end_date: str | None,
    i94_expiry_date: str | None,
    grace_period_end_date: str | None,
    unemployment_days_used: int | None,
) -> ComputedDates:
    """Return the computed estimate bundle for a profile.

    Any field whose source date is missing is returned as None (REQ-NF-3: missing
    optional fields must not cause errors).
    """
    program_end = _parse(program_end_date)
    ead_end = _parse(ead_end_date)
    i94 = _parse(i94_expiry_date)

    # OPT application window: opens 90 days before program end, deadline 60 days before.
    opt_opens = _shift(program_end, -90)
    opt_deadline = _shift(program_end, -60)

    # STEM OPT filing window: 90–60 days before the OPT EAD expiry.
    stem_start = _shift(ead_end, -90)
    stem_end = _shift(ead_end, -60)

    # Grace period end: user override wins; else F-1 = program end + 60,
    # H-1B = I-94 expiry + 60.
    if grace_period_end_date:
        grace_end = grace_period_end_date
    elif visa_type == "F-1":
        grace_end = _shift(program_end, 60)
    elif visa_type == "H-1B":
        grace_end = _shift(i94, 60)
    else:
        grace_end = None

    # Unemployment days remaining against the applicable cap.
    cap: int | None = None
    remaining: int | None = None
    if visa_type in ("OPT", "STEM_OPT"):
        cap = STEM_OPT_UNEMPLOYMENT_CAP if visa_type == "STEM_OPT" else OPT_UNEMPLOYMENT_CAP
        used = unemployment_days_used or 0
        remaining = max(cap - used, 0)

    return ComputedDates(
        optApplicationWindowOpens=opt_opens,
        optApplicationDeadline=opt_deadline,
        stemFilingWindowStart=stem_start,
        stemFilingWindowEnd=stem_end,
        gracePeriodEnd=grace_end,
        unemploymentDaysRemaining=remaining,
        unemploymentCap=cap,
    )
