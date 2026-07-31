"""Card access for the flight specialist worker module."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CARD_PATH = Path(__file__).resolve().parents[2] / "cards" / "flight_specialist_card.json"


def load_card() -> dict[str, Any]:
    return json.loads(CARD_PATH.read_text(encoding="utf-8"))


__all__ = ["CARD_PATH", "load_card"]
