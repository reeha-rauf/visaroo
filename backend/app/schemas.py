"""Pydantic schemas for request/response bodies.

Anonymity rule (see .kiro/steering/responsible-ai.md): when a post or answer is
anonymous, the author's identity must never appear in the response. This is enforced
by the ``*_to_schema`` builders below, not left to the client.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .config import VISA_CATEGORIES

# ----------------------------- Auth -----------------------------


class SignupRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=8, max_length=128)
    visa_category: str = "Other"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    username: str
    visa_category: str
    role: str = "user"


class ProfileUpdate(BaseModel):
    visa_category: str


# ----------------------------- Posts ----------------------------


class PostCreate(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    body: str = Field(min_length=1)
    visa_category: str = "Other"
    is_anonymous: bool = False


class AnswerCreate(BaseModel):
    body: str = Field(min_length=1)
    is_anonymous: bool = False


class AnswerOut(BaseModel):
    id: int
    body: str
    author: str  # username or "Anonymous"
    is_best: bool
    score: int
    created_at: datetime


class PostOut(BaseModel):
    id: int
    title: str
    body: str
    visa_category: str
    author: str  # username or "Anonymous"
    gatekeeper_flag: str | None
    score: int
    answer_count: int
    created_at: datetime


class PostDetailOut(PostOut):
    answers: list[AnswerOut]


# ------------------------- My content ---------------------------
# The owner is viewing their OWN posts/answers, so is_anonymous is surfaced (as a badge)
# rather than hiding identity — the user knows what they wrote.


class MyPostOut(BaseModel):
    id: int
    title: str
    visa_category: str
    is_anonymous: bool
    score: int
    answer_count: int
    created_at: datetime


class MyAnswerOut(BaseModel):
    id: int
    body: str
    is_anonymous: bool
    is_best: bool
    score: int
    created_at: datetime
    post_id: int
    post_title: str


# --------------------------- Gatekeeper -------------------------


class ModerationOut(BaseModel):
    relevant: bool
    reason: str
    suggested_category: str
    suggested_title: str
    harmful: bool
    warning: str | None = None  # soft-warn message, None when all clear


# ----------------------------- Votes ----------------------------


class VoteRequest(BaseModel):
    target_type: str  # "post" | "answer"
    target_id: int
    value: int  # +1 or -1


# ----------------------------- Search ---------------------------


class SearchRequest(BaseModel):
    query: str = Field(min_length=2)


class SearchResultPost(BaseModel):
    id: int
    title: str
    snippet: str
    visa_category: str
    score: int
    similarity: float


class SearchResponse(BaseModel):
    query: str
    summary: str
    grounded: bool
    used_post_ids: list[int]
    results: list[SearchResultPost]
    disclaimer: str
    personalized: bool = False


# ----------------------------- News -----------------------------


class NewsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source: str
    title: str
    url: str
    summary: str
    visa_category: str
    image_url: str | None = None
    published_at: datetime | None


# ----------------------------- Meta -----------------------------


class CategoriesOut(BaseModel):
    categories: list[str] = Field(default_factory=lambda: list(VISA_CATEGORIES))
