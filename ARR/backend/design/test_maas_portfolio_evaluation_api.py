from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from PIL import Image

from design.maas.portfolio_evaluation_catalog import (
    portfolio_evaluation_manifest,
)
from design.views import _portfolio_evaluation_root


def evaluation_record(
    *,
    candidate_id: str = "book:operative:bend",
    geometry_hash: str = "a" * 64,
    preview_path: str = "renders/book-bend.png",
) -> dict:
    return {
        "schema_version": "arr.maas.candidate_evaluation.v1",
        "candidate_id": candidate_id,
        "program_hash": "b" * 64,
        "geometry_hash": geometry_hash,
        "overall_status": "legal_pass",
        "selected": False,
        "integrity_failures": [],
        "terminal_reasons": [],
        "preview_path": preview_path,
        "lineage": {
            "book_principle_id": "book:operative:bend",
            "book_scope": "3/8",
        },
        "finalized": True,
        "stages": {
            stage: {
                "stage": stage,
                "status": "pass",
                "reasons": [],
                "evidence": {},
            }
            for stage in (
                "geometry", "law", "capacity", "parking", "program"
            )
        } | {
            "vlm": {
                "stage": "vlm",
                "status": "not_evaluated",
                "reasons": [],
                "evidence": {
                    "vlm_image_inputs": {
                        "candidate": {"geometry_hash": geometry_hash},
                    },
                },
            },
            "selection": {
                "stage": "selection",
                "status": "not_evaluated",
                "reasons": [],
                "evidence": {},
            },
        },
    }


def write_run(root: Path, run_id: str, record: dict) -> Path:
    run = root / run_id
    (run / "renders").mkdir(parents=True)
    preview = run / "renders" / "book-bend.png"
    Image.new("RGB", (24, 24), "#b87322").save(preview)
    payload = {
        "schema_version": "arr.maas.portfolio_evaluation_manifest.v1",
        "pnu": "1168011800104170004",
        "programs": [{
            "schema_version": "arr.maas.portfolio_evaluation_ledger.v1",
            "run_id": run_id,
            "program_slug": "neighborhood",
            "pnu": "1168011800104170004",
            "target_count": 20,
            "record_count": 1,
            "records": [record],
            "records_truncated": False,
        }],
    }
    (run / "maas-portfolio-evaluation.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    return run


class PortfolioEvaluationCatalogTests(SimpleTestCase):
    def test_default_catalog_selects_most_recent_evaluation_file(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            older = write_run(root, "z-older", evaluation_record())
            newer = write_run(root, "a-newer", evaluation_record())
            os.utime(
                older / "maas-portfolio-evaluation.json",
                ns=(1_000_000_000, 1_000_000_000),
            )
            os.utime(
                newer / "maas-portfolio-evaluation.json",
                ns=(2_000_000_000, 2_000_000_000),
            )

            manifest = portfolio_evaluation_manifest(root)

        self.assertEqual(manifest["run_id"], "a-newer")

    def test_catalog_returns_failed_and_passing_records_with_preview_urls(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_run(root, "run-01", evaluation_record())

            manifest = portfolio_evaluation_manifest(root, "run-01")

        self.assertEqual(
            manifest["schema_version"],
            "arr.maas.portfolio_evaluation_manifest.v1",
        )
        self.assertEqual(manifest["candidate_count"], 1)
        self.assertEqual(manifest["status_counts"], {"legal_pass": 1})
        self.assertEqual(
            manifest["candidates"][0]["preview_url"],
            "/design/maas/portfolio-evaluations/run-01/"
            "candidates/book%3Aoperative%3Abend/render/",
        )

    def test_missing_preview_is_retained_without_borrowed_image(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            record = evaluation_record(preview_path="")
            write_run(root, "run-no-preview", record)

            manifest = portfolio_evaluation_manifest(root, "run-no-preview")

        self.assertEqual(manifest["candidate_count"], 1)
        self.assertEqual(manifest["candidates"][0]["preview_url"], "")

    def test_geometry_hash_mismatch_downgrades_to_failed(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            record = evaluation_record(geometry_hash="c" * 64)
            record["stages"]["vlm"]["evidence"]["vlm_image_inputs"][
                "candidate"
            ]["geometry_hash"] = "d" * 64
            write_run(root, "run-mismatch", record)

            manifest = portfolio_evaluation_manifest(root, "run-mismatch")

        candidate = manifest["candidates"][0]
        self.assertEqual(candidate["overall_status"], "failed")
        self.assertIn(
            "geometry_hash_mismatch",
            candidate["integrity_failures"],
        )

    def test_invalid_run_id_cannot_escape_catalog_root(self):
        with TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "invalid evaluation run ID"):
                portfolio_evaluation_manifest(temporary, "../escape")


class PortfolioEvaluationApiTests(SimpleTestCase):
    def test_default_root_is_inside_repository_docs_directory(self):
        repository = Path("D:/workspace/ARR")
        with override_settings(
            BASE_DIR=repository / "backend",
            MAAS_PORTFOLIO_EVALUATION_ROOT="",
        ):
            root = _portfolio_evaluation_root()

        self.assertEqual(
            root,
            repository / "docs/playwright/design-route-live-verify",
        )

    def test_api_and_render_endpoint_serve_validated_run(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_run(root, "api-run", evaluation_record())
            with override_settings(MAAS_PORTFOLIO_EVALUATION_ROOT=str(root)):
                response = self.client.get(
                    reverse("design:maas_portfolio_evaluations"),
                    {"run_id": "api-run"},
                )
                render = self.client.get(reverse(
                    "design:maas_portfolio_evaluation_render",
                    kwargs={
                        "run_id": "api-run",
                        "candidate_id": "book:operative:bend",
                    },
                ))
                render_body = b"".join(render.streaming_content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["candidate_count"], 1)
        self.assertEqual(render.status_code, 200)
        self.assertEqual(render["Content-Type"], "image/png")
        self.assertTrue(render_body.startswith(b"\x89PNG"))
