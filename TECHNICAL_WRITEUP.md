# Visaroo — Technical Write-up

## 1. Project overview

**Problem & target users.** International students and visa holders in the US (F-1, OPT, STEM OPT,
H-1B, H-4, J-1, green-card applicants) face high-stakes decisions under constant policy
uncertainty, with information scattered across official sites and informal forums. A wrong
move (too many OPT unemployment days, a missed filing window, risky travel) can cost
someone their status.

**Solution.** A single platform that unifies **official news**, a **trustworthy community**,
a **personal profile + deadline tracker**, **webinars**, a **verified-creator feed**, an
**Ask / impact explainer**, and **legal-help preparation**, with an AI layer that stays
grounded and a responsible-AI posture throughout (never legal advice, always cited).

**Key features (shipped).**
1. **Community Q&A:** anonymous posting, voting, category tags, best answers.
2. **AI gatekeeper + search:** soft-warn relevance gatekeeping with auto-tagging, and
   summary-first semantic search over community posts.
3. **News feed:** Federal Register API + official RSS (Really Simple Syndication, the standard
   web feed format agencies publish updates through), AI plain-language summaries,
   per-visa-category ranking.
4. **User profile:** onboarding + full editor; sensitive fields **encrypted at rest with
   AWS KMS**; derived personalization context feeds the AI (never raw data).
5. **Deadline tracker:** deterministic, LLM-free deadline math (OPT/STEM windows, grace,
   SEVP, expiries) with urgency tiers, unemployment counter, `.ics` export, and SES email
   reminders.
6. **Persistent countdowns:** pin any deadline or custom date as a live, server-persisted
   countdown shown in a dockable timer on every page (built on the deadline-tracker's
   client-side date math).
7. **Webinars:** visa-filtered, local-timezone, role-gated creator posting.
8. **Creator feed + Ask/impact explainer:** labeled creator news matched to official
   sources by vector similarity, and a grounded "does this affect me?" Ask panel with
   citations and a rule-status label.
9. **In-app notifications:** write-site-generated alerts (new answer, upvote, best answer)
   with unread counts and anonymity preserved.
10. **Community profile & legal help:** a "My Posts" view of your questions/answers, plus a
    client-side **case-brief generator** and a curated attorney/legal-aid directory.


**Why this matters & who adopts it.** There are roughly **1.1 million international students**
in the US (IIE Open Doors) plus hundreds of thousands more on H-1B/H-4/J-1 and in green-card
backlogs: a large, motivated audience that already self-organizes in scattered Reddit,
Discord, and WhatsApp groups because no trustworthy, visa-aware home exists. That
existing behavior is the adoption wedge: Visaroo gives those conversations somewhere grounded
and searchable to live.

- **Beachhead to expansion.** Start with one high-anxiety cohort (F-1/OPT students at a few
  universities) where the deadline tracker and OPT unemployment counter deliver immediate,
  personal value, then expand along the natural visa lifecycle (OPT to STEM OPT to H-1B to
  green card), which doubles as a built-in retention path as users' status evolves.
- **Distribution.** International-student offices and DSOs are natural partners (the case-brief
  and deadline features reduce repetitive advising load); student orgs and existing online
  communities are low-cost referral channels.
- **Why people come back.** Deadlines, reminders, and personalized news are recurring,
  time-sensitive needs, not one-and-done, so the profile + reminder loop drives repeat use,
  while the community compounds in value as more lived experience accumulates.
- **Trust as the moat.** The responsible-AI posture (grounded, cited, never legal advice,
  anonymity-protected) is exactly what a cautious, high-stakes audience needs to adopt a tool
  about their immigration status, and what generic forums and generic chatbots don't offer.

## 2. Design decisions

**Technology choices.**
- **FastAPI + SQLAlchemy + SQLite→Postgres.** FastAPI gives typed, self-documenting APIs and
  pairs naturally with Pydantic. SQLite keeps local setup zero-friction; the same models run
  on Postgres in production.
- **React + Vite + TypeScript.** Fast dev loop, type safety across the API boundary via a
  shared `types.ts`, no heavy UI framework needed.
