# Design: User Profile

This feature stores each user's visa profile, computes deadline-relevant dates from it, and
feeds derived (non-identifying) facts to the AI layer. It is built on Visaroo's stack:
FastAPI + SQLAlchemy, JWT auth, Pydantic v2 schemas, and the `CryptoProvider` abstraction for
encryption at rest.

## Architecture

### Storage
- **SQLAlchemy `Profile` table** (SQLite in dev, Postgres-ready via the same models).
  - Primary key: `user_id` (FK to `users.id`); one profile per user.
  - All date fields stored as ISO 8601 strings (nullable).
  - Sensitive fields (`employer_everify`, `employer_ein`, `petition_receipt_number`) are
    **encrypted at rest** via the crypto provider, never stored in plaintext.
- **Auth/identity:** the existing JWT auth (the token `sub` is the user id); the user's email
  lives on the `User` row, not duplicated on the profile.

### Encryption at rest (`CryptoProvider`)
Sensitive fields are encrypted through an env-switched `CryptoProvider`:
- `KmsProvider` — real **AWS KMS** encrypt/decrypt (`CRYPTO_PROVIDER=kms`).
- `LocalProvider` — Fernet, for zero-setup local dev (`CRYPTO_PROVIDER=local`, the default).

Fields are decrypted only when returning the profile to its authenticated owner; ciphertext
is never logged.

### API (FastAPI, `routers/profile.py`)
- `GET /profile` — returns the full profile for the authenticated user (404 if none).
- `PUT /profile` — full or partial upsert; returns the updated profile.
- `DELETE /profile` — deletes the stored profile record (204).
- `GET /profile/export` — downloads all stored profile data as JSON (privacy/export).
- All routes require a valid JWT (`get_current_user`); requests/responses are validated by
  Pydantic schemas (`ProfileUpsert` with `extra="forbid"`, `ProfileOut`).

---

## Data Model

The `Profile` SQLAlchemy model (and its `ProfileOut` API shape) carries these fields. Types
are shown in TypeScript-ish notation for readability; on the wire they are camelCase JSON, in
the DB they are snake_case columns.

```
Profile {
  userId: int                   // PK, FK -> users.id

  // Identity
  fullName: string
  countryOfOrigin?: string
  universityOrEmployer?: string
  fieldOrTitle?: string

  // Visa status
  visaType: VisaType
  statusPhase: string           // depends on visaType

  // Key dates (ISO 8601 strings)
  programStartDate?: string
  programEndDate?: string
  i20ExpiryDate?: string
  portOfEntryDate?: string
  visaStampExpiry?: string
  eadStartDate?: string
  eadEndDate?: string
  nextSevpReportingDate?: string
  nextRenewalReminder?: string
  gracePeriodEndDate?: string

  // OPT / STEM OPT
  employerName?: string
  employerEVerify?: string      // encrypted at rest
  stemOptStatus?: StemOptStatus
  i983OnFile?: boolean
  unemploymentDaysUsed?: number

  // H-1B
  petitionReceiptNumber?: string // encrypted at rest
  petitionStatus?: PetitionStatus
  i94ExpiryDate?: string
  employerEIN?: string           // encrypted at rest
  h1bTransferInProgress?: boolean

  // Travel
  lastUsEntryDate?: string
  upcomingTravel?: TravelEntry[]  // JSON-encoded list
  recentCountriesVisited?: string[]
  advanceParoleFiled?: boolean

  // DSO / attorney
  dsoName?: string
  dsoEmail?: string
  attorneyName?: string
  attorneyEmail?: string

  // Notifications + privacy toggles (JSON-encoded)
  notifications: NotificationPreferences
  aiPersonalizationFields: PersonalizationToggles

  // Metadata
  createdAt: datetime
  updatedAt: datetime
}

type VisaType = 'F-1' | 'OPT' | 'STEM_OPT' | 'H-1B' | 'H-4' | 'J-1' | 'Other'
type StemOptStatus = 'not_started' | 'applied' | 'pending' | 'approved'
type PetitionStatus = 'pending' | 'approved' | 'cap_exempt'

interface TravelEntry {
  destination: string
  departureDate: string
  returnDate?: string
}

interface NotificationPreferences {
  emailEnabled: boolean
  alerts: {
    deadlineApproaching: boolean
    newRuleAffectingStatus: boolean
    newCreatorPost: boolean
    newWebinar: boolean
  }
  deadlineLeadTimeDays: number[]   // e.g. [90, 30, 7]
}

interface PersonalizationToggles {
  visaStatus: boolean
  keyDates: boolean
  travel: boolean
  employer: boolean
}
```

