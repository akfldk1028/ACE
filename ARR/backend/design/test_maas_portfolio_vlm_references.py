import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase
from PIL import Image

from design.maas.paid_provider_budget import (
    configure_paid_provider_budget,
    reset_paid_provider_budget_for_tests,
)
from design.maas.preference import vlm_scorer
from design.maas.preference.vlm_scorer import (
    score_portfolio_board_with_openai_vlm,
)


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class PortfolioVlmReferenceTests(SimpleTestCase):
    def setUp(self):
        reset_paid_provider_budget_for_tests()
        configure_paid_provider_budget(1)

    def tearDown(self):
        reset_paid_provider_budget_for_tests()
        super().tearDown()

    def test_board_request_submits_two_exact_references_once(self):
        captured_requests = []
        parsed = {
            "portfolio_hard_pass": False,
            "visible_family_count": 3,
            "dominant_family_share": 0.667,
            "failure_reasons": ["box_dominated"],
            "repeated_family_groups": [],
            "candidate_actions": [
                {
                    "candidate_id": f"mass-{index}",
                    "decision": "replace",
                    "reasons": ["too_box_like"],
                }
                for index in range(1, 4)
            ],
            "required_next_relations": ["inhabited plate and public void"],
            "required_geometry_families": ["carve_void"],
            "rationale": "Three separate cards remain too box-like.",
        }

        def fake_urlopen(request, timeout):
            captured_requests.append({
                "body": json.loads(request.data.decode("utf-8")),
                "timeout": timeout,
            })
            return _Response({
                "id": "resp-portfolio-three",
                "output_text": json.dumps(parsed),
                "usage": {"input_tokens": 120, "output_tokens": 40, "total_tokens": 160},
            })

        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            board = root / "shortlist-3.png"
            reference_one = root / "reference-1.png"
            reference_two = root / "reference-2.png"
            Image.new("RGB", (300, 120), "white").save(board)
            Image.new("RGB", (80, 80), "red").save(reference_one)
            Image.new("RGB", (80, 80), "blue").save(reference_two)
            references = [
                {
                    "source": "archdaily",
                    "source_id": "reference-1",
                    "title": "Reference One",
                    "local_path": str(reference_one),
                    "selection_role": "counterfactual",
                },
                {
                    "source": "archdaily",
                    "source_id": "reference-2",
                    "title": "Reference Two",
                    "local_path": str(reference_two),
                    "selection_role": "counterfactual",
                },
            ]
            candidates = [
                {
                    "candidate_id": f"mass-{index}",
                    "program_hash": f"program-{index}",
                    "geometry_hash": f"geometry-{index}",
                }
                for index in range(1, 4)
            ]

            with (
                patch.dict(
                    "os.environ",
                    {
                        "OPENAI_API_KEY": "test-key",
                        "MAAS_PORTFOLIO_VLM_CACHE_DIR": str(root / "cache"),
                        "MAAS_PREFERENCE_VLM_REFERENCE_LIMIT": "2",
                    },
                    clear=False,
                ),
                patch.object(vlm_scorer, "_LIVE_VLM_REQUEST_COUNT", 0),
                patch(
                    "design.maas.preference.vlm_scorer.urllib.request.urlopen",
                    side_effect=fake_urlopen,
                ),
            ):
                result = score_portfolio_board_with_openai_vlm(
                    image_path=board,
                    program_context={"pnu": "1168011800104170004"},
                    candidate_summaries=candidates,
                    reference_matches=references,
                    model="test-model",
                    image_detail="high",
                    expected_candidate_count=3,
                )

        self.assertEqual(len(captured_requests), 1)
        content = captured_requests[0]["body"]["input"][1]["content"]
        images = [item for item in content if item["type"] == "input_image"]
        self.assertEqual(len(images), 3)
        self.assertEqual(images[0]["detail"], "high")
        self.assertEqual(images[1]["detail"], "low")
        self.assertEqual(images[2]["detail"], "low")
        prompt = content[0]["text"]
        self.assertIn("three separate candidate cards", prompt)
        self.assertNotIn("four-view candidate", prompt)
        self.assertEqual(result["response_id"], "resp-portfolio-three")
        self.assertEqual(result["expected_candidate_count"], 3)
        self.assertEqual(result["api_usage"]["total_tokens"], 160)
        self.assertEqual(result["vlm_image_inputs"]["reference_count"], 2)
        self.assertEqual(
            result["vlm_image_inputs"]["candidate_program_hashes"],
            ["program-1", "program-2", "program-3"],
        )
        self.assertEqual(
            result["vlm_image_inputs"]["candidate_geometry_hashes"],
            ["geometry-1", "geometry-2", "geometry-3"],
        )
        for reference in result["vlm_image_inputs"]["references"]:
            self.assertTrue(reference["used_by_vlm"])
            self.assertEqual(reference["response_id"], "resp-portfolio-three")
            self.assertTrue(reference["sha256"])
