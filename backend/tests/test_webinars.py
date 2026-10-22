"""Webinars feature tests: list filtering and role perms."""
from datetime import datetime, timedelta, timezone

from app.models import User
from tests.conftest import auth_headers


def _future(days: int) -> str:
    d = (datetime.now(timezone.utc) + timedelta(days=days)).replace(
        hour=17, minute=0, second=0, microsecond=0
    )
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def _past(days: int) -> str:
    d = (datetime.now(timezone.utc) - timedelta(days=days)).replace(
        hour=17, minute=0, second=0, microsecond=0
    )
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def _set_role(db_session, username: str, role: str) -> None:
    user = db_session.query(User).filter(User.username == username).one()
    user.role = role
    db_session.commit()


def _webinar_body(**over) -> dict:
    body = {
        "title": "OPT basics",
        "hostName": "SEVP",
        "hostType": "official",
        "startDateUtc": _future(10),
        "durationMinutes": 60,
        "visaTypeTags": ["OPT", "STEM_OPT"],
        "description": "Overview of OPT.",
        "registrationUrl": "https://studyinthestates.dhs.gov/",
    }
    body.update(over)
    return body


# ------------------------------ roles -------------------------------

def test_regular_user_cannot_post(client):
    headers = auth_headers(client)  # default role=user
    r = client.post("/webinars", headers=headers, json=_webinar_body())
    assert r.status_code == 403


def test_creator_can_post_and_delete_own(client, db_session):
    headers = auth_headers(client, email="c@test.com", username="cre")
    _set_role(db_session, "cre", "creator")
    r = client.post("/webinars", headers=headers, json=_webinar_body())
    assert r.status_code == 201, r.text
    wid = r.json()["id"]
    assert client.delete(f"/webinars/{wid}", headers=headers).status_code == 204


def test_creator_cannot_delete_others(client, db_session):
    # creator A posts
    ha = auth_headers(client, email="a@test.com", username="crea")
    _set_role(db_session, "crea", "creator")
    wid = client.post("/webinars", headers=ha, json=_webinar_body()).json()["id"]
    # creator B tries to delete
    hb = auth_headers(client, email="b@test.com", username="creb")
    _set_role(db_session, "creb", "creator")
    assert client.delete(f"/webinars/{wid}", headers=hb).status_code == 403


def test_admin_can_delete_any(client, db_session):
    ha = auth_headers(client, email="a@test.com", username="crea")
    _set_role(db_session, "crea", "creator")
    wid = client.post("/webinars", headers=ha, json=_webinar_body()).json()["id"]
    hadmin = auth_headers(client, email="admin@test.com", username="adm")
    _set_role(db_session, "adm", "admin")
    assert client.delete(f"/webinars/{wid}", headers=hadmin).status_code == 204


def test_post_validation_requires_a_tag(client, db_session):
    headers = auth_headers(client, email="c@test.com", username="cre")
    _set_role(db_session, "cre", "creator")
    r = client.post("/webinars", headers=headers, json=_webinar_body(visaTypeTags=[]))
    assert r.status_code == 422


# ------------------------------ listing -----------------------------

def test_list_excludes_past_by_default(client, db_session):
    headers = auth_headers(client, email="c@test.com", username="cre")
    _set_role(db_session, "cre", "creator")
    client.post("/webinars", headers=headers, json=_webinar_body(title="Upcoming one"))
    client.post("/webinars", headers=headers,
                json=_webinar_body(title="Past one", startDateUtc=_past(10)))

    titles = [w["title"] for w in client.get("/webinars").json()]
    assert "Upcoming one" in titles
    assert "Past one" not in titles

    with_past = [w["title"] for w in client.get("/webinars?includePast=true").json()]
    assert "Past one" in with_past


def test_list_filters_by_visa_type_and_all(client, db_session):
    headers = auth_headers(client, email="c@test.com", username="cre")
    _set_role(db_session, "cre", "creator")
    client.post("/webinars", headers=headers,
                json=_webinar_body(title="H1B only", visaTypeTags=["H-1B"]))
    client.post("/webinars", headers=headers,
                json=_webinar_body(title="All visas", visaTypeTags=["ALL"]))
    client.post("/webinars", headers=headers,
                json=_webinar_body(title="OPT one", visaTypeTags=["OPT"]))

    opt = [w["title"] for w in client.get("/webinars?visaType=OPT").json()]
    assert "OPT one" in opt
    assert "All visas" in opt      # ALL always matches
    assert "H1B only" not in opt

