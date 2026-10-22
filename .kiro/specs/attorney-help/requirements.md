# Requirements: Attorney Help Page

## Overview
Help users prepare to get professional legal help. Generate a concise case brief from the user's profile and recent activity, provide curated links to legitimate legal resources, and make it easy to contact their DSO. Visaroo does not broker attorney relationships or collect payment.

---

## Functional Requirements

### REQ-1: Page Entry Points
- "Get legal help" link in the main nav
- "Talk to a lawyer" button on the Ask panel when a response recommends attorney consultation
- Direct URL: `/legal-help`

### REQ-2: Case Brief Generator
- A "Generate my case brief" button produces a structured summary the user can bring to an attorney or DSO
- The brief is generated from the user's profile data only — no LLM retrieval from the Knowledge Base
- Brief contents:
  - Visa type and current status phase
  - Key dates (program end, EAD expiry, grace period end) — shown as actual dates, not counts
  - Any active deadlines within 60 days
  - Unemployment days used vs. cap (OPT/STEM OPT only)
  - STEM OPT extension status (if applicable)
  - H-1B petition status and I-94 expiry (H-1B only)
  - Upcoming travel (if any)
  - A free-text "situation description" field the user fills in before generating
  - A list of suggested questions auto-generated based on the user's status and active deadlines
- Brief renders as formatted text in the page and can be copied to clipboard or downloaded as a .txt file
- Brief is never stored server-side; generated client-side only

### REQ-3: Suggested Questions
Auto-generate 3–5 suggested questions for the attorney or DSO based on the user's profile.

Examples by situation:
- OPT with 45 unemployment days used: "What happens if I exceed 90 unemployment days before finding a job?"
- STEM OPT extension pending: "What is my status if my STEM OPT extension is not approved before my OPT EAD expires?"
- H-1B transfer in progress: "Am I authorized to continue working during an H-1B transfer?"
- Upcoming travel on OPT: "What documents do I need to re-enter the US on OPT after traveling abroad?"

Questions are generated deterministically from profile fields in code — not by the LLM.

### REQ-4: DSO Contact
- If the user has a DSO name and email stored in their profile, show a "Contact my DSO" button that opens a pre-filled mailto link
- Mailto subject: "Immigration question — [visa type]"
- Mailto body: the generated brief (plain text)
- If no DSO stored: prompt the user to add their DSO in profile settings with a direct link

### REQ-5: Legal Resource Directory
A curated static list of legitimate resources, grouped by category:

**Find an immigration attorney:**
- AILA lawyer search (aila.org/find-an-immigration-lawyer)
- Immigrant Legal Resource Center (ilrc.org)
- National Immigration Law Center (nilc.org)

**Free and low-cost legal help:**
- CLINIC (Catholic Legal Immigration Network) — clinic.org
- immigration-specific legal aid clinics (list 3–5 by region: Pacific Northwest, Bay Area, NYC, Texas, Midwest)

**University and campus resources:**
- Generic prompt: "Search '[your university] international student office' for DSO contact"
- Link to Study in the States DSO locator: studyinthestates.dhs.gov

**Official government resources:**
- USCIS contact center: uscis.gov/contactcenter
- SEVP contact: ice.gov/sevis/contact
- E-Verify employer helpdesk (for STEM OPT employers)

### REQ-6: Disclaimer
- The page must display prominently: "Visaroo does not provide legal advice and is not a law firm. The resources listed are provided for informational purposes only. Visaroo has no affiliation with any listed attorney or organization."
- This disclaimer appears at the top of the page and at the bottom of the generated brief

### REQ-7: No Attorney Marketplace
- Visaroo does not collect attorney listings, reviews, or referral fees
- No booking, scheduling, or payment flow in v1 or roadmap
- All attorney links go to established third-party directories only

---

## Non-Functional Requirements

### REQ-NF-1: No server calls
- The case brief is generated entirely client-side from the cached profile
- No Lambda, no DynamoDB read on this page beyond the profile already loaded in app state
- Page must be fully functional offline if profile is cached

### REQ-NF-2: Privacy
- Brief is never sent to any server
- The situation description field is never logged or transmitted
- Mailto link is constructed client-side; no server involvement

### REQ-NF-3: Link accuracy
- All external links must be verified as live before submission
- Links checked once manually at build time; no automated link checking in v1