"""Explicit source ancestry for development diversity, never a morphology label."""
from __future__ import annotations

import json
import re
from pathlib import Path


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _completed(home: Path) -> bool:
    try:
        receipt = _read(home / "complete.json")
        return receipt.get("status") == "complete" and receipt.get("round") == home.name.removeprefix("cycle-")
    except (OSError, ValueError, AttributeError):
        return False


def champion_parents(ws: Path) -> dict[str, str]:
    """Recorded child -> parent links from completed cycles only."""
    found: dict[str, str] = {}
    for home in sorted((ws / "runs").glob("cycle-*")):
        if not _completed(home):
            continue
        round_name = home.name.removeprefix("cycle-")
        completion = _read(home / "complete.json")
        source = (completion.get("feedback") or {}).get("source")
        paths = ([Path(source)] if source else
                 [ws / "runs" / f"develop-{round_name}-{suffix}" / "champion.json"
                  for suffix in ("book-exact", "authored")])
        for path in paths:
            if not path.resolve().is_relative_to((ws / "runs").resolve()):
                continue
            try:
                record = _read(path)
            except (OSError, ValueError):
                continue
            parent = record.get("parent")
            if not isinstance(parent, str) or not parent:
                continue
            names = [record.get("champion")] + [c.get("name") for c in record.get("children", [])]
            for name in names:
                if isinstance(name, str) and name and name != parent:
                    if name in found and found[name] != parent:
                        raise ValueError(f"conflicting development ancestry for {name}")
                    found[name] = parent
    return found


def _book_source(name: str, ws: Path) -> str:
    """Use only the name's originating run, never the merged carried registry.

    Portfolio source hashes identify the authored AST across restagings. If
    legacy evidence cannot resolve that source exactly, preserve the full name
    as unknown ancestry rather than inventing kinship from a family caption.
    """
    parts = name.split(":")
    if len(parts) != 4:
        return name
    _, run, family, candidate_id = parts
    try:
        registry = _read(ws / "runs" / "books" / f"{run}.json")
        entry = registry["entries"][name]
        if entry.get("trace") != name.removeprefix("book:"):
            return name
        directory = Path(registry["book_dir"])
        if not directory.is_absolute():
            directory = ws.parent.parent / directory
        portfolio = _read(directory / "maas-creative-portfolio.json")
        if portfolio.get("run_id") != run:
            return name
        matches = [c for c in portfolio.get("candidates", [])
                   if c.get("candidate_id") == candidate_id and c.get("family") == family]
        if len(matches) != 1:
            return name
        source = matches[0].get("source_program_hash")
        if isinstance(source, str) and re.fullmatch(r"[0-9a-f]{64}", source):
            return f"book-source:{source}"
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return name


def lineage_of(name: str, ws: Path, parents: dict[str, str] | None = None) -> str:
    parents = champion_parents(ws) if parents is None else parents
    seen: set[str] = set()
    current = name
    while current in parents and current not in seen:
        seen.add(current)
        current = parents[current]
    if current.startswith("book:"):
        return _book_source(current, ws)
    scheme = current.split("~")[0].split("^")[0]
    return re.sub(r"__d\d+_.*$", "", scheme)


def recent_lineages(ws: Path, current_round: str, *, window: int = 3) -> list[str]:
    """Completed preceding cycles only; numeric rounds must precede this one.

    For nonnumeric round names the completion receipt timestamp orders history,
    bounded by the current cycle directory creation time when it exists.
    """
    if window < 1:
        return []
    parents = champion_parents(ws)
    current = ws / "runs" / f"cycle-{current_round}"
    current_number = re.fullmatch(r"(.*?)(\d+)", current_round)
    cutoff = current.stat().st_ctime_ns if current.exists() else None
    rounds = []
    for directory in (ws / "runs").glob("cycle-*"):
        if directory == current or not _completed(directory):
            continue
        previous = re.fullmatch(r"(.*?)(\d+)", directory.name.removeprefix("cycle-"))
        if current_number and previous and current_number[1] == previous[1]:
            if int(previous[2]) >= int(current_number[2]):
                continue
        if cutoff is not None and (directory / "complete.json").stat().st_mtime_ns > cutoff:
            continue
        try:
            row = _read(directory / "development-parent.json")
        except (OSError, ValueError):
            continue
        name = row.get("name") if isinstance(row, dict) else None
        if isinstance(name, str) and name:
            rounds.append(((directory / "complete.json").stat().st_mtime_ns, name))
    rounds.sort()
    return sorted({lineage_of(name, ws, parents) for _key, name in rounds[-window:]})
