"""Deadline reminder checker (spec TASK-9).

For each user whose profile has email alerts enabled, compute their upcoming deadlines
and send a reminder when a deadline's days-remaining matches one of the user's configured
lead-time thresholds (90/60/30/14/7). Each (user, deadline, threshold) fires at most once
thanks to the ReminderSent dedup table.

Email goes through the EmailProvider abstraction (local preview or Amazon SES). This is
the reference implementation of the design's EventBridge-scheduled reminder Lambda; here
it runs as a callable function (via scripts/send_reminders.py or POST /deadlines/remind).
"""
from __future__ import annotations

import json
import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..deadline_calc import compute_server_deadlines
from ..email.provider import get_email_provider
from ..models import Profile, ReminderSent, User

logger = logging.getLogger("visaroo.reminders")

_DISCLAIMER = (
    "Visaroo shares general information only — not legal advice. "
    "Always verify with your DSO or an immigration attorney."
)


def _notifications(profile: Profile) -> dict:
    if not profile.notifications:
        return {}
    try:
        return json.loads(profile.notifications)
    except (ValueError, TypeError):
        return {}


def _email_body(label: str, when: date, days: int) -> str:
    settings = get_settings()
    return (
        f"Your {label} is on {when.isoformat()} — {days} days from today.\n\n"
        f"Review the deadline and your options in Visaroo.\n\n"
        f"---\n{_DISCLAIMER}\n\n"
        f"Manage notification settings: {settings.frontend_origin}/profile"
    )


def run_reminders(db: Session, today: date | None = None) -> dict:
    """Send due reminders. Returns a summary dict. Idempotent per threshold."""
    today = today or date.today()
    email = get_email_provider()

    users = db.execute(select(User)).scalars().all()
    sent = 0
    skipped_already = 0
    checked = 0

    for user in users:
        profile = db.get(Profile, user.id)
        if profile is None:
            continue
        notif = _notifications(profile)
        if not notif.get("emailEnabled"):
            continue
        lead_times = set(notif.get("deadlineLeadTimeDays", []))
        if not lead_times:
            continue

        for d in compute_server_deadlines(profile, today):
            checked += 1
            if d.days_remaining not in lead_times:
                continue
            pk = f"{user.id}#{d.id}#{d.days_remaining}"
            if db.get(ReminderSent, pk) is not None:
                skipped_already += 1
                continue
            subject = f"[Visaroo] {d.label} in {d.days_remaining} days"
            email.send(user.email, subject, _email_body(d.label, d.date, d.days_remaining))
            db.add(ReminderSent(pk=pk))
            sent += 1

    db.commit()
    logger.info("reminders: sent=%d skipped=%d checked=%d", sent, skipped_already, checked)
    return {"sent": sent, "skipped_already_sent": skipped_already, "deadlines_checked": checked}
