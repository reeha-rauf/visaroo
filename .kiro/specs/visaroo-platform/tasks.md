# Implementation Plan

- [x] 1. Backend scaffolding & config
  - Create FastAPI app, config (env), database engine/session, health route.
  - Add requirements.txt and .env.example (AI_PROVIDER=local default).
  - _Requirements: 6.1_

- [x] 2. Data model & schemas
  - SQLAlchemy models: User, Post, Answer, Vote, NewsItem.
  - Pydantic schemas with anonymity-safe serialization.
  - _Requirements: 1, 2.2_

- [x] 3. Auth
  - Signup/login/me/update; JWT; bcrypt; current-user dependency; 401 on bad token.
  - _Requirements: 1.1, 1.3, 1.4, 1.5_

- [x] 4. AI provider abstraction
  - provider.py interface + factory; local.py deterministic fallback; bedrock.py.
  - _Requirements: 3, 4, 6.1, 6.2, 6.3_

- [x] 5. Community Q&A
  - Posts CRUD (+category filter), answers, votes (unique), best-answer.
  - Store post embedding on create.
  - _Requirements: 2.1–2.6_

- [x] 6. AI Gatekeeper on posting
  - moderate_post integration; soft-warn response; suggestions; preview endpoint.
  - _Requirements: 3.1–3.4_

- [x] 7. AI Search
  - Embed query, cosine rank posts, summarize matched posts, grounding + sources.
  - _Requirements: 4.1–4.5_

- [x] 8. News ingestion + feed
  - Federal Register + RSS fetch, dedupe (DB + in-batch), AI summarize/classify,
    personalized feed. scripts/fetch_news.py wrapper. Verified against live API.
  - _Requirements: 5.1–5.5_

- [x] 9. Frontend
  - Auth context + pages: Feed, Search, PostDetail, NewPost, News, Profile, Login/Signup.
  - Gatekeeper soft-warn UX; search summary card; disclaimer banner; Visaroo branding.
  - _Requirements: 1–5_

- [x] 10. Kiro hooks
  - News fetch hook (SessionStart) + backend tests-on-save + responsible-AI review hook.
  - _Requirements: 5.1_

- [x] 11. Tests
  - Auth, anonymity non-leak, voting uniqueness, local provider determinism, search
    grounding. Run under AI_PROVIDER=local. 8/8 passing.
  - _Requirements: 1–6_

- [x] 12. Docs
  - README technical write-up + docs/ARCHITECTURE.md + Bedrock enablement steps +
    seed_demo.py for demos.
  - _Requirements: all_
