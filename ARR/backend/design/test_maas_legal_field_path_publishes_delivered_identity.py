"""The legal field affine route must publish the mesh it actually delivers.

`append_floorwise_legal_projection` certifies the *compiler's* mesh hash of the
finalized program, taken in the compiler frame. What the candidate delivers is
the `SourceMass` compiled from that program, whose identity is its surfaces
offset by the footprint centroid. Two identities of two different things.

Copying the compiler hash into `geometry_program_bridge_evidence` therefore
published a digest that could never match the surfaces it claimed to describe,
and nothing noticed until the final visual authority certificate - the first
place that recomputes the identity from the delivered surfaces - killed the
whole run twenty minutes later with a bare `final_geometry_hash`.
"""

from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from design.maas.book_language import candidate_generation
from design.maas.geometry_language import compile_geometry_program
from design.maas.geometry_language.projected_visual_contract import (
    final_floorwise_visual_geometry_hash,
)
from design.maas.geometry_language.source_bridge import (
    compile_site_bound_geometry_program_to_source_mass,
)
from design.test_maas_floorwise_candidate_rejection import _slab_fallback_case


class LegalFieldPathPublishesDeliveredIdentityTests(SimpleTestCase):
    def _delivered_mass(self, program, legal_section):
        delivered = compile_site_bound_geometry_program_to_source_mass(
            program,
            legal_section,
            name="delivered-legal-field-mass",
            floor_count=4,
        )
        self.assertIsNotNone(delivered)
        assert delivered is not None
        self.assertTrue(delivered.surfaces)
        return delivered

    def test_compiler_hash_is_not_the_delivered_mesh_identity(self):
        """The premise: the two hashes name different things, always."""

        _source, program, legal_section, _sequence, _context = (
            _slab_fallback_case()
        )
        delivered = self._delivered_mass(program, legal_section)

        self.assertNotEqual(
            str(compile_geometry_program(program).geometry_hash or ""),
            final_floorwise_visual_geometry_hash(delivered),
        )

    def test_legal_field_route_ignores_the_upstream_certificate_hash(self):
        source, program, legal_section, sequence, context = (
            _slab_fallback_case()
        )
        delivered = self._delivered_mass(program, legal_section)
        # A projection certificate carrying the compiler identity, exactly as
        # `append_floorwise_legal_projection` writes it.
        projection = SimpleNamespace(
            projection=SimpleNamespace(
                program=program,
                certificate={
                    "hard_pass": True,
                    "final_geometry_hash": str(
                        compile_geometry_program(program).geometry_hash or ""
                    ),
                    "achieved_floor_areas_m2": (180.0,) * 4,
                },
            ),
            evidence={},
        )
        failure_sink = []

        with (
            patch.object(
                candidate_generation,
                "_geometry_program_registry",
                return_value={"real-slab": program},
            ),
            patch.object(
                candidate_generation,
                "select_legal_field_affine_projection",
                return_value=projection,
            ),
            patch.object(
                candidate_generation,
                "compile_site_bound_geometry_program_to_source_mass",
                return_value=delivered,
            ),
        ):
            candidate_generation._materialize_directed_geometry(
                source,
                sequence,
                containment_host=legal_section,
                upper_containment_host=legal_section,
                floor_containment_hosts=(legal_section,) * 4,
                floor_capacity_plan_hash="contained-stack-plan",
                target_floor_areas_m2=(180.0,) * 4,
                terminal_failure_sink=failure_sink,
                **context,
            )

        # The candidate may still be rejected further downstream; what it may
        # not do is die on an identity it never published.
        self.assertNotIn(
            "final_identity_binding",
            [record.get("stage") for record in failure_sink],
        )


class LegalFloorFieldMustDeclareCoverageCapacityTests(SimpleTestCase):
    """A missing 건폐율 capacity used to mean "no bound", not "stop"."""

    def _materialize(self, *, legal_floor_field_hash, coverage_capacity_m2):
        source, _program, legal_section, sequence, context = (
            _slab_fallback_case()
        )
        failure_sink = []
        candidate_generation._materialize_directed_geometry(
            source,
            sequence,
            containment_host=legal_section,
            upper_containment_host=legal_section,
            floor_containment_hosts=(legal_section,) * 4,
            floor_capacity_plan_hash="contained-stack-plan",
            legal_floor_field_hash=legal_floor_field_hash,
            coverage_capacity_m2=coverage_capacity_m2,
            target_floor_areas_m2=(180.0,) * 4,
            terminal_failure_sink=failure_sink,
            **context,
        )
        return [record.get("stage") for record in failure_sink]

    def test_a_legal_field_without_a_capacity_stops_the_candidate(self):
        self.assertIn(
            "coverage_capacity",
            self._materialize(
                legal_floor_field_hash="legal-field-with-no-capacity",
                coverage_capacity_m2=0.0,
            ),
        )

    def test_a_declared_capacity_passes_this_gate(self):
        self.assertNotIn(
            "coverage_capacity",
            self._materialize(
                legal_floor_field_hash="legal-field-with-capacity",
                coverage_capacity_m2=499.938,
            ),
        )

    def test_candidates_with_no_legal_field_are_left_alone(self):
        """Context-fitted candidates have no capacity to be bounded by."""

        self.assertNotIn(
            "coverage_capacity",
            self._materialize(
                legal_floor_field_hash="",
                coverage_capacity_m2=0.0,
            ),
        )
