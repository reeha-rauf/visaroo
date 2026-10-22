# Visaroo — Architecture

This document explains how Visaroo is put together and the reasoning behind the key
technical decisions. It complements the technical write-up in the root `README.md`.

## 1. System overview

Visaroo is a two-tier application:

- **Frontend** — a React + Vite + TypeScript single-page app.
- **Backend** — a FastAPI service exposing a JSON/REST API, backed by SQLAlchemy.
- **AI layer** — an abstraction (`AIProvider`) with a local fallback and an Amazon
  Bedrock implementation.
- **News ingestion** — a standalone, idempotent pipeline over the Federal Register API
  and curated RSS feeds, runnable by a Kiro hook locally or EventBridge→Lambda in prod.

```
React SPA ──REST/JWT──▶ FastAPI ──▶ AIProvider ──▶ (Local | Bedrock: Claude + Titan)
                           │
                           └──▶ SQLAlchemy ──▶ SQLite (dev) / Postgres (prod)

news ingest (scripts/fetch_news.py)
   ├─ Federal Register API (public JSON)
   └─ curated official RSS (USCIS, Study in the States / SEVP)
```

## 2. Request lifecycle

1. The SPA stores a JWT (from `/auth/login` or `/auth/signup`) and attaches it to every
   request via an Axios interceptor.
2. FastAPI resolves the current user with a dependency (`get_current_user`) that validates
   the token and loads the user, or returns 401.
3. Routers stay thin; anything with logic (news ingestion, serialization, AI) lives in
   services / dedicated modules.
4. Responses are always Pydantic schemas built by `serializers.py`, never raw ORM objects.

## 3. Data model

| Table | Key fields | Notes |
|---|---|---|
| `users` | email (unique), username (unique), password_hash, visa_category | bcrypt hashes |
| `posts` | author_id, title, body, visa_category, is_anonymous, gatekeeper_flag, **embedding** | embedding is a JSON-encoded `list[float]` stored at creation |
| `answers` | post_id, author_id, body, is_anonymous, is_best | exactly one best answer per post |
| `votes` | user_id, target_type, target_id, value | unique on (user, target_type, target_id) |
| `news_items` | source, source_id (unique), title, url, summary, visa_category, published_at | dedupe by source_id |

### Anonymity guarantee
The author foreign key is **always** stored (for integrity and moderation), but the
serialization layer (`serializers.py`) substitutes `"Anonymous"` and omits the user id when
`is_anonymous` is true. Centralizing this in one place — rather than trusting each route —
is what makes the guarantee testable (`test_anonymous_identity_not_leaked`).

## 4. The AI provider abstraction

The single most important design element. Everything AI goes through one interface:

```python
class AIProvider(Protocol):
    def moderate_post(self, title, body) -> ModerationResult
    def embed_text(self, text) -> list[float]
    def summarize_search(self, query, posts) -> SearchSummary
    def summarize_news(self, title, content) -> tuple[str, str]  # (summary, category)
```

- **`LocalProvider`** (default): deterministic heuristics — a visa-domain lexicon for
  relevance, a keyword map for category classification, a harm lexicon for the fraud flag, a
  hashing bag-of-words embedding (so cosine similarity is meaningful offline), and an
  extractive search/news summarizer. It never invents immigration rules.
- **`BedrockProvider`**: Claude via the Bedrock messages API for generation, Titan for
  embeddings. Every method wraps its Bedrock call in a `try/except` that falls back to the
  local provider, so a single failure degrades gracefully instead of 500-ing.

`get_provider()` reads `AI_PROVIDER` and returns the right instance (cached). This yields
three properties: the app always runs, tests are hermetic, and production is resilient.

## 5. Semantic search flow

1. Embed the query (`embed_text`).
2. Load candidate posts, compute cosine similarity against each stored post embedding, keep
   the top-K above a small threshold.
3. `summarize_search(query, topK)` returns a summary grounded **only** in those posts, plus
   the ids it used and a `grounded` flag.
4. The API returns the summary card, the `grounded` flag, the used post ids, the ranked
   results, and a disclaimer. If nothing matches, it says so rather than fabricating an answer.

For a demo-sized corpus, in-process cosine is simple and fast. At scale, embeddings move to
**pgvector** (Postgres) or **OpenSearch Serverless**, and retrieval becomes an index query —
the interface and the route stay the same.

## 6. News ingestion pipeline

`services/news_ingest.py`:
1. Fetch recent immigration documents from the **Federal Register API** (filtered by terms
   like *immigration*, *nonimmigrant visa*, *optional practical training*), requesting only
   the fields needed.
2. Fetch curated official **RSS** feeds (USCIS newsroom, Study in the States / SEVP).
3. Normalize to a common `RawItem` shape and **dedupe** by `source_id` — both against the DB
   and within the current batch (overlapping query terms can return the same document twice).
4. For each new item, `summarize_news()` produces a plain-language summary and a visa-category
   classification; store title + summary + source URL only (never full article text).

The pipeline is **idempotent**, so scheduled re-runs are safe. `scripts/fetch_news.py` wraps
it with its own DB session so it runs independently of the API — identical whether invoked by
a Kiro hook (dev) or EventBridge→Lambda (prod).

## 7. API surface

```
POST /auth/signup        POST /auth/login       GET /auth/me       PATCH /auth/me
GET  /posts (?category)  POST /posts            GET /posts/{id}    POST /posts/moderate
POST /posts/{id}/answers POST /answers/{id}/best
POST /votes
POST /search
GET  /news (?category)   POST /news/refresh
GET  /meta/categories    GET /healthz
```

## 8. Production deployment (target)

| Concern | Local (this repo) | Production (AWS) |
|---|---|---|
| API | uvicorn | ECS Fargate or Lambda + API Gateway |
| Database | SQLite file | RDS Postgres |
| Embeddings / search | in-process cosine | pgvector or OpenSearch Serverless |
| AI | LocalProvider default | Bedrock (Claude + Titan) via IAM role |
| News ingest | Kiro hook / manual script | EventBridge schedule → Lambda |
| Secrets | `.env` | SSM Parameter Store / Secrets Manager |
| Frontend | Vite dev server | S3 + CloudFront static hosting |

The code is structured so this transition changes configuration and deployment wiring, not
application logic: the ORM models are Postgres-ready, the AI interface already has the Bedrock
implementation, and the ingestion entry point is already a standalone callable.

## 9. Security notes

- JWT auth, bcrypt hashing, 401 on missing/invalid tokens for protected routes.
- Anonymity enforced centrally and covered by a test.
- All externally fetched content treated as untrusted; embedded instructions are never
  executed. Prompts to the LLM instruct it to summarize only provided content.
- No secrets in code; configuration is environment-only with a committed `.env.example`.
