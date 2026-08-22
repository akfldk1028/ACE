import json
from pathlib import Path
from tempfile import TemporaryDirectory
import urllib.error
from unittest.mock import patch

from django.test import SimpleTestCase
from PIL import Image

from design.maas.geometry_language import llm_adapter
from design.maas.geometry_language.llm_adapter import (
    GeometryAuthorError,
    author_geometry_programs_with_openai,
)
from design.maas.geometry_language import base_seed_programs
from design.maas.preference import vlm_scorer
from design.maas.preference.vlm_scorer import (
    VlmScoringError,
    score_portfolio_board_with_openai_vlm,
)
from design.maas.paid_provider_budget import (
    PaidProviderBudgetError,
    configure_paid_provider_budget,
    paid_provider_budget_snapshot,
    reserve_paid_provider_request,
    reset_paid_provider_budget_for_tests,
)


def _structured_author_item(program, *, name: str, base_seed: str) -> dict:
    def parameter(name, value):
        if isinstance(value, bool):
            return {"name": name, "value_type": "boolean", "boolean_value": value}
        if isinstance(value, (int, float)):
            return {"name": name, "value_type": "number", "numeric_value": value}
        if isinstance(value, str):
            return {"name": name, "value_type": "string", "string_value": value}
        if isinstance(value, (list, tuple)) and all(
            isinstance(component, (int, float)) for component in value
        ):
            return {"name": name, "value_type": "vector", "vector_value": list(value)}
        return {
            "name": name,
            "value_type": "structured_json",
            "structured_json": json.dumps(value, sort_keys=True),
        }
    return {
        "name": name,
        "base_seed": base_seed,
        "intent_tags": [],
        "nodes": [{
            "id": node.id,
            "kind": node.kind,
            "operator": node.operator,
            "inputs": list(node.inputs),
            "parameters": [
                parameter(key, value)
                for key, value in sorted(node.parameters.items())
            ],
            "semantic_role": node.semantic_role,
        } for node in program.nodes],
        "root_id": program.root_id,
        "rationale": "structural test fixture",
    }


