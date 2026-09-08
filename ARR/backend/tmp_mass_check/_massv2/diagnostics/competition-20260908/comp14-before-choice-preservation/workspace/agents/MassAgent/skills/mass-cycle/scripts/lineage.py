"""What a board seat descends from, so development does not keep returning to one figure.

Six cycles in a row developed the same curved figure: comp06, comp08 and
comp09 each took `morph-curved-low:creative-001` as the parent, comp10 took
that lineage's own champion, and the carried champions sat in the top three
of every board from comp06 on. The selection rule was "highest score", the
board re-seated the champions each round, and the author re-proposed the
same figure, so the loop closed by itself. A prompt asked the external
selector to consider "organizations not developed recently"; nothing checked.

A lineage is the figure a name descends from:
- a BOOK figure `book:<run>:<figure>:creative-NNN` is its figure;
- a development champion is its parent's lineage, read from the champion
  receipt of the round that developed it;
- an authored scheme is its scheme name without the variant suffixes, and a
  development child (`__dNN_…`) is its parent scheme.
"""
from __future__ import annotations

import json
import re
from pathlib import Path


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def champion_parents(ws: Path) -> dict[str, str]:
    """champion name -> parent name, over every development receipt in the workspace."""

    found: dict[str, str] = {}
    for path in sorted((ws / "runs").glob("develop-*/champion.json")):
        try:
            record = _read(path)
        except (OSError, ValueError):
            continue
        champion = record.get("champion")
        parent = record.get("parent")
        if isinstance(champion, str) and isinstance(parent, str) and champion and parent:
            found[champion] = parent
    return found


def lineage_of(name: str, ws: Path, parents: dict[str, str] | None = None) -> str:
    parents = champion_parents(ws) if parents is None else parents
    seen: set[str] = set()
    current = name
    while current in parents and current not in seen:
        seen.add(current)
        current = parents[current]
    if current.startswith("book:"):
        parts = current.split(":")
        # book:<run>:<figure>:creative-NNN - the figure is the lineage. A
        # champion whose receipt is missing keeps its own development label.
        return parts[2] if len(parts) >= 4 else current
    scheme = current.split("~")[0].split("^")[0]
    return re.sub(r"__d\d+_.*$", "", scheme)


def _cycle_order_key(directory: Path) -> tuple[int, str]:
    match = re.search(r"(\d+)$", directory.name)
    return (int(match.group(1)) if match else -1, directory.name)


def recent_lineages(ws: Path, current_round: str, *, window: int = 3) -> list[str]:
    """Lineages developed in the last `window` completed cycles before this one."""

    parents = champion_parents(ws)
    rounds = []
    for directory in (ws / "runs").glob("cycle-*"):
        if directory.name == f"cycle-{current_round}":
            continue
        selected = directory / "development-parent.json"
        if not selected.is_file():
            continue
        try:
            row = _read(selected)
        except (OSError, ValueError):
            continue
        name = row.get("name") if isinstance(row, dict) else None
        if isinstance(name, str) and name:
            rounds.append((_cycle_order_key(directory), name))
    rounds.sort()
    recent = [lineage_of(name, ws, parents) for _key, name in rounds[-window:]]
    return sorted(set(recent))
