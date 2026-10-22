# Design: Impact Explainer

The "Ask Visaroo" panel answers "does this rule affect me?" grounded only in retrieved
official documents, with numbered citations, a rule-status label, and the user's derived
personalization context. Built on Visaroo's stack: FastAPI + the `AIProvider` abstraction over
Amazon Bedrock, with a local fallback.

Grounding, citation-from-metadata-only, the no-info fallback, and the mandatory disclaimer are
enforced by `.kiro/steering/impact-explainer.md`.

## Architecture

```
Client (Ask panel)
  → POST /ask  (FastAPI, routers/ask.py)
    → build personalization context from the user's profile (derived facts only)
    → AIProvider.answer_impact(question, context, history, candidates)
        - retrieve top-3 relevant official docs
        - answer grounded ONLY in those docs, with citations + a rule-status label
    → return the answer + citations as JSON
```

`AIProvider.answer_impact` resolves to:
- **`BedrockProvider`** — retrieves from a **Bedrock Knowledge Base** (when
  `BEDROCK_KNOWLEDGE_BASE_ID` is set) or, if not, over the already-ingested `NewsItem` corpus,
  then calls Bedrock via the Converse API (temperature 0.1, max 800 tokens) with the grounded
  prompt. Any failure degrades gracefully to the local answerer.
- **`LocalProvider`** — a deterministic extractive answerer: ranks the candidate docs by
  overlap with the question, answers only from the top matches with citations, and returns the
  honest no-info fallback when nothing is relevant.

The retrieval step is not exposed separately to the client; one `/ask` call does it all.

---

## Document corpus

In production the corpus is a **Bedrock Knowledge Base** backed by an S3 data source of
curated official documents, embedded with Amazon Titan Embeddings V2. In the running
reference implementation, the same documents are represented by the ingested `NewsItem`
records (Federal Register + official RSS), so retrieval works with zero extra setup. Document
metadata carries `title`, `sourceUrl`, `documentType` (proposed_rule / final_rule / guidance /
faq), `visaTypeTags`, and `effectiveDate`.

### Priority corpus documents

| Document | Source | Visa types |
|---|---|---|
| 8 CFR 214.2(f) — F-1 student regulations | eCFR | F-1, OPT, STEM OPT |
| USCIS OPT overview page | USCIS.gov | OPT |
| USCIS STEM OPT overview page | USCIS.gov | STEM OPT |
| SEVP STEM OPT reporting requirements | ICE/SEVP | STEM OPT |
| SEVP employer reporting obligations | ICE/SEVP | OPT, STEM OPT |
| 8 CFR 214.2(h) — H-1B regulations | eCFR | H-1B |
| USCIS H-1B overview page | USCIS.gov | H-1B |
| H-1B cap season FAQ | USCIS.gov | H-1B |
| USCIS OPT unemployment FAQ | USCIS.gov | OPT, STEM OPT |
| Recent proposed rules (DHS, last 12 months) | Federal Register API | varies |
| Recent final rules (DHS, last 12 months) | Federal Register API | varies |

The `corpus/` directory holds the curated documents and a manifest for seeding the Knowledge
Base when one is configured.

---

## Prompt Design

### System prompt

```
You are Visaroo's immigration information assistant. You help international students and visa holders understand how US immigration rules affect their specific situation.

Rules you must always follow:
1. Answer ONLY from the retrieved documents provided below. Do not use your training knowledge about immigration law.
2. If the retrieved documents do not contain relevant information, say: "I don't have official information about this yet. Please check uscis.gov directly."
3. Every factual claim must reference a specific retrieved document by its [citation number].
4. Label the rule status prominently: PROPOSED, FINAL, or IN EFFECT, based only on the document metadata.
5. Never give specific legal advice. Never say "you should file" or "you will be approved". Never state specific filing fees.
6. If the question is about a specific personal legal situation requiring attorney judgment, say so and recommend consulting a qualified immigration attorney or the user's DSO.
7. End every response with: "This is general information only, not legal advice. Always verify with your DSO or a qualified immigration attorney."

User's visa context:
{personalizationContext}

Retrieved documents:
{retrievedDocuments}
```

### Personalization context block

Built by `app/personalization.py` (derived counts/booleans/enums only; respects the user's
`aiPersonalizationFields` toggles; empty for unauthenticated users):

```
Visa type: {visaType}
Status phase: {statusPhase}
{if daysUntilEadExpiry} Days until EAD expiry: {daysUntilEadExpiry}
{if daysUntilProgramEnd} Days until program end: {daysUntilProgramEnd}
{if unemploymentDaysUsed} Unemployment days used: {unemploymentDaysUsed} of {cap}
{if stemOptExtensionStatus} STEM OPT extension status: {stemOptExtensionStatus}
{if h1bTransferInProgress} H-1B transfer in progress: yes
```

Raw dates, employer names, and case numbers are never included; only derived counts and
booleans.

### Retrieved documents block

For each retrieved document:

```
[{n}] {title}
Source: {sourceUrl}
Type: {documentType}
Relevant excerpt:
{retrievedText}
```

### User turn

```
Question: {userQuestion}

Answer whether and how this affects someone with the visa context above. Be specific about what changes for their situation.
```

Conversation history is capped at the last 3 turns.

---

## Response Rendering

The Ask panel renders the answer as markdown.

Citation format in the body: `[1]`, `[2]`, `[3]`. Citation footnotes are rendered beneath the
answer:

```
─────────────────────────────
Sources
[1] DHS Proposed Rule: STEM OPT Extension
    Federal Register · federalregister.gov/...
    "...the Department proposes to extend the period of OPT..."

[2] 8 CFR 214.2(f)(10)(ii)(F)
    eCFR · ecfr.gov/...
    "...unemployment for no more than an aggregate of 150 days..."
```

Citation URLs come only from the retrieved document metadata; the model never constructs a
URL. A document with no URL is cited without one.

Rule-status label rendered above the answer as a colored chip:
- PROPOSED: amber
- FINAL: blue
- IN EFFECT: green
- UNCLEAR: grey

The status label is derived from the retrieved document type/metadata, never from the model's
own judgment.

---

## Guardrails

The guardrail rules are enforced in the system prompt and the mandatory closing disclaimer
(see the steering file). In a production Bedrock deployment these would be reinforced by a
Bedrock Guardrail as the enforced layer; the prompt-level rules are what the reference
implementation runs:

- Never give specific legal advice ("you should file by…").
- Never state specific USCIS filing-fee dollar amounts (tell the user to verify).
- Never predict a case outcome (approval/denial).
- For a specific personal legal situation, recommend a qualified attorney or the DSO.

Temperature is fixed at 0.1; max output tokens 800; conversation history capped at 3 turns.
