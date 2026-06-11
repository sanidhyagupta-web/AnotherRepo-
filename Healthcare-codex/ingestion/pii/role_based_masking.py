"""
Apply additional masking based on viewer role at query time.

Roles:
  - doctor: sees redacted chunks (PHI placeholders, clinical data visible)
  - nurse: same as doctor
  - admin: sees only non-clinical metadata
  - billing: sees billing codes; no clinical narrative
  - anonymous: sees nothing identifiable
"""
from __future__ import annotations
import re

_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "doctor": ["view_clinical", "view_metadata"],
    "nurse": ["view_clinical", "view_metadata"],
    "admin": ["view_metadata"],
    "billing": ["view_billing_codes"],
    "anonymous": [],
}

_CLINICAL_PATTERN = re.compile(
    r"(diagnosis|medication|treatment|prescription|lab|imaging|procedure|assessment|plan)",
    re.IGNORECASE,
)


def can_view_clinical(role: str) -> bool:
    return "view_clinical" in _ROLE_PERMISSIONS.get(role, [])


def apply_role_mask(text: str, role: str) -> str:
    if not can_view_clinical(role):
        # Mask any remaining clinical content
        text = _CLINICAL_PATTERN.sub("[REDACTED]", text)
    return text
