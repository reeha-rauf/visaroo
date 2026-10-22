# Requirements: Deadline Tracker

## Overview
Track all immigration-critical deadlines for the user's visa type and status, calculate them deterministically from profile data, surface them with urgency indicators, and send configurable reminders. The LLM explains deadlines; it never calculates them.

---

## Functional Requirements

### REQ-1: Deadline List per Visa Type
The app must display all applicable deadlines for the user's current visa type and status phase.

**F-1 / OPT / STEM OPT deadlines:**
- OPT application window opens (90 days before program end date)
- OPT application deadline (60 days before program end date; USCIS must receive by this date)
- EAD card expiry
- STEM OPT filing window opens (90 days before OPT EAD expiry)
- STEM OPT filing deadline (60 days before OPT EAD expiry)
- I-20 expiry
- Grace period end (60 days after program end or OPT EAD expiry)
- Next SEVP employer/address reporting deadline (10 days after a reportable change)
- Unemployment cap warning threshold (at 60 days used for OPT; at 120 days for STEM OPT)
- Unemployment cap hard limit (90 days for OPT; 150 days for STEM OPT)

**H-1B deadlines:**
- I-94 expiry
- H-1B petition expiry (derived from approval notice; user-entered)
- Cap-gap coverage end (if applicable)
- Grace period end (60 days after status end)
- H-1B renewal filing reminder (user-set lead time)

**All visa types:**
- Visa stamp expiry
- Passport expiry (user-entered)
- Next renewal reminder (user-set)

### REQ-2: Urgency Tiers
Each deadline must be assigned an urgency tier based on days remaining:

| Tier | Days remaining | Color |
|---|---|---|
| Critical | 0–7 | Red |
| Warning | 8–30 | Amber |
| Upcoming | 31–90 | Yellow |
| OK | 91+ | Green / neutral |
| Expired | Past | Grey |
| N/A | Not applicable to current status | Hidden |

Tiers recalculate on every page load using the current date. No stale cached tiers.

### REQ-3: Unemployment Day Counter
For OPT and STEM OPT users only:
- Display days used and days remaining as a progress bar
- Cap: 90 days for OPT, 150 days for STEM OPT
- User updates the count manually via an inline input on the tracker page
- Show a warning badge when within 30 days of the cap
- Show a critical badge when within 7 days of the cap
- Display the date on which the cap will be hit if the current daily rate continues (optional projection based on days used divided by days since EAD start)

### REQ-4: SEVP Reporting Countdown
For F-1, OPT, and STEM OPT users:
- Display a countdown to the next SEVP reporting deadline
- Reportable events: employer change, address change, program extension, loss of employment
- User marks a reportable event from the tracker; the app sets the deadline to 10 days from that event date
- Once reported, user marks as reported and the deadline clears
- If no pending event, show "No pending SEVP report" in OK state

### REQ-5: Deadline Detail View
Each deadline card must expand to show:
- Plain-language description of what the deadline is and why it matters
- The regulation or official source it comes from (cited, not summarized by LLM)
- What happens if the deadline is missed (consequences)
- Recommended action with a link to the relevant USCIS or SEVP page
- "Ask about this deadline" button that opens the Ask panel pre-filled with context

### REQ-6: Reminders
- When a deadline enters the Warning tier (≤30 days), send an email notification if email alerts are enabled in the profile
- Respect the lead time preferences from the profile (90 / 60 / 30 / 14 / 7 days)
- Each deadline fires at most one reminder per lead-time threshold per deadline (no repeated daily emails)
- Email includes: deadline name, date, days remaining, recommended action link
- No SMS in v1; roadmap only

### REQ-7: Manual Date Overrides
- All auto-calculated deadlines must be overridable with a user-entered date
- Overridden dates show an "Overridden" badge so users know the displayed date is not auto-calculated
- Resetting an override restores the auto-calculated value
- Override is stored in the profile DynamoDB item alongside the source date

### REQ-8: Roadmap Items Not in v1
- Automatic USCIS case status polling
- Push notifications
- iCal / Google Calendar sync (provide .ics download only)
- Attorney escalation trigger from a missed deadline

---

## Non-Functional Requirements

### REQ-NF-1: Determinism
All deadline dates must be calculated in pure functions with no LLM involvement. Given the same profile dates, the same deadlines must always be produced. Unit tests must cover every formula.

### REQ-NF-2: Accuracy
Formulas must match the current regulatory rules:
- OPT application window: 8 CFR 214.2(f)(11)(i)(A) — 90 days before program end
- OPT application deadline: 8 CFR 214.2(f)(11)(i)(B) — 60 days before program end
- SEVP reporting window: 8 CFR 214.2(f)(18) — 10 days
- OPT unemployment cap: 8 CFR 214.2(f)(10)(ii)(E) — 90 days
- STEM OPT unemployment cap: 8 CFR 214.2(f)(10)(ii)(F) — 150 days
- Grace period: 8 CFR 214.2(f)(5)(iv) — 60 days

### REQ-NF-3: Performance
Deadline list must render in under 300ms. Calculations run client-side from cached profile data; no API call required to render the list.

### REQ-NF-4: Empty State
If required profile dates are missing for a deadline calculation, display "Complete your profile to see this deadline" with a link to the relevant profile section. Never show a wrong date; prefer showing nothing.
