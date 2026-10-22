"""Core behavioral tests. Run hermetically with AI_PROVIDER=local."""
from tests.conftest import auth_headers


def test_signup_login_me(client):
    headers = auth_headers(client)
    me = client.get("/auth/me", headers=headers).json()
    assert me["username"] == "alice"
    assert me["visa_category"] == "OPT"


def test_protected_requires_token(client):
    assert client.get("/auth/me").status_code == 401


def test_create_post_and_gatekeeper_flag(client):
    headers = auth_headers(client)
    # On-topic post
    r = client.post(
        "/posts",
        headers=headers,
        json={"title": "OPT unemployment days question",
              "body": "How many unemployment days do I get on OPT and STEM OPT?",
              "visa_category": "OPT", "is_anonymous": False},
    )
    assert r.status_code == 201
    assert r.json()["gatekeeper_flag"] is None

    # Off-topic post -> soft flag, still created
    r2 = client.post(
        "/posts",
        headers=headers,
        json={"title": "Selling my couch", "body": "Cheap sofa for sale downtown",
              "visa_category": "Other", "is_anonymous": False},
    )
    assert r2.status_code == 201
    assert r2.json()["gatekeeper_flag"] == "off_topic"


def test_moderation_preview_soft_warn(client):
    headers = auth_headers(client)
    r = client.post(
        "/posts/moderate",
        headers=headers,
        json={"title": "random off topic", "body": "my cat is cute",
              "visa_category": "Other"},
    )
    data = r.json()
    assert data["relevant"] is False
    assert data["warning"] is not None  # soft-warn, not a block


def test_anonymous_identity_not_leaked(client):
    headers = auth_headers(client)
    pid = client.post(
        "/posts",
        headers=headers,
        json={"title": "Anonymous H-1B lottery worry",
              "body": "Nervous about the H-1B lottery cap this year.",
              "visa_category": "H-1B", "is_anonymous": True},
    ).json()["id"]
    detail = client.get(f"/posts/{pid}").json()
    assert detail["author"] == "Anonymous"
    assert "alice" not in str(detail)


def test_voting_is_unique_and_toggles(client):
    headers = auth_headers(client)
    pid = client.post(
        "/posts", headers=headers,
        json={"title": "OPT travel reentry", "body": "Can I travel on OPT with EAD?",
              "visa_category": "OPT", "is_anonymous": False},
    ).json()["id"]

    client.post("/votes", headers=headers,
                json={"target_type": "post", "target_id": pid, "value": 1})
    assert client.get(f"/posts/{pid}").json()["score"] == 1
    # Same vote again toggles off
    client.post("/votes", headers=headers,
                json={"target_type": "post", "target_id": pid, "value": 1})
    assert client.get(f"/posts/{pid}").json()["score"] == 0


def test_best_answer_single(client):
    headers = auth_headers(client)
    pid = client.post(
        "/posts", headers=headers,
        json={"title": "STEM OPT I-983 question", "body": "Who signs the I-983?",
              "visa_category": "STEM-OPT", "is_anonymous": False},
    ).json()["id"]
    a1 = client.post(f"/posts/{pid}/answers", headers=headers,
                     json={"body": "Your employer and you.", "is_anonymous": False}).json()["id"]
    a2 = client.post(f"/posts/{pid}/answers", headers=headers,
                     json={"body": "The DSO reviews it.", "is_anonymous": False}).json()["id"]
    client.post(f"/answers/{a1}/best", headers=headers)
    client.post(f"/answers/{a2}/best", headers=headers)
    answers = {a["id"]: a["is_best"] for a in client.get(f"/posts/{pid}").json()["answers"]}
    assert answers[a2] is True and answers[a1] is False


def test_search_grounding(client):
    headers = auth_headers(client)
    # No posts yet -> not grounded
    r = client.post("/search", json={"query": "H-1B lottery odds"})
    assert r.json()["grounded"] is False

    client.post("/posts", headers=headers,
                json={"title": "H-1B lottery experience",
                      "body": "I registered for the H-1B lottery cap and got selected in the second round.",
                      "visa_category": "H-1B", "is_anonymous": False})
    r2 = client.post("/search", json={"query": "H-1B lottery cap selected"})
    data = r2.json()
    assert data["grounded"] is True
    assert len(data["results"]) >= 1
    assert data["disclaimer"]
