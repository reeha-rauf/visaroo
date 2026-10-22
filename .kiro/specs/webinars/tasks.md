# Tasks: Webinars

## Task List

### TASK-1: DynamoDB table
- [ ] Add `visatrack-webinars` table to SAM template
- [ ] Deploy and verify table exists

**Acceptance**: table visible in AWS console

---

### TASK-2: Webinar Lambda — GET list and GET by id
- [ ] Create `src/handlers/webinars.ts`
- [ ] `GET /webinars`: scan table, filter by `startDateUtc > now`, optionally filter by visaType, optionally include past
- [ ] `GET /webinars/:id`: GetItem by id; 404 if not found
- [ ] No auth required on GET routes

**Acceptance**: returns correct list with upcoming filter; past webinars excluded by default; visaType filter works

---

### TASK-3: Webinar Lambda — POST and DELETE
- [ ] `POST /webinars`: validate body with Zod; check Cognito group is VerifiedCreator or Admin; write to DynamoDB
- [ ] `DELETE /webinars/:id`: check caller owns the item or is Admin; delete; return 204
- [ ] Return 403 if caller is neither owner nor Admin

**Acceptance**: creator can post and delete their own webinar; cannot delete another creator's webinar; non-creator gets 403 on POST

---

### TASK-4: ICS generation
- [ ] Create `src/utils/icsGenerator.ts`
- [ ] `generateSingleIcs(webinar)` → string
- [ ] `generateMultiIcs(webinars[])` → string
- [ ] Add `GET /webinars/ics` and `GET /webinars/:id/ics` routes to Lambda
- [ ] Response headers: `Content-Type: text/calendar`, `Content-Disposition: attachment; filename="visaroo-webinars.ics"`
- [ ] Unit test: generated .ics contains correct DTSTART, SUMMARY, URL for a known input

**Acceptance**: downloaded file imports into Apple Calendar and Google Calendar with correct title and time

---

### TASK-5: Seed script
- [ ] Create `scripts/seedWebinars.ts`
- [ ] Seeds the 5 webinars from design.md with real upcoming dates
- [ ] Run via `ts-node scripts/seedWebinars.ts`
- [ ] Idempotent: skip if a webinar with the same title already exists

**Acceptance**: running the script twice does not create duplicates; all 5 webinars appear in `GET /webinars`

---

### TASK-6: FilterChips component
- [ ] Create `src/components/FilterChips.tsx`
- [ ] Props: `selected`, `onChange`, `availableTags`
- [ ] Single-select; "All" deselects other chips
- [ ] Defaults to user's visa type from profile on mount

**Acceptance**: selecting a chip filters the list; "All" shows everything

---

### TASK-7: WebinarCard component
- [ ] Create `src/components/WebinarCard.tsx`
- [ ] Renders all fields from REQ-3
- [ ] Date/time formatted in browser local timezone using Intl.DateTimeFormat with UTC offset
- [ ] Host type badge with correct colors from design.md
- [ ] "Register →" opens registration URL in new tab
- [ ] "Add to calendar" calls `GET /webinars/:id/ics` and triggers download

**Acceptance**: card renders correctly; time shown in local timezone; calendar download works

---

### TASK-8: WebinarsPage
- [ ] Create `src/pages/WebinarsPage.tsx`
- [ ] Load webinars via `GET /webinars` with default visa type filter on mount
- [ ] Render FilterChips, DownloadAllButton, WebinarList, ShowPastToggle
- [ ] "Download all (.ics)" calls `GET /webinars/ics?visaType=<current filter>` and triggers download
- [ ] "Show past webinars" toggle re-fetches with `includePast=true`
- [ ] Loading skeleton while fetching
- [ ] Empty state per REQ-1
- [ ] Add "Webinars" link to main nav

**Acceptance**: page loads filtered to user's visa type; toggle shows past webinars; download all works
