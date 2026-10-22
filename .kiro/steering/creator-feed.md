---
inclusion: always
---

# Creator Feed — Source Matching & Trust Steering

Governs all code for the creator feed (`.kiro/specs/creator-feed/`).

## Official source matching
- A post's official-source match is decided ONLY by the retrieval **similarity score**
  from the vector search (Bedrock Knowledge Base `retrieve` in production, or the local
  NewsItem matcher in dev). The LLM NEVER judges whether a source matches.
- The confidence threshold is **0.75**, hardcoded. Score >= 0.75 → `matched`; otherwise
  → `no_match` ("Awaiting official confirmation").
- NEVER fabricate a source match. If nothing clears the threshold, show no match.
- The confidence score is stored for debugging but MUST NEVER be returned to the client
  or displayed to users.

## Per-card trust label (non-negotiable)
- Every creator post card MUST display: "Creator commentary — verify with official
  sources." The site-wide "not legal advice" disclaimer does NOT substitute for this
  per-card label.
- Creator posts are commentary, not legal guidance, and not official confirmation —
  even when an official source match is attached.

## Status labels are author-declared
- The status label (`rumor_reported` | `proposed` | `final` | `in_effect`) is chosen by
  the creator. The system does not infer or change it. Display it prominently and
  truthfully; never upgrade a "proposed" to "final" automatically.

## No automated ingestion
- Creators post manually through the UI. No scraping of LinkedIn, newsletters, or any
  third party in v1.
