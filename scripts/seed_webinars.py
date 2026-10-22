"""Seed demo webinars (spec TASK-5).

Creates a demo "verified creator" user and 5 webinars covering OPT, STEM OPT, and H-1B
with upcoming dates computed relative to today (so they're always in the future).
Idempotent: skips a webinar whose title already exists. Run from the repo root:

    python scripts/seed_webinars.py
"""
import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from app.auth import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import User, Webinar  # noqa: E402


def _future(days: int, hour_utc: int = 17) -> str:
    d = datetime.now(timezone.utc) + timedelta(days=days)
    d = d.replace(hour=hour_utc, minute=0, second=0, microsecond=0)
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        creator = db.query(User).filter(User.username == "creator").one_or_none()
        if creator is None:
            creator = User(
                email="creator@demo.com",
                username="creator",
                password_hash=hash_password("password123"),
                visa_category="OPT",
                role="creator",
            )
            db.add(creator)
            db.flush()

        seed = [
            {
                "title": "OPT & STEM OPT: What You Need to Know in 2026",
                "host_name": "SEVP",
                "host_type": "official",
                "start_date_utc": _future(7),
                "duration_minutes": 60,
                "visa_type_tags": ["OPT", "STEM_OPT"],
                "description": "An overview of OPT and STEM OPT rules, timelines, and common pitfalls for F-1 students.",
                "registration_url": "https://studyinthestates.dhs.gov/",
            },
            {
                "title": "H-1B Cap Season 2027: Timeline and Preparation",
                "host_name": "USCIS",
                "host_type": "official",
                "start_date_utc": _future(14),
                "duration_minutes": 45,
                "visa_type_tags": ["H-1B"],
                "description": "Key dates and preparation steps for the upcoming H-1B cap registration season.",
                "registration_url": "https://www.uscis.gov/working-in-the-united-states/h-1b-specialty-occupations",
            },
            {
                "title": "Navigating OPT Unemployment Rules",
                "host_name": "International Student Services — University of Washington",
                "host_type": "community",
                "start_date_utc": _future(21),
                "duration_minutes": 50,
                "visa_type_tags": ["OPT", "STEM_OPT"],
                "description": "How the unemployment-day caps work on OPT and STEM OPT, and how to stay compliant.",
                "registration_url": "https://iss.washington.edu/",
            },
            {
                "title": "Travel on OPT: Re-entry Risks and How to Prepare",
                "host_name": "Boundless Immigration",
                "host_type": "verified_creator",
                "start_date_utc": _future(28),
                "duration_minutes": 60,
                "visa_type_tags": ["OPT", "STEM_OPT", "F-1"],
                "description": "What to carry, timing risks, and how to prepare for re-entry while on OPT.",
                "registration_url": "https://www.boundless.com/",
            },
            {
                "title": "Immigration Policy Update: What Changed in Fall 2026",
                "host_name": "Immigration Law Help",
                "host_type": "verified_creator",
                "start_date_utc": _future(35),
                "duration_minutes": 75,
                "visa_type_tags": ["ALL"],
                "description": "A plain-language rundown of recent immigration policy changes affecting students and workers.",
                "registration_url": "https://www.uscis.gov/newsroom",
            },
        ]

        added = 0
        for item in seed:
            exists = db.query(Webinar).filter(Webinar.title == item["title"]).one_or_none()
            if exists:
                continue
            db.add(
                Webinar(
                    id=str(uuid.uuid4()),
                    title=item["title"],
                    host_name=item["host_name"],
                    host_type=item["host_type"],
                    posted_by=creator.id if item["host_type"] == "verified_creator" else None,
                    start_date_utc=item["start_date_utc"],
                    duration_minutes=item["duration_minutes"],
                    visa_type_tags=json.dumps(item["visa_type_tags"]),
                    description=item["description"],
                    registration_url=item["registration_url"],
                )
            )
            added += 1

        db.commit()
        total = db.query(Webinar).count()
        print(f"[visaroo] webinars seeded: added={added} total={total}")
        print("[visaroo] creator login: creator@demo.com / password123")
    finally:
        db.close()


if __name__ == "__main__":
    main()
