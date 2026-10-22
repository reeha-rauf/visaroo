"""Pytest fixtures: isolated in-memory DB + TestClient with the local AI/crypto providers."""
import os

os.environ.setdefault("AI_PROVIDER", "local")
os.environ.setdefault("CRYPTO_PROVIDER", "local")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def _db():
    """A fresh in-memory DB engine + session factory shared by client and db_session."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    return TestingSession


@pytest.fixture()
def client(_db):
    def override_get_db():
        db = _db()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def db_session(_db):
    """Direct session on the same DB the client uses, for inspecting raw rows."""
    db = _db()
    try:
        yield db
    finally:
        db.close()


def auth_headers(client, email="a@test.com", username="alice", visa="OPT"):
    client.post(
        "/auth/signup",
        json={"email": email, "username": username, "password": "password123",
              "visa_category": visa},
    )
    token = client.post(
        "/auth/login", json={"email": email, "password": "password123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
