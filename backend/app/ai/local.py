"""Deterministic, no-network AI provider.

This is the default provider. It uses lightweight heuristics so every AI feature works
offline and reproducibly — critical for demos when Bedrock access may be pending. It is
intentionally conservative and honest: it never fabricates immigration rules, and the
search summary is purely extractive from the matched community posts.
"""
from __future__ import annotations

import hashlib
import math
import re

from ..config import VISA_CATEGORIES
from .provider import ModerationResult, PostLite, SearchSummary

_EMBED_DIM = 256

# Domain lexicon used for relevance detection and category classification.
_DOMAIN_TERMS = {
    "visa", "immigration", "uscis", "sevis", "sevp", "opt", "stem", "ead",
    "h-1b", "h1b", "f-1", "f1", "j-1", "j1", "l-1", "l1", "h-4", "h4",
    "green card", "i-20", "i-765", "i-983", "i-140", "i-485", "ds-160",
    "dso", "status", "unemployment", "stamping", "consulate", "uscis",
    "work authorization", "employment", "cpt", "rfe", "premium processing",
    "travel", "reentry", "port of entry", "visa bulletin", "priority date",
    "international student", "international", "sponsorship", "lottery",
}

# Category keywords matched as whole words/phrases (see _classify). These are specific
# enough that a match is a strong signal for that visa category. Over-generic terms
# ("opt", "cap", "status", "employment", "travel") are deliberately excluded because they
# match unrelated Federal Register documents as substrings and mis-tag them.
_CATEGORY_KEYWORDS = {
    "STEM-OPT": ["stem opt", "i-983", "24-month extension", "stem extension"],
    "OPT": [
        "optional practical training", "opt employment", "ead", "i-765",
        "unemployment days", "post-completion opt", "pre-completion opt",
    ],
    "F-1": ["f-1 student", "f-1 visa", "i-20", "sevis", "sevp", "cpt",
            "curricular practical training", "student and exchange visitor"],
    "H-1B": ["h-1b", "h1b", "specialty occupation", "h-1b cap", "lca",
             "labor condition application"],
    "H-4": ["h-4", "h4 ead", "h-4 dependent"],
    "J-1": ["j-1 exchange", "exchange visitor", "ds-2019", "212(e)",
            "home residency requirement"],
    "L-1": ["l-1 visa", "intracompany transferee", "blanket l"],
    "Green-Card": [
        "green card", "i-140", "i-485", "visa bulletin", "priority date",
        "adjustment of status", "perm labor", "eb-1", "eb-2", "eb-3",
        "permanent resident",
    ],
}

# A document is only classified into a visa category if it shows a genuine immigration
# signal. Without this, unrelated Federal Register rules (securities, energy, health) that
# happen to contain a stray keyword get mis-tagged and pollute the feed.
_IMMIGRATION_SIGNALS = [
    "visa", "immigration", "immigrant", "nonimmigrant", "uscis", "sevis", "sevp",
    "optional practical training", "practical training", "f-1", "h-1b", "h1b",
    "j-1", "l-1", "h-4", "green card", "permanent resident", "ead",
    "employment authorization document", "i-765", "i-983", "i-20", "i-140", "i-485",
    "student and exchange visitor", "exchange visitor", "adjustment of status",
    "naturalization", "asylum", "dhs", "department of homeland security",
    "citizenship and immigration",
]

# Terms that suggest the post may be encouraging fraud / illegal activity.
_HARM_TERMS = [
    "fake document", "fake documents", "forged", "forge ", "fraud", "lie to uscis",
    "lie on", "fake marriage", "sham marriage", "buy ssn", "fake offer letter",
    "shell company opt", "ghost employer", "pay for sponsorship fake",
]

_WORD_RE = re.compile(r"[a-z0-9][a-z0-9\-]+")


