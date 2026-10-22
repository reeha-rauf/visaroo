"""Build the non-identifying personalization context sent to the LLM.

Enforces the steering rule (.kiro/steering/profile.md): NEVER include raw dates,
employer names, case numbers, or any sensitive field in a prompt. Only derived counts,
booleans, and status enums are allowed. Fields whose personalization toggle is off are
omitted entirely.

The output is a small dict of derived facts plus a ready-to-embed text block.
"""
from __future__ import annotations

from datetime import date

from .models import Profile
from .profile_domain import OPT_UNEMPLOYMENT_CAP, STEM_OPT_UNEMPLOYMENT_CAP


def _days_until(iso: str | None, today: date | None = None) -> int | None:
    if not iso:
        return None
    try:
        target = date.fromisoformat(iso)
    except ValueError:
        return None
    today = today or date.today()
    return (target - today).days


def build_personalization_context(
    profile: Profile, today: date | None = None
) -> dict:
    """Return a dict of derived, non-identifying facts honoring the user's toggles.

    Only counts/booleans/enums are included — never raw dates or sensitive fields.
    """
    toggles = _toggles(profile)
    ctx: dict = {"fieldsEnabled": [k for k, v in toggles.items() if v]}

    # Visa status (always safe: type + phase enums)
    if toggles.get("visaStatus", True):
        ctx["visaType"] = profile.visa_type
        ctx["statusPhase"] = profile.status_phase
        if profile.stem_opt_status:
            ctx["stemOptExtensionStatus"] = profile.stem_opt_status
        if profile.h1b_transfer_in_progress is not None:
            ctx["h1bTransferInProgress"] = bool(profile.h1b_transfer_in_progress)

    # Key dates -> derived day counts only (never the raw dates)
    if toggles.get("keyDates", True):
        d_ead = _days_until(profile.ead_end_date, today)
        if d_ead is not None:
            ctx["daysUntilEadExpiry"] = d_ead
        d_prog = _days_until(profile.program_end_date, today)
        if d_prog is not None:
            ctx["daysUntilProgramEnd"] = d_prog
        if profile.unemployment_days_used is not None and profile.visa_type in (
            "OPT",
            "STEM_OPT",
        ):
            cap = (
                STEM_OPT_UNEMPLOYMENT_CAP
                if profile.visa_type == "STEM_OPT"
                else OPT_UNEMPLOYMENT_CAP
            )
            ctx["unemploymentDaysUsed"] = profile.unemployment_days_used
            ctx["unemploymentDaysRemaining"] = max(
                cap - profile.unemployment_days_used, 0
            )

    # Travel -> boolean only (never destinations/dates)
    if toggles.get("travel", False):
        has_travel = bool(_parse_json_list(profile.upcoming_travel))
        ctx["upcomingTravel"] = has_travel

    return ctx


def context_to_prompt_block(ctx: dict) -> str:
    """Render the context dict as a short fact block for a system prompt."""
    lines = ["User context (derived, non-identifying):"]
    label_map = {
        "visaType": "Visa type",
        "statusPhase": "Status phase",
        "daysUntilEadExpiry": "Days until EAD expiry",
        "daysUntilProgramEnd": "Days until program end",
        "unemploymentDaysUsed": "Unemployment days used",
        "unemploymentDaysRemaining": "Unemployment days remaining",
        "stemOptExtensionStatus": "STEM OPT extension status",
        "h1bTransferInProgress": "H-1B transfer in progress",
        "upcomingTravel": "Has upcoming travel",
    }
    for key, label in label_map.items():
        if key in ctx:
            lines.append(f"- {label}: {ctx[key]}")
    if len(lines) == 1:
        return ""  # nothing enabled / available
    return "\n".join(lines)


def _toggles(profile: Profile) -> dict:
    import json

    default = {"visaStatus": True, "keyDates": True, "travel": False, "employer": False}
    if not profile.ai_personalization_fields:
        return default
    try:
        stored = json.loads(profile.ai_personalization_fields)
        default.update({k: bool(v) for k, v in stored.items() if k in default})
    except (ValueError, TypeError):
        pass
    return default


def _parse_json_list(raw: str | None) -> list:
    import json

    if not raw:
        return []
    try:
        value = json.loads(raw)
        return value if isinstance(value, list) else []
    except (ValueError, TypeError):
        return []
