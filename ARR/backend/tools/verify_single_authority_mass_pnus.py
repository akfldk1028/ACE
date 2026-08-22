"""Run isolated BOOK benchmark probes and aggregate authority evidence by PNU."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Iterable

from design.maas.agents.law_graph_agent.evidence import (
    canonical_agent_evidence_hash,
    validate_persisted_law_agent_evidence,
)
from design.maas.agents.shared.types import ExecutionIdentity


STRICT_PNUS = (
    "1168011800104170004",
    "1168011800104670003",
)
DIAGNOSTIC_PNU = "1168011800104230007"
SUMMARY_FILENAME = "maas-book-programs-summary.json"
STATE_FILENAME = "maas-run-state.json"


def unique_output_directory(
    root: Path,
    *,
    pnu: str,
    ordinal: int,
) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    safe_pnu = "".join(character for character in str(pnu) if character.isdigit())
    return Path(root).resolve() / f"{stamp}-{int(ordinal):02d}-pnu-{safe_pnu}"


def build_benchmark_command(
    *,
    pnu: str,
    output_directory: Path,
    diagnostic_target: int | None,
) -> list[str]:
    command = [
        sys.executable,
        "manage.py",
        "benchmark_maas_book_program_portfolios",
        "--pnu",
        str(pnu),
        "--output-dir",
        str(Path(output_directory).resolve()),
    ]
    if diagnostic_target is None:
        command.append("--smoke")
    if diagnostic_target is not None:
        if int(diagnostic_target) not in (1, 2, 3, 20):
            raise ValueError("diagnostic_target must be one of 1, 2, 3, or 20")
        command.extend(("--diagnostic-target", str(int(diagnostic_target))))
    return command


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _rows(program: dict[str, Any]) -> list[dict[str, Any]]:
    display_rows = [
        dict(row)
        for row in program.get("rows") or ()
        if isinstance(row, dict)
    ]
    downstream_rows = [
        dict(row)
        for row in _mapping(program.get("downstream_hard_gate")).get("rows") or ()
        if isinstance(row, dict)
    ]
    size = max(len(display_rows), len(downstream_rows))
    return [
        {
            **(display_rows[index] if index < len(display_rows) else {}),
            **(downstream_rows[index] if index < len(downstream_rows) else {}),
        }
        for index in range(size)
    ]


def _final_identity_channels(row: dict[str, Any]) -> dict[str, str]:
    render = _mapping(
        row.get("archive_render_evidence")
        or row.get("render_evidence")
    )
    passport = _mapping(row.get("mass_execution_passport"))
    elevation = _mapping(
        row.get("elevation_evidence")
        or passport.get("elevation_evidence")
    )
    archive = _mapping(row.get("archive"))
    return {
        "selected_row": str(
            row.get("final_legal_geometry_hash") or ""
        ).strip(),
        "render": str(
            render.get("final_legal_geometry_hash") or ""
        ).strip(),
        "passport": str(
            passport.get("final_legal_geometry_hash") or ""
        ).strip(),
        "elevation": str(
            elevation.get("final_legal_geometry_hash") or ""
        ).strip(),
        "archive": str(
            archive.get("final_legal_geometry_hash") or ""
        ).strip(),
    }


def _final_hashes(row: dict[str, Any]) -> set[str]:
    return {
        value
        for value in _final_identity_channels(row).values()
        if value
    }


def summarize_pnu_result(result: dict[str, Any]) -> dict[str, Any]:
    programs = [
        dict(program)
        for program in result.get("programs") or ()
        if isinstance(program, dict)
    ]
    rows = [
        row
        for program in programs
        for row in _rows(program)
    ]
    far_values: list[float] = []
    law_hashes: set[str] = set()
    parking: list[dict[str, Any]] = []
    final_hash_sets: list[set[str]] = []
    final_geometry_continuity: list[dict[str, Any]] = []
    law_continuity_failures: list[dict[str, Any]] = []
    law_missing_count = 0
    achieved_counts: dict[str, int] = {}
    png_paths: list[str] = []
    stepped_count = roof_count = phenotype_count = 0

    for program in programs:
        metrics = _mapping(
            program.get("program_language_metrics")
            or program.get("language_metrics")
        )
        stepped_count += int(metrics.get("stepped_count") or 0)
        roof_count += int(metrics.get("roof_archetype_count") or 0)
        phenotype_count += int(metrics.get("solid_phenotype_count") or 0)
        capacity = _mapping(
            _mapping(program.get("counts")).get(
                "capacity_alternative_diagnostics"
            )
        )
        bands = _mapping(
            capacity.get("selected_achieved_band_counts")
            or metrics.get("achieved_capacity_band_counts")
        )
        for key, value in bands.items():
            achieved_counts[str(key)] = (
                achieved_counts.get(str(key), 0) + int(value or 0)
            )
        if program.get("png"):
            png_paths.append(str(program["png"]))

    for row in rows:
        projected = _mapping(row.get("projected_metrics"))
        far_value = row.get("far_pct")
        if far_value is None:
            far_value = projected.get("far_pct")
        try:
            far_values.append(float(far_value))
        except (TypeError, ValueError):
            pass
        explicit_law_hash = str(
            row.get("law_graph_evidence_hash") or ""
        ).strip()
        if explicit_law_hash:
            law_hashes.add(explicit_law_hash)
        law_payload = _mapping(row.get("law_graph_agent_evidence"))
        law_issues: list[str] = []
        expected_identity: ExecutionIdentity | None = None
        if not explicit_law_hash:
            law_issues.append("law_agent_payload_hash_missing")
        if not law_payload:
            law_issues.append("law_agent_payload_missing")
        expected_fields = {
            "execution_id": str(
                row.get("selected_execution_id") or ""
            ).strip(),
            "program_hash": str(
                row.get("final_legal_program_hash") or ""
            ).strip(),
            "geometry_hash": str(
                row.get("final_legal_geometry_hash") or ""
            ).strip(),
            "floor_capacity_plan_hash": str(
                row.get("floor_capacity_plan_hash") or ""
            ).strip(),
            "pnu": str(result.get("pnu") or "").strip(),
        }
        for key, value in expected_fields.items():
            if not value or "UNRESOLVED" in value.upper():
                law_issues.append(
                    f"law_agent_expected_identity_missing:{key}"
                )
        if not any(
            reason.startswith("law_agent_expected_identity_missing:")
            for reason in law_issues
        ):
            expected_identity = ExecutionIdentity(**expected_fields)
        if law_payload and explicit_law_hash and expected_identity is not None:
            law_issues.extend(validate_persisted_law_agent_evidence(
                law_payload,
                explicit_law_hash,
                expected_identity=expected_identity,
            ))
        elif law_payload and explicit_law_hash:
            if canonical_agent_evidence_hash(law_payload) != explicit_law_hash:
                law_issues.append("law_agent_payload_hash_mismatch")
            if str(law_payload.get("status") or "") != "passed":
                law_issues.append(
                    "law_agent_status_not_passed:"
                    f"{law_payload.get('status') or 'missing'}"
                )
        if row.get("law_graph_evidence_hard_pass") is not True:
            law_issues.append("law_agent_row_hard_pass_missing")

        passport = _mapping(row.get("mass_execution_passport"))
        passport_payload = _mapping(
            passport.get("law_graph_agent_evidence")
        )
        passport_hash = str(
            passport.get("law_graph_evidence_hash") or ""
        ).strip()
        if not passport_payload or not passport_hash:
            law_issues.append("law_agent_passport_copy_missing")
        else:
            if passport_payload != law_payload:
                law_issues.append(
                    "law_agent_passport_payload_mismatch"
                )
            if passport_hash != explicit_law_hash:
                law_issues.append("law_agent_passport_hash_mismatch")
            if passport.get("law_graph_evidence_hard_pass") is not True:
                law_issues.append(
                    "law_agent_passport_hard_pass_missing"
                )
            if expected_identity is not None:
                law_issues.extend(
                    f"passport:{reason}"
                    for reason in validate_persisted_law_agent_evidence(
                        passport_payload,
                        passport_hash,
                        expected_identity=expected_identity,
                    )
                )

        artifact_binding = _mapping(
            row.get("geometry_artifact_law_binding")
        )
        artifact_payload = _mapping(
            artifact_binding.get("law_graph_agent_evidence")
        )
        artifact_hash = str(
            artifact_binding.get("law_graph_evidence_hash") or ""
        ).strip()
        if (
            artifact_binding.get("schema_version")
            != "arr.maas.geometry_artifact_law_binding.v1"
            or not artifact_payload
            or not artifact_hash
        ):
            law_issues.append("law_agent_artifact_copy_missing")
        else:
            if artifact_payload != law_payload:
                law_issues.append(
                    "law_agent_artifact_payload_mismatch"
                )
            if artifact_hash != explicit_law_hash:
                law_issues.append("law_agent_artifact_hash_mismatch")
            if (
                artifact_binding.get("law_graph_evidence_hard_pass")
                is not True
            ):
                law_issues.append(
                    "law_agent_artifact_hard_pass_missing"
                )
            artifact_identity = _mapping(
                artifact_binding.get("identity")
            )
            if artifact_identity != expected_fields:
                law_issues.append(
                    "law_agent_artifact_identity_mismatch"
                )
            if expected_identity is not None:
                law_issues.extend(
                    f"artifact:{reason}"
                    for reason in validate_persisted_law_agent_evidence(
                        artifact_payload,
                        artifact_hash,
                        expected_identity=expected_identity,
                    )
                )
        if not explicit_law_hash or not law_payload:
            law_missing_count += 1
        if law_issues:
            law_continuity_failures.append({
                "variant_id": str(row.get("variant_id") or ""),
                "reasons": list(dict.fromkeys(law_issues)),
            })
        parking_gate = _mapping(row.get("parking_hard_gate"))
        parking.append({
            "required_spaces": (
                row.get("parking_required")
                if row.get("parking_required") is not None
                else parking_gate.get("required_spaces")
            ),
            "provided_spaces": parking_gate.get("provided_spaces"),
            "layout_status": str(
                row.get("parking_layout_status")
                or parking_gate.get("layout_status")
                or ""
            ),
            "hard_pass": parking_gate.get("hard_pass"),
        })
        identity_channels = _final_identity_channels(row)
        hashes = {
            value for value in identity_channels.values() if value
        }
        final_hash_sets.append(hashes)
        required_channels = {
            key: identity_channels[key]
            for key in ("selected_row", "render", "passport")
        }
        optional_channels = {
            key: identity_channels[key]
            for key in ("elevation", "archive")
        }
        final_geometry_continuity.append({
            "variant_id": str(row.get("variant_id") or ""),
            "channels": identity_channels,
            "missing_required_channels": [
                key for key, value in required_channels.items() if not value
            ],
            "missing_optional_channels": [
                key for key, value in optional_channels.items() if not value
            ],
            "hashes": sorted(hashes),
            "hard_pass": bool(
                all(required_channels.values())
                and len(hashes) == 1
            ),
        })

    if result.get("summary_png"):
        png_paths.append(str(result["summary_png"]))
    flattened_hashes = {
        value for values in final_hash_sets for value in values
    }
    final_hash_agreement = bool(
        final_hash_sets
        and all(len(values) == 1 for values in final_hash_sets)
        and all(
            row["hard_pass"]
            for row in final_geometry_continuity
        )
    )
    failures = [
        {
            "program": str(program.get("slug") or program.get("program") or ""),
            "status": str(program.get("status") or ""),
            "reasons": [str(value) for value in program.get("failures") or ()],
        }
        for program in programs
    ]
    law_evidence_hard_pass = bool(rows) and not law_continuity_failures
    bounded_probe_failures: list[str] = []
    result_status = str(result.get("status") or "").strip().lower()
    if result_status in {
        "fail",
        "failed",
        "completed_with_failed_gate",
    }:
        bounded_probe_failures.append(
            f"explicit_result_status_{result_status}"
        )
    if not law_evidence_hard_pass:
        bounded_probe_failures.append(
            "explicit_law_graph_evidence_failed"
        )
    diagnostic_target = result.get("diagnostic_target")
    if diagnostic_target is not None:
        if result_status != "diagnostic_only":
            bounded_probe_failures.append(
                "top_status_not_diagnostic_only"
            )
        if result.get("diagnostic_only") is not True:
            bounded_probe_failures.append(
                "diagnostic_only_flag_missing"
            )
        try:
            requested_target = int(diagnostic_target)
        except (TypeError, ValueError):
            requested_target = 0
        if requested_target not in (1, 2, 3, 20):
            bounded_probe_failures.append(
                "diagnostic_target_invalid"
            )
        else:
            for program in programs:
                if (
                    str(program.get("status") or "").strip().lower()
                    != "diagnostic_only"
                ):
                    bounded_probe_failures.append(
                        "program_status_not_diagnostic_only"
                    )
                    break
                if program.get("diagnostic_only") is not True:
                    bounded_probe_failures.append(
                        "program_diagnostic_only_flag_missing"
                    )
                    break
            for program in programs:
                selected_count = int(program.get("selected_count") or 0)
                selected_rows = _rows(program)
                if (
                    selected_count != requested_target
                    or len(selected_rows) != requested_target
                ):
                    bounded_probe_failures.append(
                        "program_diagnostic_target_not_met"
                    )
                    break
    if not rows:
        bounded_probe_failures.append("selected_rows_missing")
    if any(row.get("combined_hard_pass") is not True for row in rows):
        bounded_probe_failures.append(
            "selected_row_combined_hard_gate_failed"
        )
    if any(
        _mapping(row.get("legal_projection")).get(
            "shared_floor_contract_hard_pass"
        )
        is not True
        for row in rows
    ):
        bounded_probe_failures.append(
            "selected_row_shared_floor_contract_failed"
        )
    if any(
        _mapping(row.get("parking_hard_gate")).get("hard_pass") is not True
        for row in rows
    ):
        bounded_probe_failures.append(
            "selected_row_parking_hard_gate_failed"
        )
    if any(
        _mapping(
            row.get("archive_render_evidence")
            or row.get("render_evidence")
        ).get("hard_pass") is not True
        for row in rows
    ):
        bounded_probe_failures.append(
            "selected_row_render_hard_gate_failed"
        )
    if any(
        row["missing_required_channels"]
        for row in final_geometry_continuity
    ):
        bounded_probe_failures.append(
            "selected_row_final_geometry_identity_missing"
        )
    if any(
        not row["missing_required_channels"] and len(row["hashes"]) != 1
        for row in final_geometry_continuity
    ):
        bounded_probe_failures.append(
            "selected_row_final_geometry_identity_mismatch"
        )
    for program in programs:
        downstream_status = str(
            _mapping(program.get("downstream_hard_gate")).get("status")
            or ""
        ).strip().lower()
        if downstream_status in {
            "fail",
            "failed",
            "completed_with_failed_gate",
        }:
            bounded_probe_failures.append(
                "downstream_hard_gate_status_failed"
            )
            break
    bounded_probe_failures = list(dict.fromkeys(bounded_probe_failures))
    bounded_probe_hard_pass = not bounded_probe_failures
    return {
        "status": (
            str(result.get("status") or "passed")
            if law_evidence_hard_pass
            else "failed"
        ),
        "pnu": str(result.get("pnu") or ""),
        "diagnostic_only": result.get("diagnostic_only") is True,
        "final_count": sum(
            int(program.get("selected_count") or 0)
            for program in programs
        ),
        "six_scope_counts": [
            int(program.get("book_base_volume_scope_count") or 0)
            for program in programs
        ],
        "achieved_capacity_counts": dict(sorted(achieved_counts.items())),
        "far_range": (
            [round(min(far_values), 6), round(max(far_values), 6)]
            if far_values
            else []
        ),
        "stepped_count": stepped_count,
        "roof_archetype_count": roof_count,
        "solid_phenotype_count": phenotype_count,
        "law_graph_evidence_hashes": sorted(law_hashes),
        "law_graph_hash_source": "persisted_explicit_agent_evidence_only",
        "law_graph_missing_count": law_missing_count,
        "law_graph_evidence_hard_pass": law_evidence_hard_pass,
        "law_graph_continuity_failures": law_continuity_failures,
        "parking_requirement_layout": parking,
        "final_geometry_hashes": sorted(flattened_hashes),
        "final_geometry_hash_agreement": final_hash_agreement,
        "final_geometry_continuity": final_geometry_continuity,
        "bounded_probe_evidence_hard_pass": bounded_probe_hard_pass,
        "bounded_probe_failure_reasons": bounded_probe_failures,
        "png_paths": list(dict.fromkeys(png_paths)),
        "pass_fail_reasons": failures,
    }


def run_benchmark(
    *,
    backend_root: Path,
    pnu: str,
    output_directory: Path,
    diagnostic_target: int | None,
    inactivity_timeout_seconds: int = 60,
) -> dict[str, Any]:
    output_directory.mkdir(parents=True, exist_ok=False)
    log_path = output_directory / "benchmark.log"
    command = build_benchmark_command(
        pnu=pnu,
        output_directory=output_directory,
        diagnostic_target=diagnostic_target,
    )
    environment = dict(os.environ)
    for name in (
        "OPENAI_API_KEY",
        "MAAS_LIVE_GEOMETRY_VLM",
        "MAAS_LIVE_VLM_CREDENTIAL_ROTATED",
    ):
        environment.pop(name, None)
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command,
            cwd=Path(backend_root).resolve(),
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        state_path = output_directory / STATE_FILENAME
        last_signature: tuple[int, int] | None = None
        last_progress_at = time.monotonic()
        while process.poll() is None:
            try:
                signature = (
                    state_path.stat().st_mtime_ns,
                    state_path.stat().st_size,
                )
            except OSError:
                signature = None
            if signature is not None and signature != last_signature:
                last_signature = signature
                last_progress_at = time.monotonic()
            if (
                time.monotonic() - last_progress_at
                > max(1, int(inactivity_timeout_seconds))
            ):
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)
                raise TimeoutError(
                    f"PNU {pnu} made no state progress for "
                    f"{inactivity_timeout_seconds}s"
                )
            time.sleep(2)
        if process.returncode != 0:
            raise RuntimeError(
                f"PNU {pnu} benchmark failed with exit code "
                f"{process.returncode}; see {log_path}"
            )
    summary_path = output_directory / SUMMARY_FILENAME
    result = json.loads(summary_path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError(f"invalid summary payload: {summary_path}")
    return result


def aggregate_runs_hard_pass(runs: Iterable[dict[str, Any]]) -> bool:
    """Fail the runner when explicit law evidence is absent or discontinuous."""

    normalized = tuple(runs)
    return bool(normalized) and all(
        "error" not in run
        and run.get("law_graph_evidence_hard_pass") is True
        and run.get("bounded_probe_evidence_hard_pass") is True
        for run in normalized
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify isolated single-authority MASS results across PNUs.",
    )
    parser.add_argument("--pnu", action="append", default=[])
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument(
        "--diagnostic-target",
        type=int,
        choices=(1, 2, 3, 20),
        default=3,
    )
    parser.add_argument("--inactivity-timeout-seconds", type=int, default=60)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    options = _parser().parse_args(list(argv) if argv is not None else None)
    pnus = tuple(options.pnu or STRICT_PNUS)
    root = Path(options.output_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    backend_root = Path(__file__).resolve().parents[1]
    aggregate: dict[str, Any] = {
        "schema_version": "arr.maas.single_authority_cross_pnu.v1",
        "diagnostic_only": True,
        "diagnostic_target": int(options.diagnostic_target),
        "strict_pnus": list(STRICT_PNUS),
        "diagnostic_pnu": DIAGNOSTIC_PNU,
        "runs": [],
    }
    for ordinal, pnu in enumerate(pnus, start=1):
        output_directory = unique_output_directory(
            root,
            pnu=pnu,
            ordinal=ordinal,
        )
        try:
            result = run_benchmark(
                backend_root=backend_root,
                pnu=pnu,
                output_directory=output_directory,
                diagnostic_target=int(options.diagnostic_target),
                inactivity_timeout_seconds=int(
                    options.inactivity_timeout_seconds
                ),
            )
            run_summary = summarize_pnu_result(result)
            run_summary["output_directory"] = str(output_directory)
            run_summary["pnu_classification"] = (
                "strict"
                if pnu in STRICT_PNUS
                else "diagnostic_parcel_provenance_incomplete"
                if pnu == DIAGNOSTIC_PNU
                else "caller_supplied"
            )
        except Exception as exc:
            run_summary = {
                "pnu": pnu,
                "output_directory": str(output_directory),
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            }
        aggregate["runs"].append(run_summary)
        (root / "combined-summary.json").write_text(
            json.dumps(
                aggregate,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    return 0 if aggregate_runs_hard_pass(aggregate["runs"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
