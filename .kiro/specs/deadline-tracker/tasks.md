# Tasks: Deadline Tracker

## Task List

### TASK-1: Deadline calculation utilities
- [ ] Create `src/utils/deadlineCalculations.ts`
- [ ] Implement all formulas from design.md as pure functions
- [ ] Each function returns `Date | null`; null when required source field is missing
- [ ] Implement `getUrgencyTier(date, today)` function
- [ ] Write unit tests for every formula:
  - Standard case
  - Source date missing → returns null
  - Calculated date already past → tier is expired
  - Calculated date is today → tier is critical
  - Leap year edge case for +/- 90 day calculations

**Acceptance**: `npm run test` passes; no formula touches any LLM or API call

---

### TASK-2: Deadline definitions data file
- [ ] Create `src/data/deadlineDefinitions.ts`
- [ ] Define all deadlines from REQ-1 as `DeadlineDefinition` objects
- [ ] Each definition includes: id, label, description, consequence, regulationCite, officialUrl, applicableVisaTypes, calculate function
- [ ] Regulation cites must reference specific CFR sections from REQ-NF-2
- [ ] Official URLs must point to live USCIS or SEVP pages

**Acceptance**: every deadline in REQ-1 has a definition; all CFR cites are present

---

### TASK-3: computeDeadlines function
- [ ] Create `src/utils/computeDeadlines.ts`
- [ ] Takes `UserProfile` and `today: Date`
- [ ] Filters definitions to applicable visa type and phase
- [ ] Applies manual overrides from profile
- [ ] Returns sorted array of `ComputedDeadline` per design.md sort order
- [ ] Unit test: STEM OPT profile with all dates filled → correct set of deadlines in correct sort order
- [ ] Unit test: profile with missing eadEndDate → STEM OPT deadlines show null date and na tier

**Acceptance**: all unit tests pass

---

### TASK-4: UnemploymentCounter component
- [ ] Create `src/components/UnemploymentCounter.tsx`
- [ ] Props: `daysUsed`, `cap`, `eadStartDate`, `onUpdate(days: number)`
- [ ] Progress bar color-coded by tier
- [ ] Inline number input; calls `onUpdate` on blur; validates 0 ≤ value ≤ cap
- [ ] Projected cap date shown when calculable
- [ ] Calls `PUT /profile` via `onUpdate` in parent; shows "Saved" on success
- [ ] Hidden entirely for non-OPT visa types

**Acceptance**: updating days used saves to profile and re-renders projection; value outside 0–cap shows validation error

---

### TASK-5: SevpReportingCard component
- [ ] Create `src/components/SevpReportingCard.tsx`
- [ ] Shows "No pending SEVP report" when no active event
- [ ] "I had a reportable event" opens inline date picker
- [ ] On date selection: calls `PUT /profile` to store event date; deadline = event date + 10 days
- [ ] Countdown renders with urgency tier styling
- [ ] "Mark as reported" clears the event date from profile; records report date
- [ ] Hidden for H-1B and other non-F-1/OPT types

**Acceptance**: full event → report cycle saves correctly and clears the deadline

---

### TASK-6: DeadlineCard component
- [ ] Create `src/components/DeadlineCard.tsx`
- [ ] Collapsed: label, formatted date, days remaining pill, urgency color left border
- [ ] Expanded: description, consequence, regulation cite, official URL button, "Ask about this" button
- [ ] "Ask about this" opens Ask panel pre-filled with deadline label and date
- [ ] Override: pencil icon opens date input; save stores override to profile; "Overridden" badge shown
- [ ] Reset override link restores auto-calculated date
- [ ] Missing data state: grey card, "Complete your profile" link, no date or days remaining shown

**Acceptance**: all states render correctly; override saves and restores correctly

---

### TASK-7: DeadlineTrackerPage
- [ ] Create `src/pages/DeadlineTrackerPage.tsx`
- [ ] Load profile on mount via `GET /profile`
- [ ] Run `computeDeadlines(profile, today)` client-side
- [ ] Render UnemploymentCounter, SevpReportingCard, DeadlineList
- [ ] "Show non-applicable deadlines" toggle at bottom
- [ ] Loading skeleton while profile loads
- [ ] Empty state if profile has no visa type set: "Set up your profile to see your deadlines"
- [ ] Add "Deadlines" to main nav

**Acceptance**: page renders correct deadlines for a STEM OPT profile; non-applicable deadlines hidden by default

---

### TASK-8: ICS download
- [ ] Create `src/handlers/icsDownload.ts` Lambda
- [ ] `GET /deadlines/ics` — authenticated; computes deadlines from profile; returns `.ics` file
- [ ] Each deadline becomes a VEVENT with DTSTART, SUMMARY, DESCRIPTION, URL
- [ ] Expired and na deadlines excluded
- [ ] Add "Download calendar (.ics)" button to DeadlineTrackerPage

**Acceptance**: downloaded .ics file imports correctly into Apple Calendar and Google Calendar with all deadlines

---

### TASK-9: Reminder checker Lambda
- [ ] Create `src/handlers/reminderChecker.ts`
- [ ] Scan all profiles with `emailEnabled = true`
- [ ] For each profile: compute deadlines, check lead time thresholds against today
- [ ] For each triggered threshold: check `visatrack-reminders-sent` table; skip if already sent
- [ ] Send SES email using template from design.md
- [ ] Write sent record with TTL to `visatrack-reminders-sent`
- [ ] Add SAM resources: RemindersTable, EventBridge daily schedule, SES email identity

**Acceptance**: integration test with a seeded profile at 30 days to deadline sends exactly one email and writes sent record; second run sends nothing

---

### TASK-10: Steering file
- [ ] Create `.kiro/steering/deadline-tracker.md`
- [ ] Rules: deadline dates must never be calculated by the LLM; all formulas live in `deadlineCalculations.ts`; the LLM may only explain a deadline when given its pre-calculated date and definition; CFR cites must be hardcoded in definitions, not generated

**Acceptance**: steering file present before any Bedrock-touching code references deadlines
