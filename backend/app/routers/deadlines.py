"""Deadline tracker routes: calendar (.ics) export.

The deadline list itself is computed client-side (REQ-NF-3). This endpoint exists so a
user can export their upcoming deadlines to Apple/Google Calendar (TASK-8).
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..deadline_calc import compute_server_deadlines
from ..deps import get_current_user
from ..models import Profile, User
from ..services.reminder_checker import run_reminders

router = APIRouter(prefix="/deadlines", tags=["deadlines"])

_DISCLAIMER = (
    "Visaroo shares general information only, not legal advice. "
    "Verify with your DSO or an immigration attorney."
)


def _ics_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _build_ics(deadlines, now: datetime) -> str:
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Visaroo//Deadline Tracker//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Visaroo Deadlines",
    ]
    for d in deadlines:
        dt = d.date.strftime("%Y%m%d")
        lines += [
            "BEGIN:VEVENT",
            f"UID:visaroo-{d.id}-{dt}@visaroo",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{dt}",
            f"SUMMARY:{_ics_escape('Visaroo: ' + d.label)}",
            f"DESCRIPTION:{_ics_escape(d.label + ' — ' + str(d.days_remaining) + ' days from export. ' + _DISCLAIMER)}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    # RFC 5545 uses CRLF line endings.
    return "\r\n".join(lines) + "\r\n"


@router.get("/ics")
def download_ics(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    profile = db.get(Profile, user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    deadlines = compute_server_deadlines(profile)
    ics = _build_ics(deadlines, datetime.now(timezone.utc))
    return Response(
        content=ics,
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=visaroo-deadlines.ics"},
    )


@router.post("/remind")
def trigger_reminders(db: Session = Depends(get_db)) -> dict:
    """Run the deadline reminder checker for all users (TASK-9).

    In production this is the EventBridge-scheduled Lambda; here it's callable so a Kiro
    hook or `scripts/send_reminders.py` can trigger it. Idempotent per lead-time threshold.
    """
    return run_reminders(db)
