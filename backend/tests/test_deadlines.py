"""Deadline tracker backend tests: server deadline calc, .ics export, reminders."""
from datetime import date, timedelta

from app.deadline_calc import compute_server_deadlines
from app.models import Profile, ReminderSent
from app.services.reminder_checker import run_reminders
from tests.conftest import auth_headers


def _put_stem_profile(client, headers, **over):
    body = {
        "fullName": "Dee",
        "visaType": "STEM_OPT",
        "statusPhase": "active",
        "eadEndDate": "2027-05-01",
        "notifications": {
            "emailEnabled": True,
            "alerts": {
                "deadlineApproaching": True,
                "newRuleAffectingStatus": True,
                "newCreatorPost": False,
                "newWebinar": False,
            },
            "deadlineLeadTimeDays": [90, 30, 7],
        },
        "aiPersonalizationFields": {
            "visaStatus": True, "keyDates": True, "travel": False, "employer": False,
        },
    }
    body.update(over)
    r = client.put("/profile", headers=headers, json=body)
    assert r.status_code == 200, r.text
    return r.json()


# ----------------------------- server calc --------------------------

def test_server_deadlines_exclude_expired_and_na():
    p = Profile(user_id=1, visa_type="STEM_OPT", status_phase="active")
    p.ead_end_date = (date.today() + timedelta(days=120)).isoformat()
    out = compute_server_deadlines(p, date.today())
    ids = {d.id for d in out}
    # ead_expiry (120d) and stem windows (30d/60d) should appear; none expired
    assert "ead_expiry" in ids
    assert all(d.days_remaining >= 0 for d in out)


def test_server_deadlines_apply_override():
    import json
    p = Profile(user_id=1, visa_type="STEM_OPT", status_phase="active")
    p.ead_end_date = (date.today() + timedelta(days=200)).isoformat()
    override_day = (date.today() + timedelta(days=10)).isoformat()
    p.deadline_overrides = json.dumps({"ead_expiry": override_day})
    out = {d.id: d for d in compute_server_deadlines(p, date.today())}
    assert out["ead_expiry"].date.isoformat() == override_day


# ------------------------------- .ics -------------------------------

def test_ics_download(client):
    headers = auth_headers(client)
    future = (date.today() + timedelta(days=100)).isoformat()
    _put_stem_profile(client, headers, eadEndDate=future)
    r = client.get("/deadlines/ics", headers=headers)
    assert r.status_code == 200
    assert "text/calendar" in r.headers["content-type"]
    text = r.text
    assert "BEGIN:VCALENDAR" in text
    assert "BEGIN:VEVENT" in text
    assert "EAD card expiry" in text


# ---------------------------- reminders -----------------------------

def test_reminder_sends_once_then_dedups(client, db_session):
    headers = auth_headers(client)
    # Put EAD end exactly 30 days out so it hits the 30-day lead time.
    ead = (date.today() + timedelta(days=30)).isoformat()
    _put_stem_profile(client, headers, eadEndDate=ead)

    first = run_reminders(db_session, date.today())
    assert first["sent"] >= 1  # ead_expiry at 30 days triggers

    second = run_reminders(db_session, date.today())
    assert second["sent"] == 0  # dedup: nothing re-sent
    assert second["skipped_already_sent"] >= 1

    # A record exists in the dedup table.
    assert db_session.query(ReminderSent).count() >= 1


def test_reminder_respects_email_disabled(client, db_session):
    headers = auth_headers(client, email="b@test.com", username="bob")
    ead = (date.today() + timedelta(days=30)).isoformat()
    # Save a profile with email alerts turned OFF.
    _put_stem_profile(
        client,
        headers,
        eadEndDate=ead,
        notifications={
            "emailEnabled": False,
            "alerts": {
                "deadlineApproaching": True,
                "newRuleAffectingStatus": True,
                "newCreatorPost": False,
                "newWebinar": False,
            },
            "deadlineLeadTimeDays": [90, 30, 7],
        },
    )
    result = run_reminders(db_session, date.today())
    assert result["sent"] == 0
