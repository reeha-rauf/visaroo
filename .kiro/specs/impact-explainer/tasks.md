# Tasks: Impact Explainer

## Task List

### TASK-1: S3 corpus bucket
- [ ] Add `visatrack-kb-documents` S3 bucket to SAM template with AES256 encryption
- [ ] Deploy bucket
- [ ] Manually download and save the priority corpus documents listed in design.md to `corpus/` directory

**Acceptance**: bucket exists; corpus/ directory contains at least 10 documents

---

### TASK-2: Corpus upload script
- [ ] Create `scripts/uploadCorpus.ts`
- [ ] Upload all files from `corpus/` to S3 with metadata: title, sourceUrl, documentType, visaTypeTags
- [ ] Run after upload: trigger Knowledge Base sync via `bedrock-agent:StartIngestionJob`
- [ ] Idempotent: skip files already in S3 with matching ETag

**Acceptance**: all corpus documents appear in S3 with correct metadata tags

---

### TASK-3: Bedrock Knowledge Base setup
- [ ] Create Knowledge Base manually in AWS Bedrock console
  - Embedding model: Amazon Titan Embeddings V2
  - Data source: `visatrack-kb-documents` S3 bucket
  - Vector store: Bedrock-managed default
  - Chunking: default semantic, max 300 tokens
- [ ] Run first ingestion job
- [ ] Copy Knowledge Base ID into SSM Parameter Store as `/visaroo/knowledgeBaseId`
- [ ] Update SAM template to read KNOWLEDGE_BASE_ID from SSM

**Acceptance**: ingestion job completes with 0 failed documents; test retrieval query returns relevant chunks

---

### TASK-4: Bedrock Guardrail setup
- [ ] Create Guardrail manually in AWS Bedrock console
- [ ] Configure denied topics per design.md: legal advice, case outcome prediction, filing fees, personal representation
- [ ] Copy Guardrail ID into SSM Parameter Store as `/visaroo/guardrailId`
- [ ] Test guardrail blocks "will USCIS approve my case?" style questions

**Acceptance**: guardrail blocks the four denied topic types in console test

---

### TASK-5: buildPersonalizationContext utility
- [ ] Create `src/utils/personalizationContext.ts` (reuse from profile spec if already built)
- [ ] Takes userId, loads profile from DynamoDB, returns PersonalizationContext
- [ ] Respects aiPersonalizationFields toggles: omits fields where toggle is off
- [ ] Returns emptyContext() when userId is null (unauthenticated)
- [ ] Unit test: all toggles off → context contains only visaType and statusPhase; raw dates never present

**Acceptance**: unit tests pass; no raw dates or sensitive fields in output

---

### TASK-6: Ask Lambda — retrieval and prompt building
- [ ] Create `src/handlers/ask.ts`
- [ ] Retrieve top 3 documents from Knowledge Base using question as query
- [ ] Build system prompt per design.md template with context and retrieved docs
- [ ] Build messages array with conversation history (last 3 turns)
- [ ] Unit test prompt builder: given mock retrieval results, verify system prompt contains all three document excerpts and the personalization context block

**Acceptance**: prompt structure matches design.md; history capped at 3 turns

---

### TASK-7: Ask Lambda — streaming response
- [ ] Call Bedrock ConverseStream with system prompt and messages
- [ ] Stream tokens back via API Gateway HTTP streaming response
- [ ] Apply Guardrail config to the request
- [ ] Log to CloudWatch: userId hash, visaType, num retrieved docs, response length, latency — no raw question text
- [ ] Return 400 if question is empty or over 500 chars
- [ ] Return 503 with "service unavailable" if Bedrock throws; do not surface internal error details

**Acceptance**: streaming response starts within 3s; full response under 15s; CloudWatch logs contain required fields; guardrail blocks denied topics

---

### TASK-8: AskPanel component — input and state
- [ ] Create `src/components/AskPanel.tsx`
- [ ] Slide-in panel from right, available on all pages
- [ ] Text input, max 500 chars, with character counter
- [ ] Disabled while response streaming
- [ ] Accepts `prefillText` prop; populates input when panel opens with prefill
- [ ] Retains last question and answer in component state within session
- [ ] Unauthenticated banner: "Sign in for personalized answers" if no JWT present

**Acceptance**: panel opens from nav Ask button; pre-fill works from deadline cards and creator posts; banner shows for unauthenticated users

---

### TASK-9: AskPanel component — response rendering
- [ ] Render streaming response as markdown with incremental display
- [ ] Rule status label chip (PROPOSED / FINAL / IN EFFECT / UNCLEAR) above answer — parsed from response metadata or first line
- [ ] Citation footnotes rendered below response after streaming completes
- [ ] Each footnote: document title, source name, URL link, excerpt
- [ ] "Not legal advice" disclaimer always visible at bottom
- [ ] Follow-up input appears after first response; passes conversation history on submit

**Acceptance**: citations render as footnotes; status chip correct color; disclaimer always present; follow-up sends history

---

### TASK-10: Wire Ask button to panel
- [ ] Add persistent "Ask" button to nav bar (all pages)
- [ ] Clicking opens AskPanel
- [ ] "Does this affect me?" buttons on deadline cards, creator post cards, and news cards pass pre-fill text and open panel
- [ ] Panel closes on Escape key or clicking outside

**Acceptance**: Ask button works from every page; pre-fill arrives from all three trigger points

---

### TASK-11: Eval set
- [ ] Create `evals/impact-explainer.json` with 20 test cases
- [ ] Cases cover: STEM OPT unemployment rule question, H-1B cap question, proposed rule question, question with no relevant docs in KB, follow-up question
- [ ] Each case has: input question, personalization context, expected response properties (contains citation, contains disclaimer, does not contain specific legal advice, rule status label present)
- [ ] Run evals and fix any cases where guardrail over-blocks or response lacks citations

**Acceptance**: all 20 eval cases pass; no response lacks a citation when relevant docs exist; disclaimer present in every response

---

### TASK-12: Steering file
- [ ] Create `.kiro/steering/impact-explainer.md`
- [ ] Rules: LLM must only answer from retrieved documents; never answer from parametric knowledge; raw dates never in prompt; citations must come from retrieved metadata URLs only; guardrail must be applied on every request; disclaimer must appear in every response; temperature fixed at 0.1; max output tokens 800

**Acceptance**: steering file present before any Bedrock code is written