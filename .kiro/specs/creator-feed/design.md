# Design: Creator Feed

Verified creators post fast, labeled news commentary; each post is matched against official
sources by vector similarity and tagged accordingly. Built on Visaroo's stack: FastAPI +
SQLAlchemy, JWT auth with a `User.role` check, Pydantic validation, and the `AIProvider`
abstraction for source matching.

Routes live under **`/creator-posts`** (not `/posts`) to avoid colliding with the existing
community Q&A, and the feed has its own **"Feed"** nav entry (the Q&A community stays at
"Community").

The 0.75 match threshold and the "match from the retrieval score only, never the LLM's
judgment" rule are enforced by `.kiro/steering/creator-feed.md`. The confidence score is
stored for debugging but never serialized to the client.

## Architecture

The matcher runs **synchronously, right after save**, in the same request:

```
Creator posts via UI
  → POST /creator-posts  (FastAPI, routers/creator_posts.py)
    → writes CreatorPost (match_status: pending)
    → _run_matcher(post) runs AIProvider.match_post(...)
    → updates the row with the match result (matched / no_match)
  → frontend polls GET /creator-posts/{id} (handles the async-in-production shape; here the
    result is usually ready immediately)
```

`AIProvider.match_post` resolves to either a **Bedrock Knowledge Base `retrieve`** (when
`BEDROCK_KNOWLEDGE_BASE_ID` is set) or a **local matcher over the already-ingested `NewsItem`
records**. Both return a similarity score compared against the 0.75 threshold; the LLM never
decides the match.

---

## Data Model

The `CreatorPost` SQLAlchemy model (and its `CreatorPostOut` API shape):

```
CreatorPost {
  id: string                         // UUID, primary key
  creatorId: int                     // FK -> users.id
  creatorDisplayName: string         // denormalized for display
  headline: string                   // max 120 chars
  body: string                       // max 1000 chars
  visaTypeTags: VisaTypeTag[]        // JSON-encoded
  statusLabel: PostStatusLabel
  sourceUrl: string
  sourceLabel: string
  effectiveDate?: string             // ISO 8601
  expiryDate?: string                // ISO 8601
  postedAt: datetime
  updatedAt: datetime

  // Official source match (populated by _run_matcher)
  matchStatus: 'pending' | 'matched' | 'no_match'
  matchedDocumentTitle?: string
  matchedDocumentUrl?: string
  matchConfidenceScore?: number      // stored, NEVER serialized to the client

  // Soft delete
  deleted: boolean
}

type PostStatusLabel = 'rumor_reported' | 'proposed' | 'final' | 'in_effect'
type VisaTypeTag = 'F-1' | 'OPT' | 'STEM_OPT' | 'H-1B' | 'H-4' | 'J-1' | 'ALL'
```

`visaTypeTags` is stored as a JSON-encoded text column. `matchConfidenceScore` is present on
the model but deliberately omitted from `CreatorPostOut` (steering rule).

### Query patterns
- **List non-deleted posts:** select where `deleted == false`, newest first.
- **Filter by visa type / status:** filtered in the router after load (fine at demo scale).
- **Get by id:** `db.get(CreatorPost, id)` (404 if missing or soft-deleted).
- **Creator's own posts:** select where `creator_id == user.id`.

### Creator profile
The verified-creator fields live on the existing `Profile` model (populated for users in the
`creator` role): `creator_display_name`, `creator_bio` (max 160 chars), `creator_avatar_url`,
`creator_source_links` (JSON list).

---

## API Routes (FastAPI, `routers/creator_posts.py`)

```
GET    /creator-posts          — list; query params: ?visaType=&statusLabel=
GET    /creator-posts/{id}     — single post detail
POST   /creator-posts          — create (role: creator or admin); runs the matcher after save
PUT    /creator-posts/{id}     — edit own post (re-runs the matcher)
DELETE /creator-posts/{id}     — soft delete own post (or admin)
```

GET routes are public. POST / PUT / DELETE require a valid JWT and a `User.role` check of
`creator` or `admin`; editing or deleting another user's post returns 403 (unless admin).

---

## Source matcher (`_run_matcher` + `AIProvider.match_post`)

After a create or edit, `_run_matcher(db, post)` calls `AIProvider.match_post(headline, body,
candidates)` and writes the result back:

```python
match = provider.match_post(post.headline, post.body, candidates)
if match.matched:              # match.score >= 0.75
    post.match_status = "matched"
    post.matched_document_title = match.title
    post.matched_document_url = match.url
    post.match_confidence_score = match.score   # stored, never serialized
else:
    post.match_status = "no_match"
    post.match_confidence_score = match.score
```

`match_post` implementation:
- **Bedrock KB** (when `BEDROCK_KNOWLEDGE_BASE_ID` is configured): `bedrock-agent-runtime
  retrieve` with `numberOfResults=1`; uses the returned `score` and document metadata.
- **Local matcher** (default): token-overlap similarity over the ingested `NewsItem` corpus.

Both compare the top score against the hardcoded **0.75** threshold. The match decision is the
score, never the model's opinion.

---

## Frontend

### Page structure

```
/feed
  <CreatorFeedPage>
    <FeedFilterBar>
      <VisaTypeChips />
      <StatusLabelChips />
    </FeedFilterBar>
    <PostList>
      <CreatorPostCard />        // one per post
    </PostList>
    <CreatorPostButton />        // visible only to creator/admin users
  </CreatorFeedPage>
```

### CreatorPostCard — collapsed state

```
[Verified Creator badge]  [creatorDisplayName]  [time ago]
[StatusLabel chip]  [VisaType tags]
Headline
[sourceLabel → sourceUrl]
[Official source found] or [Awaiting official confirmation]
"Creator commentary — verify with official sources"
```

### CreatorPostCard — expanded state (click to expand)

```
... collapsed content ...
Body text
Effective date / Expiry date (if set)
[Does this affect me?]  [View official source]
```

"Does this affect me?" reuses the AI Ask/search flow, pre-filled with the post headline.

### Match status display
- `pending`: "Checking official sources…"
- `matched`: "Official source found", links to `matchedDocumentUrl`
- `no_match`: "Awaiting official confirmation"

Because the matcher runs synchronously on save, the status is usually resolved by the time the
client reads it. The frontend still polls `GET /creator-posts/{id}` while `pending` (up to a
short cap) so the UI matches the production async shape.

### Creator post form
Modal triggered by the "New post" button. Fields per REQ-2, validated client-side before
submit; the backend re-validates with the `CreatorPostCreate` Pydantic schema.

---

## Demo Seed Data

Seed script: `scripts/seed_creator_posts.py` (run from the repo root).

Demo creator account (role `creator`):
```
email: creator@visaroo-demo.com
displayName: ImmigrationInsider
bio: Covering US immigration policy changes for international students and workers.
sourceLinks: [https://linkedin.com/in/demo]
```

Five seeded posts (per REQ-8) with `match_status` pre-set so the demo shows every status label
and match state:
- Post 1: `proposed` | STEM_OPT | `matched` (pre-attached to a real Federal Register document)
- Post 2: `in_effect` | H-1B | `no_match`
- Post 3: `rumor_reported` | OPT | `no_match`
- Post 4: `final` | ALL | `matched`
- Post 5: `proposed` | F-1 | `pending` (shows the checking state in the demo)
