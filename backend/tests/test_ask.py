"""Impact explainer / Ask tests. Hermetic (AI_PROVIDER=local)."""
import json

from app.models import NewsItem
from tests.conftest import auth_headers


def _seed_news(db_session) -> None:
    db_session.add(
        NewsItem(
            source="federal_register",
            source_id="fr:test-1",
            title="Proposed rule on STEM OPT unemployment",
            url="https://www.federalregister.gov/x",
            summary="A proposed rule adjusting STEM OPT unemployment limits for students.",
            visa_category="STEM-OPT",
        )
    )
    db_session.commit()


def test_empty_question_rejected(client):
    r = client.post("/ask", json={"question": "   "})
    assert r.status_code in (400, 422)


def test_too_long_question_rejected(client):
    r = client.post("/ask", json={"question": "x" * 501})
    assert r.status_code == 422


def test_no_docs_returns_ungrounded_fallback(client):
    # No NewsItems seeded -> nothing to retrieve.
    r = client.post("/ask", json={"question": "Does the H-1B lottery affect me?"})
    data = r.json()
    assert data["grounded"] is False
    assert "don't have official information" in data["answer"]
    assert data["disclaimer"]


def test_grounded_answer_has_citations_and_disclaimer(client, db_session):
    _seed_news(db_session)
    r = client.post("/ask", json={"question": "How does the STEM OPT unemployment rule affect me?"})
    data = r.json()
    assert data["grounded"] is True
    assert len(data["citations"]) >= 1
    # Citation URL comes from the stored doc, never fabricated.
    assert data["citations"][0]["url"] == "https://www.federalregister.gov/x"
    assert "not legal advice" in data["answer"].lower()
    assert data["statusLabel"] in ("PROPOSED", "FINAL", "IN_EFFECT", "UNCLEAR")


def test_personalized_flag_for_logged_in_user(client, db_session):
    _seed_news(db_session)
    headers = auth_headers(client, email="p@test.com", username="pat")
    # Give pat a profile so personalization context is non-empty.
    client.put(
        "/profile",
        headers=headers,
        json={
            "fullName": "Pat", "visaType": "STEM_OPT", "statusPhase": "active",
            "eadEndDate": "2027-05-01",
            "notifications": {"emailEnabled": True, "alerts": {
                "deadlineApproaching": True, "newRuleAffectingStatus": True,
                "newCreatorPost": False, "newWebinar": False},
                "deadlineLeadTimeDays": [90, 30, 7]},
            "aiPersonalizationFields": {"visaStatus": True, "keyDates": True,
                                        "travel": False, "employer": False},
        },
    )
    r = client.post("/ask", headers=headers,
                    json={"question": "How does the STEM OPT unemployment rule affect me?"})
    assert r.json()["personalized"] is True


def test_history_capped(client, db_session):
    _seed_news(db_session)
    hist = [{"question": f"q{i}", "answer": f"a{i}"} for i in range(10)]
    r = client.post("/ask", json={"question": "STEM OPT unemployment?", "history": hist})
    assert r.status_code == 200  # over-long history accepted and truncated server-side