class PaidProviderBudgetTests(SimpleTestCase):
    def tearDown(self):
        reset_paid_provider_budget_for_tests()
        super().tearDown()

    def test_author_and_vlm_requests_share_one_hard_ceiling(self):
        configure_paid_provider_budget(3)

        reserve_paid_provider_request("geometry_author")
        reserve_paid_provider_request("final_pair_vlm")
        reserve_paid_provider_request("portfolio_vlm")

        self.assertEqual(
            paid_provider_budget_snapshot(),
            {
                "schema_version": "arr.maas.paid_provider_budget.v1",
                "limit": 3,
                "request_count": 3,
                "remaining_count": 0,
                "request_counts_by_kind": {
                    "final_pair_vlm": 1,
                    "geometry_author": 1,
                    "portfolio_vlm": 1,
                },
            },
        )
        with self.assertRaisesRegex(
            PaidProviderBudgetError,
            r"paid_provider_request_budget_exhausted:3/3",
        ):
            reserve_paid_provider_request("repair")

    def test_partitioned_quotas_cannot_steal_each_other(self):
        configure_paid_provider_budget(
            6,
            quotas={
                "author_initial": 1,
                "author_replenishment": 0,
                "base_candidate": 1,
                "exact_candidate": 1,
                "portfolio_board": 1,
                "reference_audit": 1,
                "retry": 1,
            },
        )

        reserve_paid_provider_request("geometry_author_initial")
        reserve_paid_provider_request("base_candidate_vlm")
        reserve_paid_provider_request("exact_candidate_vlm")
        reserve_paid_provider_request("reference_audit_vlm")
        reserve_paid_provider_request("retry")

        for kind, quota in (
            ("geometry_author_initial", "author_initial"),
            ("base_candidate_vlm", "base_candidate"),
            ("exact_candidate_vlm", "exact_candidate"),
            ("reference_audit_vlm", "reference_audit"),
            ("retry", "retry"),
        ):
            with self.assertRaisesRegex(
                PaidProviderBudgetError,
                rf"paid_provider_request_quota_exhausted:kind={kind}:quota={quota}",
            ):
                reserve_paid_provider_request(kind)

        reserve_paid_provider_request("portfolio_vlm")
        self.assertEqual(paid_provider_budget_snapshot()["remaining_count"], 0)

    def test_board_reserve_survives_exhausted_non_board_quotas(self):
        configure_paid_provider_budget(
            3,
            quotas={
                "author_initial": 1,
                "author_replenishment": 0,
                "base_candidate": 0,
                "exact_candidate": 1,
                "portfolio_board": 1,
                "reference_audit": 0,
                "retry": 0,
            },
        )

        reserve_paid_provider_request("geometry_author_initial")
        reserve_paid_provider_request("exact_candidate_vlm")
        with self.assertRaisesRegex(
            PaidProviderBudgetError,
            "quota=exact_candidate",
        ):
            reserve_paid_provider_request("exact_candidate_vlm")
        reserve_paid_provider_request("portfolio_vlm")

        snapshot = paid_provider_budget_snapshot()
        self.assertEqual(snapshot["quota_request_counts"]["portfolio_board"], 1)
        self.assertEqual(snapshot["remaining_count"], 0)

    def test_partitioned_mode_rejects_unclassified_callers_explicitly(self):
        configure_paid_provider_budget(
            1,
            quotas={
                "author_initial": 0,
                "author_replenishment": 0,
                "base_candidate": 0,
                "exact_candidate": 0,
                "portfolio_board": 1,
                "reference_audit": 0,
                "retry": 0,
            },
        )

        with self.assertRaisesRegex(
            PaidProviderBudgetError,
            "paid_provider_request_kind_unpartitioned:vlm",
        ):
            reserve_paid_provider_request("vlm")
        with self.assertRaisesRegex(
            PaidProviderBudgetError,
            "paid_provider_request_kind_unpartitioned:candidate_vlm",
        ):
            reserve_paid_provider_request("candidate_vlm")
        self.assertEqual(paid_provider_budget_snapshot()["request_count"], 0)

    def test_provider_errors_expose_stable_structured_fields(self):
        configure_paid_provider_budget(
            1,
            quotas={
                "author_initial": 0, "author_replenishment": 0,
                "base_candidate": 0, "exact_candidate": 1,
                "portfolio_board": 0, "reference_audit": 0, "retry": 0,
            },
        )
        reserve_paid_provider_request("exact_candidate_vlm")

        with self.assertRaises(PaidProviderBudgetError) as raised:
            reserve_paid_provider_request("exact_candidate_vlm")

        error = raised.exception
        self.assertEqual(error.code, "request_quota_exhausted")
        self.assertEqual(error.request_kind, "exact_candidate_vlm")
        self.assertEqual(error.quota, "exact_candidate")
        self.assertEqual((error.used, error.limit, error.remaining), (1, 1, 0))

    def test_vlm_budget_mapping_does_not_parse_provider_message(self):
        provider_error = PaidProviderBudgetError(
            "message format intentionally unrelated to fields",
            code="request_quota_exhausted",
            request_kind="base_candidate_vlm",
            quota="base_candidate",
            used=3,
            limit=3,
            remaining=0,
        )
        with (
            patch.object(vlm_scorer, "_LIVE_VLM_REQUEST_COUNT", 0),
            patch.object(
                vlm_scorer,
                "reserve_paid_provider_request",
                side_effect=provider_error,
            ),
        ):
            with self.assertRaises(vlm_scorer.VlmBudgetExhaustedError) as raised:
                vlm_scorer._consume_live_vlm_request_budget(
                    kind="base_candidate_vlm"
                )

        mapped = raised.exception
        self.assertEqual(mapped.budget_code, "request_quota_exhausted")
        self.assertEqual(mapped.request_kind, "base_candidate_vlm")
        self.assertEqual(mapped.quota, "base_candidate")
        self.assertEqual((mapped.used, mapped.limit, mapped.remaining), (3, 3, 0))

    def test_geometry_author_reserves_after_cache_miss_before_http(self):
        configure_paid_provider_budget(1)
        with (
            TemporaryDirectory() as cache_directory,
            patch.dict(
                "os.environ",
                {
                    "OPENAI_API_KEY": "test-key",
                    "MAAS_GEOMETRY_AUTHOR_CACHE_DIR": cache_directory,
                },
                clear=False,
            ),
            patch(
                "design.maas.geometry_language.llm_adapter."
                "urllib.request.urlopen",
                side_effect=urllib.error.URLError("offline"),
            ),
        ):
            with self.assertRaisesRegex(
                GeometryAuthorError,
                "geometry author request failed",
            ):
                author_geometry_programs_with_openai(
                    {"building_type": "neighborhood living"},
                    target_count=1,
                    model="test-model",
                )

        self.assertEqual(
            paid_provider_budget_snapshot()["request_counts_by_kind"],
            {"geometry_author_initial": 1},
        )

    def test_geometry_author_http_429_exposes_redacted_typed_diagnostics(self):
        configure_paid_provider_budget(1)
        provider_error = urllib.error.HTTPError(
            "https://api.openai.com/v1/responses?api_key=secret-query",
            429,
            "secret-provider-error-body",
            {"Retry-After": "17", "X-Request-Id": "secret-response-id"},
            None,
        )

        with (
            TemporaryDirectory() as cache_directory,
            patch.dict(
                "os.environ",
                {
                    "OPENAI_API_KEY": "secret-api-key",
                    "MAAS_GEOMETRY_AUTHOR_CACHE_DIR": cache_directory,
                },
                clear=False,
            ),
            patch(
                "design.maas.geometry_language.llm_adapter.urllib.request.urlopen",
                side_effect=provider_error,
            ),
        ):
            with self.assertRaises(GeometryAuthorError) as raised:
                author_geometry_programs_with_openai(
                    {"building_type": "neighborhood living"},
                    target_count=1,
                    model="test-model",
                )

        self.assertEqual(
            raised.exception.diagnostics,
            {
                "schema_version": "arr.maas.geometry_author_failure_diagnostics.v1",
                "provider_error": {
                    "category": "rate_limited",
                    "http_status": 429,
                    "retry_after_seconds": 17,
                },
            },
        )
        rendered = f"{raised.exception}:{raised.exception.diagnostics}"
        self.assertNotIn("secret-provider-error-body", rendered)
        self.assertNotIn("secret-api-key", rendered)
        self.assertNotIn("secret-response-id", rendered)
        self.assertNotIn("secret-query", rendered)

    def test_geometry_author_real_mixed_batch_reports_reconciled_exact_codes(self):
        configure_paid_provider_budget(1)
        authored = base_seed_programs()[0]
        inferred_seed = llm_adapter._infer_base_seed(authored)
        wrong_seed = next(
            spec.seed_id for spec in llm_adapter.BASE_SEED_SPECS
            if spec.seed_id != inferred_seed
        )
        payload = {"programs": [
            "secret-non-object-payload",
            _structured_author_item(
                authored, name="secret-invalid-name", base_seed=wrong_seed
            ),
            _structured_author_item(
                authored, name="accepted", base_seed=inferred_seed
            ),
            _structured_author_item(
                authored, name="accepted", base_seed=inferred_seed
            ),
        ]}

        class _Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps({
                    "id": "resp-invalid",
                    "output_text": json.dumps(payload),
                }).encode("utf-8")

        with (
            TemporaryDirectory() as cache_directory,
            patch.dict(
                "os.environ",
                {
                    "OPENAI_API_KEY": "test-key",
                    "MAAS_GEOMETRY_AUTHOR_CACHE_DIR": cache_directory,
                },
                clear=False,
            ),
            patch(
                "design.maas.geometry_language.llm_adapter.urllib.request.urlopen",
                return_value=_Response(),
            ),
            patch(
                "design.maas.geometry_language.llm_adapter.MAX_AUTHOR_COMPILER_REPAIR_GENERATIONS",
                0,
            ),
        ):
            programs = author_geometry_programs_with_openai(
                {"building_type": "neighborhood living"},
                target_count=4,
                model="test-model",
            )

        diagnostics = programs[0].metadata["author_failure_diagnostics"]
        self.assertEqual(
            diagnostics["batches"],
            [{
                "batch_role": "initial",
                "repair_generation": 0,
                "raw_program_count": 4,
                "valid_program_count": 1,
                "rejected_program_count": 3,
                "rejection_category_counts": {
                    "compiler_or_gate": 1,
                    "duplicate": 1,
                    "schema": 1,
                },
                "rejection_code_counts": {
                    "declared_base_seed_mismatch": 1,
                    "duplicate_program": 1,
                    "non_object_program": 1,
                },
            }],
        )
        batch = diagnostics["batches"][0]
        self.assertEqual(
            sum(batch["rejection_category_counts"].values()),
            batch["rejected_program_count"],
        )
        rendered = json.dumps(diagnostics, sort_keys=True)
        self.assertNotIn("secret-non-object-payload", rendered)
        self.assertNotIn("secret-invalid-name", rendered)

    def test_geometry_author_recursive_zero_yield_keeps_each_batch_and_secondary_cause(self):
        configure_paid_provider_budget(2)
        payload = {"programs": [
            "secret-first-raw-value",
            {"name": "secret-broken-name", "dsl": "not executable AST"},
        ]}

        class _Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps({
                    "id": "secret-provider-response-id",
                    "output_text": json.dumps(payload),
                }).encode("utf-8")

        with (
            TemporaryDirectory() as cache_directory,
            patch.dict(
                "os.environ",
                {
                    "OPENAI_API_KEY": "secret-api-key",
                    "MAAS_GEOMETRY_AUTHOR_CACHE_DIR": cache_directory,
                },
                clear=False,
            ),
            patch(
                "design.maas.geometry_language.llm_adapter.urllib.request.urlopen",
                side_effect=[_Response(), _Response()],
            ),
        ):
            with self.assertRaises(GeometryAuthorError) as raised:
                author_geometry_programs_with_openai(
                    {"building_type": "neighborhood living"},
                    target_count=2,
                    model="test-model",
                )

        diagnostics = raised.exception.diagnostics
        self.assertEqual(
            [(batch["repair_generation"], batch["raw_program_count"], batch["valid_program_count"])
             for batch in diagnostics["batches"]],
            [(0, 2, 0), (1, 2, 0)],
        )
        repair_failure = diagnostics["secondary_failures"][0]
        self.assertEqual(repair_failure["category"], "repair_author_failure")
        self.assertEqual(
            repair_failure["diagnostics"]["secondary_failures"][0]["category"],
            "retry_budget",
        )
        rendered = json.dumps(diagnostics, sort_keys=True)
        for secret in (
            "secret-first-raw-value",
            "secret-broken-name",
            "secret-provider-response-id",
            "secret-api-key",
            "not executable AST",
        ):
            self.assertNotIn(secret, rendered)

    def test_geometry_author_partial_initial_preserves_repair_http_failure(self):
        configure_paid_provider_budget(2)
        partial = base_seed_programs()[1]
        inferred_seed = llm_adapter._infer_base_seed(partial)
        wrong_seed = next(
            spec.seed_id for spec in llm_adapter.BASE_SEED_SPECS
            if spec.seed_id != inferred_seed
        )
        payload = {"programs": [
            "not-an-object",
            _structured_author_item(
                partial, name="wrong-seed", base_seed=wrong_seed
            ),
            _structured_author_item(
                partial, name="partial", base_seed=inferred_seed
            ),
            _structured_author_item(
                partial, name="partial", base_seed=inferred_seed
            ),
        ]}

        class _Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps({
                    "id": "initial-response",
                    "output_text": json.dumps(payload),
                }).encode("utf-8")

        repair_error = urllib.error.HTTPError(
            "https://api.openai.com/v1/responses?secret=query",
            429,
            "secret-repair-body",
            {"Retry-After": "19", "X-Request-Id": "secret-id"},
            None,
        )
        with (
            TemporaryDirectory() as cache_directory,
            patch.dict(
                "os.environ",
                {
                    "OPENAI_API_KEY": "secret-api-key",
                    "MAAS_GEOMETRY_AUTHOR_CACHE_DIR": cache_directory,
                },
                clear=False,
            ),
            patch(
                "design.maas.geometry_language.llm_adapter.urllib.request.urlopen",
                side_effect=[_Response(), repair_error],
            ) as urlopen,
        ):
            programs = author_geometry_programs_with_openai(
                {"building_type": "neighborhood living"},
                target_count=4,
                model="test-model",
            )

        diagnostics = programs[0].metadata["author_failure_diagnostics"]
        self.assertEqual(urlopen.call_count, 2)
        self.assertEqual(len(programs), 1)
        self.assertEqual(len(diagnostics["batches"]), 1)
        repair_failure = diagnostics["secondary_failures"][0]
        self.assertEqual(repair_failure["category"], "repair_author_failure")
        self.assertEqual(
            repair_failure["diagnostics"]["provider_error"],
            {
                "category": "rate_limited",
                "http_status": 429,
                "retry_after_seconds": 19,
            },
        )
        rendered = json.dumps(diagnostics, sort_keys=True)
        for secret in (
            "secret-repair-body", "secret-api-key", "secret-id", "query",
        ):
            self.assertNotIn(secret, rendered)

    def test_geometry_author_keeps_partial_valid_batch_when_repair_budget_ends(self):
        configure_paid_provider_budget(1)
        partial = base_seed_programs()[1]
        inferred_seed = llm_adapter._infer_base_seed(partial)
        wrong_seed = next(
            spec.seed_id for spec in llm_adapter.BASE_SEED_SPECS
            if spec.seed_id != inferred_seed
        )
        payload = {"programs": [
            "not-an-object",
            _structured_author_item(
                partial, name="wrong-seed", base_seed=wrong_seed
            ),
            _structured_author_item(
                partial, name="partial", base_seed=inferred_seed
            ),
            _structured_author_item(
                partial, name="partial", base_seed=inferred_seed
            ),
        ]}

        class _Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps({
                    "id": "resp-partial",
                    "output_text": json.dumps(payload),
                }).encode("utf-8")

        with (
            TemporaryDirectory() as cache_directory,
            patch.dict(
                "os.environ",
                {
                    "OPENAI_API_KEY": "test-key",
                    "MAAS_GEOMETRY_AUTHOR_CACHE_DIR": cache_directory,
                },
                clear=False,
            ),
            patch(
                "design.maas.geometry_language.llm_adapter."
                "urllib.request.urlopen",
                return_value=_Response(),
            ),
        ):
            programs = author_geometry_programs_with_openai(
                {"building_type": "neighborhood living"},
                target_count=4,
                model="test-model",
            )

        self.assertEqual(len(programs), 1)
        self.assertEqual(programs[0].name, "partial")
        self.assertEqual(
            paid_provider_budget_snapshot()["request_counts_by_kind"],
            {"geometry_author_initial": 1},
        )
        self.assertEqual(
            programs[0].metadata["author_failure_diagnostics"],
            {
                "schema_version": "arr.maas.geometry_author_failure_diagnostics.v1",
                "batches": [{
                    "batch_role": "initial",
                    "repair_generation": 0,
                    "raw_program_count": 4,
                    "valid_program_count": 1,
                    "rejected_program_count": 3,
                    "rejection_category_counts": {
                        "compiler_or_gate": 1,
                        "duplicate": 1,
                        "schema": 1,
                    },
                    "rejection_code_counts": {
                        "declared_base_seed_mismatch": 1,
                        "duplicate_program": 1,
                        "non_object_program": 1,
                    },
                }],
                "secondary_failures": [{
                    "category": "retry_budget",
                    "code": "total_budget_exhausted",
                    "used": 1,
                    "limit": 1,
                    "remaining": 0,
                }],
            },
        )

    def test_geometry_author_revalidates_kernel_unavailable_rejection_without_http(self):
        configure_paid_provider_budget(1)
        with TemporaryDirectory() as cache_directory:
            cache_path = Path(cache_directory) / "author.json"
            rejected_path = cache_path.with_suffix(".rejected.json")
            rejected_path.write_text(
                json.dumps(
                    {
                        "cache_schema_version": "arr.maas.geometry_llm_author_cache.v3",
                        "validation_status": "rejected",
                        "model": "test-model",
                        "response_id": "resp_existing",
                        "payload": {
                            "programs": [
                                {
                                    "name": "cached_box",
                                    "dsl": "mass result = box(10, 8, 6)",
                                }
                            ]
                        },
                        "compiler_repair_feedback": [
                            {
                                "candidate_name": "cached_box",
                                "compile_status": "kernel_unavailable",
                                "issues": [
                                    {
                                        "code": "kernel_unavailable",
                                        "message": "manifold3d>=3.4 is required",
                                        "node_id": "",
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with (
                patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=False),
                patch(
                    "design.maas.geometry_language.llm_adapter._author_cache_path",
                    return_value=cache_path,
                ),
                patch(
                    "design.maas.geometry_language.llm_adapter.urllib.request.urlopen"
                ) as urlopen,
            ):
                programs = author_geometry_programs_with_openai(
                    {},
                    target_count=1,
                    model="test-model",
                )

        self.assertEqual(len(programs), 1)
        self.assertEqual(programs[0].name, "cached_box")
        self.assertTrue(programs[0].metadata["author_cache_hit"])
        urlopen.assert_not_called()
        self.assertEqual(paid_provider_budget_snapshot()["request_count"], 0)

    def test_vlm_transport_consumes_the_same_shared_budget(self):
        configure_paid_provider_budget(1)

        with patch.object(vlm_scorer, "_LIVE_VLM_REQUEST_COUNT", 0):
            self.assertEqual(
                vlm_scorer._consume_live_vlm_request_budget(),
                1,
            )
            self.assertEqual(
                paid_provider_budget_snapshot()["request_counts_by_kind"],
                {"vlm": 1},
            )
            with self.assertRaisesRegex(
                vlm_scorer.VlmScoringError,
                r"paid_provider_request_budget_exhausted:1/1",
            ):
                vlm_scorer._consume_live_vlm_request_budget()

    def test_vlm_transport_records_the_request_kind(self):
        configure_paid_provider_budget(1)

        with patch.object(vlm_scorer, "_LIVE_VLM_REQUEST_COUNT", 0):
            vlm_scorer._consume_live_vlm_request_budget(
                kind="portfolio_vlm"
            )

        self.assertEqual(
            paid_provider_budget_snapshot()["request_counts_by_kind"],
            {"portfolio_vlm": 1},
        )

    def test_portfolio_vlm_transport_records_portfolio_kind(self):
        configure_paid_provider_budget(1)
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            board = root / "board.png"
            Image.new("RGB", (64, 64), "white").save(board)
            with (
                patch.dict(
                    "os.environ",
                    {
                        "OPENAI_API_KEY": "test-key",
                        "MAAS_PORTFOLIO_VLM_CACHE_DIR": str(root / "cache"),
                    },
                    clear=False,
                ),
                patch.object(vlm_scorer, "_LIVE_VLM_REQUEST_COUNT", 0),
                patch(
                    "design.maas.preference.vlm_scorer."
                    "urllib.request.urlopen",
                    side_effect=urllib.error.URLError("offline"),
                ),
            ):
                with self.assertRaisesRegex(
                    VlmScoringError,
                    "OpenAI portfolio VLM response failed",
                ):
                    score_portfolio_board_with_openai_vlm(
                        image_path=board,
                        program_context={},
                        candidate_summaries=[],
                        model="test-model",
                    )

        self.assertEqual(
            paid_provider_budget_snapshot()["request_counts_by_kind"],
            {"portfolio_vlm": 1},
        )