- **Amazon Bedrock (Claude + Titan)** for generation and embeddings, behind a provider
  interface.

**From an AWS-native plan to pragmatic choices.** The project was first scoped as a fully
AWS-native serverless design (DynamoDB, Cognito, Lambda + API Gateway, EventBridge). As the
build progressed I deliberately simplified to a single FastAPI service with SQLAlchemy, JWT
auth, and SQLite, for three reasons: it keeps the whole app runnable with zero AWS setup (and
therefore demoable even while Bedrock quota was still provisioning), it collapses many moving
parts into one testable codebase under a tight deadline, and it stays portable (the same
SQLAlchemy models move to Postgres, and the same contracts could move to the serverless
services later). The
design docs describe this actual stack; the AWS-native version is noted as a future scaling
path rather than presented as what runs today.


**The most important decision: env-switched provider abstractions with local fallbacks.** Each
AWS integration (AI via Bedrock, encryption via KMS, email via SES) sits behind an interface
with a local fallback chosen by an env var, so a cloud error degrades gracefully and the whole
app runs with zero AWS setup. This mattered most for AI: my account's Bedrock access was stuck
in new-account provisioning (zero token quota during verification), so the fallback is what let
the demo work. The local providers use simpler heuristics than the cloud models, but they stay
honest: they never fabricate rules, and grounded features answer only from retrieved documents.

**Grounding & responsible AI.** The impact explainer and creator-feed matcher are built so the
AI answers **only** from retrieved documents (a Bedrock Knowledge Base in production, the
ingested news corpus locally), cite sources, and refuse when nothing is retrieved. The
source-match decision is a similarity score vs. a hardcoded 0.75 threshold, never the LLM's
judgment. Every AI surface carries a "not legal advice" disclaimer.

**Alternatives considered.**
- *Vector database (OpenSearch Serverless / pgvector)* for search. For a demo-sized corpus,
  in-process cosine similarity over stored embeddings is simpler and fast enough; the design
  documents the swap-in path for scale.
- *RAG over official rules inside search.* Deferred to keep v1 honest: v1 search summarizes
  **only** community posts (clearly labeled as experience, not law), avoiding any appearance
  of giving authoritative legal answers.
- *A news API (NewsAPI/Bing).* Rejected in favor of the free, key-less, authoritative
  **Federal Register API** plus official RSS: better provenance, no cost or rate-limit risk.

