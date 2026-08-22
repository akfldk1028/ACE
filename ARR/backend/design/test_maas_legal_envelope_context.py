from django.test import SimpleTestCase
from shapely.geometry import Polygon, box, mapping

from design.maas.geometry_language.legal_envelope import (
    SCHEMA_VERSION,
    normalized_legal_field_design_context,
)


def _contract(sections):
    return {
        "candidate_legal_floor_sections": [mapping(s) for s in sections]
    }


class LegalEnvelopeDesignContextTests(SimpleTestCase):
    """The lawful field must reach form decisions as relations, never coordinates."""

    def test_contracting_field_is_reported_as_band_relations(self):
        sections = [box(0, 0, 12, 8), box(0, 0, 12, 6), box(0, 0, 12, 4)]

        context = normalized_legal_field_design_context(_contract(sections))

        self.assertEqual(context["schema_version"], SCHEMA_VERSION)
        self.assertEqual(context["floor_band_count"], 3)
        self.assertEqual(context["ground_long_to_short_aspect"], 1.5)
        self.assertEqual(
            [band["area_ratio_to_ground"] for band in context["bands"]],
            [1.0, 0.75, 0.5],
        )

    def test_no_parcel_coordinates_survive_into_the_context(self):
        # Same shape, far from the origin: the payload must be identical.
        near = [box(0, 0, 12, 8), box(0, 0, 12, 6)]
        far = [
            box(321000, 552000, 321012, 552008),
            box(321000, 552000, 321012, 552006),
        ]

        self.assertEqual(
            normalized_legal_field_design_context(_contract(near)),
            normalized_legal_field_design_context(_contract(far)),
        )
        self.assertIs(
            normalized_legal_field_design_context(
                _contract(far)
            )["absolute_parcel_coordinates_included"],
            False,
        )

    def test_rotated_parcel_is_normalized_into_the_principal_frame(self):
        upright = [box(0, 0, 12, 8), box(0, 0, 12, 6)]
        rotated = [
            Polygon(((0, 0), (8, 0), (8, 12), (0, 12))),
            Polygon(((2, 0), (8, 0), (8, 12), (2, 12))),
        ]

        self.assertEqual(
            normalized_legal_field_design_context(_contract(upright))[
                "ground_long_to_short_aspect"
            ],
            normalized_legal_field_design_context(_contract(rotated))[
                "ground_long_to_short_aspect"
            ],
        )

    def test_missing_or_degenerate_field_returns_one_empty_result(self):
        for contract in (
            {},
            {"candidate_legal_floor_sections": []},
            {"candidate_legal_floor_sections": [{"type": "Point", "coordinates": [0, 0]}]},
            {"candidate_legal_floor_sections": ["not-a-geometry"]},
            {"legal_floor_field": {"legal_floor_sections": []}},
        ):
            with self.subTest(contract=contract):
                self.assertEqual(
                    normalized_legal_field_design_context(contract),
                    {},
                )

    def test_nested_legal_floor_field_is_read_when_candidate_key_is_absent(self):
        sections = [box(0, 0, 12, 8), box(0, 0, 12, 6)]

        context = normalized_legal_field_design_context({
            "legal_floor_field": {
                "legal_floor_sections": [mapping(s) for s in sections]
            }
        })

        self.assertEqual(context["floor_band_count"], 2)

    def test_context_declares_itself_as_constraint_not_recipe(self):
        context = normalized_legal_field_design_context(
            _contract([box(0, 0, 12, 8)])
        )

        self.assertEqual(
            context["authority"],
            "constraint_context_only_not_morphology_recipe",
        )
        self.assertIn("never replay band boundaries", context["authorship_instruction"])
