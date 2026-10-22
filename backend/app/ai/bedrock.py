"""Amazon Bedrock implementation of the AIProvider protocol.

Uses Claude (messages API) for text generation and Titan for embeddings. Every method
degrades gracefully to the LocalProvider on any error, so a transient Bedrock failure
or missing model access never crashes a request (Requirement 6.3).
"""
from __future__ import annotations

import json
import logging

from ..config import VISA_CATEGORIES, get_settings
from .local import LocalProvider
from .provider import ModerationResult, PostLite, SearchSummary

logger = logging.getLogger("visaroo.bedrock")

_DISCLAIMER = (
    "You provide general information for international students and visa holders. "
    "You are NOT a lawyer and must not give legal advice or state that an action is "
    "definitely legal or illegal. Never fabricate immigration rules."
)


class BedrockProvider:
    """Bedrock-backed provider with a local fallback for resilience."""

    def __init__(self) -> None:
        import boto3  # imported lazily so the app runs without boto3 configured

        self.settings = get_settings()
        self._client = boto3.client(
            "bedrock-runtime", region_name=self.settings.aws_region
        )
        self._fallback = LocalProvider()

    # --------------------------- Text call ------------------------------
    def _invoke_claude(self, system: str, user: str, max_tokens: int = 512) -> str:
        """Generate text via the Bedrock **Converse** API.

        Converse is model-agnostic — the same call works for Anthropic Claude, Amazon
        Nova, Meta Llama, etc. — so the active model is driven purely by
        ``bedrock_text_model_id`` with no per-model request shaping. (Named for history;
        it is no longer Claude-specific.)
        """
        resp = self._client.converse(
            modelId=self.settings.bedrock_text_model_id,
            system=[{"text": system}],
            messages=[{"role": "user", "content": [{"text": user}]}],
            inferenceConfig={"maxTokens": max_tokens, "temperature": 0.1},
        )
        return resp["output"]["message"]["content"][0]["text"]

    @staticmethod
    def _extract_json(text: str) -> dict:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("no JSON object in model output")
        return json.loads(text[start : end + 1])

    # ---------------------------- Gatekeeper ----------------------------
    def moderate_post(self, title: str, body: str) -> ModerationResult:
        try:
            system = (
                _DISCLAIMER
                + " Classify a community post. Respond with ONLY a JSON object with keys: "
                "relevant (bool, is it about US visas/immigration/international students), "
                "reason (short string), suggested_category (one of "
                f"{VISA_CATEGORIES}), suggested_title (a cleaned-up version of the title), "
                "harmful (bool, does it encourage visa fraud or clearly illegal activity)."
            )
            user = f"Title: {title}\n\nBody: {body}"
            data = self._extract_json(self._invoke_claude(system, user, 400))
            category = data.get("suggested_category", "Other")
            if category not in VISA_CATEGORIES:
                category = "Other"
            return ModerationResult(
                relevant=bool(data.get("relevant", True)),
                reason=str(data.get("reason", "")),
                suggested_category=category,
                suggested_title=str(data.get("suggested_title", title)).strip() or title,
                harmful=bool(data.get("harmful", False)),
            )
        except Exception as exc:  # noqa: BLE001 - degrade gracefully
            logger.warning("Bedrock moderate_post failed, using local fallback: %s", exc)
            return self._fallback.moderate_post(title, body)

    # ---------------------------- Embeddings ----------------------------
    def embed_text(self, text: str) -> list[float]:
        try:
            resp = self._client.invoke_model(
                modelId=self.settings.bedrock_embed_model_id,
                body=json.dumps({"inputText": text[:8000]}),
            )
            payload = json.loads(resp["body"].read())
            return payload["embedding"]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Bedrock embed_text failed, using local fallback: %s", exc)
            return self._fallback.embed_text(text)

    # ------------------------------ Search ------------------------------
    def summarize_search(
        self, query: str, posts: list[PostLite], personalization: str | None = None
    ) -> SearchSummary:
        if not posts:
            return self._fallback.summarize_search(query, posts, personalization)
        try:
            joined = "\n\n".join(
                f"[Post {p.id}] {p.title}\n{p.body[:800]}" for p in posts
            )
            system = (
                _DISCLAIMER
                + " Summarize ONLY what the community posts below say in answer to the "
                "user's question. Do not add outside rules. Start by stating how many "
                "posts you used. If the posts disagree, say so."
            )
            if personalization:
                # Derived, non-identifying facts only (never raw dates/sensitive data).
                # Used to tailor relevance/tone; the answer must still come from the posts.
                system += (
                    " The reader has this status (use only to tailor relevance; do not "
                    f"treat as fact to answer from):\n{personalization}"
                )
            user = f"Question: {query}\n\nCommunity posts:\n{joined}"
            summary = self._invoke_claude(system, user, 500).strip()
            return SearchSummary(
                summary=summary,
                used_post_ids=[p.id for p in posts],
                grounded=True,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Bedrock summarize_search failed, using local fallback: %s", exc)
            return self._fallback.summarize_search(query, posts, personalization)

    # -------------------------- Source matching -------------------------
    def match_post(self, headline, body, candidates):
        """Match via the Bedrock Knowledge Base retrieve score. Falls back to the local
        matcher if no KB is configured or the call fails (graceful degradation)."""
        from .provider import MATCH_THRESHOLD, SourceMatch

        kb_id = getattr(self.settings, "bedrock_knowledge_base_id", "") or ""
        if not kb_id:
            return self._fallback.match_post(headline, body, candidates)
        try:
            import boto3

            agent = boto3.client("bedrock-agent-runtime", region_name=self.settings.aws_region)
            resp = agent.retrieve(
                knowledgeBaseId=kb_id,
                retrievalQuery={"text": f"{headline}\n\n{body}"},
                retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 1}},
            )
            results = resp.get("retrievalResults", [])
            if not results:
                return SourceMatch(matched=False, score=0.0)
            top = results[0]
            score = float(top.get("score", 0.0))
            meta = top.get("metadata", {}) or {}
            if score >= MATCH_THRESHOLD:
                return SourceMatch(
                    matched=True,
                    score=round(score, 3),
                    title=meta.get("title"),
                    url=meta.get("sourceUrl") or meta.get("source_url"),
                )
            return SourceMatch(matched=False, score=round(score, 3))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Bedrock match_post failed, using local fallback: %s", exc)
            return self._fallback.match_post(headline, body, candidates)

    # ----------------------- Impact explainer ---------------------------
    def answer_impact(self, question, context, history, candidates):
        """Retrieve official docs (KB when configured, else the provided candidates) and
        answer with Claude, grounded only in those docs. Falls back to the local provider
        on any error (graceful degradation)."""
        from .provider import Citation, ImpactAnswer

        # 1) Gather retrieved docs: Bedrock KB when configured, else local candidates.
        kb_id = getattr(self.settings, "bedrock_knowledge_base_id", "") or ""
        retrieved: list[dict] = []
        try:
            if kb_id:
                import boto3

                agent = boto3.client(
                    "bedrock-agent-runtime", region_name=self.settings.aws_region
                )
                resp = agent.retrieve(
                    knowledgeBaseId=kb_id,
                    retrievalQuery={"text": question},
                    retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 3}},
                )
                for r in resp.get("retrievalResults", []):
                    meta = r.get("metadata", {}) or {}
                    retrieved.append(
                        {
                            "title": meta.get("title", "Official document"),
                            "url": meta.get("sourceUrl") or meta.get("source_url"),
                            "text": (r.get("content", {}) or {}).get("text", ""),
                        }
                    )
            else:
                # Reuse the local provider's ranking over the candidate corpus.
                local_ans = self._fallback.answer_impact(question, context, history, candidates)
                retrieved = [
                    {"title": c.title, "url": c.url, "text": c.excerpt}
                    for c in local_ans.citations
                ]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Bedrock KB retrieve failed, using local fallback: %s", exc)
            return self._fallback.answer_impact(question, context, history, candidates)

        if not retrieved:
            return self._fallback.answer_impact(question, context, history, candidates)

        # 2) Build the grounded prompt and call Claude at temp 0.1, max 800 tokens.
        try:
            docs_block = "\n\n".join(
                f"[{i + 1}] {d['title']}\nSource: {d['url'] or 'n/a'}\nExcerpt: {d['text'][:800]}"
                for i, d in enumerate(retrieved)
            )
            system = (
                _DISCLAIMER
                + " Answer ONLY from the retrieved documents below — never from your own "
                "knowledge. Cite claims by [number]. Label the rule status (PROPOSED / "
                "FINAL / IN EFFECT) from the documents only. Do not give specific legal "
                "advice, state filing fees, or predict case outcomes. If the documents "
                "don't cover it, say you don't have official information and point to "
                "uscis.gov. End with: 'This is general information only — not legal "
                "advice. Always verify with your DSO or a qualified immigration attorney.'"
                f"\n\nUser context (derived, non-identifying):\n{context or 'none'}"
                f"\n\nRetrieved documents:\n{docs_block}"
            )
            answer = self._invoke_claude(system, f"Question: {question}", 800).strip()
            citations = [
                Citation(
                    n=i + 1,
                    title=d["title"],
                    source=self._fallback._source_name(d["url"]),
                    url=d["url"],
                    excerpt=(d["text"][:240] + "…") if len(d["text"]) > 240 else d["text"],
                )
                for i, d in enumerate(retrieved)
            ]
            status = self._fallback._status_from(
                type("C", (), {"title": retrieved[0]["title"], "text": retrieved[0]["text"]})()
            )
            return ImpactAnswer(answer=answer, status_label=status, citations=citations, grounded=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Bedrock answer_impact failed, using local fallback: %s", exc)
            return self._fallback.answer_impact(question, context, history, candidates)

    # ------------------------------ News --------------------------------
    def summarize_news(self, title: str, content: str) -> tuple[str, str]:
        try:
            system = (
                _DISCLAIMER
                + " Summarize this immigration news item in 2 plain-language sentences, "
                "then classify which visa category it most affects. Respond with ONLY a "
                f"JSON object: {{\"summary\": str, \"category\": one of {VISA_CATEGORIES}}}."
            )
            user = f"Title: {title}\n\nContent: {content[:4000]}"
            data = self._extract_json(self._invoke_claude(system, user, 300))
            category = data.get("category", "Other")
            if category not in VISA_CATEGORIES:
                category = "Other"
            return str(data.get("summary", title)).strip(), category
        except Exception as exc:  # noqa: BLE001
            logger.warning("Bedrock summarize_news failed, using local fallback: %s", exc)
            return self._fallback.summarize_news(title, content)
