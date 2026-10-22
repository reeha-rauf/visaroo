"""Pydantic schemas for the user profile (validation per REQ-NF-2).

Mirrors the design.md data model. Dates are validated as real ISO-8601 calendar dates.
Enums are constrained to the domain lists. Sensitive fields appear here in plaintext
only in transit with the authenticated owner — they are encrypted before storage.
"""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .profile_domain import (
    OPT_UNEMPLOYMENT_CAP,
    PETITION_STATUSES,
    STATUS_PHASES,
    STEM_OPT_STATUSES,
    STEM_OPT_UNEMPLOYMENT_CAP,
    VISA_TYPES,
    valid_phase,
)

# Max cap used to bound the unemployment counter (REQ-NF-2: reject outside 0–150).
_MAX_UNEMPLOYMENT = STEM_OPT_UNEMPLOYMENT_CAP


def _validate_iso_date(value: str | None) -> str | None:
    """Ensure a value is a real ISO-8601 calendar date (YYYY-MM-DD) or None."""
    if value is None or value == "":
        return None
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"must be a valid ISO-8601 date (YYYY-MM-DD): {value}") from exc
    return value


class TravelEntry(BaseModel):
    destination: str = Field(min_length=1, max_length=120)
    departureDate: str
    returnDate: str | None = None

    @field_validator("departureDate", "returnDate")
    @classmethod
    def _dates(cls, v: str | None) -> str | None:
        return _validate_iso_date(v)


class NotificationAlerts(BaseModel):
    deadlineApproaching: bool = True
    newRuleAffectingStatus: bool = True
    newCreatorPost: bool = False
    newWebinar: bool = False


class NotificationPreferences(BaseModel):
    emailEnabled: bool = True
    alerts: NotificationAlerts = Field(default_factory=NotificationAlerts)
    deadlineLeadTimeDays: list[int] = Field(default_factory=lambda: [90, 30, 7])

    @field_validator("deadlineLeadTimeDays")
    @classmethod
    def _lead_times(cls, v: list[int]) -> list[int]:
        allowed = {90, 60, 30, 14, 7}
        bad = [d for d in v if d not in allowed]
        if bad:
            raise ValueError(f"lead times must be among {sorted(allowed)}; got {bad}")
        return v


class PersonalizationToggles(BaseModel):
    visaStatus: bool = True
    keyDates: bool = True
    travel: bool = False
    employer: bool = False


# ISO date field names, validated uniformly.
_DATE_FIELDS = [
    "programStartDate", "programEndDate", "i20ExpiryDate", "portOfEntryDate",
    "visaStampExpiry", "eadStartDate", "eadEndDate", "nextSevpReportingDate",
    "nextRenewalReminder", "gracePeriodEndDate", "i94ExpiryDate", "lastUsEntryDate",
    "h1bPetitionExpiry", "capGapEnd", "passportExpiry",
    "lastReportableEventDate", "lastSevpReportedDate",
]


class ProfileBase(BaseModel):
    """Shared profile fields (camelCase to match the design.md TypeScript model)."""

    model_config = ConfigDict(extra="forbid")

    # Identity
    fullName: str = Field(default="", max_length=200)
    countryOfOrigin: str | None = None
    universityOrEmployer: str | None = None
    fieldOrTitle: str | None = None

    # Visa status
    visaType: str = "Other"
    statusPhase: str = "active"

    # Key dates
    programStartDate: str | None = None
    programEndDate: str | None = None
    i20ExpiryDate: str | None = None
    portOfEntryDate: str | None = None
    visaStampExpiry: str | None = None
    eadStartDate: str | None = None
    eadEndDate: str | None = None
    nextSevpReportingDate: str | None = None
    nextRenewalReminder: str | None = None
    gracePeriodEndDate: str | None = None

    # OPT / STEM OPT
    employerName: str | None = None
    employerEVerify: str | None = None  # sensitive — encrypted at rest
    stemOptStatus: str | None = None
    i983OnFile: bool | None = None
    unemploymentDaysUsed: int | None = None

    # H-1B
    petitionReceiptNumber: str | None = None  # sensitive — encrypted at rest
    petitionStatus: str | None = None
    i94ExpiryDate: str | None = None
    employerEIN: str | None = None  # sensitive — encrypted at rest
    h1bTransferInProgress: bool | None = None
    h1bPetitionExpiry: str | None = None
    capGapEnd: str | None = None

    # Deadline tracker extras
    passportExpiry: str | None = None
    lastReportableEventDate: str | None = None
    lastSevpReportedDate: str | None = None
    deadlineOverrides: dict[str, str] | None = None

    # Travel
    lastUsEntryDate: str | None = None
    upcomingTravel: list[TravelEntry] | None = None
    recentCountriesVisited: list[str] | None = None
    advanceParoleFiled: bool | None = None

    # DSO / attorney
    dsoName: str | None = None
    dsoEmail: EmailStr | None = None
    attorneyName: str | None = None
    attorneyEmail: EmailStr | None = None

    # Notifications + privacy
    notifications: NotificationPreferences = Field(default_factory=NotificationPreferences)
    aiPersonalizationFields: PersonalizationToggles = Field(
        default_factory=PersonalizationToggles
    )

    @field_validator(*_DATE_FIELDS)
    @classmethod
    def _iso_dates(cls, v: str | None) -> str | None:
        return _validate_iso_date(v)

    @field_validator("visaType")
    @classmethod
    def _visa_type(cls, v: str) -> str:
        if v not in VISA_TYPES:
            raise ValueError(f"visaType must be one of {VISA_TYPES}")
        return v

    @field_validator("stemOptStatus")
    @classmethod
    def _stem_status(cls, v: str | None) -> str | None:
        if v is not None and v not in STEM_OPT_STATUSES:
            raise ValueError(f"stemOptStatus must be one of {STEM_OPT_STATUSES}")
        return v

    @field_validator("petitionStatus")
    @classmethod
    def _petition_status(cls, v: str | None) -> str | None:
        if v is not None and v not in PETITION_STATUSES:
            raise ValueError(f"petitionStatus must be one of {PETITION_STATUSES}")
        return v

    @field_validator("unemploymentDaysUsed")
    @classmethod
    def _unemployment(cls, v: int | None) -> int | None:
        if v is not None and not (0 <= v <= _MAX_UNEMPLOYMENT):
            raise ValueError(f"unemploymentDaysUsed must be between 0 and {_MAX_UNEMPLOYMENT}")
        return v


class ProfileUpsert(ProfileBase):
    """Body for PUT /profile. Validates the phase against the chosen visa type."""

    def validate_phase(self) -> None:
        if self.statusPhase and not valid_phase(self.visaType, self.statusPhase):
            allowed = STATUS_PHASES.get(self.visaType, [])
            raise ValueError(
                f"statusPhase '{self.statusPhase}' is not valid for {self.visaType}; "
                f"allowed: {allowed}"
            )


class ComputedDates(BaseModel):
    """Server-computed deadline estimates (labelled as computed in the UI)."""

    optApplicationWindowOpens: str | None = None
    optApplicationDeadline: str | None = None
    stemFilingWindowStart: str | None = None
    stemFilingWindowEnd: str | None = None
    gracePeriodEnd: str | None = None
    unemploymentDaysRemaining: int | None = None
    unemploymentCap: int | None = None


class ProfileOut(ProfileBase):
    """Response for GET/PUT. Includes metadata and computed estimates."""

    email: EmailStr
    computed: ComputedDates
    createdAt: datetime
    updatedAt: datetime
