# Requirements: Creator Feed

## Overview
Allow verified creators to post immigration news updates directly to Visaroo. Each post is matched against official sources in the knowledge base, labeled with a status tag, and filtered to the user's visa type. The pipeline turns creator speed into verified, personalized information.

---

## Functional Requirements

### REQ-1: Creator Role
- A Verified Creator is a Cognito user in the `VerifiedCreator` group
- For v1 demo: one seeded dummy creator account simulates the feature
- Creator profile displays: display name, bio (max 160 chars), avatar, source links (e.g. LinkedIn, newsletter URL)
- Creator posts are labeled with the creator's display name and a "Verified Creator" badge
- Regular users cannot post to the feed

### REQ-2: Post Creation
A creator post must include:
- Headline (max 120 chars, required)
- Body (max 1000 chars, required)
- Visa type tags: at least one of F-1, OPT, STEM OPT, H-1B, H-4, J-1, All (required)
- Status label: one of `rumor_reported` | `proposed` | `final` | `in_effect` (required)
- Source URL: link to original source (required)
- Source label: short name of source e.g. "Federal Register", "USCIS", "Reuters" (required)

Optional fields:
- Effective date (ISO 8601)
- Expiry date (ISO 8601)

### REQ-3: Status Labels
Every post must carry exactly one status label. Labels are displayed prominently on each card.

| Label | Display text | Color |
|---|---|---|
| `rumor_reported` | Reported — not confirmed | Grey |
| `proposed` | Proposed — not yet final | Amber |
| `final` | Final rule | Blue |
| `in_effect` | In effect | Green |

Users must be able to filter the feed by status label.

### REQ-4: Official Source Matching
After a creator posts, the system attempts to match the post against official documents in the Bedrock Knowledge Base.

Matching behavior:
- Run a similarity search against the Knowledge Base using the post headline and body as the query
- If a match is found above a confidence threshold (0.75): attach the matched document title, source URL, and a "Official source found" badge to the post; store the match in DynamoDB
- If no match is found: show "Awaiting official confirmation" label
- Matching runs asynchronously after save; the post appears immediately without waiting for the match result
- Match result updates the post record in DynamoDB; the frontend polls or uses optimistic UI

### REQ-5: Feed Display
- Feed is a reverse-chronological list of creator posts
- Default filter: show posts tagged with the user's visa type or "All"
- Filter chips: All | F-1 | OPT | STEM OPT | H-1B | H-4 | J-1
- Filter by status label: All statuses | Proposed | Final | In effect | Reported
- Each post card shows: creator name + badge, headline, status label, visa type tags, time posted, source link, official match status
- Clicking a card expands to show full body, effective/expiry dates, and "Does this affect me?" button

### REQ-6: "Does This Affect Me?" Button
- Each expanded post card has a "Does this affect me?" button
- Clicking opens the Ask panel pre-filled with the post headline and the user's personalization context
- This reuses the impact explainer feature; the creator feed is the trigger point, not a separate AI call

### REQ-7: Post Management
- Creators can edit or delete their own posts
- Admins can delete any post
- Deleted posts are soft-deleted (hidden from feed, retained in DynamoDB with `deleted: true`)
- Edit re-triggers the official source matching job

### REQ-8: Demo Seed Data
For the demo, the dummy creator account must have at least 5 pre-seeded posts covering:
- One `proposed` rule affecting STEM OPT
- One `in_effect` rule affecting H-1B
- One `rumor_reported` post affecting OPT
- One `final` rule affecting all visa types
- One post with an official source match already attached

---

## Non-Functional Requirements

### REQ-NF-1: Source matching accuracy
- Only attach an official source match when confidence >= 0.75
- Never fabricate a source match; if below threshold show "Awaiting official confirmation"
- Store the confidence score in DynamoDB for debugging; do not display it to users

### REQ-NF-2: Post latency
- Post appears in feed within 2 seconds of save
- Official source match result appears within 30 seconds (async)

### REQ-NF-3: Trust boundary
- Creator posts are commentary, not legal guidance
- Every post card must display: "Creator commentary — verify with official sources"
- The existing site-wide disclaimer does not substitute for this per-card label

### REQ-NF-4: No automated ingestion
- No scraping of LinkedIn or newsletters in v1
- Creators post manually through the Visaroo UI