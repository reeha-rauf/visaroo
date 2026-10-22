"""AI provider interface and factory.

All AI behaviour in Visaroo flows through this interface so the rest of the app never
depends directly on AWS. Two implementations exist:

* ``LocalProvider``  — deterministic, no-network fallback (default).
* ``BedrockProvider`` — real Amazon Bedrock calls.

The active provider is selected by the ``AI_PROVIDER`` env var. Defaulting to ``local``
means the app always runs and demos even if Bedrock model access is still pending.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Protocol

from ..config import get_settings

# Official-source match threshold (hardcoded per steering/creator-feed.md).
MATCH_THRESHOLD = 0.75


@dataclass
class ModerationResult:
    """Result of the posting gatekeeper. Behaviour is soft-warn, never a hard block."""

    relevant: bool
    reason: str
    suggested_category: str
    suggested_title: str
    harmful: bool


@dataclass
class PostLite:
    """Lightweight post representation passed to search summarization."""

    id: int
    title: str
    body: str


@dataclass
class SearchSummary:
    summary: str
    used_post_ids: list[int] = field(default_factory=list)
    grounded: bool = False


@dataclass
class SourceCandidate:
    """An official document to match a creator post against (local provider input)."""

    title: str
    url: str
    text: str


@dataclass
class SourceMatch:
    """Result of matching a creator post against official sources.

    ``score`` is the raw retrieval similarity (stored for debugging, never shown to
    users). ``matched`` is True only when score >= the 0.75 threshold.
    """

    matched: bool
    score: float
    title: str | None = None
    url: str | None = None


@dataclass
class Citation:
    """A cited source backing an impact-explainer answer. URL comes only from the
    retrieved document metadata (never model-constructed)."""

    n: int
    title: str
    source: str
    url: str | None
    excerpt: str


@dataclass
class ImpactAnswer:
    """Result of the impact explainer. ``grounded`` is False when no relevant docs were
    retrieved (the answer is then the honest no-information fallback)."""

    answer: str
    status_label: str  # PROPOSED | FINAL | IN_EFFECT | UNCLEAR
    citations: list[Citation] = field(default_factory=list)
    grounded: bool = False


class AIProvider(Protocol):
    """Contract every AI backend must satisfy."""

    def moderate_post(self, title: str, body: str) -> ModerationResult: ...

    def embed_text(self, text: str) -> list[float]: ...

    def summarize_search(
        self, query: str, posts: list[PostLite], personalization: str | None = None
    ) -> SearchSummary:
        """Summarize matched posts. ``personalization`` is an optional block of derived,
        non-identifying facts about the user (never raw dates/sensitive data)."""
        ...

    def summarize_news(self, title: str, content: str) -> tuple[str, str]:
        """Return ``(plain_language_summary, visa_category)``."""
        ...

    def match_post(
        self, headline: str, body: str, candidates: list["SourceCandidate"]
    ) -> SourceMatch:
        """Match a creator post against official sources via vector similarity.

        ``candidates`` are official documents to match against (used by the local
        provider; the Bedrock provider queries its Knowledge Base instead). Returns a
        SourceMatch whose ``matched`` flag reflects ONLY the retrieval score against the
        0.75 threshold — the LLM never judges the match."""
        ...

    def answer_impact(
        self,
        question: str,
        context: str,
        history: list[dict],
        candidates: list["SourceCandidate"],
    ) -> "ImpactAnswer":
        """Answer "does this affect me?" grounded ONLY in the retrieved ``candidates``.

        ``context`` is the derived personalization block (no raw dates). ``history`` is
        up to 3 prior turns. If no candidate is relevant, returns an ungrounded honest
        no-information answer — never fabricates (see steering/impact-explainer.md)."""
        ...


@lru_cache
def get_provider() -> AIProvider:
    """Return the configured AI provider (cached)."""
    settings = get_settings()
    if settings.ai_provider.lower() == "bedrock":
        from .bedrock import BedrockProvider

        return BedrockProvider()
    from .local import LocalProvider

    return LocalProvider()
