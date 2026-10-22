# Requirements: User Profile

## Overview
Allow users to create and manage a personal profile so the app can personalize rule-change impact checks, deadline calculations, and creator post filtering to their specific visa status and dates.

---

## Functional Requirements

### REQ-1: Profile Creation
The user must be able to create a profile from an onboarding flow on first login.
- Collect: full name, email (pre-filled from auth), visa type, status phase, and at least one key date
- Profile must be usable for personalized impact checks with only those five fields filled in
- All other fields are optional

### REQ-2: Visa Type and Status Phase
The user must be able to select their visa type and current phase.

Supported visa types:
- F-1
- OPT (post-completion)
- STEM OPT
- H-1B
- H-4
- J-1
- Other (free text)

Status phases per visa type:
- F-1: coursework | pre-completion OPT | post-completion OPT | STEM OPT extension | grace period
- OPT / STEM OPT: active | grace period
- H-1B: pending | approved | cap-exempt | transfer in progress
- H-4 / J-1 / Other: active | grace period

### REQ-3: OPT / STEM OPT Fields
When visa type is OPT or STEM OPT, the user may optionally provide:
- EAD start date and end date
- Employer name
- Employer E-Verify case number
- STEM OPT extension status: applied | approved | pending | not started
- I-983 training plan on file: yes | no
- Unemployment days used (integer, 0–150 for OPT; 0–150 for STEM OPT)
  - The app must display a running counter of days remaining against the applicable cap

### REQ-4: H-1B Fields
When visa type is H-1B, the user may optionally provide:
- Petition receipt number
- Petition status: pending | approved | cap-exempt
- I-94 expiration date
- Current employer name and EIN
- H-1B transfer in progress: yes | no

### REQ-5: Key Dates
The user must be able to enter the following dates where applicable:
- Program start date and end date (I-20 dates for F-1)
- I-20 expiry (separate from program end if extended)
- EAD start date and end date
- OPT application window open date (auto-calculated: 90 days before program end; editable)
- OPT application deadline (auto-calculated: 60 days before program end; editable)
- STEM OPT filing window (auto-calculated: 90–60 days before OPT EAD expiry; display only)
- Grace period end date (auto-calculated from visa rules; editable)
- Visa stamp expiry date
- Port of entry date
- Next SEVP reporting deadline (auto-calculated from last reported event; editable)
- Next renewal reminder (user-set; no auto-calculation)

Auto-calculated dates must update immediately when their source dates change.
Auto-calculated dates must be editable so users can override with their actual I-20 or USCIS dates.

### REQ-6: Travel
The user may optionally provide:
- Last US entry date
- Upcoming travel: destination country and departure / return dates (multiple entries allowed)
- Countries visited in the last 12 months (free-text list)
- Advance parole filed: yes | no (shown for H-4 EAD users)

### REQ-7: DSO / Immigration Contact
The user may optionally store:
- DSO name and email (F-1, OPT, STEM OPT)
- Attorney name and email

### REQ-8: Notification Preferences
The user must be able to configure:
- Email alerts: on | off
- Alert categories: deadline approaching | new rule affecting my status | new creator post | new webinar matching my status (each independently toggleable)
- Lead time for deadline reminders: checkboxes for 90 / 60 / 30 / 14 / 7 days (multi-select)

### REQ-9: Privacy Controls
The user must be able to:
- Toggle each optional section's use in AI personalization independently
- Export all their stored data as JSON
- Delete their account and all associated data

### REQ-10: Data Not Collected
The following must never be collected, stored, or prompted for:
- Social Security number
- Passport number
- A-number (alien registration number)
- Bank or financial account information
- SEVIS ID (removed from scope; roadmap only)
- EAD card number (removed from scope; roadmap only)
- Petition receipt number storage beyond session (encrypt at rest or defer to roadmap)

---

## Non-Functional Requirements

### REQ-NF-1: Security
- All dates and case numbers stored in DynamoDB must be encrypted at rest using AWS KMS
- JWT from Cognito required for all profile read/write operations
- No profile data passed as plain text to the LLM; only derived facts (e.g., "visa type: STEM OPT, days remaining: 47") are included in prompts

### REQ-NF-2: Validation
- All dates validated as real calendar dates in ISO 8601 format
- Unemployment day counter must reject values outside 0–150
- Email validated on save, not on keystroke

### REQ-NF-3: Minimum Viable Profile
- The impact explainer endpoint must return a meaningful response if only visa type, status phase, and one key date are provided
- Missing optional fields must not cause errors; they must be treated as unknown

### REQ-NF-4: Performance
- Profile read and write operations must complete in under 500ms at p95

---

## Out of Scope (Roadmap)
- Document upload and storage (I-20, EAD scans)
- SEVIS ID storage
- Biometric or passport data
- Direct USCIS case status lookup
- Attorney marketplace booking