**Security & responsible-AI considerations.**
- JWT auth, bcrypt password hashing, protected routes via dependency injection.
- **Anonymity is enforced server-side** in one serialization layer: the author FK is stored
  for integrity but never serialized for anonymous posts (there's a test for this).
- Every AI surface carries a visible "not legal advice" disclaimer; the search summary states
  how many posts it used and links them; news always links to the original source and never
  republishes full article text.
- The gatekeeper is deliberately **soft-warn**: it warns and auto-tags but never blocks, so a
  genuine question is never silenced.
- External content (RSS, Federal Register, user posts) is treated as untrusted input.

**Scalability considerations.**
- Stateless API allows horizontal scaling behind a load balancer; SQLite moves to Postgres
  via the same ORM models.
- News ingestion is **idempotent** (dedupe by `source_id`, including within a single batch),
  so it's safe to run on a schedule: locally via a Kiro hook, in production via a scheduled
  job calling the same `scripts/fetch_news.py` logic.
- Embeddings move from in-process cosine to pgvector / OpenSearch Serverless at scale.

## 3. Kiro usage

Visaroo was built inside Kiro end to end, from first product conversation to deployment. The
`.kiro/` directory is committed and shows the workflow: 7 specs, 7 steering files, and 4
agent hooks. This section covers each capability I leaned on.

### Vibe coding (how I structured conversations)

Before any spec existed, the product itself was shaped through open conversation. I used a
repeatable four-beat structure for those chats:

1. **Pick the problem** in plain language ("a platform for people on visas").
2. **Pressure-test the scope** out loud, letting the idea grow and then cutting it back
   (community + news + profile + deadlines + webinars + creator feed + a grounded Ask).
3. **Lock decisions** explicitly before writing code: the name (Visaroo 🦘), the theme, and the provider-abstraction rule.
4. **Then spec** the locked decision.

Keeping conversations in that shape stopped the classic vibe-coding failure of a model generating a big, incoherent blob. Each chat ended with a small, buildable unit.

The **best generation moments** were the ones anchored by context that was already locked in.
Two stand out: the env-switched **provider abstractions** (`AIProvider` / `CryptoProvider` /
`EmailProvider`) and the **anonymity-safe serialization layer** both came out correct on the
first pass, because the "runs without AWS" rule and the "never leak an anonymous author" rule
were already in steering when the code was generated, so I didn't have to retrofit them. The
later UI/feature works in the same session also benefited: each inherited existing rules automatically rather
than reintroducing them.

### Spec-driven development (how I structured specs, and how it compared)

The whole platform was specified before implementation in `.kiro/specs/visaroo-platform/`:
`requirements.md` (EARS-style acceptance criteria per feature, including the "runs without AWS"
reliability requirement), `design.md` (data model, the `AIProvider` interface, search and
ingestion flows, the API surface), and `tasks.md` (ordered, requirement-linked tasks). Each
later feature got its **own per-feature spec**, giving seven in total: `visaroo-platform`,
`profile`, `deadline-tracker`, `webinars`, `creator-feed`, `impact-explainer`, and
`attorney-help`, each with the full requirements/design/tasks trilogy.

**How I structured a spec:** requirements first (numbered, testable, with the non-negotiables
called out), then a design doc describing the real stack it would be built on (SQLAlchemy
models, FastAPI routers, JWT auth with a `User.role` check, Pydantic schemas, and the provider
abstractions), then a task list where each task cites the requirement it satisfies. Keeping the
design docs aligned to the actual stack made the "spec says X, code does X" link tight.

**Spec vs. vibe coding, concretely:** vibe coding was faster and better for exploration and for
small, self-contained UI work; specs were indispensable when a feature touched more than
one layer. With a spec, "done" was unambiguous due to the acceptance criteria, scope didn't drift,
and when I came back to a feature after a break I could re-read one document instead of
reconstructing intent from a chat log. The honest tradeoff is upfront cost: writing a spec for
a tiny feature is overkill, so the countdown/notifications/My-Posts additions later in the
build were done vibe-style against the already-established patterns rather than as new specs.

### Steering docs (how they improved responses, and the best strategy)

Seven always-on steering files encoded the project's non-negotiables so every generation
respected them without re-explaining: `product.md` (what/who/scope), `responsible-ai.md` (no
legal advice, always ground/cite, soft-warn not hard-block, protect anonymity, treat external
content as untrusted), `tech.md` (stack, the provider-abstraction rule, layout, canonical visa
categories), plus four feature-scoped files (`profile.md`, `deadline-tracker.md`,
`creator-feed.md`, `impact-explainer.md`), each loaded as context for its feature.

**The single highest-leverage strategy was putting the responsible-AI rules in steering rather
than in prompts.** Because those rules were always in context, safe behavior came out *by
default* instead of being bolted on afterward: the gatekeeper generated as soft-warn (never a
hard block), the grounded features generated already citing sources and refusing when nothing
was retrieved, the deadline math generated LLM-free (pure functions), and the "not legal
advice" disclaimer appeared on AI surfaces without being asked for. In a high-stakes,
immigration-adjacent domain, that default-safe posture is the difference between a trustworthy
tool and a liability.

The rules kept paying off for work added much later in the build: the persistent-countdown
timer reused the deadline-tracker's "the LLM never computes dates" rule unchanged, and the
notifications feature inherited the anonymity rule automatically (an anonymous answerer is
never named in a notification) because that constraint was already steering context.

### Agent hooks (what I automated, and how it improved the process)

Four hooks live in `.kiro/hooks/`:

- `backend-tests-on-save.json` runs the hermetic pytest suite whenever a backend `.py` file is
  saved. This tightened the feedback loop to near-zero: regressions in auth, the anonymity
  non-leak guarantee, voting, gatekeeping, or search grounding showed up the instant I saved,
  not at some later "let me run tests" moment.
- `responsible-ai-review.json` triggers a review against `responsible-ai.md` whenever any
  `backend/app/ai/` file changes. This is the one most valuable to the project: it automated
  the review step most likely to be skipped under time pressure. It fired during this build
  when the Bedrock provider was switched to the model-agnostic Converse API and confirmed the
  change kept all four responsible-AI guarantees (no legal advice, grounded search, soft-warn
  gatekeeper, graceful local fallback) intact.
- `fetch-news.json` runs the news-ingestion pipeline on session start, so the feed is always
  fresh without a manual step (the dev counterpart to a production scheduled job).
- `send-deadline-reminders.json` runs the reminder checker so the email path is exercised
  without waiting for a real cron schedule.

Net effect: the hooks turned "things I should remember to do" (run tests, re-check AI safety,
refresh data) into things that happened automatically, which is what let me move quickly
without the safety and data-freshness guarantees quietly rotting.

### AWS provisioning from inside Kiro

The cloud setup also ran through Kiro: creating the KMS key, SES identity, S3 buckets, the ECR
repo, the App Runner service and its IAM roles, and CloudFront, all driven and verified from
inside the session via the AWS CLI and captured as reusable JSON in `deploy/`. Live testing
through Kiro is also what surfaced the real Bedrock issues described in section 4 (region,
inference profiles, quota) that static code could never have revealed.

### MCP (extending Kiro's capabilities)

Kiro used the **AWS MCP server** to go
beyond editing code and actually reach into my AWS account from inside the session: listing
Bedrock foundation models, running real `Converse` test invocations across regions, and reading
the exact **Service Quotas** values. That live access is what let Kiro diagnose the problem
precisely, that every Bedrock quota was literally `0` while the account finished verification,
rather than guessing from the generic `ThrottlingException` messages. It also tested the same
call across us-east-2, us-west-2, and eu-west-1 to prove the block was account-level, not
model- or region-specific, and surfaced the actual AWS verification notice.

Kiro used these MCP tools effectively in two ways worth calling out: it loaded them on demand
only when a task needed them, and it chained read calls
together to form a diagnosis (list models → test invoke → read quota → compare regions) instead
of making one isolated query. Without MCP, that whole investigation would have meant me copying
AWS CLI output back and forth by hand; with it, the diagnosis happened in the same loop as the
code changes. The clearest future MCP use is in the product itself: a server exposing **live
USCIS case-status or the monthly Visa Bulletin** would let the Ask panel answer the
time-sensitive personal questions it currently refuses by design.

## 4. Learning journey & forward thinking

### Biggest challenges and how I overcame them

- **The Bedrock access maze.** Getting real AI running surfaced a chain of
  issues that static code could never reveal, each with a *different* error message: the model
  I wanted only existed in **us-east-2** (not the us-east-1 I first tried); newer Claude models
  require a **cross-region inference profile** (the `us.` prefix) instead of a raw model ID;
  and, most blocking of all, a brand-new account starts with **every Bedrock quota at zero**
  while the account finishes **verification**, which throttles every call regardless of model
  or region. I diagnosed it from the inside out (querying quotas directly, testing across
  regions to prove it was account-level), which pinned the cause to verification rather than my
  config. The practical resolution was to
  (a) switch the provider to the model-agnostic **Converse API** so the model becomes a
  one-line config change, and (b) rely on the local fallback for the demo while verification
  completes.
- **Not getting blocked on AWS at all.** The provider-abstraction + local-fallback pattern was
  the single best decision for a time-boxed build: neither development nor the demo ever
  depended on cloud access. It paid off literally, because at demo time the Bedrock quota was
  still provisioning and the app kept working with zero changes.
- **A real bug only live testing caught.** The first news ingest crashed on a `UNIQUE`
  constraint because overlapping Federal Register query terms returned the same document twice
  in one run. Fixed by deduping **within the batch** (not just against the DB) and verified
  idempotent. Running against the real API surfaced it; a mock never would have.
- **A silent data foot-gun.** A relative SQLite path meant the API server and the seed scripts
  were reading/writing *different* database files depending on the working directory. Fixed by
  anchoring to an absolute path.
- **Tooling friction.** The shell frequently swallowed CLI output, so I learned to verify every
  AWS resource and command with a second, targeted query rather than trusting a silent exit
  code.

### What I'd do differently, and skills gained

- **Smoke-test each cloud service on day one.** One tiny real call to Bedrock / KMS / SES at
  the start would have surfaced the region, inference-profile, and quota issues days earlier
  instead of at deploy time. "The code is correct" is not the same as "the account can run it."
- **Request Bedrock quota the moment the account is created,** since new-account verification
  and zero quotas are now a known, days-long lead time rather than a surprise.
- **Add migrations from the start.** Using `create_all` meant every schema change (new column)
  forced a delete-and-reseed. Alembic from day one would have made schema evolution painless.
- **Skills gained.** Writing responsible-AI constraints as *steering before code* (safe-by-
  default beats retrofitting); designing provider abstractions so a project is never tied to
  one vendor's provisioning; and diagnosing cloud issues empirically (quotas, regions,
  inference profiles) instead of trusting error strings at face value.

