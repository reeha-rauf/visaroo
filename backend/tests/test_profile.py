"""Profile feature tests. Run hermetically with AI_PROVIDER=local, CRYPTO_PROVIDER=local."""
import json
from datetime import date, timedelta

from app.computed_dates import compute_dates
from app.crypto.provider import get_crypto
from app.models import Profile
from app.personalization import (
    build_personalization_context,
    context_to_prompt_block,
)
from tests.conftest import auth_headers


def _min_profile(**over):
    """A minimal valid PUT body (REQ-NF-3: visa type + phase + one date is enough)."""
    body = {
        "fullName": "Maya",
        "visaType": "STEM_OPT",
        "statusPhase": "active",
        "eadEndDate": "2027-05-01",
    }
    body.update(over)
    return body


# ------------------------------- CRUD -------------------------------

def test_get_profile_404_when_absent(client):
    headers = auth_headers(client)
    assert client.get("/profile", headers=headers).status_code == 404


def test_put_then_get_profile(client):
    headers = auth_headers(client)
    r = client.put("/profile", headers=headers, json=_min_profile())
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["visaType"] == "STEM_OPT"
    assert data["email"]  # pulled from the user
    # GET returns the same
    g = client.get("/profile", headers=headers).json()
    assert g["visaType"] == "STEM_OPT"
    assert g["eadEndDate"] == "2027-05-01"


def test_profile_requires_auth(client):
    assert client.get("/profile").status_code == 401
    assert client.put("/profile", json=_min_profile()).status_code == 401


def test_delete_profile(client):
    headers = auth_headers(client)
    client.put("/profile", headers=headers, json=_min_profile())
    assert client.delete("/profile", headers=headers).status_code == 204
    assert client.get("/profile", headers=headers).status_code == 404


def test_export_returns_json_download(client):
    headers = auth_headers(client)
    client.put("/profile", headers=headers, json=_min_profile())
    r = client.get("/profile/export", headers=headers)
    assert r.status_code == 200
    assert "attachment" in r.headers.get("content-disposition", "")
    assert r.json()["visaType"] == "STEM_OPT"


# ----------------------------- Validation ---------------------------

def test_invalid_visa_type_rejected(client):
    headers = auth_headers(client)
    r = client.put("/profile", headers=headers, json=_min_profile(visaType="K-1"))
    assert r.status_code == 422


def test_phase_must_match_visa_type(client):
    headers = auth_headers(client)
    # "pending" is an H-1B phase, not valid for STEM_OPT
    r = client.put(
        "/profile", headers=headers, json=_min_profile(statusPhase="pending")
    )
    assert r.status_code == 400
    assert "statusPhase" in r.json()["detail"]


def test_unemployment_out_of_range_rejected(client):
    headers = auth_headers(client)
    r = client.put(
        "/profile", headers=headers, json=_min_profile(unemploymentDaysUsed=200)
    )
    assert r.status_code == 422


def test_bad_iso_date_rejected(client):
    headers = auth_headers(client)
    r = client.put(
        "/profile", headers=headers, json=_min_profile(eadEndDate="2027-13-40")
    )
    assert r.status_code == 422


# ---------------------- Encryption at rest --------------------------

def test_sensitive_fields_encrypted_at_rest(client, db_session):
    headers = auth_headers(client)
    client.put(
        "/profile",
        headers=headers,
        json=_min_profile(employerEVerify="E-VERIFY-12345", employerEIN="12-3456789"),
    )
    # Read the raw stored row: sensitive values must NOT be plaintext.
    profile = db_session.query(Profile).first()
    assert profile.employer_everify is not None
    assert "E-VERIFY-12345" not in profile.employer_everify
    assert profile.employer_ein is not None
    assert "12-3456789" not in profile.employer_ein
    # But GET decrypts for the owner.
    g = client.get("/profile", headers=headers).json()
    assert g["employerEVerify"] == "E-VERIFY-12345"
    assert g["employerEIN"] == "12-3456789"


def test_crypto_round_trip():
    crypto = get_crypto()
    token = crypto.encrypt("secret-value")
    assert token != "secret-value"
    assert crypto.decrypt(token) == "secret-value"


# ---------------------- Computed dates ------------------------------

