"""SQLAlchemy ORM models for Visaroo."""
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    visa_category: Mapped[str] = mapped_column(String(32), default="Other")
    # Role maps to Cognito groups in production: "user" | "creator" | "admin".
    role: Mapped[str] = mapped_column(String(16), default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    posts: Mapped[list["Post"]] = relationship(back_populates="author")
    answers: Mapped[list["Answer"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text)
    visa_category: Mapped[str] = mapped_column(String(32), default="Other", index=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    # Nullable soft-warn flag set by the AI gatekeeper (e.g. "off_topic", "harmful").
    gatekeeper_flag: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Stored embedding as JSON-encoded list[float] for semantic search.
    embedding: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    author: Mapped["User"] = relationship(back_populates="posts")
    answers: Mapped[list["Answer"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    is_best: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    post: Mapped["Post"] = relationship(back_populates="answers")
    author: Mapped["User"] = relationship(back_populates="answers")


class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (
        UniqueConstraint("user_id", "target_type", "target_id", name="uq_vote_once"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    target_type: Mapped[str] = mapped_column(String(10))  # "post" | "answer"
    target_id: Mapped[int] = mapped_column(Integer)
    value: Mapped[int] = mapped_column(Integer)  # +1 or -1


class Profile(Base):
    """Full user profile (see .kiro/specs/profile/).

    Scalar fields are columns; nested/list structures (travel, notifications,
    personalization toggles) are JSON-encoded text. Sensitive fields
    (employer_everify, employer_ein, petition_receipt_number) are stored encrypted
    at rest via the crypto provider — never plaintext.
    """

    __tablename__ = "profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)

    # Identity
    full_name: Mapped[str] = mapped_column(String(200), default="")
    country_of_origin: Mapped[str | None] = mapped_column(String(120), nullable=True)
    university_or_employer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    field_or_title: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Visa status
    visa_type: Mapped[str] = mapped_column(String(16), default="Other")
    status_phase: Mapped[str] = mapped_column(String(40), default="active")

    # Key dates (ISO 8601 strings, nullable)
    program_start_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    program_end_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    i20_expiry_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    port_of_entry_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    visa_stamp_expiry: Mapped[str | None] = mapped_column(String(10), nullable=True)
    ead_start_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    ead_end_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    next_sevp_reporting_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    next_renewal_reminder: Mapped[str | None] = mapped_column(String(10), nullable=True)
    grace_period_end_date: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # OPT / STEM OPT
    employer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    employer_everify: Mapped[str | None] = mapped_column(Text, nullable=True)  # encrypted
    stem_opt_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    i983_on_file: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    unemployment_days_used: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # H-1B
    petition_receipt_number: Mapped[str | None] = mapped_column(Text, nullable=True)  # encrypted
    petition_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    i94_expiry_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    employer_ein: Mapped[str | None] = mapped_column(Text, nullable=True)  # encrypted
    h1b_transfer_in_progress: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    h1b_petition_expiry: Mapped[str | None] = mapped_column(String(10), nullable=True)
    cap_gap_end: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Deadline tracker extras
    passport_expiry: Mapped[str | None] = mapped_column(String(10), nullable=True)
    last_reportable_event_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    last_sevp_reported_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    # JSON map of deadlineId -> ISO date for manual overrides (REQ-7).
    deadline_overrides: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Travel
    last_us_entry_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    upcoming_travel: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    recent_countries_visited: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    advance_parole_filed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # DSO / attorney
    dso_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    dso_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attorney_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    attorney_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Verified-creator profile (populated for users in the creator role)
    creator_display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    creator_bio: Mapped[str | None] = mapped_column(String(160), nullable=True)
    creator_avatar_url: Mapped[str | None] = mapped_column(String(800), nullable=True)
    creator_source_links: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list

    # Notifications + privacy toggles (JSON)
    notifications: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_personalization_fields: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class Countdown(Base):
    """A user-pinned, persistent deadline countdown (see deadline-tracker steering).

    A countdown is a label + a target date the user chose to keep visible across the
    app. It may originate from a computed deadline (``source_deadline_id`` set) or be a
    free-form personal reminder. The target date is stored verbatim as an ISO-8601
    string; the server NEVER computes or adjusts it (steering/deadline-tracker.md — all
    deadline math is client-side pure functions). The live "days remaining" is derived
    on the client on every render from this stored date.
    """

    __tablename__ = "countdowns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    target_date: Mapped[str] = mapped_column(String(10))  # ISO 8601 (YYYY-MM-DD)
    # When pinned from a computed deadline, its DeadlineId; null for custom countdowns.
    source_deadline_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class Notification(Base):
    """An in-app notification for a user about activity on their own content.

    Generated synchronously at the community write sites (new answer on your question,
    your answer marked best, a new upvote on your content). Author anonymity is
    respected: when the acting user posted/answered anonymously, ``actor`` is stored as
    "Anonymous" — the real username never appears here.
    """

    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # "new_answer" | "best_answer" | "post_upvote" | "answer_upvote"
    type: Mapped[str] = mapped_column(String(20))
    actor: Mapped[str] = mapped_column(String(80), default="Someone")  # display name or "Anonymous"
    message: Mapped[str] = mapped_column(String(300))
    # The post to navigate to when the notification is clicked (always a post id).
    post_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    answer_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ReminderSent(Base):
    """Dedup record so each (user, deadline, threshold) reminder fires at most once.

    Mirrors the production `visatrack-reminders-sent` DynamoDB table (design.md): the
    composite key is stored as a single string PK `${userId}#${deadlineId}#${threshold}`.
    """

    __tablename__ = "reminders_sent"

    pk: Mapped[str] = mapped_column(String(200), primary_key=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class CreatorPost(Base):
    """A verified-creator news-commentary post (see .kiro/specs/creator-feed/).

    ``match_confidence_score`` is stored for debugging but is NEVER serialized to the
    client (steering/creator-feed.md). Posts are soft-deleted via ``deleted``.
    Production target: DynamoDB `visatrack-posts`.
    """

    __tablename__ = "creator_posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    creator_display_name: Mapped[str] = mapped_column(String(120), default="")
    headline: Mapped[str] = mapped_column(String(120))
    body: Mapped[str] = mapped_column(String(1000))
    visa_type_tags: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    status_label: Mapped[str] = mapped_column(String(20))  # rumor_reported|proposed|final|in_effect
    source_url: Mapped[str] = mapped_column(String(800))
    source_label: Mapped[str] = mapped_column(String(120))
    effective_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    expiry_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    posted_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Official-source match (populated by the matcher).
    match_status: Mapped[str] = mapped_column(String(12), default="pending")  # pending|matched|no_match
    matched_document_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    matched_document_url: Mapped[str | None] = mapped_column(String(800), nullable=True)
    match_confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # never serialized

    deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class Webinar(Base):
    """An immigration-related webinar (see .kiro/specs/webinars/).

    Datetimes are stored in UTC (ISO 8601 string). ``visa_type_tags`` and
    ``related_resources`` are JSON-encoded lists. Production target: DynamoDB
    `visatrack-webinars`.
    """

    __tablename__ = "webinars"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    title: Mapped[str] = mapped_column(String(300))
    host_name: Mapped[str] = mapped_column(String(200))
    host_type: Mapped[str] = mapped_column(String(20))  # official|verified_creator|community
    posted_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    start_date_utc: Mapped[str] = mapped_column(String(32), index=True)  # ISO 8601 UTC
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    visa_type_tags: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    description: Mapped[str] = mapped_column(String(280), default="")
    registration_url: Mapped[str] = mapped_column(String(800), default="")
    speaker_bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_resources: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class NewsItem(Base):
    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(32))  # "federal_register" | "rss"
    source_id: Mapped[str] = mapped_column(String(400), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(800))
    summary: Mapped[str] = mapped_column(Text, default="")
    visa_category: Mapped[str] = mapped_column(String(32), default="Other", index=True)
    # Real article image (og:image) when the source has one; else None → the frontend
    # falls back to a curated category image, then a gradient banner.
    image_url: Mapped[str | None] = mapped_column(String(800), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
