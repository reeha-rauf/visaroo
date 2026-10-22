---
inclusion: always
---

# User Profile — Data Safety Steering

Governs all code that touches the user profile, especially anything that builds prompts
for the LLM. Derived from `.kiro/specs/profile/` (REQ-10, REQ-NF-1, TASK-16).

## Never collect or store
These must never be collected, prompted for, logged, or stored anywhere:
- Social Security number (SSN)
- Passport number
- A-number (alien registration number)
- Bank or financial account information
- SEVIS ID (roadmap only — out of scope)
- EAD card number (roadmap only — out of scope)

If any input or feature appears to request these, stop and remove the field.

## Sensitive fields that ARE stored must be encrypted at rest
- `employerEVerify`, `employerEIN`, `petitionReceiptNumber` are sensitive.
- They must be encrypted at rest via the crypto provider (AWS KMS in production,
  local Fernet fallback for dev). Never store them in plaintext.
- Never return these fields in logs. Decrypt only when returning to the authenticated
  owner.

## Never send raw personal data to the LLM
When building any prompt (impact explainer, search personalization, etc.):
- NEVER include raw dates, employer names, case numbers, or any encrypted field.
- Include ONLY derived, non-identifying facts: counts, booleans, and status enums.
  Example allowed: `visa type: STEM OPT, unemployment days remaining: 110,
  upcoming travel: true`. Example forbidden: `EAD expires 2026-03-14`.
- Respect the user's `aiPersonalizationFields` toggles: if a section's toggle is off,
  omit all of its derived facts from the context.

## Computed dates
- Dates like the OPT application window, STEM filing window, and grace-period end are
  COMPUTED from stored base dates. Always label them as computed/estimated in the UI.
- Computed values are never persisted separately (avoid drift). If a user overrides one,
  store the override in the corresponding base field.
- Treat all computed deadlines as estimates, not legal guarantees — the "not legal
  advice" rule in responsible-ai.md still applies.

## Privacy actions
- Users can export all their data (JSON) and delete their account and all data.
- Deletion must remove the profile record (and, in production, queue identity deletion).
