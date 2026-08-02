import json
from pathlib import Path
from tempfile import TemporaryDirectory
import urllib.error
from unittest.mock import patch

from django.test import SimpleTestCase
from PIL import Image

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
            {"geometry_author": 1},
        )

    def test_geometry_author_keeps_partial_valid_batch_when_repair_budget_ends(self):
        configure_paid_provider_budget(1)
        partial = base_seed_programs()[1]

        class _Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps({
                    "id": "resp-partial",
                    "output_text": json.dumps({"programs": []}),
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
            patch(
                "design.maas.geometry_language.llm_adapter."
                "geometry_programs_from_author_payload",
                return_value=(partial,),
            ),
            patch(
                "design.maas.geometry_language.llm_adapter."
                "_author_payload_compiler_diagnostics",
                return_value=[],
            ),
        ):
            programs = author_geometry_programs_with_openai(
                {"building_type": "neighborhood living"},
                target_count=2,
                model="test-model",
            )

        self.assertEqual(len(programs), 1)
        self.assertEqual(programs[0].name, partial.name)
        self.assertEqual(
            paid_provider_budget_snapshot()["request_counts_by_kind"],
            {"geometry_author": 1},
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
