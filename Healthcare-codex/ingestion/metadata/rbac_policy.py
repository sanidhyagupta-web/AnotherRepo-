"""Map document types / departments to allowed roles."""
from __future__ import annotations
_DEPARTMENT_ROLES: dict[str, list[str]] = {
    "cardiology": ["doctor", "nurse", "admin"],
    "radiology": ["doctor", "radiologist", "admin"],
    "oncology": ["doctor", "nurse", "admin", "oncologist"],
    "general": ["doctor", "nurse", "admin"],
    "billing": ["billing", "admin"],
    "default": ["doctor", "nurse", "admin"],
}


def get_allowed_roles(department: str) -> list[str]:
    return _DEPARTMENT_ROLES.get(department.lower(), _DEPARTMENT_ROLES["default"])
