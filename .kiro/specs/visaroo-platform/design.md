# Visaroo Platform — Design

## Overview
Visaroo is a two-tier app: a FastAPI backend exposing a REST API and a React (Vite + TS)
single-page frontend. An AI provider abstraction sits between the backend and Amazon
Bedrock, with a deterministic local fallback so the system never hard-depends on AWS
model access.

## Architecture

```
┌─────────────────┐        REST/JSON        ┌───────────────────────────┐
│  React (Vite)   │  ───────────────────▶   │        FastAPI            │
│  SPA + Axios    │  ◀───────────────────   │  routers → services        │
└─────────────────┘                          │                           │
                                             │  ┌─────────────────────┐  │
                                             │  │  AIProvider (iface)  │  │
                                             │  │  ├ BedrockProvider ──┼──┼──▶ Amazon Bedrock
                                             │  │  └ LocalProvider     │  │    (Claude + Titan)
                                             │  └─────────────────────┘  │
                                             │  SQLAlchemy ──▶ SQLite/PG  │
                                             └───────────────────────────┘
                                                        ▲
                                   news ingest (scripts/fetch_news.py / Kiro hook / cron)
                                   ├─ Federal Register API (JSON)
                                   └─ Curated RSS feeds
```

## Data model (SQLAlchemy)

- **User**: id, email (unique), username, password_hash, visa_category, created_at.
- **Post**: id, author_id (FK), title, body, visa_category, is_anonymous (bool),
  gatekeeper_flag (nullable str), embedding (JSON/text of float list), created_at.
- **Answer**: id, post_id (FK), author_id (FK), body, is_anonymous, is_best (bool),
  created_at.
- **Vote**: id, user_id (FK), target_type ('post'|'answer'), target_id, value (+1/-1).
  Unique constraint on (user_id, target_type, target_id).
- **NewsItem**: id, source ('federal_register'|'rss'), source_id (unique), title, url,
  summary, visa_category, published_at, fetched_at.

### Anonymity handling
Author FK is always stored (for integrity/moderation). Serialization layer replaces
author fields with `"Anonymous"` and omits user id when `is_anonymous` is true. This is
enforced in the Pydantic response schema construction, not left to the client.

## AI provider interface (`app/ai/provider.py`)

```python
class ModerationResult(BaseModel):
    relevant: bool
    reason: str
    suggested_category: str
    suggested_title: str
    harmful: bool

class SearchSummary(BaseModel):
    summary: str
    used_post_ids: list[int]
    grounded: bool          # False when no posts matched

class AIProvider(Protocol):
    def moderate_post(self, title: str, body: str) -> ModerationResult: ...
    def embed_text(self, text: str) -> list[float]: ...
    def summarize_search(self, query: str, posts: list[PostLite]) -> SearchSummary: ...
    def summarize_news(self, title: str, content: str) -> tuple[str, str]:  # (summary, category)
```

`get_provider()` factory reads `AI_PROVIDER` and returns the right implementation.

### BedrockProvider
- Text: `bedrock-runtime.invoke_model` with Claude (messages API). Prompts instruct
  JSON-only output; responses parsed defensively. On any exception, falls back to the
  LocalProvider method so a runtime failure degrades gracefully (Req 6.3).
- Embeddings: Titan Embeddings model → vector list.

### LocalProvider (deterministic fallback)
- `moderate_post`: keyword heuristic over a visa-domain lexicon → relevance; simple
  category keyword map → suggested category; title cleanup (trim/capitalize); harm
  lexicon (fraud/fake document terms) → harmful flag.
- `embed_text`: deterministic hashing-based bag-of-words vector (fixed dim) so cosine
  similarity is meaningful and reproducible without network.
- `summarize_search`: extractive — picks top sentences from matched posts, prefixes a
  "based on N community posts" line. Returns grounded=False with a clear message if no
  posts.
- `summarize_news`: first-N-sentence extractive summary + keyword category classifier.

## Semantic search flow (Req 4)
1. Compute/embed the query (`embed_text`).
2. Load candidate posts (all in v1; indexed subset later), compute cosine similarity vs
   stored post embeddings, take top-K above a threshold.
3. Call `summarize_search(query, topK)` → summary + used ids + grounded flag.
4. Return `{ summary, grounded, used_post_ids, results: [post...] }`.
Post embeddings are computed at creation time and stored on the Post row.

## News ingestion flow (Req 5) — `services/news_ingest.py`
1. Fetch Federal Register API filtered by immigration agencies/keywords (JSON).
2. Fetch each curated RSS feed (USCIS newsroom, Study in the States / SEVP).
3. Normalize to a common shape; dedupe by `source_id`.
4. For new items: `summarize_news()` → summary + category; store NewsItem.
`scripts/fetch_news.py` wraps this so it can be invoked by a Kiro hook locally or by a
scheduled job in production.

## API surface (routers)
- `POST /auth/signup`, `POST /auth/login`, `GET /auth/me`, `PATCH /auth/me`
- `GET /posts` (filter by category), `POST /posts`, `GET /posts/{id}`
- `POST /posts/{id}/answers`, `POST /answers/{id}/best`
- `POST /votes` (target_type,target_id,value)
- `POST /search`
- `GET /news` (personalized), `POST /news/refresh` (triggers ingest; also used by hook)
- `GET /meta/categories`, `GET /healthz`

## Frontend structure
- Pages: Home/Feed, Search, PostDetail, NewPost, News, Login/Signup, Profile.
- `context/AuthContext` holds token + user; Axios interceptor attaches JWT.
- NewPost page calls a "preview moderation" before submit to show gatekeeper suggestions
  (soft-warn UX). Search page shows the AI summary card on top, then result list.
- A persistent "not legal advice" disclaimer banner appears on AI surfaces.

## Security & scalability notes
- JWT auth; bcrypt password hashing; protected routes via dependency.
- SQLite for dev, Postgres for prod (same SQLAlchemy models). Embeddings move to
  pgvector / OpenSearch Serverless at scale (v1 does in-process cosine, fine for demo).
- Ingestion is idempotent (dedupe by source_id) so re-runs are safe.
- All external content treated as untrusted; prompts never execute fetched instructions.

## Testing strategy
- Backend unit tests for: auth flow, anonymity non-leak, voting uniqueness, local
  provider determinism, search grounding behavior with/without matches.
- Run with `AI_PROVIDER=local` so tests are hermetic (no AWS needed).
