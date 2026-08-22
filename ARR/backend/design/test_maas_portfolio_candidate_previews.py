from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from design.maas.book_language.portfolio_candidate_previews import (
    render_candidate_preview_assets,
)


class PortfolioCandidatePreviewTests(SimpleTestCase):
    def test_each_identity_gets_its_own_run_relative_png(self):
        calls = []

        def renderer(features, path, *, title):
            calls.append((features, path, title))
            path.write_bytes(b"\x89PNG\r\n\x1a\n")

        with TemporaryDirectory() as temporary:
            paths = render_candidate_preview_assets(
                [("a" * 64, {"id": 1}), ("b" * 64, {"id": 2})],
                output_dir=Path(temporary),
                program_slug="neighborhood",
                renderer=renderer,
            )

        self.assertEqual(len(calls), 2)
        self.assertEqual(
            paths["a" * 64],
            "candidate-renders/neighborhood-001-aaaaaaaaaaaaaaaa.png",
        )
        self.assertNotEqual(paths["a" * 64], paths["b" * 64])

    def test_duplicate_identity_never_borrows_a_second_feature(self):
        calls = []

        def renderer(features, path, *, title):
            calls.append(features)
            path.write_bytes(b"\x89PNG\r\n\x1a\n")

        with TemporaryDirectory() as temporary:
            paths = render_candidate_preview_assets(
                [("same", {"id": 1}), ("same", {"id": 2})],
                output_dir=Path(temporary),
                program_slug="library",
                renderer=renderer,
            )

        self.assertEqual(len(calls), 1)
        self.assertEqual(paths.keys(), {"same"})

    def test_uncertified_authored_visual_is_excluded_without_hiding_rejection(self):
        exclusions = []

        def renderer(features, path, *, title):
            raise ValueError(
                "authored profiled visual mesh requires certified nonempty "
                "projection: schema=None:status=None"
            )

        with TemporaryDirectory() as temporary:
            paths = render_candidate_preview_assets(
                [("rejected", {"type": "Feature"})],
                output_dir=Path(temporary),
                program_slug="library",
                renderer=renderer,
                exclusion_sink=exclusions,
            )

        self.assertEqual(paths, {})
        self.assertEqual(
            exclusions,
            [{
                "program_hash": "rejected",
                "reason": "uncertified_authored_visual_projection",
            }],
        )

    def test_unrelated_renderer_error_remains_fatal(self):
        def renderer(features, path, *, title):
            raise ValueError("renderer configuration is broken")

        with TemporaryDirectory() as temporary:
            with self.assertRaisesMessage(
                ValueError,
                "renderer configuration is broken",
            ):
                render_candidate_preview_assets(
                    [("candidate", {"type": "Feature"})],
                    output_dir=Path(temporary),
                    program_slug="library",
                    renderer=renderer,
                )
