---
inclusion: always
---

# Visaroo — Product Steering

## What Visaroo is
Visaroo is a unified community + information platform for international students and
visa holders in the United States (F-1, OPT, STEM OPT, H-1B, H-4, J-1, green card
applicants, and related categories).

The mascot is a kangaroo 🦘 — the pouch represents keeping your immigration status
safe, and kangaroos evoke migration and movement.

## Who it is for
People living with visa uncertainty: students on F-1/OPT, workers on H-1B, dependents
on H-4/J-2, and anyone trying to understand constantly-changing US immigration rules.
The founder is an international student on OPT — this is a "solve what is close to you"
project.

## The core problem
Three kinds of knowledge are scattered across different places and never combined:
1. **Official truth** — what the rules actually say (USCIS, SEVP, Federal Register).
2. **Lived experience** — what actually happened to real people in the same situation.
3. **Personal context** — my specific visa type and dates.

Visaroo brings community lived-experience together with official news, with an AI layer
that keeps the community useful and trustworthy.

## v1 feature set
1. **Accounts & profiles** — sign up, set visa type, post with real name or anonymously.
2. **Community Q&A** — post questions, answer, upvote/downvote, visa-category tags,
   mark a best answer (Reddit/Quora hybrid).
3. **AI Gatekeeper** — when a user posts, AI checks relevance to the visa/immigration
   domain, suggests a visa-category tag and a cleaner title, and flags harmful content
   (e.g., encouraging fraud). Behavior is **soft-warn**, never a hard block.
4. **AI Search** — Google/Perplexity-style. User types a problem; AI produces a
   summary first (grounded ONLY in matching community posts in v1), then shows the
   ranked source posts underneath.
5. **News feed** — pulls from the Federal Register API and curated RSS sources,
   AI-summarizes each item in plain language, classifies the affected visa category,
   and filters/ranks the feed by the logged-in user's visa category.

## Stretch (not v1)
- Personal deadline tracker (OPT unemployment days, filing windows, EAD/program dates).
- Official-source RAG inside search (v1 search summarizes community posts only).
- Verified attorney/DSO flair.

## Product principles
- **Trust over flash.** This domain is high-stakes. Never fabricate rules or dates.
- **Always link to the source.** Especially for news and any rule statements.
- **Community voice first in search.** v1 search reflects what the community said,
  clearly labeled as community experience, not legal fact.
- **Lower the fear of asking.** Anonymous posting is a first-class feature.
