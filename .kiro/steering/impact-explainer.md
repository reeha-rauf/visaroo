---
inclusion: always
---

# Impact Explainer — Grounding & Safety Steering

Governs all code for the impact explainer / Ask panel (`.kiro/specs/impact-explainer/`).

## Answer only from retrieved documents
- The LLM must answer ONLY from documents retrieved for the question (Bedrock Knowledge
  Base in production, or the local NewsItem corpus in dev). It must NOT answer from
  parametric/training knowledge about immigration law.
- If retrieval returns nothing relevant, respond: "I don't have official information
  about this yet. Please check uscis.gov directly." — never fabricate an answer.

## Citations
- Every factual claim ties to a retrieved document by citation number.
- Citation URLs come ONLY from the retrieved document metadata. The model must never
  construct or guess a URL. A document with no URL is cited without one.

## Personalization safety (inherits profile steering)
- The personalization context contains ONLY derived counts/booleans/enums — never raw
  dates, employer names, or sensitive fields. Respect the user's AI-personalization
  toggles. Empty context for unauthenticated users.

## Rule status label
- Label the answer PROPOSED / FINAL / IN EFFECT / UNCLEAR based only on retrieved
  document type/metadata — never inferred by the model's own judgment.

## Guardrails (enforced in prompt; Bedrock Guardrail is the production layer)
- Never give specific legal advice ("you should file by…").
- Never state specific USCIS filing-fee dollar amounts (they change — tell the user to
  verify).
- Never predict a case outcome (approval/denial).
- For a specific personal legal situation, recommend a qualified attorney or the DSO.

## Always
- End every response with: "This is general information only — not legal advice. Always
  verify with your DSO or a qualified immigration attorney."
- Temperature fixed at 0.1; max output tokens 800; conversation history capped at 3 turns.