### Feedback received

The clearest input came from **talking with visa-holder friends** across F-1, OPT/STEM OPT,
and H-1B before and during the build. The recurring themes from those conversations shaped the
feature set directly: anxiety about tracking OPT **unemployment days** became the unemployment
counter; repeatedly **second-guessing travel** and filing windows became the deadline tracker
and the grounded Ask panel; and the fear of asking "obvious" questions in public forums became
**anonymous-first** community posting. The strongest signal was consistent: people didn't want
another chatbot guessing at law; they wanted the official rule, its status (proposed vs. in
effect), and what others in their exact situation actually did, which is the core of what
Visaroo organizes.

### Product and feature additions

- **Live official data via MCP.** An MCP server exposing USCIS case-status and the monthly Visa
  Bulletin would let the Ask panel answer the time-sensitive personal questions it currently
  refuses by design.
- **Richer grounded Ask.** Once the managed Knowledge Base is live, the Ask panel gains
  production-grade RAG plus streaming responses, so answers appear token-by-token instead of
  all at once.
- **Trust features.** Verified DSO/attorney flair, and semantic "similar questions" dedup at
  posting time to keep the community clean as it grows.
- **Onboard real creators.** Reach out to the immigration creators and newsletters I already
  follow and bring them in as verified creators, so the feed launches with trusted, familiar
  voices.
