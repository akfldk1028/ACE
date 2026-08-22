"""Bind canonical ARR summaries to an unfrozen ICLR 2027 site registry."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from iclr2027.io import write_json_atomic


REGISTRY_SCHEMA = "ace.iclr2027.site_registry.v1"
SUMMARY_SCHEMA = "arr.maas.book_program_portfolios.v1"
PROGRAMS = ("neighborhood", "gymnasium", "cultural")
_PROGRAM_SET = frozenset(PROGRAMS)
_PNU = re.compile(r"^[0-9]{19}$")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument(
        "--summary",
        type=Path,
        action="append",
        required=True,
        help="canonical ARR summary; repeat exactly once per registry site",
    )
    return parser


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be an object")
    return payload


def _valid_pnu(value: Any) -> str:
    if not isinstance(value, str) or not _PNU.fullmatch(value):
        raise ValueError("summary PNU must contain exactly 19 digits")
    return value


def _load_summary(path: Path) -> tuple[str, dict[str, Any]]:
    if not path.is_file():
        raise ValueError("summary must be a file")
    payload = _read_json_object(path, "ARR summary")
    if payload.get("schema_version") != SUMMARY_SCHEMA:
        raise ValueError("unsupported ARR summary schema")
    pnu = _valid_pnu(payload.get("pnu"))
    programs = payload.get("programs")
    if not isinstance(programs, list):
        raise ValueError("ARR summary program slugs must contain exactly three programs")
    slugs = [
        item.get("slug") if isinstance(item, Mapping) else None
        for item in programs
    ]
    if (
        len(slugs) != len(PROGRAMS)
        or len(set(slugs)) != len(PROGRAMS)
        or set(slugs) != _PROGRAM_SET
    ):
        raise ValueError(
            "ARR summary program slugs must be exactly neighborhood, gymnasium, cultural"
        )
    return pnu, payload


def _registry_relative_path(registry_path: Path, summary_path: Path) -> str:
    try:
        relative = os.path.relpath(
            summary_path.resolve(),
            registry_path.parent.resolve(),
        )
    except ValueError as exc:
        raise ValueError("summary cannot be represented as a registry-relative path") from exc
    return relative.replace("\\", "/")


def bind_artifacts(registry_path: Path, summary_paths: Sequence[Path]) -> dict[str, Any]:
    if not registry_path.is_file():
        raise ValueError("site registry must be a file")
    registry = _read_json_object(registry_path, "site registry")
    if registry.get("schema_version") != REGISTRY_SCHEMA:
        raise ValueError("unsupported site registry schema")
    if registry.get("frozen") is True:
        raise ValueError("site registry is frozen")
    sites = registry.get("sites")
    if not isinstance(sites, list):
        raise ValueError("site registry has no sites list")

    sites_by_pnu: dict[str, dict[str, Any]] = {}
    for site in sites:
        if not isinstance(site, dict):
            raise ValueError("site registry entry must be an object")
        pnu = site.get("pnu")
        if not isinstance(pnu, str) or not _PNU.fullmatch(pnu):
            raise ValueError("registry site PNU must contain exactly 19 digits")
        if pnu in sites_by_pnu:
            raise ValueError("duplicate registry site PNU")
        sites_by_pnu[pnu] = site

    summaries_by_pnu: dict[str, Path] = {}
    for summary_path in summary_paths:
        pnu, _ = _load_summary(summary_path)
        if pnu in summaries_by_pnu:
            raise ValueError("duplicate summary PNU")
        summaries_by_pnu[pnu] = summary_path

    extra_count = len(set(summaries_by_pnu) - set(sites_by_pnu))
    if extra_count:
        raise ValueError("summary PNU is not present in registry")
    missing_count = len(set(sites_by_pnu) - set(summaries_by_pnu))
    if missing_count:
        suffix = "site" if missing_count == 1 else "sites"
        raise ValueError(f"missing summaries for {missing_count} registry {suffix}")

    proposals: dict[str, dict[str, str]] = {}
    needs_write = False
    for pnu, site in sites_by_pnu.items():
        relative_path = _registry_relative_path(
            registry_path,
            summaries_by_pnu[pnu],
        )
        proposal = {program: relative_path for program in PROGRAMS}
        proposals[pnu] = proposal
        existing = site.get("artifacts")
        if existing is None:
            existing = {}
        if not isinstance(existing, Mapping):
            raise ValueError("site artifacts must be an object")
        if existing and dict(existing) != proposal:
            raise ValueError("site artifacts already bound differently")
        if not existing:
            needs_write = True

    if needs_write:
        for pnu, site in sites_by_pnu.items():
            if not site.get("artifacts"):
                site["artifacts"] = proposals[pnu]
        write_json_atomic(registry_path, registry)
    return registry


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    registry = bind_artifacts(args.registry, args.summary)
    site_count = len(registry["sites"])
    summary_count = len(args.summary)
    print(
        f"bound_sites={site_count} summaries={summary_count} "
        f"artifact_entries={site_count * len(PROGRAMS)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
