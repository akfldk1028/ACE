from __future__ import annotations

import json
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path


FIXTURE = Path(__file__).parent / "fixtures" / "iclr2027" / "native_summary.json"
PREEXECUTION_SUMMARY = (
    Path(__file__).parents[1]
    / "data"
    / "iclr2027"
    / "arr"
    / "dev-417-law-restored"
    / "maas-book-programs-summary.json"
)
ARR_ROOT = Path(__file__).parents[1] / "data" / "iclr2027" / "arr"
ACTUAL_SOURCES = {
    "dev-417-law-restored": "1168011800104170004",
    "dev-467-law-restored": "1168011800104670003",
    "test-01": "1121510400104130014",
    "test-02": "1117013100107390016",
    "test-03": "1165011100200390001",
    "test-04": "1162010300201040003",
    "test-05": "1144011500103140005",
}


def _attempt_candidate(index: int) -> dict[str, object]:
    program_hash = f"{index + 1:064x}"
    geometry_hash = f"{index + 101:064x}"
    return {
        "schema_version": "arr.maas.candidate_evaluation.v1",
        "candidate_id": f"candidate-{index}",
        "program_hash": program_hash,
        "geometry_hash": geometry_hash,
        "overall_status": "not_evaluated",
        "selected": False,
        "terminal_reasons": ["strict_portfolio_not_selected"],
        "stages": {
            "geometry": {
                "stage": "geometry",
                "status": "pass",
                "reasons": [],
                "evidence": {
                    "execution_passport": {
                        "schema_version": "arr.maas.mass_execution_passport.v1",
                        "status": "in_progress",
                        "program_hash": program_hash,
                        "geometry_hash": geometry_hash,
                        "execution_id": None,
                        "final_legal_geometry_hash": None,
                    }
                },
            },
            "law": {"stage": "law", "status": "not_evaluated", "reasons": [], "evidence": {}},
            "parking": {"stage": "parking", "status": "not_evaluated", "reasons": [], "evidence": {}},
            "selection": {
                "stage": "selection",
                "status": "fail",
                "reasons": ["strict_portfolio_not_selected"],
                "evidence": {"status": "rejected"},
            },
        },
    }


def _minimal_attempt_summary() -> dict[str, object]:
    records = [_attempt_candidate(0), _attempt_candidate(1)]
    return {
        "schema_version": "arr.maas.book_program_portfolios.v1",
        "pnu": "1168011800104170004",
        "programs": [
            {
                "slug": "gymnasium",
                "rows": [],
                "selected_count": 0,
                "mass_progress": {
                    "schema_version": "arr.maas.mass_progress.v1",
                    "evaluated_count": 2,
                    "compiled_count": 2,
                },
                "portfolio_completion": {
                    "schema_version": "arr.maas.portfolio_completion.v1",
                    "hard_pass": False,
                    "selected_count": 0,
                    "diagnostic_only": True,
                },
                "downstream_hard_gate": {
                    "schema_version": "arr.maas.book_downstream_hard_gate.v1",
                    "status": "fail",
                    "candidate_count": 0,
                    "rows": [],
                },
                "portfolio_evaluation": {
                    "schema_version": "arr.maas.portfolio_evaluation_ledger.v1",
                    "pnu": "1168011800104170004",
                    "program_slug": "gymnasium",
                    "run_id": "fixture-attempt",
                    "target_count": 2,
                    "record_count": 2,
                    "records_truncated": False,
                    "records": records,
                },
            }
        ],
    }


