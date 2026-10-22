"""Standalone deadline-reminder runner.

Reference implementation of the design's EventBridge-scheduled reminder Lambda. Invoked
by the Kiro hook or by hand:

    python scripts/send_reminders.py

Creates its own DB session so it runs independently of the API. Emails go through the
EmailProvider (local preview by default; Amazon SES when EMAIL_PROVIDER=ses).
"""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.services.reminder_checker import run_reminders  # noqa: E402


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        result = run_reminders(db)
        print(
            f"[visaroo] reminders: sent={result['sent']} "
            f"skipped={result['skipped_already_sent']} "
            f"checked={result['deadlines_checked']}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