- **Partner with immigration lawyers.** Advertise to and recruit immigration attorneys to
  improve access to qualified legal help through the platform.
- **Mobile app.** A native mobile app for accessibility and convenience, so deadlines,
  reminders, and the Ask panel are within reach.
- **University and DSO features.** Dedicated functionality for universities and DSOs (e.g.
  managing their students' common questions and deadlines), giving institutions a reason to
  bring their whole international-student population onto Visaroo.
- **Tax help section.** Taxes are a top source of confusion for international students
  (nonresident vs. resident status, the F-1 5-year rule, treaty benefits, Forms 8843 /
  1040-NR, FICA exemptions). A tax section would explain the general rules in plain language,
  flag likely status, and point to official IRS resources and school-provided filing tools,
  following the same "information, not tax advice" posture as the rest of the app, with specific
  situations routed to a qualified tax professional.

### Scaling and infrastructure

- **Real Bedrock Knowledge Base + higher quota.** The corpus is already staged in S3; standing
  up the managed KB (and raising the token quota once verification clears) replaces the local
  retrieval fallback, with a Bedrock Guardrail as the enforced safety layer.
- **Durable data layer.** Move from container-local SQLite to a managed database (RDS/Aurora
  Postgres via the same SQLAlchemy models) so user accounts and posts persist across restarts,
  and run the reminder job on a managed schedule.
- **Scaling path.** The API is stateless (horizontal scaling behind a load balancer), news
  ingestion is already idempotent and schedulable, and search embeddings move from in-process
  cosine similarity to pgvector or OpenSearch Serverless as the corpus grows.