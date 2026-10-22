"""Domain constants for the user profile feature.

Mirrors the enums and per-visa-type phase options from .kiro/specs/profile/design.md
and requirements REQ-2. Kept in one place so the API, validation, and frontend options
agree.
"""

# Visa types (underscore form per design.md data model).
VISA_TYPES = ["F-1", "OPT", "STEM_OPT", "H-1B", "H-4", "J-1", "Other"]

# Allowed status phases per visa type (REQ-2).
STATUS_PHASES: dict[str, list[str]] = {
    "F-1": [
        "coursework",
        "pre-completion OPT",
        "post-completion OPT",
        "STEM OPT extension",
        "grace period",
    ],
    "OPT": ["active", "grace period"],
    "STEM_OPT": ["active", "grace period"],
    "H-1B": ["pending", "approved", "cap-exempt", "transfer in progress"],
    "H-4": ["active", "grace period"],
    "J-1": ["active", "grace period"],
    "Other": ["active", "grace period"],
}

STEM_OPT_STATUSES = ["not_started", "applied", "pending", "approved"]
PETITION_STATUSES = ["pending", "approved", "cap_exempt"]

# Caps for the unemployment-day counter (REQ-3).
OPT_UNEMPLOYMENT_CAP = 90
STEM_OPT_UNEMPLOYMENT_CAP = 150

# Sensitive fields that must be encrypted at rest (steering/profile.md).
SENSITIVE_FIELDS = ["employerEVerify", "employerEIN", "petitionReceiptNumber"]


def valid_phase(visa_type: str, phase: str) -> bool:
    """True if ``phase`` is allowed for ``visa_type``."""
    return phase in STATUS_PHASES.get(visa_type, [])
