"""Standalone news ingestion runner.

Invoked by the Kiro agent hook (`.kiro/hooks/`) and suitable for an AWS
EventBridge→Lambda schedule in production. Also runnable by hand:

    python scripts/fetch_news.py

It creates its own DB session so it does not depend on the running API.
"""
import sys
from pathlib import Path

# Make the backend package importable when run from the repo root.
BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.services.news_ingest import ingest  # noqa: E402


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        result = ingest(db)
        print(
            f"[visaroo] news ingest: added={result['added']} "
            f"skipped={result['skipped']} fetched={result['fetched']}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