def _tokens(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


class LocalProvider:
    """Heuristic implementation of the AIProvider protocol."""

    # ---------------------------- Gatekeeper ----------------------------
    def moderate_post(self, title: str, body: str) -> ModerationResult:
        text = f"{title} {body}".lower()

        hits = sum(1 for term in _DOMAIN_TERMS if term in text)
        relevant = hits >= 1
        reason = (
            "Mentions visa/immigration topics." if relevant
            else "Doesn't clearly relate to visa or immigration topics."
        )

        harmful = any(term in text for term in _HARM_TERMS)
        if harmful:
            reason = "May describe or encourage visa fraud / illegal activity."

        return ModerationResult(
            relevant=relevant,
            reason=reason,
            suggested_category=self._classify(text),
            suggested_title=self._clean_title(title),
            harmful=harmful,
        )

    @staticmethod
    def _has_signal(text: str, needle: str) -> bool:
        """Whole-word/phrase containment so short keys ('ead', 'opt', 'l-1') don't match
        inside unrelated words ('adopt', 'lead', 'capitol')."""
        return re.search(r"(?<![a-z0-9])" + re.escape(needle) + r"(?![a-z0-9])", text) is not None

    def _classify(self, text: str) -> str:
        # Only tag a visa category when the text is genuinely about immigration; otherwise
        # unrelated Federal Register rules get mis-tagged and pollute the feed.
        if not any(self._has_signal(text, s) for s in _IMMIGRATION_SIGNALS):
            return "Other"
        best, best_score = "Other", 0
        for category, keywords in _CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if self._has_signal(text, kw))
            if score > best_score:
                best, best_score = category, score
        return best

    @staticmethod
    def _clean_title(title: str) -> str:
        t = re.sub(r"\s+", " ", title).strip()
        if not t:
            return t
        t = t[0].upper() + t[1:]
        if t[-1] not in ".?!" and t.lower().split(" ")[0] in {
            "how", "can", "what", "when", "does", "do", "is", "are", "should", "will",
        }:
            t += "?"
        return t

    # ---------------------------- Embeddings ----------------------------
    def embed_text(self, text: str) -> list[float]:
        """Deterministic hashing bag-of-words vector, L2-normalized."""
        vec = [0.0] * _EMBED_DIM
        for tok in _tokens(text):
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            vec[h % _EMBED_DIM] += 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    # ------------------------------ Search ------------------------------
    def summarize_search(
        self, query: str, posts: list[PostLite], personalization: str | None = None
    ) -> SearchSummary:
        if not posts:
            return SearchSummary(
                summary=(
                    "No community posts matched your question yet. Be the first to ask — "
                    "and remember this is general information, not legal advice."
                ),
                used_post_ids=[],
                grounded=False,
            )

        q_tokens = set(_tokens(query))
        picked: list[str] = []
        for post in posts[:3]:
            best_sentence = ""
            best_overlap = -1
            for sentence in _sentences(post.body) or [post.title]:
                overlap = len(q_tokens & set(_tokens(sentence)))
                if overlap > best_overlap:
                    best_sentence, best_overlap = sentence, overlap
            if best_sentence:
                picked.append(best_sentence)

        n = len(posts)
        body = " ".join(picked[:3])
        summary = (
            f"Based on {n} community post{'s' if n != 1 else ''}, here's what people "
            f"shared: {body}"
        )
        # The summary stays grounded in the posts; personalization only adds a short,
        # non-identifying note so the reader knows it was tailored to their status.
        if personalization:
            summary += " (Tailored to your saved visa status.)"
        return SearchSummary(
            summary=summary,
            used_post_ids=[p.id for p in posts],
            grounded=True,
        )

    # ------------------------------ News --------------------------------
    def summarize_news(self, title: str, content: str) -> tuple[str, str]:
        sentences = _sentences(content) or [title]
        summary = " ".join(sentences[:2])
        if len(summary) > 400:
            summary = summary[:397] + "..."
        category = self._classify(f"{title} {content}".lower())
        return summary, category

    # -------------------------- Source matching -------------------------
    def match_post(self, headline, body, candidates):
        """Deterministic match against official docs via token-overlap similarity.

        The match decision is purely the similarity score vs the 0.75 threshold — no
        LLM judgment (steering/creator-feed.md). Score is a Jaccard-style overlap.
        """
        from .provider import MATCH_THRESHOLD, SourceMatch

        query_tokens = set(_tokens(f"{headline} {body}"))
        if not query_tokens or not candidates:
            return SourceMatch(matched=False, score=0.0)

        best = None
        best_score = 0.0
        for cand in candidates:
            cand_tokens = set(_tokens(f"{cand.title} {cand.text}"))
            if not cand_tokens:
                continue
            overlap = len(query_tokens & cand_tokens)
            union = len(query_tokens | cand_tokens)
            score = overlap / union if union else 0.0
            # Boost toward the headline's strong terms so a focused post can clear the
            # threshold against a longer official abstract.
            headline_tokens = set(_tokens(headline))
            if headline_tokens:
                h_overlap = len(headline_tokens & cand_tokens) / len(headline_tokens)
                score = max(score, 0.5 * score + 0.5 * h_overlap)
            if score > best_score:
                best, best_score = cand, score

        if best is not None and best_score >= MATCH_THRESHOLD:
            return SourceMatch(
                matched=True, score=round(best_score, 3), title=best.title, url=best.url
            )
        return SourceMatch(matched=False, score=round(best_score, 3))

    # ----------------------- Impact explainer ---------------------------
    _DISCLAIMER = (
        "This is general information only — not legal advice. Always verify with your "
        "DSO or a qualified immigration attorney."
    )
    _NO_INFO = (
        "I don't have official information about this yet. Please check uscis.gov directly."
    )

    def answer_impact(self, question, context, history, candidates):
        """Extractive, grounded answer built ONLY from retrieved candidates. Never
        fabricates; returns the honest no-info fallback when nothing is relevant."""
        from .provider import Citation, ImpactAnswer

        q_tokens = set(_tokens(question))
        # Rank candidates by token overlap with the question.
        ranked: list[tuple[float, "object"]] = []
        for cand in candidates:
            cand_tokens = set(_tokens(f"{cand.title} {cand.text}"))
            if not cand_tokens:
                continue
            overlap = len(q_tokens & cand_tokens)
            if overlap > 0:
                ranked.append((overlap / (len(q_tokens) or 1), cand))
        ranked.sort(key=lambda t: t[0], reverse=True)
        top = [c for _, c in ranked[:3]]

        if not top:
            return ImpactAnswer(
                answer=f"{self._NO_INFO}\n\n{self._DISCLAIMER}",
                status_label="UNCLEAR",
                citations=[],
                grounded=False,
            )

        citations = [
            Citation(
                n=i + 1,
                title=c.title,
                source=self._source_name(c.url),
                url=c.url or None,
                excerpt=(c.text[:240] + "…") if len(c.text) > 240 else c.text,
            )
            for i, c in enumerate(top)
        ]

        ctx_line = (
            f"Based on your saved status ({context.splitlines()[0] if context else 'general'}), "
            if context
            else ""
        )
        body_bits = " ".join(f"{c.excerpt} [{c.n}]" for c in citations)
        answer = (
            f"{ctx_line}here's what the official sources say about your question. "
            f"{body_bits}\n\n{self._DISCLAIMER}"
        )
        return ImpactAnswer(
            answer=answer,
            status_label=self._status_from(top[0]),
            citations=citations,
            grounded=True,
        )

    @staticmethod
    def _source_name(url: str | None) -> str:
        if not url:
            return "Official source"
        if "federalregister.gov" in url:
            return "Federal Register"
        if "uscis.gov" in url:
            return "USCIS.gov"
        if "ice.gov" in url or "studyinthestates" in url:
            return "ICE/SEVP"
        return "Official source"

    @staticmethod
    def _status_from(cand) -> str:
        text = f"{getattr(cand, 'title', '')} {getattr(cand, 'text', '')}".lower()
        if "proposed" in text:
            return "PROPOSED"
        if "final rule" in text or "final" in text:
            return "FINAL"
        if "in effect" in text or "effective" in text:
            return "IN_EFFECT"
        return "UNCLEAR"
