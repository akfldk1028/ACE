"""Deterministically select and record unseen architecture test sites."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from iclr2027.io import write_json_atomic
from iclr2027.site_selection import (
    DEV_SITES,
    candidate_from_dict,
    registry_from_selection,
    select_test_sites,
)


_PNU = re.compile(r"^[0-9]{19}$")


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate-source",
        type=Path,
        required=True,
        help="JSON export containing a candidates list with verified availability flags",
    )
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20260818)
    parser.add_argument(
        "--max-parcel-area-m2",
        type=float,
        default=30_000.0,
        help="objective architecture-scope cap applied before deterministic sampling",
    )
    parser.add_argument("--prior-pnu-file", type=Path)
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="repository snapshot to scan for every previously used 19-digit PNU",
    )
    parser.add_argument(
        "--inventory-exclude-path",
        action="append",
        type=Path,
        default=[],
        help="explicit current-protocol artifact to exclude from prior-work inventory",
    )
    parser.add_argument("--inventory-commit", default="")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/iclr2027/site_registry.json"),
    )
    return parser


def _repository_pnus(
    root: Path,
    *,
    exclude_paths: Sequence[Path],
) -> set[str]:
    root = root.resolve()
    command = ["rg", "-o", "--no-filename"]
    if sys.platform == "win32":
        command.extend(("--glob", "!NUL"))
    for excluded in exclude_paths:
        try:
            relative = excluded.resolve().relative_to(root)
        except ValueError:
            continue
        command.extend(("--glob", f"!{relative.as_posix()}"))
    command.extend((r"[0-9]{19}", "."))
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            cwd=root,
        )
    except OSError as exc:
        raise RuntimeError("repository PNU scan requires ripgrep (rg)") from exc
    if completed.returncode not in {0, 1}:
        detail = (completed.stderr or "").strip()
        suffix = f": {detail}" if detail else ""
        raise RuntimeError(f"repository PNU scan failed{suffix}")
    return {
        line.strip()
        for line in completed.stdout.splitlines()
        if _PNU.fullmatch(line.strip())
    }


def _read_prior_pnus(
    path: Path | None,
    *,
    repository_root: Path,
    exclude_paths: Sequence[Path],
) -> set[str]:
    prior = {str(site["pnu"]) for site in DEV_SITES}
    prior.update(
        _repository_pnus(
            repository_root,
            exclude_paths=exclude_paths,
        )
    )
    if path is not None:
        prior.update(
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    return prior


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.output.is_file():
        existing = json.loads(args.output.read_text(encoding="utf-8"))
        if isinstance(existing, dict) and existing.get("frozen") is True:
            raise ValueError(
                "refusing to overwrite an existing frozen site registry"
            )
    source_bytes = args.candidate_source.read_bytes()
    payload = json.loads(source_bytes.decode("utf-8"))
    raw_candidates = payload.get("candidates") if isinstance(payload, dict) else None
    if not isinstance(raw_candidates, list):
        raise ValueError("candidate source must contain a candidates list")
    candidates = [candidate_from_dict(item) for item in raw_candidates]
    repository_root = args.repository_root.resolve()
    inventory_exclude_paths: list[Path] = []
    inventory_exclude_labels: list[str] = []
    for raw_path in args.inventory_exclude_path:
        resolved = raw_path.resolve()
        if not resolved.exists():
            raise ValueError(f"inventory exclude path does not exist: {raw_path}")
        try:
            relative = resolved.relative_to(repository_root)
        except ValueError as exc:
            raise ValueError(
                f"inventory exclude path is outside repository root: {raw_path}"
            ) from exc
        inventory_exclude_paths.append(resolved)
        inventory_exclude_labels.append(relative.as_posix())
    prior_pnus = _read_prior_pnus(
        args.prior_pnu_file,
        repository_root=repository_root,
        exclude_paths=(
            args.candidate_source,
            args.output,
            *inventory_exclude_paths,
        ),
    )
    result = select_test_sites(
        candidates,
        prior_pnus=prior_pnus,
        seed=args.seed,
        count=args.count,
        max_parcel_area_m2=args.max_parcel_area_m2,
    )
    registry = registry_from_selection(
        result,
        inventory_commit=args.inventory_commit or _git_commit(),
        candidate_source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        prior_pnus=prior_pnus,
        repository_inventory_scanned=True,
        inventory_exclude_paths=tuple(sorted(inventory_exclude_labels)),
    )
    write_json_atomic(args.output, registry)
    print(f"selected {len(result.selected)} test sites into {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
