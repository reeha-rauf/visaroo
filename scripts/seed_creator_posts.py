"""Seed demo creator feed (spec TASK-10 / REQ-8).

Creates a demo verified-creator ("ImmigrationInsider") and 5 posts with pre-set match
states so the demo shows every status label and every match state (including a spinner).
Idempotent: skips a post whose headline already exists. Run from the repo root:

    python scripts/seed_creator_posts.py
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
from app.models import CreatorPost, Profile, User  # noqa: E402

DISPLAY_NAME = "ImmigrationInsider"


def _ago(hours: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=hours)


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        creator = db.query(User).filter(User.username == DISPLAY_NAME).one_or_none()
        if creator is None:
            creator = User(
                email="creator@visaroo-demo.com",
                username=DISPLAY_NAME,
                password_hash=hash_password("password123"),
                visa_category="OPT",
                role="creator",
            )
            db.add(creator)
            db.flush()
            db.add(
                Profile(
                    user_id=creator.id,
                    full_name=DISPLAY_NAME,
                    visa_type="OPT",
                    status_phase="active",
                    creator_display_name=DISPLAY_NAME,
                    creator_bio="Covering US immigration policy changes for international students and workers.",
                    creator_source_links=json.dumps(["https://linkedin.com/in/demo"]),
                )
            )

        posts = [
            {
                "headline": "Proposed rule would adjust STEM OPT reporting requirements",
                "body": "A proposed rule in the Federal Register would change how STEM OPT students report employer and training-plan details. It is not final and public comments are open.",
                "visa": ["STEM_OPT"],
                "status": "proposed",
                "source_label": "Federal Register",
                "source_url": "https://www.federalregister.gov/",
                "hours": 3,
                "match_status": "matched",
                "matched_title": "USCIS STEM OPT Reporting — Proposed Adjustments",
                "matched_url": "https://www.federalregister.gov/agencies/u-s-citizenship-and-immigration-services",
                "score": 0.86,
            },
            {
                "headline": "H-1B electronic registration fee increase now in effect",
                "body": "The updated H-1B registration fee is now in effect for the upcoming cap season. Employers should budget accordingly before the registration window opens.",
                "visa": ["H-1B"],
                "status": "in_effect",
                "source_label": "USCIS",
                "source_url": "https://www.uscis.gov/newsroom",
                "hours": 10,
                "match_status": "no_match",
                "score": 0.41,
            },
            {
                "headline": "Reports of longer OPT EAD processing times at some service centers",
                "body": "Several applicants report longer OPT EAD processing at certain service centers. This is anecdotal and not confirmed by USCIS; verify your own case status.",
                "visa": ["OPT"],
                "status": "rumor_reported",
                "source_label": "Community reports",
                "source_url": "https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students",
                "hours": 26,
                "match_status": "no_match",
                "score": 0.22,
            },
            {
                "headline": "Final rule updates immigration fee schedule across visa categories",
                "body": "A final rule updates the USCIS fee schedule affecting multiple visa categories. Review the effective date to understand when the new fees apply to your filings.",
                "visa": ["ALL"],
                "status": "final",
                "source_label": "Federal Register",
                "source_url": "https://www.federalregister.gov/",
                "hours": 50,
                "match_status": "matched",
                "matched_title": "DHS Immigration Fee Schedule — Final Rule",
                "matched_url": "https://www.federalregister.gov/agencies/homeland-security-department",
                "score": 0.91,
            },
            {
                "headline": "Proposed guidance may clarify F-1 cap-gap travel questions",
                "body": "Draft guidance may clarify common cap-gap and travel questions for F-1 students moving to H-1B. Details are still being finalized — treat as proposed only.",
                "visa": ["F-1"],
                "status": "proposed",
                "source_label": "Study in the States",
                "source_url": "https://studyinthestates.dhs.gov/",
                "hours": 70,
                "match_status": "pending",  # shows the spinner in the demo
                "score": None,
            },
        ]

        added = 0
        for i, p in enumerate(posts):
            if db.query(CreatorPost).filter(CreatorPost.headline == p["headline"]).one_or_none():
                continue
            db.add(
                CreatorPost(
                    id=str(uuid.uuid4()),
                    creator_id=creator.id,
                    creator_display_name=DISPLAY_NAME,
                    headline=p["headline"],
                    body=p["body"],
                    visa_type_tags=json.dumps(p["visa"]),
                    status_label=p["status"],
                    source_url=p["source_url"],
                    source_label=p["source_label"],
                    posted_at=_ago(p["hours"]),
                    match_status=p["match_status"],
                    matched_document_title=p.get("matched_title"),
                    matched_document_url=p.get("matched_url"),
                    match_confidence_score=p.get("score"),
                )
            )
            added += 1

        db.commit()
        total = db.query(CreatorPost).filter(CreatorPost.deleted.is_(False)).count()
        print(f"[visaroo] creator posts seeded: added={added} total={total}")
        print("[visaroo] creator login: creator@visaroo-demo.com / password123")
    finally:
        db.close()


if __name__ == "__main__":
    main()
