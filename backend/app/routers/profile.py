"""User profile routes: GET / PUT / DELETE /profile, plus JSON export.

Maps between the camelCase API schema and the snake_case ORM model. Sensitive fields
(employerEVerify, employerEIN, petitionReceiptNumber) are encrypted at rest via the
crypto provider (AWS KMS in production, Fernet locally) and decrypted only when
returning to the authenticated owner.
"""
import json

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from ..computed_dates import compute_dates
from ..crypto.provider import get_crypto
from ..database import get_db
from ..deps import get_current_user
from ..models import Profile, User
from ..profile_schemas import ProfileOut, ProfileUpsert

router = APIRouter(prefix="/profile", tags=["profile"])

# API camelCase field -> ORM snake_case column, for straightforward scalar fields.
_SCALAR_MAP = {
    "fullName": "full_name",
    "countryOfOrigin": "country_of_origin",
    "universityOrEmployer": "university_or_employer",
    "fieldOrTitle": "field_or_title",
    "visaType": "visa_type",
    "statusPhase": "status_phase",
    "programStartDate": "program_start_date",
    "programEndDate": "program_end_date",
    "i20ExpiryDate": "i20_expiry_date",
    "portOfEntryDate": "port_of_entry_date",
    "visaStampExpiry": "visa_stamp_expiry",
    "eadStartDate": "ead_start_date",
    "eadEndDate": "ead_end_date",
    "nextSevpReportingDate": "next_sevp_reporting_date",
    "nextRenewalReminder": "next_renewal_reminder",
    "gracePeriodEndDate": "grace_period_end_date",
    "employerName": "employer_name",
    "stemOptStatus": "stem_opt_status",
    "i983OnFile": "i983_on_file",
    "unemploymentDaysUsed": "unemployment_days_used",
    "petitionStatus": "petition_status",
    "i94ExpiryDate": "i94_expiry_date",
    "h1bTransferInProgress": "h1b_transfer_in_progress",
    "h1bPetitionExpiry": "h1b_petition_expiry",
    "capGapEnd": "cap_gap_end",
    "passportExpiry": "passport_expiry",
    "lastReportableEventDate": "last_reportable_event_date",
    "lastSevpReportedDate": "last_sevp_reported_date",
    "lastUsEntryDate": "last_us_entry_date",
    "advanceParoleFiled": "advance_parole_filed",
    "dsoName": "dso_name",
    "dsoEmail": "dso_email",
    "attorneyName": "attorney_name",
    "attorneyEmail": "attorney_email",
}

# Sensitive fields: API camelCase -> ORM column (encrypted at rest).
_SENSITIVE_MAP = {
    "employerEVerify": "employer_everify",
    "employerEIN": "employer_ein",
    "petitionReceiptNumber": "petition_receipt_number",
}


def _apply_to_model(profile: Profile, payload: ProfileUpsert) -> None:
    """Write validated payload onto the ORM model, encrypting sensitive fields."""
    crypto = get_crypto()
    data = payload.model_dump()

    for api_key, col in _SCALAR_MAP.items():
        setattr(profile, col, data.get(api_key))

    for api_key, col in _SENSITIVE_MAP.items():
        value = data.get(api_key)
        setattr(profile, col, crypto.encrypt(value) if value else None)

    # JSON-encoded structures
    profile.upcoming_travel = (
        json.dumps(data["upcomingTravel"]) if data.get("upcomingTravel") else None
    )
    profile.recent_countries_visited = (
        json.dumps(data["recentCountriesVisited"])
        if data.get("recentCountriesVisited")
        else None
    )
    profile.notifications = json.dumps(data["notifications"])
    profile.ai_personalization_fields = json.dumps(data["aiPersonalizationFields"])
    profile.deadline_overrides = (
        json.dumps(data["deadlineOverrides"]) if data.get("deadlineOverrides") else None
    )


def _to_out(profile: Profile, user: User) -> ProfileOut:
    """Build the API response, decrypting sensitive fields for the owner."""
    crypto = get_crypto()
    out: dict = {"email": user.email}

    for api_key, col in _SCALAR_MAP.items():
        out[api_key] = getattr(profile, col)

    for api_key, col in _SENSITIVE_MAP.items():
        raw = getattr(profile, col)
        out[api_key] = crypto.decrypt(raw) if raw else None

    out["upcomingTravel"] = json.loads(profile.upcoming_travel) if profile.upcoming_travel else None
    out["recentCountriesVisited"] = (
        json.loads(profile.recent_countries_visited)
        if profile.recent_countries_visited
        else None
    )
    out["notifications"] = (
        json.loads(profile.notifications) if profile.notifications else {}
    )
    out["aiPersonalizationFields"] = (
        json.loads(profile.ai_personalization_fields)
        if profile.ai_personalization_fields
        else {}
    )
    out["deadlineOverrides"] = (
        json.loads(profile.deadline_overrides) if profile.deadline_overrides else None
    )

    out["computed"] = compute_dates(
        visa_type=profile.visa_type,
        program_end_date=profile.program_end_date,
        ead_end_date=profile.ead_end_date,
        i94_expiry_date=profile.i94_expiry_date,
        grace_period_end_date=profile.grace_period_end_date,
        unemployment_days_used=profile.unemployment_days_used,
    )
    out["createdAt"] = profile.created_at
    out["updatedAt"] = profile.updated_at
    return ProfileOut(**out)


@router.get("", response_model=ProfileOut)
def get_profile(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ProfileOut:
    profile = db.get(Profile, user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return _to_out(profile, user)


@router.put("", response_model=ProfileOut)
def put_profile(
    payload: ProfileUpsert,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileOut:
    # Cross-field validation (phase must match visa type).
    try:
        payload.validate_phase()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    profile = db.get(Profile, user.id)
    if profile is None:
        profile = Profile(user_id=user.id)
        db.add(profile)

    _apply_to_model(profile, payload)
    # Keep the User.visa_category roughly in sync for existing feed/news personalization.
    user.visa_category = _as_category(payload.visaType)

    db.commit()
    db.refresh(profile)
    return _to_out(profile, user)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    """Delete the user's profile record (REQ-9). In production this also queues
    identity (Cognito) deletion; here we remove the stored profile data."""
    profile = db.get(Profile, user.id)
    if profile is not None:
        db.delete(profile)
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/export")
def export_profile(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> JSONResponse:
    """Export all stored profile data as a downloadable JSON file (REQ-9)."""
    profile = db.get(Profile, user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    body = _to_out(profile, user).model_dump(mode="json")
    return JSONResponse(
        content=body,
        headers={"Content-Disposition": "attachment; filename=visaroo-profile.json"},
    )


def _as_category(visa_type: str) -> str:
    """Map the profile visaType (underscore form) to the legacy visa_category used by
    the feed/news personalization (hyphen form)."""
    mapping = {"STEM_OPT": "STEM-OPT"}
    return mapping.get(visa_type, visa_type)
