# Visaroo Platform — Requirements

## Introduction
Visaroo is a community + information platform for international students and visa holders
in the US. It combines community-contributed lived experience with official immigration
news, mediated by an AI layer that keeps the community relevant and trustworthy. This
document captures v1 requirements in EARS-style acceptance criteria.

The guiding principle (see `.kiro/steering/responsible-ai.md`): Visaroo provides
**information, not legal advice**, always links to sources, and uses AI to **soft-warn**,
never to silence genuine questions.

---

## Requirement 1 — Accounts & Profiles
**User story:** As an international student, I want an account with my visa type, so that
content can be tailored to my situation and I can participate in the community.

### Acceptance Criteria
1. WHEN a visitor submits a valid email, password, and username THEN the system SHALL
   create an account and return an auth token.
2. WHEN a user signs up THEN the system SHALL let them select a visa category from the
   canonical list (F-1, OPT, STEM-OPT, H-1B, H-4, J-1, L-1, Green-Card, Other).
3. WHEN a user logs in with valid credentials THEN the system SHALL return a valid JWT.
4. WHEN a request is made with an invalid or missing token to a protected endpoint THEN
   the system SHALL respond with 401.
5. WHERE a user updates their profile visa category THEN the system SHALL persist it and
   use it to personalize the news feed.

## Requirement 2 — Community Q&A
**User story:** As a visa holder, I want to post questions and answer others, so that we
can share lived experience the official sources don't cover.

### Acceptance Criteria
1. WHEN an authenticated user submits a post with a title and body THEN the system SHALL
   store it with the author, timestamp, and visa-category tag.
2. WHEN a user chooses to post anonymously THEN the system SHALL store authorship for
   integrity but SHALL NOT expose the author's identity in any API response.
3. WHEN a user submits an answer to a post THEN the system SHALL store and associate it.
4. WHEN a user upvotes or downvotes a post or answer THEN the system SHALL record one
   vote per user per item and reflect the aggregate score.
5. WHEN the post author marks an answer as "best" THEN the system SHALL flag exactly one
   best answer per post.
6. WHEN posts are listed THEN the system SHALL support filtering by visa category.

## Requirement 3 — AI Gatekeeper (on posting)
**User story:** As a community member, I want new posts checked for relevance, so the
platform stays useful and safe without censoring real questions.

### Acceptance Criteria
1. WHEN a user submits a post THEN the system SHALL run it through the AI provider's
   `moderate_post()` which returns: relevance (on/off topic), a suggested visa category,
   a suggested cleaner title, and a harm flag.
2. IF the gatekeeper judges a post off-topic or harmful THEN the system SHALL return a
   soft warning with a reason AND SHALL still allow the user to publish (soft-warn).
3. WHEN the gatekeeper suggests a category or title THEN the system SHALL offer these as
   suggestions the user can accept or ignore.
4. WHERE the AI provider is unavailable THEN the system SHALL fall back to the local
   provider and SHALL NOT block posting.

## Requirement 4 — AI Search (summary-first)
**User story:** As someone with a specific problem, I want to search and get an AI
summary first, then the community posts behind it, like Google/Perplexity.

### Acceptance Criteria
1. WHEN a user submits a search query THEN the system SHALL semantically rank existing
   community posts by relevance and return the top matches.
2. WHEN matches are found THEN the system SHALL generate a summary grounded ONLY in
   those matched posts and SHALL state how many posts it used.
3. WHEN the summary is returned THEN the system SHALL include links/references to the
   source posts used.
4. IF no relevant posts are found THEN the system SHALL say so and SHALL NOT fabricate
   an answer.
5. WHERE the summary is shown THEN the UI SHALL display the "not legal advice" disclaimer.

## Requirement 5 — News Feed
**User story:** As a visa holder, I want recent official immigration news summarized and
filtered to my visa type, so I know what changed and what it means for me.

### Acceptance Criteria
1. WHEN the ingestion job runs THEN the system SHALL fetch items from the Federal
   Register API and the curated RSS sources.
2. WHEN a new item is ingested THEN the system SHALL deduplicate by source URL/id.
3. WHEN an item is processed THEN the system SHALL generate a plain-language summary,
   classify the affected visa category, and store title + summary + source link.
4. WHEN the feed is requested by a logged-in user THEN the system SHALL rank/filter items
   relevant to that user's visa category first.
5. WHEN a news item is displayed THEN the system SHALL link to the original source and
   SHALL NOT display full copyrighted article text.

## Requirement 6 — Reliability without AWS access
**User story:** As the developer demoing this, I want the app to run fully even if
Bedrock model access is pending, so a demo never breaks.

### Acceptance Criteria
1. WHERE `AI_PROVIDER=local` THEN all AI features SHALL work deterministically offline.
2. WHERE `AI_PROVIDER=bedrock` AND credentials/model access are valid THEN AI features
   SHALL use Amazon Bedrock.
3. IF a Bedrock call fails at runtime THEN the system SHALL degrade gracefully to a safe
   default and SHALL NOT crash the request.

## Non-functional
- Secrets/config via environment only; `.env.example` provided.
- Anonymous author identity never leaked in responses or logs.
- External fetched content treated as untrusted; embedded instructions ignored.
