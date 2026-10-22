"""Creator feed tests: roles, matcher, soft delete, filters, confidence hiding."""
from app.ai.provider import SourceCandidate, get_provider
from app.models import CreatorPost, NewsItem, User
from tests.conftest import auth_headers


def _set_role(db_session, username: str, role: str) -> None:
    u = db_session.query(User).filter(User.username == username).one()
    u.role = role
    db_session.commit()


def _body(**over) -> dict:
    b = {
        "headline": "Proposed STEM OPT reporting change",
        "body": "A proposed rule would adjust STEM OPT reporting requirements for students.",
        "visaTypeTags": ["STEM_OPT"],
        "statusLabel": "proposed",
        "sourceUrl": "https://www.federalregister.gov/",
        "sourceLabel": "Federal Register",
    }
    b.update(over)
    return b


# ------------------------------ roles -------------------------------

def test_regular_user_cannot_post(client):
    headers = auth_headers(client)  # role=user
    assert client.post("/creator-posts", headers=headers, json=_body()).status_code == 403


def test_creator_can_post(client, db_session):
    headers = auth_headers(client, email="c@test.com", username="cre")
    _set_role(db_session, "cre", "creator")
    r = client.post("/creator-posts", headers=headers, json=_body())
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["statusLabel"] == "proposed"
    # matcher ran -> status resolved away from pending
    assert data["matchStatus"] in ("matched", "no_match")


def test_confidence_score_never_returned(client, db_session):
    headers = auth_headers(client, email="c@test.com", username="cre")
    _set_role(db_session, "cre", "creator")
    data = client.post("/creator-posts", headers=headers, json=_body()).json()
    assert "matchConfidenceScore" not in data
    assert "match_confidence_score" not in data


def test_creator_cannot_delete_others(client, db_session):
    ha = auth_headers(client, email="a@test.com", username="crea")
    _set_role(db_session, "crea", "creator")
    pid = client.post("/creator-posts", headers=ha, json=_body()).json()["id"]
    hb = auth_headers(client, email="b@test.com", username="creb")
    _set_role(db_session, "creb", "creator")
    assert client.delete(f"/creator-posts/{pid}", headers=hb).status_code == 403


def test_soft_delete_hides_from_list_and_detail(client, db_session):
    headers = auth_headers(client, email="c@test.com", username="cre")
    _set_role(db_session, "cre", "creator")
    pid = client.post("/creator-posts", headers=headers, json=_body(headline="Delete me")).json()["id"]
    assert client.delete(f"/creator-posts/{pid}", headers=headers).status_code == 204
    assert client.get(f"/creator-posts/{pid}").status_code == 404
    titles = [p["headline"] for p in client.get("/creator-posts").json()]
    assert "Delete me" not in titles
    # Row retained with deleted=true (soft delete)
    row = db_session.get(CreatorPost, pid)
    assert row is not None and row.deleted is True


# ------------------------------ filters -----------------------------

def test_filters_visa_and_status(client, db_session):
    headers = auth_headers(client, email="c@test.com", username="cre")
    _set_role(db_session, "cre", "creator")
    client.post("/creator-posts", headers=headers,
                json=_body(headline="H1B one", visaTypeTags=["H-1B"], statusLabel="in_effect"))
    client.post("/creator-posts", headers=headers,
                json=_body(headline="All one", visaTypeTags=["ALL"], statusLabel="final"))
    client.post("/creator-posts", headers=headers,
                json=_body(headline="OPT one", visaTypeTags=["OPT"], statusLabel="proposed"))

    opt = [p["headline"] for p in client.get("/creator-posts?visaType=OPT").json()]
    assert "OPT one" in opt
    assert "All one" in opt           # ALL always matches
    assert "H1B one" not in opt

    final = [p["headline"] for p in client.get("/creator-posts?statusLabel=final").json()]
    assert final == ["All one"]


def test_post_validation(client, db_session):
    headers = auth_headers(client, email="c@test.com", username="cre")
    _set_role(db_session, "cre", "creator")
    assert client.post("/creator-posts", headers=headers, json=_body(visaTypeTags=[])).status_code == 422
    assert client.post("/creator-posts", headers=headers, json=_body(statusLabel="bogus")).status_code == 422


# --------------------------- local matcher --------------------------

def test_local_matcher_threshold():
    provider = get_provider()
    cands = [
        SourceCandidate(
            title="STEM OPT reporting requirements adjusted",
            url="https://example.gov/stem",
            text="A rule adjusting STEM OPT reporting requirements for students and employers.",
        )
    ]
    # Strongly overlapping headline/body -> should match.
    m = provider.match_post(
        "STEM OPT reporting requirements adjusted",
        "A rule adjusting STEM OPT reporting requirements for students.",
        cands,
    )
    assert m.matched is True
    assert m.score >= 0.75
    assert m.url == "https://example.gov/stem"

    # Unrelated query -> no match.
    m2 = provider.match_post("Lost my student ID card", "Where do I get a replacement ID?", cands)
    assert m2.matched is False