def test_computed_opt_window_and_grace_f1():
    c = compute_dates(
        visa_type="F-1",
        program_end_date="2026-05-15",
        ead_end_date=None,
        i94_expiry_date=None,
        grace_period_end_date=None,
        unemployment_days_used=None,
    )
    assert c.optApplicationWindowOpens == "2026-02-14"  # -90
    assert c.optApplicationDeadline == "2026-03-16"      # -60
    assert c.gracePeriodEnd == "2026-07-14"              # +60


def test_computed_stem_filing_window_and_remaining():
    c = compute_dates(
        visa_type="STEM_OPT",
        program_end_date=None,
        ead_end_date="2027-05-01",
        i94_expiry_date=None,
        grace_period_end_date=None,
        unemployment_days_used=40,
    )
    assert c.stemFilingWindowStart == "2027-01-31"  # -90
    assert c.stemFilingWindowEnd == "2027-03-02"    # -60
    assert c.unemploymentCap == 150
    assert c.unemploymentDaysRemaining == 110


def test_computed_handles_missing_sources():
    c = compute_dates(
        visa_type="H-4",
        program_end_date=None,
        ead_end_date=None,
        i94_expiry_date=None,
        grace_period_end_date=None,
        unemployment_days_used=None,
    )
    assert c.optApplicationWindowOpens is None
    assert c.unemploymentDaysRemaining is None


def test_computed_days_remaining_clamped_at_cap():
    c = compute_dates(
        visa_type="OPT",
        program_end_date=None,
        ead_end_date=None,
        i94_expiry_date=None,
        grace_period_end_date=None,
        unemployment_days_used=90,
    )
    assert c.unemploymentCap == 90
    assert c.unemploymentDaysRemaining == 0


def test_grace_period_override_wins():
    c = compute_dates(
        visa_type="F-1",
        program_end_date="2026-05-15",
        ead_end_date=None,
        i94_expiry_date=None,
        grace_period_end_date="2026-08-01",  # user override
        unemployment_days_used=None,
    )
    assert c.gracePeriodEnd == "2026-08-01"


# ------------------- Personalization safety -------------------------

def _profile_obj(**over) -> Profile:
    p = Profile(user_id=1, visa_type="STEM_OPT", status_phase="active")
    for k, v in over.items():
        setattr(p, k, v)
    return p


def test_personalization_has_no_raw_dates_or_sensitive():
    future = (date.today() + timedelta(days=100)).isoformat()
    p = _profile_obj(
        ead_end_date=future,
        employer_name="Acme Corp",
        employer_everify="local:ciphertext",
        unemployment_days_used=40,
        ai_personalization_fields=json.dumps(
            {"visaStatus": True, "keyDates": True, "travel": True, "employer": True}
        ),
        upcoming_travel=json.dumps([{"destination": "India", "departureDate": future}]),
    )
    ctx = build_personalization_context(p)
    serialized = json.dumps(ctx)
    # No raw dates
    assert future not in serialized
    # No employer name / destination / ciphertext
    assert "Acme" not in serialized
    assert "India" not in serialized
    assert "ciphertext" not in serialized
    # Derived facts present
    assert ctx["daysUntilEadExpiry"] == 100
    assert ctx["unemploymentDaysRemaining"] == 110
    assert ctx["upcomingTravel"] is True


def test_personalization_respects_toggles_off():
    future = (date.today() + timedelta(days=50)).isoformat()
    p = _profile_obj(
        ead_end_date=future,
        unemployment_days_used=10,
        upcoming_travel=json.dumps([{"destination": "X", "departureDate": future}]),
        ai_personalization_fields=json.dumps(
            {"visaStatus": True, "keyDates": False, "travel": False, "employer": False}
        ),
    )
    ctx = build_personalization_context(p)
    # keyDates off -> no day counts
    assert "daysUntilEadExpiry" not in ctx
    assert "unemploymentDaysRemaining" not in ctx
    # travel off -> no travel flag
    assert "upcomingTravel" not in ctx
    # visaStatus on -> type/phase present
    assert ctx["visaType"] == "STEM_OPT"


def test_prompt_block_is_empty_when_nothing_enabled():
    p = _profile_obj(
        ai_personalization_fields=json.dumps(
            {"visaStatus": False, "keyDates": False, "travel": False, "employer": False}
        )
    )
    ctx = build_personalization_context(p)
    assert context_to_prompt_block(ctx) == ""
