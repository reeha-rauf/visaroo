# Design: Attorney Help Page

## Architecture

Entirely client-side. No backend involved, no API calls. Reads from app-level profile state already loaded by the profile feature.

---

## Case Brief Generator

### Input

```typescript
interface BriefInput {
  profile: UserProfile;
  computedDeadlines: ComputedDeadline[];  // from deadline tracker utilities
  situationDescription: string;           // user-entered free text
}
```

### Output

```typescript
interface CaseBrief {
  generatedAt: string;       // ISO 8601, shown at top of brief
  visaType: string;
  statusPhase: string;
  keyDates: BriefDate[];
  activeDeadlines: BriefDeadline[];
  unemploymentStatus?: string;    // "45 of 90 days used" — OPT/STEM OPT only
  stemOptExtensionStatus?: string;
  h1bPetitionStatus?: string;
  upcomingTravel?: string;
  situationDescription: string;
  suggestedQuestions: string[];
  disclaimer: string;
}

interface BriefDate {
  label: string;
  date: string;    // formatted: "October 23, 2026"
}

interface BriefDeadline {
  label: string;
  date: string;
  daysRemaining: number;
  tier: UrgencyTier;
}
```

### Brief generation function

`src/utils/generateBrief.ts` — pure function, no side effects.

```typescript
function generateBrief(input: BriefInput): CaseBrief {
  const { profile, computedDeadlines, situationDescription } = input;

  const keyDates = buildKeyDates(profile);
  const activeDeadlines = computedDeadlines
    .filter(d => d.daysRemaining !== null && d.daysRemaining <= 60)
    .map(d => ({ label: d.label, date: formatDate(d.date), daysRemaining: d.daysRemaining, tier: d.tier }));

  return {
    generatedAt: new Date().toISOString(),
    visaType: profile.visaType,
    statusPhase: profile.statusPhase,
    keyDates,
    activeDeadlines,
    unemploymentStatus: buildUnemploymentStatus(profile),
    stemOptExtensionStatus: profile.stemOptStatus,
    h1bPetitionStatus: profile.petitionStatus,
    upcomingTravel: buildTravelSummary(profile),
    situationDescription,
    suggestedQuestions: generateSuggestedQuestions(profile, computedDeadlines),
    disclaimer: BRIEF_DISCLAIMER,
  };
}
```

### Suggested questions logic

`src/utils/suggestedQuestions.ts` — deterministic, rule-based, no LLM.

```typescript
function generateSuggestedQuestions(
  profile: UserProfile,
  deadlines: ComputedDeadline[]
): string[] {
  const questions: string[] = [];

  if (profile.visaType === 'OPT' && profile.unemploymentDaysUsed > 60) {
    questions.push("What happens if I exceed 90 unemployment days before finding a job?");
  }
  if (profile.stemOptStatus === 'pending') {
    questions.push("What is my status if my STEM OPT extension is not approved before my OPT EAD expires?");
  }
  if (profile.h1bTransferInProgress) {
    questions.push("Am I authorized to continue working during an H-1B transfer?");
  }
  if (profile.upcomingTravel?.length > 0) {
    questions.push("What documents do I need to re-enter the US after traveling abroad?");
  }
  if (deadlines.some(d => d.tier === 'critical')) {
    questions.push("I have a deadline within 7 days — what should I do immediately?");
  }
  // Always include
  questions.push("What are the most important things I should do to protect my status right now?");

  return questions.slice(0, 5);
}
```

### Brief as plain text (for copy/mailto)

```
VISAROO IMMIGRATION CASE BRIEF
Generated: {date}
────────────────────────────────

VISA STATUS
Type: {visaType}
Phase: {statusPhase}

KEY DATES
{keyDates: label — date}

UPCOMING DEADLINES (next 60 days)
{activeDeadlines: label — date (X days)}

{if unemploymentStatus}
UNEMPLOYMENT DAYS
{unemploymentStatus}

{if situationDescription}
MY SITUATION
{situationDescription}

SUGGESTED QUESTIONS FOR MY ATTORNEY / DSO
{questions numbered list}

────────────────────────────────
DISCLAIMER
Visaroo does not provide legal advice and is not a law firm.
This brief is for informational purposes only.
Always verify information with your DSO or a qualified immigration attorney.
```

---

## Frontend

### Page structure

```
/legal-help
  <AttorneyHelpPage>
    <DisclaimerBanner />
    <CaseBriefSection>
      <SituationDescriptionInput />
      <GenerateBriefButton />
      <BriefDisplay />              // shown after generation
        <CopyButton />
        <DownloadTxtButton />
        <ContactDsoButton />        // if DSO in profile
    </CaseBriefSection>
    <ResourceDirectory>
      <ResourceGroup title="Find an immigration attorney" />
      <ResourceGroup title="Free and low-cost legal help" />
      <ResourceGroup title="University resources" />
      <ResourceGroup title="Official government resources" />
    </ResourceDirectory>
  </AttorneyHelpPage>
```

### Resource directory

Static data file: `src/data/legalResources.ts`

```typescript
interface LegalResource {
  name: string;
  description: string;
  url: string;
  category: 'attorney' | 'free_help' | 'university' | 'government';
  region?: string;
}
```

### ContactDsoButton

Constructs mailto link client-side:

```typescript
function buildMailtoLink(dsoEmail: string, visaType: string, briefText: string): string {
  const subject = encodeURIComponent(`Immigration question — ${visaType}`);
  const body = encodeURIComponent(briefText);
  return `mailto:${dsoEmail}?subject=${subject}&body=${body}`;
}
```

### "Talk to a lawyer" trigger from Ask panel

When the impact explainer guardrail redirects to an attorney, the Ask panel response includes a "Get legal help →" link that navigates to `/legal-help` with `?prefill=true`. The page reads this query param and pre-opens the brief generator with focus on the situation description field.

---

## No Infrastructure Required

This feature adds no new AWS resources. It uses:
- Profile data already in app state (loaded by profile feature)
- Deadline calculations already in `deadlineCalculations.ts` (built by deadline tracker)
- Client-side only: no backend, no database, no API calls