class SiteSelectionTests(unittest.TestCase):
    def test_selection_excludes_prior_sites_and_covers_bins_and_districts(self) -> None:
        try:
            from iclr2027.site_selection import SiteCandidate, select_test_sites
        except (ImportError, ModuleNotFoundError) as exc:
            self.fail(f"site selection module is missing: {exc}")

        candidates = [
            SiteCandidate("1111010100100000001", "11110", 120.0, True, True, True),
            SiteCandidate("1114010100100000002", "11140", 220.0, True, True, True),
            SiteCandidate("1120010100100000003", "11200", 450.0, True, True, True),
            SiteCandidate("1121510100100000004", "11215", 850.0, True, True, True),
            SiteCandidate("1135010100100000005", "11350", 1200.0, True, True, True),
            SiteCandidate("1141010100100000006", "11410", 2200.0, True, True, True),
            SiteCandidate("1168011800104170004", "11680", 264.0, True, True, True),
            SiteCandidate("1150010100100000007", "11500", 500.0, False, True, True),
        ]

        result = select_test_sites(
            candidates,
            prior_pnus={"1168011800104170004"},
            seed=20260818,
            count=5,
        )

        selected = result.selected
        self.assertEqual(len(selected), 5)
        self.assertNotIn("1168011800104170004", {item.pnu for item in selected})
        self.assertEqual({item.area_bin for item in selected}, {"small", "medium", "large"})
        self.assertGreaterEqual(len({item.district_code for item in selected}), 3)
        self.assertEqual(result.excluded["1168011800104170004"], "seen_in_repository")
        self.assertEqual(result.excluded["1150010100100000007"], "boundary_unavailable")

    def test_selection_is_deterministic_for_seed(self) -> None:
        try:
            from iclr2027.site_selection import SiteCandidate, select_test_sites
        except (ImportError, ModuleNotFoundError) as exc:
            self.fail(f"site selection module is missing: {exc}")

        candidates = [
            SiteCandidate(f"11110101001{index:08d}", f"{11110 + index}", area, True, True, True)
            for index, area in enumerate((100.0, 180.0, 400.0, 700.0, 1100.0, 1800.0), start=1)
        ]

        first = select_test_sites(candidates, prior_pnus=set(), seed=77, count=5)
        second = select_test_sites(list(reversed(candidates)), prior_pnus=set(), seed=77, count=5)

        self.assertEqual(
            [item.pnu for item in first.selected],
            [item.pnu for item in second.selected],
        )

    def test_selection_excludes_parcels_above_architecture_scope_cap(self) -> None:
        from iclr2027.site_selection import SiteCandidate, select_test_sites

        oversized = SiteCandidate(
            "1165010100100000001", "11650", 724_536.0, True, True, True
        )
        candidates = [
            SiteCandidate("1111010100100000001", "11110", 120.0, True, True, True),
            SiteCandidate("1114010100100000002", "11140", 220.0, True, True, True),
            SiteCandidate("1120010100100000003", "11200", 450.0, True, True, True),
            SiteCandidate("1121510100100000004", "11215", 850.0, True, True, True),
            SiteCandidate("1135010100100000005", "11350", 1_200.0, True, True, True),
            SiteCandidate("1141010100100000006", "11410", 12_000.0, True, True, True),
            oversized,
        ]

        result = select_test_sites(
            candidates,
            prior_pnus=set(),
            seed=20260818,
            count=5,
            max_parcel_area_m2=30_000.0,
        )

        self.assertNotIn(oversized, result.selected)
        self.assertEqual(
            result.excluded[oversized.pnu],
            "parcel_area_out_of_scope",
        )
        self.assertEqual(result.max_parcel_area_m2, 30_000.0)


