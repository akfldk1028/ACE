"""Plan and execute the leakage-safe Exp08 architecture topology pilot."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib
import json
import re
import subprocess
from collections import Counter
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any, Sequence

from iclr2027.exp08 import build_run_plan, execute_run_plans, summarize_pilot
from iclr2027.architecture_teams import ArchitectureTeamFactory
from iclr2027.dataset import CASE_MANIFEST_SCHEMA, verify_frozen_registry
from iclr2027.io import sha256_json, write_json_atomic
from iclr2027.pilot_gate import ALLOWED_CASE_STAGES
from iclr2027.projection import ProjectionIdentity, verify_private_case_binding
from iclr2027.release import load_projection_identity
from iclr2027.run_manifest import (
    RUN_IDENTITY_FIELDS,
    RUN_MANIFEST_SCHEMA,
    run_manifest_identity,
    validate_run_manifest,
)
from iclr2027.schema import (
    ArchitectureEvidencePacket,
    ArchitectureGoldRecord,
    ArchitecturePublicCase,
    PrivateCaseBinding,
)
from experiment_utils import ExperimentRunner


PILOT_PATTERNS = ("rr3", "sel3", "swm3", "refl3", "debate3")
_INPUT_HASH_KEY = re.compile(r"^input:([0-9a-f]{64})$")


def _runtime_dependency_digest(
    dependency_roots: Sequence[Path] | None = None,
) -> str:
    roots = dependency_roots
    if roots is None:
        discovered: list[Path] = []
        for module_name in (
            "AG_Cohub",
            "autogen_agentchat",
            "autogen_core",
            "autogen_ext",
            "claude_agent_sdk",
        ):
            module = importlib.import_module(module_name)
            module_file = getattr(module, "__file__", None)
            if not module_file:
                raise ValueError(f"runtime dependency has no source: {module_name}")
            module_path = Path(module_file).resolve()
            discovered.append(
                module_path.parent
                if module_path.name == "__init__.py"
                else module_path
            )
        roots = tuple(discovered)

    dependency_digest = hashlib.sha256()
    normalized_roots = sorted({Path(path).resolve() for path in roots})
    if not normalized_roots:
        raise ValueError("runtime dependency roots are empty")
    for dependency_root in normalized_roots:
        if dependency_root.is_file():
            files = (dependency_root,)
            base = dependency_root.parent
        elif dependency_root.is_dir():
            files = tuple(sorted(dependency_root.rglob("*.py")))
            base = dependency_root
        else:
            raise ValueError("runtime dependency root does not exist")
        if not files:
            raise ValueError("runtime dependency root has no Python source")
        dependency_digest.update(str(dependency_root).encode("utf-8"))
        for path in files:
            dependency_digest.update(
                path.relative_to(base).as_posix().encode("utf-8")
            )
            dependency_digest.update(path.read_bytes())
    return dependency_digest.hexdigest()


def _bind_runtime_dependencies(
    base_identity: str,
    dependency_roots: Sequence[Path] | None = None,
) -> str:
    if not isinstance(base_identity, str) or not base_identity.strip():
        raise ValueError("base code identity must be nonempty")
    digest = _runtime_dependency_digest(dependency_roots)
    return f"{base_identity}-deps-{digest[:16]}"


def _git_code_identity(
    repository_root: Path | None = None,
    scope: Path | None = None,
    *,
    dependency_roots: Sequence[Path] | None = None,
) -> str:
    """Return HEAD, extended by a scoped dirty-content hash when needed."""

    try:
        working = Path(__file__).resolve().parent
        root = (
            repository_root.resolve()
            if repository_root is not None
            else Path(
                subprocess.check_output(
                    ["git", "-C", str(working), "rev-parse", "--show-toplevel"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                ).strip()
            )
        )
        scoped = (scope or working).resolve()
        relative_scope = scoped.relative_to(root).as_posix() or "."
        prefix = "" if relative_scope == "." else f"{relative_scope}/"
        code_pathspecs = (
            f":(glob){prefix}*.py",
            f":(glob){prefix}**/*.py",
            f"{prefix}requirements.txt",
        )
        head = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        diff = subprocess.check_output(
            [
                "git",
                "-C",
                str(root),
                "diff",
                "--binary",
                "HEAD",
                "--",
                *code_pathspecs,
            ],
            stderr=subprocess.DEVNULL,
        )
        untracked_output = subprocess.check_output(
            [
                "git",
                "-C",
                str(root),
                "ls-files",
                "--others",
                "--exclude-standard",
                "--",
                *code_pathspecs,
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        untracked = sorted(line for line in untracked_output.splitlines() if line)
        digest = hashlib.sha256()
        if diff or untracked:
            digest.update(diff)
            for relative_path in untracked:
                digest.update(relative_path.encode("utf-8"))
                digest.update((root / relative_path).read_bytes())
            repository_identity = f"{head}-dirty-{digest.hexdigest()[:16]}"
        else:
            repository_identity = head

        return _bind_runtime_dependencies(
            repository_identity,
            dependency_roots,
        )
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        raise RuntimeError("code identity could not be established") from exc


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"{path}:{line_number} is not an object")
        rows.append(payload)
    return rows


def _load_public_cases(
    cases_dir: Path,
    split: str,
) -> tuple[list[ArchitecturePublicCase], dict[str, str]]:
    cases: list[ArchitecturePublicCase] = []
    source_hashes: dict[str, str] = {}
    for condition in ("native", "challenged"):
        path = cases_dir / f"{split}.{condition}.public.jsonl"
        if not path.is_file():
            raise ValueError(f"public case file is missing: {path}")
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        neutral_key = f"input:{digest}"
        if neutral_key in source_hashes:
            raise ValueError("public fixture input hash collision")
        source_hashes[neutral_key] = digest
        cases.extend(ArchitecturePublicCase.from_dict(row) for row in _read_jsonl(path))
    if len({case.case_id for case in cases}) != len(cases):
        raise ValueError("duplicate public case identity")
    return cases, source_hashes


def _load_manifest_bound_cases(
    split_manifest: dict[str, Any],
    *,
    split_manifest_path: Path,
    split: str,
    projection_identity: ProjectionIdentity,
) -> tuple[
    list[ArchitecturePublicCase],
    dict[str, ArchitectureEvidencePacket],
    dict[str, ArchitectureGoldRecord],
    dict[str, str],
]:
    """Load and recompute exact public/internal/gold bindings for execution."""

    bundles = split_manifest.get("bundles")
    if not isinstance(bundles, dict):
        raise ValueError("split manifest has no bundles")
    public_cases: list[ArchitecturePublicCase] = []
    packets_by_case: dict[str, ArchitectureEvidencePacket] = {}
    gold_by_case: dict[str, ArchitectureGoldRecord] = {}
    input_hashes: dict[str, str] = {}
    for condition in ("native", "challenged"):
        key = f"{split}.{condition}"
        entry = bundles.get(key)
        if not isinstance(entry, dict):
            raise ValueError(f"split manifest bundle is missing: {key}")
        manifest_path = (
            split_manifest_path.parent / str(entry.get("manifest_path") or "")
        ).resolve()
        if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != entry.get(
            "manifest_sha256"
        ):
            raise ValueError(f"case manifest hash mismatch: {key}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or manifest.get(
            "schema_version"
        ) != CASE_MANIFEST_SCHEMA:
            raise ValueError(f"unsupported case manifest schema: {key}")
        files = manifest.get("files")
        if not isinstance(files, dict):
            raise ValueError(f"case manifest files are missing: {key}")
        typed_by_side: dict[str, list[Any]] = {}
        for side in ("public", "internal", "gold"):
            file_entry = files.get(side)
            if not isinstance(file_entry, dict):
                raise ValueError(f"case manifest {side} file is missing: {key}")
            data_path = (
                manifest_path.parent / str(file_entry.get("path") or "")
            ).resolve()
            actual_hash = hashlib.sha256(data_path.read_bytes()).hexdigest()
            if actual_hash != file_entry.get("sha256"):
                raise ValueError(f"{side} file hash mismatch: {key}")
            rows = _read_jsonl(data_path)
            if side == "public":
                typed_by_side[side] = [
                    ArchitecturePublicCase.from_dict(row) for row in rows
                ]
            elif side == "internal":
                typed_by_side[side] = [
                    PrivateCaseBinding.from_dict(row) for row in rows
                ]
            else:
                typed_by_side[side] = [
                    ArchitectureGoldRecord.from_dict(row) for row in rows
                ]
            neutral_key = f"input:{actual_hash}"
            if neutral_key in input_hashes:
                raise ValueError("manifest-bound input hash collision")
            input_hashes[neutral_key] = actual_hash
        publics = typed_by_side["public"]
        bindings = typed_by_side["internal"]
        gold_records = typed_by_side["gold"]
        if not (len(publics) == len(bindings) == len(gold_records)):
            raise ValueError(f"case triplet cardinality mismatch: {key}")
        for public_case, binding, gold_record in zip(
            publics, bindings, gold_records
        ):
            packet = verify_private_case_binding(
                public_case,
                binding,
                gold_record,
                projection_identity,
            )
            case_id = public_case.case_id
            if case_id in packets_by_case:
                raise ValueError("duplicate public case identity")
            public_cases.append(public_case)
            packets_by_case[case_id] = packet
            gold_by_case[case_id] = gold_record
    if len(input_hashes) != 6:
        raise ValueError("manifest-bound runner requires exactly six input hashes")
    return public_cases, packets_by_case, gold_by_case, input_hashes


def _validate_input_hashes(value: Any, *, expected_count: int) -> None:
    if not isinstance(value, dict) or len(value) != expected_count:
        raise ValueError("run manifest input_hashes cardinality is invalid")
    for key, digest in value.items():
        match = _INPUT_HASH_KEY.fullmatch(str(key))
        if (
            match is None
            or not isinstance(digest, str)
            or match.group(1) != digest
        ):
            raise ValueError("run manifest input_hashes are not condition-blind")


def _stage_case_counts(
    cases: Sequence[ArchitecturePublicCase | dict[str, Any]],
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for case in cases:
        row = case.to_dict() if isinstance(case, ArchitecturePublicCase) else case
        subject_kind = str(row.get("subject_kind") or "execution")
        if subject_kind == "execution":
            stage = "execution"
        else:
            stage = str(row.get("attempt_stage") or "").strip()
            if not stage:
                raise ValueError("portfolio attempt is missing attempt_stage")
        if stage not in ALLOWED_CASE_STAGES:
            raise ValueError(f"unsupported evidence stage: {stage}")
        counts[stage] += 1
    return dict(sorted(counts.items()))


def _existing_compatible_manifest(
    output_dir: Path,
    proposed: dict[str, Any],
) -> dict[str, Any] | None:
    path = output_dir / "run_manifest.json"
    if not path.is_file():
        return None
    raw_existing = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(raw_existing, dict)
        or raw_existing.get("schema_version") != RUN_MANIFEST_SCHEMA
    ):
        raise ValueError(
            "unsupported run manifest schema; use a new --checkpoint-dir"
        )
    proposed_hashes = proposed.get("input_hashes")
    expected_hash_count = (
        len(proposed_hashes) if isinstance(proposed_hashes, dict) else 0
    )
    try:
        _validate_input_hashes(
            raw_existing.get("input_hashes"),
            expected_count=expected_hash_count,
        )
    except ValueError as exc:
        raise ValueError(
            "incompatible run directory; use a new --checkpoint-dir "
            "(mismatched: input_hashes)"
        ) from exc
    try:
        existing = validate_run_manifest(raw_existing)
        proposed = validate_run_manifest(proposed)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
    existing_identity = run_manifest_identity(existing)
    proposed_identity = run_manifest_identity(proposed)
    mismatched = [
        field
        for field in RUN_IDENTITY_FIELDS
        if existing_identity[field] != proposed_identity[field]
    ]
    if mismatched:
        raise ValueError(
            "incompatible run directory; use a new --checkpoint-dir "
            f"(mismatched: {', '.join(mismatched)})"
        )
    return existing


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("dev", "test"), required=True)
    parser.add_argument("--patterns", nargs="+", default=list(PILOT_PATTERNS))
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--code-commit", default="")
    parser.add_argument("--cases-dir", type=Path, default=Path("data/iclr2027/cases"))
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("data/iclr2027/site_registry.json"),
    )
    parser.add_argument(
        "--split-manifest",
        type=Path,
        default=Path("data/iclr2027/split_manifest.json"),
    )
    parser.add_argument(
        "--projection-identity",
        type=Path,
        default=Path("data/iclr2027/projection_identity.private.json"),
    )
    parser.add_argument(
        "--public-registry",
        type=Path,
        default=Path("data/iclr2027/site_registry.public.json"),
    )
    parser.add_argument(
        "--freeze-receipt",
        type=Path,
        default=Path("data/iclr2027/freeze_receipt.json"),
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=Path("results/exp08_architecture/pilot"),
    )
    parser.add_argument("--limit-cases", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--allow-unfrozen",
        action="store_true",
        help="permit fixture-only dry runs without a frozen registry",
    )
    parser.add_argument("--confirm-paid-run", action="store_true")
    parser.add_argument("--estimated-cost-per-run-usd", type=float)
    parser.add_argument("--estimated-completion-date")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.allow_unfrozen and not args.dry_run:
        raise ValueError("--allow-unfrozen is permitted only with --dry-run")
    if not args.allow_unfrozen:
        projection_identity = load_projection_identity(args.projection_identity)
        split_manifest = verify_frozen_registry(
            args.registry,
            split_manifest_path=args.split_manifest,
            projection_identity=projection_identity,
            public_registry_path=args.public_registry,
            freeze_receipt_path=args.freeze_receipt,
        )
        cases, packets_by_case, gold_by_case, input_hashes = _load_manifest_bound_cases(
            split_manifest,
            split_manifest_path=args.split_manifest,
            split=args.split,
            projection_identity=projection_identity,
        )
        expected_case_count = sum(
            split_manifest["bundles"][f"{args.split}.{condition}"]["case_count"]
            for condition in ("native", "challenged")
        )
        input_mode = "frozen_private_binding"
        identity_commitment: str | None = projection_identity.commitment
        registry_core_hash: str | None = str(
            split_manifest["registry_core_sha256"]
        )
        split_manifest_hash: str | None = hashlib.sha256(
            args.split_manifest.read_bytes()
        ).hexdigest()
    else:
        cases, input_hashes = _load_public_cases(args.cases_dir, args.split)
        packets_by_case = {}
        gold_by_case = {}
        expected_case_count = len(cases)
        input_mode = "public_fixture"
        identity_commitment = None
        registry_core_hash = None
        split_manifest_hash = None
    if len(cases) != expected_case_count:
        raise ValueError("loaded case count does not match full split manifest")
    _validate_input_hashes(
        input_hashes,
        expected_count=2 if input_mode == "public_fixture" else 6,
    )
    cases.sort(key=lambda case: case.case_id)
    if args.limit_cases is not None:
        if args.limit_cases <= 0:
            raise ValueError("limit-cases must be positive")
        cases = cases[: args.limit_cases]
    selected_case_ids = {case.case_id for case in cases}
    code_commit = (
        _bind_runtime_dependencies(args.code_commit)
        if args.code_commit
        else _git_code_identity()
    )
    plans = build_run_plan(
        cases,
        patterns=args.patterns,
        repeats=args.repeats,
        model=args.model,
        code_commit=code_commit,
    )
    args.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    manifest = validate_run_manifest({
        "schema_version": RUN_MANIFEST_SCHEMA,
        "input_mode": input_mode,
        "split": args.split,
        "patterns": list(args.patterns),
        "repeats": args.repeats,
        "model": args.model,
        "code_commit": code_commit,
        "case_count": len(cases),
        "expected_case_count": expected_case_count,
        "planned_run_count": len(plans),
        "stage_case_counts": _stage_case_counts(cases),
        "decision_case_counts": dict(
            sorted(
                Counter(
                    record.expected_decision
                    for case_id, record in gold_by_case.items()
                    if case_id in selected_case_ids
                ).items()
            )
        ),
        "input_hashes": input_hashes,
        "identity_commitment": identity_commitment,
        "registry_core_sha256": registry_core_hash,
        "split_manifest_sha256": split_manifest_hash,
        "plan_sha256": sha256_json(
            [plan.resume_identity for plan in plans]
        ),
        "executed": False,
    })
    existing_manifest = _existing_compatible_manifest(
        args.checkpoint_dir,
        manifest,
    )
    resuming_executed = bool(
        existing_manifest is not None and existing_manifest["executed"]
    )
    if existing_manifest is not None:
        manifest = existing_manifest if existing_manifest["executed"] else manifest
    write_json_atomic(
        args.checkpoint_dir / "run_plan.json",
        [plan.to_dict() for plan in plans],
    )
    if not resuming_executed:
        write_json_atomic(args.checkpoint_dir / "run_manifest.json", manifest)
    print(f"cases={len(cases)}")
    print(f"planned_runs={len(plans)}")
    print(f"checkpoint_dir={args.checkpoint_dir}")
    if args.dry_run:
        return 0

    if not args.confirm_paid_run:
        raise ValueError("actual execution requires --confirm-paid-run")
    if (
        args.estimated_cost_per_run_usd is None
        or args.estimated_cost_per_run_usd < 0.0
    ):
        raise ValueError("actual execution requires a nonnegative cost estimate per run")
    if not args.estimated_completion_date:
        raise ValueError("actual execution requires --estimated-completion-date")
    completion_date = date.fromisoformat(args.estimated_completion_date)

    packets_by_case = {
        case_id: packet
        for case_id, packet in packets_by_case.items()
        if case_id in selected_case_ids
    }
    gold_by_case = {
        case_id: record
        for case_id, record in gold_by_case.items()
        if case_id in selected_case_ids
    }
    if set(packets_by_case) != set(gold_by_case):
        raise ValueError("selected public and gold case IDs do not match")

    execution = asyncio.run(
        execute_run_plans(
            plans=plans,
            packets_by_case=packets_by_case,
            gold_by_case=gold_by_case,
            output_dir=args.checkpoint_dir,
            team_builder=lambda pattern, model, allowed_evidence_ids: ArchitectureTeamFactory.build(
                pattern,
                model=model,
                allowed_evidence_ids=allowed_evidence_ids,
            ),
            run_single=ExperimentRunner.run_single,
            enforce_pilot_protocol=True,
        )
    )
    if resuming_executed:
        expected_noop = {
            "completed_runs": 0,
            "skipped_runs": len(plans),
            "error_runs": 0,
            "parsed_states": 0,
            "successful_parses": 0,
        }
        if asdict(execution) != expected_noop:
            raise ValueError("executed resume produced a non-noop execution delta")
        print("completed_runs_this_invocation=0")
        print(f"skipped_runs={len(plans)}")
        print(
            "estimated_total_cost_usd="
            f"{float(manifest['estimated_total_cost_usd']):.2f}"
        )
        return 0
    estimated_total_cost = args.estimated_cost_per_run_usd * len(plans)
    summary = summarize_pilot(
        output_dir=args.checkpoint_dir,
        plans=plans,
        packets_by_case=packets_by_case,
        gold_by_case=gold_by_case,
        estimated_completion_date=completion_date,
        estimated_total_cost_usd=estimated_total_cost,
    )
    summary_payload = {
        **asdict(summary),
        "estimated_completion_date": summary.estimated_completion_date.isoformat(),
        "fault_families": list(summary.fault_families),
        "stage_case_counts": manifest["stage_case_counts"],
    }
    write_json_atomic(args.checkpoint_dir / "pilot_summary.json", summary_payload)
    processed_runs = summary.completed_runs + summary.run_errors
    canonical_execution = {
        "completed_runs": processed_runs,
        "skipped_runs": summary.planned_runs - processed_runs,
        "error_runs": summary.run_errors,
        "parsed_states": summary.parsed_states,
        "successful_parses": summary.successful_parses,
    }
    executed_manifest = validate_run_manifest(
        {
            **run_manifest_identity(manifest),
            "executed": True,
            "execution": canonical_execution,
            "estimated_cost_per_run_usd": args.estimated_cost_per_run_usd,
            "estimated_total_cost_usd": estimated_total_cost,
            "estimated_completion_date": completion_date.isoformat(),
        }
    )
    write_json_atomic(args.checkpoint_dir / "run_manifest.json", executed_manifest)
    print(f"completed_runs_this_invocation={execution.completed_runs}")
    print(f"skipped_runs={execution.skipped_runs}")
    print(f"estimated_total_cost_usd={estimated_total_cost:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
