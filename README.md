# 🦘 Visaroo

**A community + information platform for international students and visa holders in the US.**

Visaroo brings together the three kinds of knowledge a visa holder needs and never finds
in one place: what the **rules** actually say, what **actually happened** to real people
in the same situation, and what any of it means for **your** specific visa type. An AI
layer keeps the community relevant, safe, and searchable.

> ⚠️ **Visaroo provides general information and community experiences, not legal advice.**
> Always verify with your DSO or an immigration attorney.

Built for the AWS "Within Reach Kiro Hackathon 2026" hackathon.

**🎥 Demo video:** https://youtu.be/JekyxTTxkSU

**📄 Technical write-up:** [TECHNICAL_WRITEUP.md](TECHNICAL_WRITEUP.md)

---

## Table of contents-visaroo)
- [Features](#features)
- [Quick start](#quick-start)
- [Live deployment (AWS)](#live-deployment-aws-us-east-2)
- [AWS cloud integration](#aws-cloud-integration)
- [Architecture](#architecture)
- [Project structure](#project-structure)
- [Testing](#testing)

---

## Why Visaroo

International students and visa holders live with constant uncertainty: OPT unemployment
limits, STEM extension filing windows, H-1B lottery odds, travel risk, policy changes that
land as dense government text. The information that exists is scattered across USCIS pages,
your DSO's inbox, and a dozen Reddit/Discord/WhatsApp threads. Official sources tell you the
rules but they never tell you what happened to someone who was in your exact spot.

Visaroo combines **official news** (summarized and personalized) with a **community** where
people share lived experience, and uses AI to keep that community trustworthy by screening
posts on the way in and summarizing answers on the way out.

The recent stream of policy shifts and
proposed rule changes (around OPT and STEM OPT, H-1B selection, visa stamping and travel, and
grace periods) has left people unsure on what actually applies to them right now,
what's only proposed, and what already changed. That
confusion, and the anxiety that comes with it, is a big part of what motivated me to build
Visaroo: to clearly separate what the rules say, what status a change is in (proposed vs.
final vs. in effect), and what it means for a specific visa type.

This isn't only my own experience. I talked with several visa-holder friends to understand their real stories. Those conversations helped shape the feature set, from the deadline tracker
and unemployment counter to the grounded "does this affect me?" Ask panel and the
anonymous-first community.

## Features

| Feature | What it does |
|---|---|
| **Accounts & profiles** | Sign up, set your visa category, post with your name or **anonymously** (identity never leaked by the API). |
| **Community Q&A** | Ask questions, answer others, upvote/downvote, tag by visa category, mark a best answer. |
| **AI Gatekeeper** | On posting, AI checks topical relevance, suggests a category + cleaner title, and flags harmful content. **Soft-warn, never a hard block**, so a real question is never silenced. |
| **AI Search** | Type a problem, get an **AI summary first** (grounded only in matching community posts, with a source count), then the ranked posts behind it. |
| **News feed** | Pulls real items from the **Federal Register API** + curated official **RSS**, AI-summarizes each in plain language, classifies the affected visa category, and ranks your category first. |
| **User profile** | A guided 3-step onboarding + full profile editor: visa type & phase, key dates with proximity badges, **computed deadline estimates** (OPT window, STEM filing window, grace period, unemployment-days remaining), travel, DSO/attorney contacts, notification preferences, and privacy controls (data export + delete). Sensitive fields are **encrypted at rest with AWS KMS**. |
| **Personalized AI** | With consent, the profile contributes **derived, non-identifying facts** (counts/booleans only, never raw dates or case numbers) to tailor AI search answers to your status. |
| **Deadline tracker** | Computes every immigration-critical deadline from your profile with **deterministic, LLM-free formulas** (OPT/STEM windows, grace periods, SEVP 10-day reporting, I-94/EAD/passport expiry), tags each with an urgency tier, tracks the unemployment-day cap, supports manual overrides, exports to calendar (`.ics`), and sends **email reminders** at your chosen lead times. Each formula is unit-tested and cites the governing CFR section. |
| **Webinars** | Upcoming immigration webinars filtered to your visa type (with an "All" view), shown in **your local timezone**, with a "show past" toggle. Verified creators and admins can post webinars (role-gated); anyone can open the registration link. |
| **Creator feed** | Verified creators post fast, labeled news commentary (`reported` / `proposed` / `final` / `in effect`).  |
| **Persistent countdowns** | Pin any tracked deadline (or a custom personal date) as a **live countdown** that persists server-side across sessions and devices. A dockable timer on the left edge of every page shows the soonest one ticking down to the second, color-coded by urgency. Dates stay client-computed; the countdown only displays them. |
| **In-app notifications** | A notifications bell alerts you when someone answers your question, upvotes your post/answer, or marks your answer best. Generated at the write sites with unread counts, mark-read, and **anonymity preserved** (an anonymous actor is never named). |
| **My Posts** | A dedicated page listing everything you've asked and answered, split into Questions and Answers tabs, each linking back to the thread (with best-answer and score badges). |
| **Legal help** | Generates a shareable **case brief** from your profile + upcoming deadlines (visa status, key dates, unemployment, suggested questions), built entirely client-side, never sent to a server. Copy, download `.txt`, or email it to your DSO, plus a curated directory of legitimate attorney / free-legal-aid / government resources. Not legal advice, no attorney marketplace. |
| **Ask / Impact explainer** | A slide-in **"Ask Visaroo"** panel on every page answers "does this rule affect me?", grounded **only** in retrieved official documents (Bedrock Knowledge Base, or the ingested news corpus), with numbered **citations**, a rule-status chip (proposed / final / in effect), and your derived personalization context. Refuses to answer when it has no sources, carries a per-response "not legal advice" disclaimer, and supports follow-up questions. |

## Quick start

Prereqs: **Python 3.11+** and **Node 18+**. No AWS account required to run locally; the AI
layer defaults to a deterministic local provider.

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env       # macOS/Linux: cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

API now at `http://localhost:8000` (interactive docs at `/docs`).

### 2. Seed demo data (optional but recommended for a demo)

From the **repo root**, with the backend venv active:

```bash
python scripts/seed_demo.py     # creates demo users + posts + answers
python scripts/fetch_news.py    # pulls real immigration news from official sources
```

Demo login: `maya@demo.com` / `password123`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The dev server proxies `/api` to the backend on port 8000.

## Live deployment (AWS, us-east-2)

Visaroo was deployed on AWS to prove out the full cloud path. **The backend App Runner service
is currently paused to avoid ongoing cost**, so the hosted frontend has no live API to talk to.
To run or evaluate the app, use the [Quick start](#quick-start) above (localhost); it's the
intended way to review it and needs no AWS account. The deployment details below document the
architecture that was stood up and can be resumed at any time.

| Component | Service | URL / identifier |
|---|---|---|
| **Frontend** | S3 + CloudFront (OAC, HTTPS, SPA fallback) | https://d3a97o58gvqmqx.cloudfront.net |
| **Backend API** | App Runner (container from ECR) | https://3gixvis6vu.us-east-2.awsapprunner.com (paused) |
| **AI** | Amazon Bedrock (Claude via the model-agnostic Converse API + Titan embeddings) | model access granted; on-demand token quota pending new-account verification, so it degrades to the local provider |
| **Encryption** | AWS KMS | `alias/visaroo-profiles` |
| **Email** | Amazon SES | `reeyarauf@gmail.com` (sandbox) |
| **KB corpus** | S3 | `visatrack-kb-documents-<acct>-ue2` (Knowledge Base optional) |

The backend runs the FastAPI container on App Runner with an instance IAM role granting
Bedrock / KMS / SES. SQLite lives in the container and is re-seeded on each deploy by
`docker-entrypoint.sh`. The frontend is built with `VITE_API_BASE` pointing at the App
Runner URL and served via CloudFront with Origin Access Control over a private S3 bucket.

### Redeploy

**Backend** (after code changes):
```bash
docker build --platform linux/amd64 -t visaroo-backend .
docker tag visaroo-backend:latest <acct>.dkr.ecr.us-east-2.amazonaws.com/visaroo-backend:latest
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin <acct>.dkr.ecr.us-east-2.amazonaws.com
docker push <acct>.dkr.ecr.us-east-2.amazonaws.com/visaroo-backend:latest
aws apprunner start-deployment --service-arn <service-arn> --region us-east-2
```

**Frontend** (after code changes):
```bash
cd frontend
$env:VITE_API_BASE="https://3gixvis6vu.us-east-2.awsapprunner.com"; npm run build
aws s3 sync dist s3://visaroo-frontend-<acct> --region us-east-2 --delete
aws cloudfront create-invalidation --distribution-id E3F47O8IN4ECSA --paths "/*"
```

### Teardown (after the demo, to stop costs)
```bash
aws apprunner delete-service --service-arn <service-arn> --region us-east-2
aws cloudfront delete-distribution --id E3F47O8IN4ECSA   # disable first, then delete
aws ecr delete-repository --repository-name visaroo-backend --force --region us-east-2
aws s3 rb s3://visaroo-frontend-<acct> --force --region us-east-2
aws s3 rb s3://visatrack-kb-documents-<acct>-ue2 --force --region us-east-2
aws kms schedule-key-deletion --key-id alias/visaroo-profiles --pending-window-in-days 7 --region us-east-2
aws ses delete-identity --identity reeyarauf@gmail.com --region us-east-2
# then delete IAM roles VisarooAppRunnerAccessRole / VisarooAppRunnerInstanceRole
```

## AWS cloud integration

Visaroo uses **three real AWS services**, each behind an env-switched provider abstraction
with a local fallback so the whole app still runs with zero AWS setup for development and
demos:

1. **Amazon Bedrock**: the AI layer (Claude for text, Titan for embeddings): gatekeeper,
   search summarization, news summaries, and profile-personalized answers.
2. **AWS KMS**: cloud encryption at rest for sensitive profile fields (E-Verify number,
   employer EIN, petition receipt number), as required by the profile spec.
3. **Amazon SES**: delivers deadline-reminder emails (`EMAIL_PROVIDER=ses`); defaults to a
   logged local preview so reminders work without AWS.

`GET /healthz` reports the active AI and crypto providers.

### Enable Amazon Bedrock
1. In the AWS console, open **Bedrock → Model access** and request access to a text model
   (any Claude, Amazon Nova, etc.) and `amazon.titan-embed-text-v2` in your region. Approval
   is usually quick, but new accounts also start with a **near-zero on-demand token quota**
   until account verification completes, hence the local fallback.
2. Make AWS credentials available via the standard chain (env vars, `aws configure`, or an
   IAM role).
3. In `backend/.env` set:
   ```env
   AI_PROVIDER=bedrock
   AWS_REGION=us-west-2
   BEDROCK_TEXT_MODEL_ID=amazon.nova-lite-v1:0
   BEDROCK_EMBED_MODEL_ID=amazon.titan-embed-text-v2:0
   ```
   Text generation goes through Bedrock's **model-agnostic Converse API**, so the text model
   is pluggable: swap in any Converse-compatible id (e.g. a `us.anthropic.claude-*`
   cross-region inference profile) with no code change.
4. Restart the backend. If any Bedrock call fails at runtime (throttling, missing access,
   quota), that single call degrades gracefully to the local provider so a request never
   crashes.

### Enable AWS KMS (encryption at rest)
1. Create a symmetric KMS key (console or `aws kms create-key`) and note its id/ARN/alias.
2. Ensure your AWS credentials can `kms:Encrypt` / `kms:Decrypt` with that key.
3. In `backend/.env` set:
   ```env
   CRYPTO_PROVIDER=kms
   AWS_REGION=us-east-1
   KMS_KEY_ID=alias/your-visaroo-key   # or the key id / ARN
   ```
4. Restart the backend. Sensitive profile fields are now encrypted via KMS before being
   stored. The default `CRYPTO_PROVIDER=local` uses Fernet so fields are still encrypted
   at rest without any AWS setup.

### Enable Amazon SES (deadline reminder emails)
1. Verify a sender identity (email or domain) in the SES console.
2. In `backend/.env` set:
   ```env
   EMAIL_PROVIDER=ses
   AWS_REGION=us-east-1
   SES_FROM_EMAIL=you@yourdomain.com   # a verified SES identity
   ```
3. Run the reminder checker: `python scripts/send_reminders.py` (or `POST /deadlines/remind`).
   It sends one email per deadline per lead-time threshold, deduped via the `reminders_sent`
   table. The default `EMAIL_PROVIDER=local` logs an email preview instead of sending. In
   production this runs on a daily scheduled job.

## Architecture

```
┌─────────────────┐    REST/JSON (JWT)    ┌──────────────────────────────────┐
│  React + Vite   │  ──────────────────▶  │             FastAPI              │
│  (TypeScript)   │  ◀──────────────────  │        routers → services        │
└─────────────────┘                       │                                  │
                                          │  ┌────────────────────────────┐  │
                                          │  │  AIProvider interface      │  │
                                          │  │  ├ LocalProvider (default) │  │
                                          │  │  └ BedrockProvider ────────┼──┼──▶ Amazon Bedrock
                                          │  ├────────────────────────────┤  │     (Claude + Titan)
                                          │  │  CryptoProvider interface  │  │
                                          │  │  ├ LocalProvider (Fernet)  │  │
                                          │  │  └ KmsProvider ────────────┼──┼──▶ AWS KMS
                                          │  ├────────────────────────────┤  │     (encrypt at rest)
                                          │  │  EmailProvider interface   │  │
                                          │  │  ├ LocalProvider (preview) │  │
                                          │  │  └ SesProvider ────────────┼──┼──▶ Amazon SES
                                          │  └────────────────────────────┘  │     (reminder email)
                                          │                                  │
                                          │ SQLAlchemy ──▶SQLite / Postgres  │
                                          └──────────────────────────────────┘
                                                          ▲
                        news ingest  (scripts/fetch_news.py · Kiro hook / scheduled job)
                        ├─ Federal Register API (public JSON, real rule changes)
                        └─ Curated official RSS (USCIS, Study in the States / SEVP)
```

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the deep dive.

---

## Project structure

```
.
├─ .kiro/
│  ├─ steering/        product · responsible-ai · tech · profile · deadline-tracker · creator-feed · impact-explainer
│  ├─ specs/
│  │  ├─ visaroo-platform/   requirements.md · design.md · tasks.md
│  │  ├─ profile/            requirements.md · design.md · tasks.md
│  │  ├─ deadline-tracker/   requirements.md · design.md · tasks.md
│  │  ├─ webinars/           requirements.md · design.md · tasks.md
│  │  ├─ creator-feed/       requirements.md · design.md · tasks.md
│  │  ├─ impact-explainer/   requirements.md · design.md · tasks.md
│  │  └─ attorney-help/      requirements.md · design.md · tasks.md
│  └─ hooks/           fetch-news · backend-tests-on-save · responsible-ai-review · send-deadline-reminders
├─ deploy/             Dockerfile refs · App Runner / CloudFront / IAM / budget JSON
├─ corpus/             official-doc corpus for the Knowledge Base (+ manifest)
├─ backend/
│  ├─ app/
│  │  ├─ ai/           provider.py (interface) · local.py · bedrock.py   (incl. match_post)
│  │  ├─ crypto/       provider.py (interface) · local.py (Fernet) · kms.py (AWS KMS)
│  │  ├─ email/        provider.py (interface) · local.py (preview) · ses.py (Amazon SES)
│  │  ├─ routers/      auth · posts · votes · search · news · profile · deadlines · countdowns · webinars · creator_posts · ask · notifications · me
│  │  ├─ services/     news_ingest.py · reminder_checker.py · notifications.py
│  │  ├─ computed_dates · personalization · deadline_calc · profile_* · webinar_schemas · creator_post_schemas
│  │  ├─ models.py · schemas.py · serializers.py · auth.py · deps.py · config.py · main.py
│  └─ tests/           test_core · test_profile · test_deadlines · test_webinars · test_creator_posts · test_ask
├─ frontend/
│  └─ src/             pages/ · components/ · context/ · api/ · data/ · utils/ (+ tests) · lib/
├─ scripts/            fetch_news · seed_demo · seed_webinars · seed_creator_posts · send_reminders · check_bedrock · upload_corpus
└─ README.md · ARCHITECTURE.md · TECHNICAL_WRITEUP.md
```

## Testing

```bash
cd backend
.venv\Scripts\activate            # or source .venv/bin/activate
pytest -q
```

**53 backend tests** run hermetically against the local AI provider (no AWS, no network),
covering auth, the anonymity non-leak guarantee, vote uniqueness/toggling, the
single-best-answer rule, the gatekeeper's soft-warn behavior, search grounding with and
without matching posts, the deterministic deadline formulas and reminder dedup, profile
encryption round-trips, creator-feed source matching at the 0.75 threshold, and the grounded
Ask/impact-explainer (citations + refuse-when-empty). The frontend adds a Vitest suite over
the pure deadline-calculation utilities.

---

*Visaroo is an information and community tool, not a provider of legal advice.*
