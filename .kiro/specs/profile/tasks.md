# Tasks: User Profile

## Task List

### TASK-1: DynamoDB table and KMS key
- [ ] Create SAM resource for `visatrack-profiles` DynamoDB table with KMS SSE enabled
- [ ] Create KMS key resource for profile encryption
- [ ] Add IAM policy for profile Lambda to read/write table and use KMS key
- [ ] Run `sam deploy` and verify table appears in AWS console

**Acceptance**: table exists with KMS encryption; Lambda can write and read a test item

---

### TASK-2: Profile data model and TypeScript types
- [ ] Create `src/types/profile.ts` with all interfaces from design.md
- [ ] Add Zod schemas for runtime validation of all profile fields
- [ ] Write unit tests for Zod schemas covering: missing required fields, invalid date format, unemployment days out of range, invalid visa type enum

**Acceptance**: all unit tests pass; `npm run test` exits 0

---

### TASK-3: Profile Lambda — GET and PUT
- [ ] Create `src/handlers/profile.ts` with handler for `GET /profile` and `PUT /profile`
- [ ] GET: read from DynamoDB by Cognito userId from JWT; return 404 if not found
- [ ] PUT: validate with Zod; encrypt sensitive fields via KMS; write to DynamoDB; return updated profile
- [ ] Decrypt sensitive fields on GET before returning to client
- [ ] Add exponential backoff retry (max 3) for DynamoDB throttle errors

**Acceptance**: integration test covers GET (not found → 404, found → 200 with decrypted fields), PUT (invalid body → 400, valid body → 200 with stored item)

---

### TASK-4: Profile Lambda — DELETE
- [ ] Add handler for `DELETE /profile`
- [ ] Delete DynamoDB item by userId
- [ ] Queue Cognito user deletion (or delete synchronously if within timeout budget)
- [ ] Return 204 on success

**Acceptance**: after DELETE, GET returns 404; Cognito user no longer exists

---

### TASK-5: API Gateway routes
- [ ] Add `GET /profile`, `PUT /profile`, `DELETE /profile` to SAM template
- [ ] Attach Cognito JWT authorizer to all three routes
- [ ] Test all three routes with a valid JWT and with an expired JWT (expect 401)

**Acceptance**: routes return correct status codes; expired JWT returns 401

---

### TASK-6: Computed date utilities
- [ ] Create `src/utils/computedDates.ts`
- [ ] Implement all computed date formulas from design.md (OPT window, STEM filing window, grace period end, days remaining)
- [ ] Write unit tests for each formula including edge cases: program end on a weekend, EAD expiry in the past, unemploymentDaysUsed at cap

**Acceptance**: all unit tests pass

---

### TASK-7: Onboarding flow — Step 1 (visa type and phase)
- [ ] Create `src/pages/onboarding/Step1.tsx`
- [ ] Render visa type selector; on selection render phase selector with correct options per REQ-2
- [ ] Persist selection to local state; do not call API until step 3 is complete
- [ ] Show progress indicator (Step 1 of 3)

**Acceptance**: selecting each visa type renders the correct phase options; state persists when navigating back from step 2

---

### TASK-8: Onboarding flow — Step 2 (key dates)
- [ ] Create `src/pages/onboarding/Step2.tsx`
- [ ] Render date fields conditionally based on visa type selected in step 1
- [ ] Show auto-calculated dates as read-only with an "Override" toggle that unlocks editing
- [ ] Validate dates on blur; show inline error on invalid format

**Acceptance**: correct date fields shown per visa type; auto-calculated dates update when source dates change; invalid dates blocked

---

### TASK-9: Onboarding flow — Step 3 (notifications) and profile save
- [ ] Create `src/pages/onboarding/Step3.tsx`
- [ ] Render notification preference checkboxes per REQ-8
- [ ] On "Finish" button: call `PUT /profile` with all three steps' data; redirect to dashboard on success

**Acceptance**: PUT is called once with the complete profile; successful save redirects to dashboard; API error shows inline message

---

### TASK-10: Profile edit page — identity and visa status sections
- [ ] Create `src/pages/profile/VisaStatus.tsx`
- [ ] Load existing profile via GET on mount
- [ ] Render all fields from REQ-2 and REQ-3/REQ-4 conditionally by visa type
- [ ] Auto-save on field blur (debounced 800ms); show "Saved" confirmation

**Acceptance**: page loads with existing data; field changes auto-save; conditional sections appear and disappear correctly when visa type changes

---

### TASK-11: Profile edit page — dates section
- [ ] Create `src/pages/profile/Dates.tsx`
- [ ] Display all key dates from REQ-5 with color badges (amber/red/grey) based on proximity
- [ ] Display computed dates alongside stored dates
- [ ] Unemployment day counter with progress bar

**Acceptance**: past dates show grey/expired; dates within 7 days show red; counter reflects stored value and updates on edit

---

### TASK-12: Profile edit page — travel section
- [ ] Create `src/pages/profile/Travel.tsx`
- [ ] Add / remove upcoming travel entries
- [ ] Recent countries visited: free-text chips input
- [ ] Advance parole toggle visible only for H-4 visa type

**Acceptance**: travel entries can be added and deleted; changes save correctly

---

### TASK-13: Profile edit page — contacts, notifications, privacy
- [ ] Create `src/pages/profile/Contacts.tsx`, `Notifications.tsx`, `Privacy.tsx`
- [ ] Privacy page: render per-section AI personalization toggles
- [ ] Privacy page: "Export my data" button calls GET /profile and triggers JSON download
- [ ] Privacy page: "Delete account" button shows confirmation modal before calling DELETE /profile

**Acceptance**: export downloads valid JSON; delete modal requires explicit confirmation; toggles persist correctly

---

### TASK-14: Personalization context builder
- [ ] Create `src/utils/personalizationContext.ts`
- [ ] Build `PersonalizationContext` from a `UserProfile` per design.md
- [ ] Strip raw dates and sensitive fields; derive only counts and booleans
- [ ] Respect `aiPersonalizationFields` toggles: omit fields whose toggle is off

**Acceptance**: unit test verifies no raw dates or encrypted fields appear in output; toggled-off fields are absent

---

### TASK-15: Integration with impact explainer
- [ ] Import `buildPersonalizationContext` in the impact explainer Lambda
- [ ] Prepend context to the Bedrock prompt as a system-level fact block
- [ ] Test: profile with STEM OPT + 40 days remaining + a rule about OPT unemployment caps → response should mention "you have 110 days remaining"

**Acceptance**: end-to-end test confirms personalized response differs from non-personalized baseline

---

### TASK-16: Steering file
- [ ] Create `.kiro/steering/profile.md`
- [ ] Rules: never include raw dates in LLM prompts; always derive counts; never store SSN, passport, or A-number; label all computed dates as computed

**Acceptance**: steering file present and reviewed before any LLM-touching code is merged
