# Tasks: Attorney Help Page

## Task List

### TASK-1: Legal resources data file
- [ ] Create `src/data/legalResources.ts`
- [ ] Add all resources from REQ-5 with name, description, url, category, region fields
- [ ] Manually verify every URL is live before committing

**Acceptance**: all URLs resolve to correct pages; no broken links

---

### TASK-2: Suggested questions generator
- [ ] Create `src/utils/suggestedQuestions.ts`
- [ ] Implement all rule-based conditions from design.md
- [ ] Returns 3–5 questions maximum; always includes the fallback "most important things" question
- [ ] Unit tests: OPT profile with 70 days used → includes unemployment question; STEM OPT pending → includes extension question; no travel → no travel question

**Acceptance**: all unit tests pass; no LLM call involved

---

### TASK-3: Brief generator
- [ ] Create `src/utils/generateBrief.ts`
- [ ] Implement `generateBrief(input: BriefInput): CaseBrief`
- [ ] Implement `briefToPlainText(brief: CaseBrief): string` for copy/download/mailto
- [ ] Key dates show actual formatted dates, not day counts
- [ ] Active deadlines filtered to next 60 days only
- [ ] Unit test: STEM OPT profile with 2 critical deadlines → brief contains both deadlines; unemployment section present; disclaimer present

**Acceptance**: plain text output matches template in design.md; no server calls

---

### TASK-4: DisclaimerBanner component
- [ ] Create `src/components/DisclaimerBanner.tsx`
- [ ] Renders REQ-6 disclaimer text prominently at top of page
- [ ] Not dismissible

**Acceptance**: disclaimer visible on page load; cannot be closed

---

### TASK-5: CaseBriefSection component
- [ ] Create `src/components/CaseBriefSection.tsx`
- [ ] Situation description textarea (max 500 chars) with character counter
- [ ] "Generate my case brief" button calls `generateBrief` with profile + computed deadlines + description
- [ ] BriefDisplay renders formatted brief after generation
- [ ] Copy button copies plain text to clipboard; shows "Copied!" confirmation
- [ ] Download button downloads plain text as `visaroo-brief-{date}.txt`
- [ ] ContactDsoButton: visible if profile has dsoEmail; constructs and opens mailto link
- [ ] If no DSO in profile: show "Add your DSO in profile settings →" link instead
- [ ] `?prefill=true` query param: auto-focus situation description field on mount

**Acceptance**: full generate → copy → download → mailto flow works; DSO button absent when no DSO email in profile

---

### TASK-6: ResourceDirectory component
- [ ] Create `src/components/ResourceDirectory.tsx`
- [ ] Render resources grouped by category from `legalResources.ts`
- [ ] Each resource: name, description, external link (opens in new tab with rel="noopener noreferrer")
- [ ] Free/low-cost group shows region label where applicable

**Acceptance**: all resources render with correct links; external links open in new tab

---

### TASK-7: AttorneyHelpPage
- [ ] Create `src/pages/AttorneyHelpPage.tsx`
- [ ] Load profile and computed deadlines from app state (no API call)
- [ ] Render DisclaimerBanner, CaseBriefSection, ResourceDirectory
- [ ] Handle `?prefill=true` query param
- [ ] Add "Legal help" link to main nav
- [ ] Add "Get legal help →" link to Ask panel when guardrail redirects to attorney

**Acceptance**: page renders without API calls; nav link present; Ask panel link navigates with prefill param