List/nested structures (`upcomingTravel`, `notifications`, `aiPersonalizationFields`) are
stored as JSON-encoded text columns.

---

## Computed Dates

Computed from stored base dates (see `computed_dates.py`, surfaced on the API and rendered in
the UI). Never persisted separately, to avoid drift (REQ-NF-1).

| Computed field | Formula |
|---|---|
| OPT application window opens | programEndDate − 90 days |
| OPT application deadline | programEndDate − 60 days |
| STEM OPT filing window start | eadEndDate − 90 days |
| STEM OPT filing window end | eadEndDate − 60 days |
| Grace period end (F-1) | programEndDate + 60 days |
| Grace period end (H-1B) | i94ExpiryDate + 60 days |
| OPT unemployment days remaining | 90 − unemploymentDaysUsed (OPT cap) |
| STEM OPT unemployment days remaining | 150 − unemploymentDaysUsed (STEM cap) |

Unemployment caps are **90 days (OPT) / 150 days (STEM OPT)** per REQ-3.

Overrides: if a user edits a computed date, the override is stored in the corresponding base
field (e.g. their actual grace-period end date in `gracePeriodEndDate`) rather than as a
separate computed value.

---

## Frontend

### Pages and components

```
/onboarding         — first-time profile setup (3 steps)
  Step 1: visa type + status phase
  Step 2: key dates for selected visa type
  Step 3: notifications

/profile            — view and edit the full profile (one page, sectioned cards):
  Identity · Visa status · Key dates · Travel · DSO/attorney · Notifications · Privacy
```

### Conditional rendering
Sections visible per visa type:
- OPT / STEM OPT section: visible only when visaType is OPT or STEM_OPT
- H-1B section: visible only when visaType is H-1B
- Advance parole field: visible only when visaType is H-4
- DSO fields: visible when visaType is F-1, OPT, or STEM_OPT

### Deadline display
- Dates within 30 days of today: amber badge
- Dates within 7 days: red badge
- Past dates: grey with strikethrough, "Expired" label

---

## Personalization Context Sent to the AI

When a user asks "does this rule affect me?", the backend builds a context object from stored
fields (`personalization.py`). Only non-sensitive derived facts are included; it respects the
user's `aiPersonalizationFields` toggles.

```
interface PersonalizationContext {
  visaType: string
  statusPhase: string
  daysUntilEadExpiry?: number        // derived; never the raw date
  daysUntilProgramEnd?: number
  unemploymentDaysUsed?: number
  unemploymentDaysRemaining?: number
  stemOptExtensionStatus?: string
  h1bTransferInProgress?: boolean
  upcomingTravel?: boolean           // boolean only; no destination
  fieldsEnabled: string[]            // which personalization toggles are on
}
```

Raw dates, employer details, and any encrypted field never appear in the prompt.

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Required fields missing on save | 400 with field-level error messages (Pydantic) |
| Date parse failure | 400 with field name and expected format |
| Cross-field validation (phase must match visa type) | 400 with a descriptive message |
| Encryption failure (KMS or local) | 500; generic error surfaced, ciphertext never logged |
| Missing/expired JWT | 401; client redirects to login |
| Profile not found | 404 on GET/DELETE/export |

---

## Cloud integration kept

The real AWS integrations used by this feature are **AWS KMS** (encryption at rest, via the
`KmsProvider`) and **Amazon Bedrock** (for the personalized AI answers). Both sit behind
provider abstractions with local fallbacks, so the whole feature runs end-to-end with zero
AWS setup for development and demos.
