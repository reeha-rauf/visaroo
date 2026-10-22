# Tasks: Creator Feed

## Task List

### TASK-1: DynamoDB table and EventBridge bus
- [ ] Add `visatrack-posts` table to SAM template
- [ ] Add `visaroo-events` EventBridge custom bus to SAM template
- [ ] Deploy and verify both resources exist

**Acceptance**: table and event bus visible in AWS console

---

### TASK-2: Posts Lambda — GET routes
- [ ] Create `src/handlers/posts.ts`
- [ ] `GET /posts`: scan table, filter `deleted = false`, apply visaType and statusLabel query params, return sorted by `postedAt` descending
- [ ] `GET /posts/:id`: GetItem by id; 404 if not found or deleted
- [ ] No auth required

**Acceptance**: returns posts filtered correctly; deleted posts excluded; 404 on missing id

---

### TASK-3: Posts Lambda — POST, PUT, DELETE
- [ ] `POST /posts`: validate body with Zod per REQ-2; check VerifiedCreator or Admin group; write to DynamoDB with `matchStatus: pending`; publish `PostCreated` event to EventBridge
- [ ] `PUT /posts/:id`: verify caller owns post; update fields; publish `PostUpdated` event
- [ ] `DELETE /posts/:id`: verify caller owns post or is Admin; set `deleted: true`
- [ ] Return 403 if group check fails

**Acceptance**: post appears in GET /posts immediately after creation with matchStatus pending; non-creator gets 403; edit re-publishes event

---

### TASK-4: Source matcher Lambda
- [ ] Create `src/handlers/sourceMatcher.ts`
- [ ] Triggered by EventBridge `PostCreated` and `PostUpdated` events
- [ ] Query Bedrock Knowledge Base with post headline + body
- [ ] If score >= 0.75: update post with matched document title, URL, score, matchStatus: matched
- [ ] If score < 0.75: update post with matchStatus: no_match and score
- [ ] Unit test: mock Bedrock response above threshold → correct fields written; below threshold → no_match

**Acceptance**: after posting, DynamoDB record updates to matched or no_match within 30 seconds

---

### TASK-5: PostCard component — collapsed state
- [ ] Create `src/components/PostCard.tsx`
- [ ] Render: creator name + Verified Creator badge, time ago, status label chip, visa type tags, headline, source link, match status indicator, disclaimer label
- [ ] Status label chip colors per REQ-3
- [ ] Match status: spinner for pending, green check for matched with link, grey clock for no_match
- [ ] Poll `GET /posts/:id` every 5 seconds while matchStatus is pending; stop after 60 seconds

**Acceptance**: all three match states render correctly; polling stops after 60s

---

### TASK-6: PostCard component — expanded state
- [ ] Expand on card click
- [ ] Show full body, effective date, expiry date
- [ ] "Does this affect me?" button opens Ask panel pre-filled with post headline and user personalization context
- [ ] "View official source" button links to matchedDocumentUrl (hidden when no_match or pending)

**Acceptance**: expansion shows all fields; Ask panel receives correct pre-fill text

---

### TASK-7: Creator post form
- [ ] Create `src/components/CreatePostModal.tsx`
- [ ] Fields per REQ-2 with client-side Zod validation
- [ ] Status label selector with color preview
- [ ] Visa type tag multi-select
- [ ] Submit calls `POST /posts`; closes modal and prepends new post to feed on success
- [ ] "New post" button visible only to VerifiedCreator Cognito group users

**Acceptance**: form validates all required fields; successful post appears at top of feed immediately

---

### TASK-8: FeedFilterBar component
- [ ] Create `src/components/FeedFilterBar.tsx`
- [ ] Visa type chips: All | F-1 | OPT | STEM OPT | H-1B | H-4 | J-1
- [ ] Status label chips: All | Proposed | Final | In effect | Reported
- [ ] Default visa type from user profile on mount
- [ ] Changing either filter re-fetches `GET /posts` with updated query params

**Acceptance**: filter changes update the feed; default matches user's visa type

---

### TASK-9: CreatorFeedPage
- [ ] Create `src/pages/CreatorFeedPage.tsx`
- [ ] Load posts on mount via `GET /posts` with default filters
- [ ] Render FeedFilterBar, PostList, CreatePostButton
- [ ] Loading skeleton while fetching
- [ ] Empty state: "No posts match your current filters"
- [ ] "Community" nav link routes here

**Acceptance**: page loads with correct default filter; empty state shows when no results

---

### TASK-10: Seed script
- [ ] Create `scripts/seedCreatorPosts.ts`
- [ ] Create dummy creator Cognito user in VerifiedCreator group
- [ ] Seed 5 posts per REQ-8 design.md seed data with pre-set matchStatus values
- [ ] Idempotent: skip posts that already exist by checking headline

**Acceptance**: running twice does not duplicate posts; all 5 posts appear in feed with correct status labels and match states

---

### TASK-11: Steering file
- [ ] Create `.kiro/steering/creator-feed.md`
- [ ] Rules: official source match confidence must come from Bedrock retrieve score only, never LLM judgment; threshold is 0.75 hardcoded; confidence score must never be displayed to users; every post card must include the per-card disclaimer from REQ-NF-3

**Acceptance**: steering file present before source matcher Lambda is written