class ArrAdapterTests(unittest.TestCase):
    def test_checked_in_zero_row_program_becomes_attempt_bound_selection_reject(self) -> None:
        from iclr2027.arr_adapter import packet_from_arr_artifacts
        from iclr2027.validators import validate_evidence_packet

        packet, gold = packet_from_arr_artifacts(
            PREEXECUTION_SUMMARY,
            pnu="1168011800104170004",
            program="gymnasium",
            case_id="dev-417-gymnasium-native",
        )

        self.assertEqual(packet.subject_kind, "portfolio_attempt")
        self.assertIsNone(packet.execution_id)
        self.assertIsNone(packet.program_hash)
        self.assertIsNone(packet.geometry_hash)
        self.assertEqual(
            packet.source_artifact_sha256,
            hashlib.sha256(PREEXECUTION_SUMMARY.read_bytes()).hexdigest(),
        )
        self.assertEqual(len(packet.attempt_hash or ""), 64)
        self.assertEqual(packet.attempt_stage, "selection")
        self.assertIsNone(packet.route_kind)
        self.assertRegex(packet.attempt_id or "", r"^attempt:[0-9a-f]{64}$")
        self.assertNotIn(packet.pnu, packet.attempt_id or "")
        self.assertEqual(
            {item["evidence_id"] for item in packet.evidence},
            {"evidence:portfolio_attempt"},
        )
        validation = validate_evidence_packet(packet)
        self.assertEqual(
            validation.blocking_issue_codes,
            ("selection.no_admitted_candidate",),
        )
        self.assertEqual(gold.expected_decision, "STOP_REJECT")
        self.assertEqual(
            gold.blocking_issue_codes,
            ("selection.no_admitted_candidate",),
        )
        public_text = json.dumps(packet.to_dict(), sort_keys=True)
        self.assertNotIn("law.projection_failed", public_text)
        self.assertNotIn("parking.supply_shortage", public_text)
        self.assertNotIn("geometry.compilation_failed", public_text)
        manifest_text = json.dumps(
            packet.to_dict()["evidence"][0]["evidence"], sort_keys=True
        )
        self.assertNotIn(packet.pnu, manifest_text)

    def test_actual_inventory_is_stage_classified_without_fabricated_execution_identity(self) -> None:
        from iclr2027.arr_adapter import packet_from_arr_artifacts
        from iclr2027.validators import validate_evidence_packet

        expected = {
            ("dev-417-law-restored", "neighborhood"): ("execution", None, None, "STOP_ACCEPT"),
            ("dev-417-law-restored", "gymnasium"): ("portfolio_attempt", "selection", None, "STOP_REJECT"),
            ("dev-417-law-restored", "cultural"): ("execution", None, None, "STOP_ACCEPT"),
            ("dev-467-law-restored", "neighborhood"): ("portfolio_attempt", "materialization", "capacity_admission_empty", "STOP_REJECT"),
            ("dev-467-law-restored", "gymnasium"): ("portfolio_attempt", "preflight", None, "STOP_REJECT"),
            ("dev-467-law-restored", "cultural"): ("portfolio_attempt", "materialization", "capacity_admission_empty", "STOP_REJECT"),
            ("test-01", "neighborhood"): ("execution", None, None, "STOP_ACCEPT"),
            ("test-01", "gymnasium"): ("portfolio_attempt", "selection", None, "STOP_REJECT"),
            ("test-01", "cultural"): ("execution", None, None, "STOP_ACCEPT"),
            ("test-02", "neighborhood"): ("portfolio_attempt", "materialization", "capacity_admission_empty", "STOP_REJECT"),
            ("test-02", "gymnasium"): ("portfolio_attempt", "selection", None, "STOP_REJECT"),
            ("test-02", "cultural"): ("execution", None, None, "STOP_ACCEPT"),
            ("test-03", "neighborhood"): ("portfolio_attempt", "materialization", "all_invocations_failed", "STOP_REJECT"),
            ("test-03", "gymnasium"): ("portfolio_attempt", "candidate_floor_context", None, "CONTINUE"),
            ("test-03", "cultural"): ("portfolio_attempt", "materialization", "all_invocations_failed", "STOP_REJECT"),
            ("test-04", "neighborhood"): ("portfolio_attempt", "materialization", "program_routing_empty", "STOP_REJECT"),
            ("test-04", "gymnasium"): ("portfolio_attempt", "candidate_floor_context", None, "CONTINUE"),
            ("test-04", "cultural"): ("portfolio_attempt", "materialization", "program_routing_empty", "STOP_REJECT"),
            ("test-05", "neighborhood"): ("execution", None, None, "STOP_ACCEPT"),
            ("test-05", "gymnasium"): ("portfolio_attempt", "preflight", None, "STOP_REJECT"),
            ("test-05", "cultural"): ("execution", None, None, "STOP_ACCEPT"),
        }
        observed = {}
        for (directory, program), expected_row in expected.items():
            path = ARR_ROOT / directory / "maas-book-programs-summary.json"
            pnu = ACTUAL_SOURCES[directory]
            packet, gold = packet_from_arr_artifacts(
                path,
                pnu=pnu,
                program=program,
                case_id=f"{directory}-{program}-native",
            )
            validation = validate_evidence_packet(packet)
            observed[(directory, program)] = (
                packet.subject_kind,
                packet.attempt_stage,
                packet.route_kind,
                gold.expected_decision,
            )
            self.assertEqual(gold.expected_decision, validation.expected_decision)
            self.assertEqual(gold.missing_evidence_codes, validation.missing_evidence_codes)
            if packet.subject_kind == "portfolio_attempt":
                self.assertIsNone(packet.execution_id)
                self.assertIsNone(packet.program_hash)
                self.assertIsNone(packet.geometry_hash)
                self.assertRegex(packet.attempt_id or "", r"^attempt:[0-9a-f]{64}$")
                manifest_text = json.dumps(
                    packet.to_dict()["evidence"][0]["evidence"], sort_keys=True
                )
                self.assertNotIn(pnu, manifest_text)
                self.assertNotIn(directory, manifest_text)
        self.assertEqual(observed, expected)

    def test_stage_classification_fails_closed_on_ambiguous_or_inconsistent_signatures(self) -> None:
        from iclr2027.arr_adapter import packet_from_arr_artifacts

        cases = (
            (
                "materialization count equation",
                "test-03",
                "neighborhood",
                lambda record: record["counts"].update(
                    terminal_materialization_failure_count=35
                ),
            ),
            (
                "materialization released candidate",
                "test-03",
                "neighborhood",
                lambda record: record["counts"]["capacity_stage_counts"].update(
                    qd_stream_candidates_released=1
                ),
            ),
            (
                "capacity admission retained row",
                "dev-467-law-restored",
                "neighborhood",
                lambda record: record["counts"]["capacity_selection_admission"].update(
                    retained_count=1
                ),
            ),
            (
                "capacity admission boolean retained count",
                "dev-467-law-restored",
                "neighborhood",
                lambda record: record["counts"]["capacity_selection_admission"].update(
                    retained_count=False
                ),
            ),
            (
                "capacity admission malformed exclusion",
                "dev-467-law-restored",
                "neighborhood",
                lambda record: record["counts"]["capacity_selection_admission"][
                    "exclusions"
                ][0].update(reason=""),
            ),
            (
                "program routing admits canonical row",
                "test-04",
                "neighborhood",
                lambda record: record["counts"]["program_selection_routing"].update(
                    canonical_hard_pass_count=1
                ),
            ),
            (
                "program routing boolean canonical count",
                "test-04",
                "neighborhood",
                lambda record: record["counts"]["program_selection_routing"].update(
                    canonical_hard_pass_count=False
                ),
            ),
            (
                "preflight embedded context mismatch",
                "dev-467-law-restored",
                "gymnasium",
                lambda record: record["counts"]["early_stop"][
                    "dimensional_evidence"
                ].update(effective_floors=1),
            ),
            (
                "preflight generation was attempted",
                "dev-467-law-restored",
                "gymnasium",
                lambda record: record["counts"]["early_stop"].update(
                    generation_attempted=True
                ),
            ),
            (
                "preflight boolean floor count",
                "dev-467-law-restored",
                "gymnasium",
                lambda record: record["program_dimensional_context"].update(
                    effective_floors=False
                ),
            ),
            (
                "candidate floor routing count",
                "test-03",
                "gymnasium",
                lambda record: record["counts"]["program_selection_routing"].update(
                    input_count=1
                ),
            ),
            (
                "candidate floor boolean routing count",
                "test-03",
                "gymnasium",
                lambda record: record["counts"]["program_selection_routing"].update(
                    input_count=False
                ),
            ),
            (
                "candidate floor aggregate mismatch",
                "test-03",
                "gymnasium",
                lambda record: record["counts"]["capacity_stage_counts"].update(
                    candidate_floor_context_failed=35
                ),
            ),
        )
        with tempfile.TemporaryDirectory() as tmp:
            for label, directory, program, mutate in cases:
                with self.subTest(label=label):
                    source = ARR_ROOT / directory / "maas-book-programs-summary.json"
                    payload = json.loads(source.read_text(encoding="utf-8"))
                    record = next(
                        item for item in payload["programs"] if item["slug"] == program
                    )
                    mutate(record)
                    path = Path(tmp) / f"{directory}-{program}.json"
                    path.write_text(json.dumps(payload), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        packet_from_arr_artifacts(
                            path,
                            pnu=ACTUAL_SOURCES[directory],
                            program=program,
                            case_id=f"{directory}-{program}-native",
                        )

    def test_zero_row_adapter_fails_closed_on_incomplete_or_mixed_attempt_identity(self) -> None:
        from iclr2027.arr_adapter import packet_from_arr_artifacts

        mutations = {
            "unsupported ledger schema": lambda p: p["programs"][0]["portfolio_evaluation"].update(schema_version="bad"),
            "truncated ledger": lambda p: p["programs"][0]["portfolio_evaluation"].update(records_truncated=True),
            "record count mismatch": lambda p: p["programs"][0]["portfolio_evaluation"].update(record_count=3),
            "missing run id": lambda p: p["programs"][0]["portfolio_evaluation"].update(run_id=""),
            "duplicate program hash": lambda p: p["programs"][0]["portfolio_evaluation"]["records"][1].update(program_hash="1".zfill(64)),
            "selected candidate": lambda p: p["programs"][0]["portfolio_evaluation"]["records"][0].update(selected=True),
            "final execution id": lambda p: p["programs"][0]["portfolio_evaluation"]["records"][0]["stages"]["geometry"]["evidence"]["execution_passport"].update(execution_id="must-not-exist"),
            "no evaluated attempts": lambda p: p["programs"][0]["mass_progress"].update(evaluated_count=0),
            "admitted downstream row": lambda p: p["programs"][0]["downstream_hard_gate"].update(candidate_count=1),
        }
        with tempfile.TemporaryDirectory() as tmp:
            for label, mutate in mutations.items():
                with self.subTest(label=label):
                    payload = _minimal_attempt_summary()
                    mutate(payload)
                    path = Path(tmp) / (label.replace(" ", "-") + ".json")
                    path.write_text(json.dumps(payload), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        packet_from_arr_artifacts(
                            path,
                            pnu="1168011800104170004",
                            program="gymnasium",
                            case_id="dev-417-gymnasium-native",
                        )

    def test_attempt_public_manifest_does_not_publish_private_failure_claims(self) -> None:
        from iclr2027.arr_adapter import packet_from_arr_artifacts
        from iclr2027.validators import validate_evidence_packet

        payload = _minimal_attempt_summary()
        candidate = payload["programs"][0]["portfolio_evaluation"]["records"][0]
        candidate["overall_status"] = "law_failed"
        candidate["stages"]["selection"]["reasons"] = ["law.projection_failed"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "private-reason.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            packet, _ = packet_from_arr_artifacts(
                path,
                pnu="1168011800104170004",
                program="gymnasium",
                case_id="dev-417-gymnasium-native",
            )

        public = json.dumps(packet.to_dict(), sort_keys=True)
        self.assertNotIn("law_failed", public)
        self.assertNotIn("law.projection_failed", public)
        self.assertEqual(
            validate_evidence_packet(packet).blocking_issue_codes,
            ("selection.no_admitted_candidate",),
        )

    def test_attempt_validator_requires_canonical_candidate_order(self) -> None:
        from iclr2027.arr_adapter import packet_from_arr_artifacts
        from iclr2027.io import sha256_json
        from iclr2027.schema import ArchitectureEvidencePacket
        from iclr2027.validators import validate_evidence_packet

        packet, _ = packet_from_arr_artifacts(
            PREEXECUTION_SUMMARY,
            pnu="1168011800104170004",
            program="gymnasium",
            case_id="dev-417-gymnasium-native",
        )
        payload = packet.to_dict()
        manifest = payload["evidence"][0]["evidence"]
        manifest["candidates"] = list(reversed(manifest["candidates"]))
        payload["attempt_hash"] = sha256_json(manifest)
        reordered = ArchitectureEvidencePacket.from_dict(payload)

        self.assertIn(
            "evidence.portfolio_attempt_incomplete",
            validate_evidence_packet(reordered).blocking_issue_codes,
        )

    def test_native_artifact_becomes_hash_bound_public_and_gold_pair(self) -> None:
        try:
            from iclr2027.arr_adapter import packet_from_arr_artifacts
        except (ImportError, ModuleNotFoundError) as exc:
            self.fail(f"ARR adapter module is missing: {exc}")

        packet, gold = packet_from_arr_artifacts(
            FIXTURE,
            pnu="1168011800104170004",
            program="neighborhood",
            case_id="dev-417-neighborhood-native",
        )

        self.assertEqual(packet.geometry_hash, "b" * 64)
        self.assertEqual(packet.program_hash, "a" * 64)
        self.assertEqual(packet.condition, "native")
        self.assertEqual(
            {item["evidence_id"] for item in packet.evidence},
            {
                "evidence:site_agent",
                "evidence:geometry_agent",
                "evidence:law_graph_agent",
                "evidence:parking_agent",
                "evidence:program_agent",
                "evidence:review_agent",
            },
        )
        self.assertEqual(gold.expected_decision, "STOP_ACCEPT")
        self.assertEqual(gold.blocking_issue_codes, ())

    def test_execution_row_rejects_unsupported_root_summary_schema(self) -> None:
        from iclr2027.arr_adapter import packet_from_arr_artifacts

        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["schema_version"] = "arr.maas.book_program_portfolios.unsupported"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "unsupported ARR summary schema"):
                packet_from_arr_artifacts(
                    path,
                    pnu="1168011800104170004",
                    program="neighborhood",
                    case_id="dev-417-neighborhood-native",
                )

    def test_adapter_rejects_passport_geometry_hash_mismatch(self) -> None:
        try:
            from iclr2027.arr_adapter import packet_from_arr_artifacts
        except (ImportError, ModuleNotFoundError) as exc:
            self.fail(f"ARR adapter module is missing: {exc}")

        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["programs"][0]["rows"][0]["mass_execution_passport"][
            "final_legal_geometry_hash"
        ] = "d" * 64

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "passport geometry hash mismatch"):
                packet_from_arr_artifacts(
                    path,
                    pnu="1168011800104170004",
                    program="neighborhood",
                    case_id="dev-417-neighborhood-native",
                )

    def test_adapter_prefers_independently_validated_row_over_stale_combined_pass(self) -> None:
        from iclr2027.arr_adapter import packet_from_arr_artifacts

        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        valid_row = payload["programs"][0]["rows"][0]
        valid_row["combined_hard_pass"] = False
        stale_row = copy.deepcopy(valid_row)
        stale_row.update(
            {
                "variant_id": "maas_02",
                "selected_execution_id": "book:neighborhood:maas_02",
                "score": 0.99,
                "combined_hard_pass": True,
            }
        )
        stale_row["law_graph_agent_evidence"]["identity"][
            "execution_id"
        ] = "book:neighborhood:maas_02"
        stale_row["candidate_finalization_evidence"].update(
            {"status": "failed", "hard_pass": False}
        )
        payload["programs"][0]["rows"].append(stale_row)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            packet, gold = packet_from_arr_artifacts(
                path,
                pnu="1168011800104170004",
                program="neighborhood",
                case_id="dev-417-neighborhood-native",
            )

        self.assertEqual(packet.execution_id, valid_row["selected_execution_id"])
        self.assertEqual(gold.expected_decision, "STOP_ACCEPT")

    def test_adapter_rejects_reported_parking_pass_when_counts_show_shortage(self) -> None:
        from iclr2027.arr_adapter import packet_from_arr_artifacts

        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        parking = payload["programs"][0]["rows"][0]["parking_hard_gate"]
        parking.update(
            {
                "evaluated": True,
                "hard_pass": True,
                "required_spaces": 3,
                "provided_spaces": 2,
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            _, gold = packet_from_arr_artifacts(
                path,
                pnu="1168011800104170004",
                program="neighborhood",
                case_id="dev-417-neighborhood-native",
            )

        self.assertEqual(gold.expected_decision, "STOP_REJECT")
        self.assertEqual(gold.blocking_issue_codes, ("parking.supply_shortage",))

    def test_adapter_rejects_parking_evidence_with_missing_counts(self) -> None:
        from iclr2027.arr_adapter import packet_from_arr_artifacts

        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        parking = payload["programs"][0]["rows"][0]["parking_hard_gate"]
        parking.pop("required_spaces", None)
        parking.pop("provided_spaces", None)
        parking.update({"evaluated": True, "hard_pass": True})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            _, gold = packet_from_arr_artifacts(
                path,
                pnu="1168011800104170004",
                program="neighborhood",
                case_id="dev-417-neighborhood-native",
            )

        self.assertEqual(gold.expected_decision, "STOP_REJECT")
        self.assertEqual(gold.blocking_issue_codes, ("parking.supply_shortage",))


if __name__ == "__main__":
    unittest.main()
