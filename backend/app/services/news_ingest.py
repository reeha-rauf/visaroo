"""News ingestion: Federal Register API + curated RSS feeds.

Idempotent by design — items are deduplicated by ``source_id`` so the job is safe to
re-run (manually, via the Kiro hook, or via EventBridge→Lambda in production).

Responsible-AI note (.kiro/steering/responsible-ai.md): we store only title + a short
AI summary + a link to the original source. We never republish full article text, and
fetched content is treated as untrusted input.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai.provider import get_provider
from ..models import NewsItem

logger = logging.getLogger("visaroo.news")

FEDERAL_REGISTER_URL = "https://www.federalregister.gov/api/v1/documents.json"
# Narrow, student/worker-visa-specific terms. We deliberately avoid the broad
# "immigration" term, which pulls in unrelated documents (asylum, border, refugee
# rulemaking) that are off-topic for Visaroo's F-1/OPT/H-1B audience.
FEDERAL_REGISTER_TERMS = [
    "optional practical training",
    "nonimmigrant student",
    "H-1B specialty occupation",
    "student and exchange visitor",
    "employment authorization F-1",
]

# Curated RSS sources (government / official where possible).
RSS_FEEDS = [
    "https://www.uscis.gov/news/rss-feed/19672",  # USCIS newsroom
    "https://studyinthestates.dhs.gov/blog/feed",  # SEVP / Study in the States
]

HTTP_TIMEOUT = 20.0


@dataclass
class RawItem:
    source: str
    source_id: str
    title: str
    url: str
    content: str
    published_at: datetime | None


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=None)
        except ValueError:
            continue
    return None


def fetch_federal_register(per_term: int = 10) -> list[RawItem]:
    """Fetch recent immigration documents from the Federal Register API.

    Scoped to the agencies that actually publish student/worker-visa rules (USCIS, ICE,
    DHS, State) AND matched on a visa-specific term. Agency scoping is what keeps
    unrelated rulemaking (securities, energy, health) out of the feed — a plain full-text
    term search returns any document that merely mentions a word like "employment".
    """
    items: list[RawItem] = []
    with httpx.Client(timeout=HTTP_TIMEOUT) as client:
        for term in FEDERAL_REGISTER_TERMS:
            try:
                resp = client.get(
                    FEDERAL_REGISTER_URL,
                    params={
                        "per_page": per_term,
                        "order": "newest",
                        "conditions[term]": term,
                        # Restrict to immigration-relevant agencies.
                        "conditions[agencies][]": [
                            "u-s-citizenship-and-immigration-services",
                            "u-s-immigration-and-customs-enforcement",
                            "homeland-security-department",
                            "state-department",
                        ],
                        "fields[]": [
                            "title",
                            "abstract",
                            "html_url",
                            "document_number",
                            "publication_date",
                            "agencies",
                        ],
                    },
                )
                resp.raise_for_status()
                for doc in resp.json().get("results", []):
                    # Fold agency names into the content so the classifier's immigration
                    # signal (e.g. "homeland security") is reliably present.
                    agency_names = " ".join(
                        a.get("name", "") for a in (doc.get("agencies") or [])
                    )
                    abstract = doc.get("abstract") or doc.get("title", "")
                    items.append(
                        RawItem(
                            source="federal_register",
                            source_id=f"fr:{doc.get('document_number')}",
                            title=doc.get("title", "Untitled"),
                            url=doc.get("html_url", ""),
                            content=f"{abstract} {agency_names}".strip(),
                            published_at=_parse_date(doc.get("publication_date")),
                        )
                    )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Federal Register fetch failed for '%s': %s", term, exc)
    return items


def fetch_rss() -> list[RawItem]:
    """Fetch curated RSS feeds. Uses feedparser; failures are skipped gracefully."""
    import feedparser

    items: list[RawItem] = []
    for feed_url in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed_url)
            for entry in parsed.entries[:10]:
                link = getattr(entry, "link", "")
                summary = getattr(entry, "summary", "") or getattr(entry, "title", "")
                items.append(
                    RawItem(
                        source="rss",
                        source_id=f"rss:{getattr(entry, 'id', link) or link}",
                        title=getattr(entry, "title", "Untitled"),
                        url=link,
                        content=summary,
                        published_at=_parse_date(getattr(entry, "published", None)),
                    )
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("RSS fetch failed for '%s': %s", feed_url, exc)
    return items


# Curated fallback images per visa category (keyless Unsplash hotlinks). Used only when
# an article has no real og:image. Picked deterministically by item id so a given article
# always shows the same image.
_FALLBACK_IMAGES: dict[str, list[str]] = {
    "F-1": [
        "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=800&q=80",
        "https://images.unsplash.com/photo-1498243691581-b145c3f54a5a?w=800&q=80",
    ],
    "OPT": [
        "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=800&q=80",
        "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800&q=80",
    ],
    "STEM-OPT": [
        "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80",
        "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=800&q=80",
    ],
    "H-1B": [
        "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=800&q=80",
        "https://images.unsplash.com/photo-1554469384-e58fac16e23a?w=800&q=80",
    ],
    "H-4": [
        "https://images.unsplash.com/photo-1511895426328-dc8714191300?w=800&q=80",
    ],
    "J-1": [
        "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=800&q=80",
    ],
    "Green-Card": [
        "https://images.unsplash.com/photo-1540910419892-4a36d2c3266c?w=800&q=80",
    ],
    "Other": [
        "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=800&q=80",
        "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=800&q=80",
    ],
}


def _fetch_og_image(client: httpx.Client, url: str) -> str | None:
    """Return the article's og:image URL if the page exposes one, else None.

    Best-effort: a failure (timeout, no tag, non-HTML) just yields None so the caller
    uses a curated fallback. Fetched content is untrusted — we only read a meta tag.
    """
    import re

    try:
        resp = client.get(url, timeout=8.0, follow_redirects=True)
        if resp.status_code != 200 or "text/html" not in resp.headers.get("content-type", ""):
            return None
        html = resp.text[:200_000]  # cap: og tags live in <head>
        m = re.search(
            r'<meta[^>]+(?:property|name)=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE,
        )
        if not m:
            m = re.search(
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']og:image["\']',
                html,
                re.IGNORECASE,
            )
        if m:
            img = m.group(1).strip()
            if img.startswith("http"):
                return img
    except Exception as exc:  # noqa: BLE001
        logger.debug("og:image fetch failed for %s: %s", url, exc)
    return None


def _fallback_image(category: str, seed: str) -> str:
    """Pick a stable curated image for the category, varied by a seed string."""
    pool = _FALLBACK_IMAGES.get(category) or _FALLBACK_IMAGES["Other"]
    idx = sum(ord(c) for c in seed) % len(pool)
    return pool[idx]


def ingest(db: Session) -> dict:
    """Fetch, dedupe, AI-summarize, and store news items. Returns a count summary."""
    provider = get_provider()
    raw = fetch_federal_register() + fetch_rss()

    added = 0
    skipped = 0
    # Track ids seen in THIS batch so overlapping query terms (which can return the
    # same document) don't violate the unique constraint before commit.
    seen_in_batch: set[str] = set()
    client = httpx.Client(headers={"User-Agent": "VisarooBot/1.0"})
    try:
        for item in raw:
            if not item.source_id or not item.url:
                skipped += 1
                continue
            if item.source_id in seen_in_batch:
                skipped += 1
                continue
            exists = db.execute(
                select(NewsItem).where(NewsItem.source_id == item.source_id)
            ).scalar_one_or_none()
            if exists:
                skipped += 1
                continue

            summary, category = provider.summarize_news(item.title, item.content)
            # Real article image when available, else a curated category fallback.
            image_url = _fetch_og_image(client, item.url) or _fallback_image(
                category, item.source_id
            )
            db.add(
                NewsItem(
                    source=item.source,
                    source_id=item.source_id,
                    title=item.title,
                    url=item.url,
                    summary=summary,
                    visa_category=category,
                    image_url=image_url,
                    published_at=item.published_at,
                )
            )
            seen_in_batch.add(item.source_id)
            added += 1
    finally:
        client.close()

    db.commit()
    logger.info("News ingest complete: added=%d skipped=%d", added, skipped)
    return {"added": added, "skipped": skipped, "fetched": len(raw)}
