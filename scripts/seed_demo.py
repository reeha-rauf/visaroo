"""Seed Visaroo with realistic demo content.

Creates a few users and community posts (with answers and votes) so the Feed and AI
Search have something to show in a demo. Safe to run repeatedly — it skips users that
already exist. Run from the repo root:

    python scripts/seed_demo.py
"""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from app.auth import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.ai.provider import get_provider  # noqa: E402
import json  # noqa: E402
from app.models import Answer, Post, User, Vote  # noqa: E402

USERS = [
    ("maya@demo.com", "maya", "OPT"),
    ("arjun@demo.com", "arjun", "STEM-OPT"),
    ("li@demo.com", "li", "H-1B"),
    ("sofia@demo.com", "sofia", "F-1"),
]

POSTS = [
    (
        "maya",
        "How many unemployment days do I have on OPT?",
        "I just started my 12-month OPT and I'm between jobs. I know there's a limit on "
        "unemployment days. How many do I get, and does STEM OPT add more?",
        "OPT",
        False,
    ),
    (
        "arjun",
        "Who signs the I-983 for STEM OPT?",
        "Filing my STEM OPT extension. Confused about the I-983 training plan — does my "
        "employer sign it, do I sign it, and does the DSO need to review it before I send?",
        "STEM-OPT",
        False,
    ),
    (
        "li",
        "Got selected in the H-1B lottery second round — what now?",
        "My employer registered me for the H-1B cap and I was selected in a later round. "
        "What are the next steps and typical timeline for the petition?",
        "H-1B",
        True,
    ),
    (
        "sofia",
        "Can I do CPT in my first semester on F-1?",
        "I'm a new F-1 master's student and got a part-time offer. Can I use CPT in my "
        "first semester or do I need to wait a full academic year?",
        "F-1",
        False,
    ),
    (
        "maya",
        "Traveling abroad while STEM OPT extension is pending",
        "My STEM OPT extension is pending with USCIS and my current EAD expires soon. Is "
        "it risky to travel internationally while it's pending?",
        "STEM-OPT",
        False,
    ),
]

ANSWERS = [
    (
        "How many unemployment days do I have on OPT?",
        "arjun",
        "On standard 12-month OPT you generally get up to 90 days of unemployment, and the "
        "STEM extension adds 60 more for a total of 150. Keep your SEVP portal updated. "
        "(General info — confirm with your DSO.)",
        True,
    ),
    (
        "Who signs the I-983 for STEM OPT?",
        "maya",
        "You and your employer both complete and sign the I-983, then your DSO reviews it "
        "before you submit the extension. Mine wanted it a few weeks early.",
        True,
    ),
    (
        "Got selected in the H-1B lottery second round — what now?",
        "sofia",
        "Once selected, your employer's attorney files the full petition within the filing "
        "window. Premium processing can speed up the decision. Timelines vary a lot.",
        False,
    ),
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    provider = get_provider()
    try:
        by_name: dict[str, User] = {}
        for email, username, visa in USERS:
            user = db.query(User).filter(User.username == username).one_or_none()
            if user is None:
                user = User(
                    email=email,
                    username=username,
                    password_hash=hash_password("password123"),
                    visa_category=visa,
                )
                db.add(user)
                db.flush()
            by_name[username] = user

        posts_by_title: dict[str, Post] = {}
        for author, title, body, category, anon in POSTS:
            existing = db.query(Post).filter(Post.title == title).one_or_none()
            if existing:
                posts_by_title[title] = existing
                continue
            post = Post(
                author_id=by_name[author].id,
                title=title,
                body=body,
                visa_category=category,
                is_anonymous=anon,
                embedding=json.dumps(provider.embed_text(f"{title}\n{body}")),
            )
            db.add(post)
            db.flush()
            posts_by_title[title] = post

        for post_title, author, body, is_best in ANSWERS:
            post = posts_by_title[post_title]
            exists = (
                db.query(Answer)
                .filter(Answer.post_id == post.id, Answer.body == body)
                .one_or_none()
            )
            if exists:
                continue
            db.add(
                Answer(
                    post_id=post.id,
                    author_id=by_name[author].id,
                    body=body,
                    is_best=is_best,
                )
            )

        # A few votes so scores aren't all zero.
        for title in list(posts_by_title)[:3]:
            post = posts_by_title[title]
            for voter in list(by_name.values())[:2]:
                has = (
                    db.query(Vote)
                    .filter(
                        Vote.user_id == voter.id,
                        Vote.target_type == "post",
                        Vote.target_id == post.id,
                    )
                    .one_or_none()
                )
                if not has:
                    db.add(
                        Vote(
                            user_id=voter.id,
                            target_type="post",
                            target_id=post.id,
                            value=1,
                        )
                    )

        db.commit()
        print(
            f"[visaroo] seed complete: users={db.query(User).count()} "
            f"posts={db.query(Post).count()} answers={db.query(Answer).count()}"
        )
        print("[visaroo] demo login: maya@demo.com / password123")
    finally:
        db.close()


if __name__ == "__main__":
    main()
