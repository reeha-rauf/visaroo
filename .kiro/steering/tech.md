---
inclusion: always
---

# Technical Conventions Steering

## Stack
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, SQLite for local dev (Postgres-ready).
  Pydantic v2 for schemas. JWT auth with password hashing (passlib/bcrypt).
- **Frontend:** React (Vite) + TypeScript, React Router, plain CSS modules / lightweight
  styling (no heavy UI framework required). Axios for API calls.
- **AI:** Amazon Bedrock (Claude for text generation, Titan for embeddings) accessed via
  boto3, behind a provider interface with a deterministic local fallback.

## AI provider abstraction (critical)
- All AI calls go through `app/ai/provider.py` which defines an `AIProvider` interface:
  `moderate_post()`, `summarize_search()`, `embed_text()`, `summarize_news()`.
- Two implementations:
  - `BedrockProvider` — real AWS Bedrock calls.
  - `LocalProvider` — deterministic, no-network fallback (keyword heuristics +
    extractive summaries) so the app ALWAYS runs and demos even without Bedrock access.
- The active provider is chosen by env var `AI_PROVIDER` (`bedrock` | `local`,
  default `local`). This prevents being blocked on AWS model-access approval.

## Project layout
```
backend/
  app/
    main.py            # FastAPI app + router registration
    config.py          # settings via env
    database.py        # engine/session
    models.py          # SQLAlchemy models
    schemas.py         # Pydantic schemas
    auth.py            # JWT + password hashing
    deps.py            # shared dependencies (current user, db session)
    ai/
      provider.py      # AIProvider interface + factory
      bedrock.py       # BedrockProvider
      local.py         # LocalProvider fallback
    routers/
      auth.py, posts.py, answers.py, votes.py, search.py, news.py
    services/
      news_ingest.py   # Federal Register + RSS ingestion
  requirements.txt
  .env.example
frontend/
  src/
    api/, components/, pages/, context/
  package.json
scripts/
  fetch_news.py        # callable by the Kiro hook / EventBridge
```

## Conventions
- Keep routers thin; put logic in services where it grows.
- Use dependency injection for the DB session and current user.
- Return Pydantic schemas, never raw ORM objects.
- Never leak author identity for anonymous posts in any response.
- Env config only; never hardcode secrets or region. Provide `.env.example`.
- Prefer small, composable functions. Add docstrings on public functions.

## Running (local)
- Backend: `uvicorn app.main:app --reload` from `backend/` (venv with requirements).
- Frontend: `npm install && npm run dev` from `frontend/`.
- Default `AI_PROVIDER=local` so no AWS credentials are needed to run.

## Visa categories (canonical list — reuse everywhere)
`F-1`, `OPT`, `STEM-OPT`, `H-1B`, `H-4`, `J-1`, `L-1`, `Green-Card`, `Other`.
