# Requirements: Impact Explainer

## Overview
Answer the question "does this rule affect me?" using the user's personalization context and a Bedrock Knowledge Base of official immigration documents. Every answer must be grounded in retrieved source documents, cited, and labeled as information rather than legal advice.

---

## Functional Requirements

### REQ-1: Ask Panel
- A persistent "Ask" button in the nav bar opens a slide-in panel from the right
- The panel is available on every page
- The panel contains a text input and a response area
- The panel retains the last question and answer within the session; clears on logout

### REQ-2: Question Input
- Free-text input, max 500 characters
- Pre-fill supported: other features (deadline cards, creator posts, news cards) pass a pre-filled question string that populates the input when the panel opens
- "Ask" button or Enter key submits
- Input disabled while a response is streaming

### REQ-3: Personalized Impact Check
When a question is submitted:
- Build a personalization context from the user's profile (visa type, status phase, derived date counts, toggles) per the profile spec's `PersonalizationContext` interface
- Include only fields where the user has enabled AI personalization in their privacy settings
- Pass context + question to the impact explainer Lambda
- Stream the response back to the panel

### REQ-4: Response Format
Every response must contain:
- A direct answer to whether the rule or change affects the user, given their status (yes / no / depends / unclear)
- A plain-language explanation of what the rule means
- The specific implication for the user's visa type and status phase
- At least one cited source with title, URL, and the relevant excerpt that supports the answer
- A "not legal advice" disclaimer at the end of every response

If the Knowledge Base returns no relevant documents, the response must say "I don't have official information about this yet" and suggest checking USCIS.gov directly. It must not fabricate an answer.

### REQ-5: Citations
- Every factual claim in the response must be tied to a retrieved document
- Citations rendered as numbered footnotes at the bottom of the response
- Each citation shows: document title, source (e.g. Federal Register, USCIS.gov), URL, and the retrieved excerpt that supports the claim
- Clicking a citation scrolls to the footnote

### REQ-6: Proposed vs. Final Labeling
- If the retrieved source document is a proposed rule, the response must prominently label it as "Proposed — not yet in effect"
- If final, label as "Final rule"
- If in effect, label as "Currently in effect"
- This label appears above the answer, not buried in the body

### REQ-7: Follow-up Questions
- After a response, the user can ask a follow-up in the same panel
- Follow-up includes the previous question and answer as context (up to 3 turns of history)
- Each follow-up re-runs retrieval; context window is not assumed to retain retrieved documents

### REQ-8: Unauthenticated Access
- Unauthenticated users can ask questions but receive a generic (non-personalized) response
- A banner prompts them to sign in for personalized answers
- Personalization context is empty for unauthenticated requests

### REQ-9: Guardrails
- Bedrock Guardrails must be configured to:
  - Block responses that give specific legal advice ("you should file by...")
  - Block responses that state specific filing fees (these change and should always be verified)
  - Redirect any question about a specific personal legal situation to a qualified attorney
  - Never claim USCIS will approve or deny a specific case

---

## Non-Functional Requirements

### REQ-NF-1: Grounding
- Responses must only draw on documents retrieved from the Knowledge Base
- The LLM must not answer from parametric knowledge alone
- If retrieval returns nothing relevant, respond with "I don't have official information about this"

### REQ-NF-2: Latency
- First token must stream within 3 seconds
- Full response must complete within 15 seconds for typical questions

### REQ-NF-3: No hallucination of sources
- Citation URLs must come directly from retrieved document metadata
- The LLM must not construct or guess URLs
- If a retrieved document has no URL in its metadata, it must not be cited with a URL

### REQ-NF-4: Cost control
- Maximum 3 retrieved documents per query (numberOfResults: 3)
- Maximum output tokens: 800
- Conversation history limited to last 3 turns to control context size

### REQ-NF-5: Logging
- Every query and response logged to CloudWatch with: userId (or anonymous), question hash (not raw text), visa type from context, number of retrieved documents, response length, latency
- Raw question text not logged to protect privacy