"""Visaroo FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import Base, engine
from .routers import (
    ask,
    auth,
    countdowns,
    creator_posts,
    deadlines,
    me,
    news,
    notifications,
    posts,
    profile,
    search,
    votes,
    webinars,
)
from .schemas import CategoriesOut

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Create tables on startup (SQLite dev convenience; use Alembic in prod)."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Visaroo API",
    description=(
        "Community + information platform for international students and visa holders. "
        "Provides general information, not legal advice."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

if settings.frontend_origin == "*":
    # Wildcard origin can't be combined with credentials per the CORS spec. Visaroo
    # uses Bearer tokens (not cookies), so disabling credentials is safe.
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=".*",
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin, "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/healthz", tags=["meta"])
def healthz() -> dict:
    return {
        "status": "ok",
        "ai_provider": settings.ai_provider,
        "crypto_provider": settings.crypto_provider,
    }


@app.get("/meta/categories", response_model=CategoriesOut, tags=["meta"])
def categories() -> CategoriesOut:
    return CategoriesOut()


app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(votes.router)
app.include_router(search.router)
app.include_router(news.router)
app.include_router(profile.router)
app.include_router(deadlines.router)
app.include_router(countdowns.router)
app.include_router(notifications.router)
app.include_router(me.router)
app.include_router(webinars.router)
app.include_router(creator_posts.router)
app.include_router(ask.router)
