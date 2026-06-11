"""Simple role-based access check for search results."""
from __future__ import annotations
def can_access_chunk(chunk_metadata: dict, user_role: str) -> bool:
    allowed = chunk_metadata.get("allowed_roles", [])
    return user_role in allowed or "admin" == user_role


def filter_results_by_role(results: list[dict], user_role: str) -> list[dict]:
    return [r for r in results if can_access_chunk(r.get("metadata", {}), user_role)]
