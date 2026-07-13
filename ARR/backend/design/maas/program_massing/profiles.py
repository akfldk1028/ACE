"""Data-backed building-program massing profiles."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


PROFILE_PATH = Path(__file__).resolve().parent / "data" / "program_profiles.v1.json"


@lru_cache(maxsize=1)
def load_program_profiles() -> tuple[dict[str, Any], ...]:
    data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    if data.get("schema_version") != "arr.maas.program_profiles.v1":
        raise ValueError("unsupported program massing profile schema")
    profiles = data.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        raise ValueError("program massing profiles are empty")
    ids = [str(item.get("id") or "") for item in profiles]
    if len(ids) != len(set(ids)) or any(not item for item in ids):
        raise ValueError("program massing profile ids must be unique and non-empty")
    return tuple(dict(item) for item in profiles)


def resolve_program_profile(building_type: str) -> dict[str, Any]:
    text = str(building_type or "").strip().lower()
    for profile in load_program_profiles():
        if any(str(alias).lower() in text for alias in profile.get("aliases") or []):
            return profile
    return {
        "id": "generic",
        "aliases": [],
        "design_intent": "clear dominant public mass with restrained supporting volumes",
        "target_volume_range": [1, 4],
        "target_floor_range": [1, 40],
        "preferred_families": [],
        "sequences": [],
    }


__all__ = ["PROFILE_PATH", "load_program_profiles", "resolve_program_profile"]
