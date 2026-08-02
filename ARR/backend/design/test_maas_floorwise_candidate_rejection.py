from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import box

from design.maas.book_language import candidate_generation
from design.maas.geometry_language import base_seed_program
from design.maas.grammar.component_graph import graph_from_sequence
from design.maas.grammar.verb_sequence import VerbSequence
from design.maas.program_massing import program_seed_sequences
from design.maas.program_massing.semantic_carriers import semantic_site_context_hash
from design.maas.source_geometry.ir import SourceMass, SourceVolume


def _slab_fallback_case():
    source_footprint = box(0.0, 0.0, 10.0, 10.0)
    source = SourceMass(
        name="source-placeholder",
        footprint=source_footprint,
        volumes=(
            SourceVolume(
                "gym_main_long_span_hall",
                source_footprint,
                0.0,
                1.0,
                "geometry_program",
            ),
            SourceVolume(
                "gym_service_spine",
                box(1.0, 4.0, 3.0, 6.0),
                0.0,
                0.5,
                "attach",
            ),
            SourceVolume(
                "gym_entry_canopy",
                box(7.0, 4.0, 8.5, 6.0),
                0.0,
                0.5,
                "attach",
            ),
        ),
        metadata={
            "component_graph": graph_from_sequence(
                program_seed_sequences("gymnasium")[0]
            ).to_dict(),
            "candidate_floor_context": {
                "height_m": 16.0,
                "floors": 4,
            },
        },
    )
    legal_section = box(-15.0, -10.0, 15.0, 10.0)
    program = base_seed_program("slab")
    sequence = VerbSequence(
        "real-slab",
        "real-slab",
        (),
        ("geometry_program_directive=real-slab",),
    )
    context = {
        "building_type": "gymnasium",
        "site_access_side": "south",
        "pnu": "1168011800104170004",
        "capacity_alternative_id": "balanced_yield",
        "capacity_measurement_hash": "pending_capacity_measurement",
        "site_context_hash": semantic_site_context_hash(
            pnu="1168011800104170004",
            building_type="gymnasium",
            site=legal_section,
        ),
    }
    return source, program, legal_section, sequence, context


class FloorwiseCandidateReplayRejectionTests(SimpleTestCase):
    def test_unreplayable_floor_volume_is_rejected_as_one_candidate(self):
        source, program, legal_section, sequence, context = _slab_fallback_case()

        with (
            patch.object(
                candidate_generation,
                "_geometry_program_registry",
                return_value={"real-slab": program},
            ),
            patch.object(
                candidate_generation,
                "select_legal_field_affine_projection",
                return_value=None,
            ),
            patch.object(
                candidate_generation,
                "_authored_projection_identity_evidence",
                return_value={"hard_pass": True},
            ),
            patch.object(
                candidate_generation,
                "floorwise_source_to_geometry_program",
                side_effect=ValueError(
                    "floorwise volume has no replayable footprint"
                ),
            ),
        ):
            materialized = candidate_generation._materialize_directed_geometry(
                source,
                sequence,
                containment_host=legal_section,
                upper_containment_host=legal_section,
                floor_containment_hosts=(
                    legal_section,
                    legal_section,
                    legal_section,
                    legal_section,
                ),
                floor_capacity_plan_hash="contained-stack-plan",
                target_floor_areas_m2=(180.0, 180.0, 180.0, 180.0),
                **context,
            )

        self.assertIsNone(materialized)

    def test_other_floorwise_replay_value_error_still_aborts(self):
        source, program, legal_section, sequence, context = _slab_fallback_case()

        with (
            patch.object(
                candidate_generation,
                "_geometry_program_registry",
                return_value={"real-slab": program},
            ),
            patch.object(
                candidate_generation,
                "select_legal_field_affine_projection",
                return_value=None,
            ),
            patch.object(
                candidate_generation,
                "_authored_projection_identity_evidence",
                return_value={"hard_pass": True},
            ),
            patch.object(
                candidate_generation,
                "floorwise_source_to_geometry_program",
                side_effect=ValueError(
                    "source has no materialized floorwise legal matrix stack"
                ),
            ),
        ):
            materialized = candidate_generation._materialize_directed_geometry(
                source,
                sequence,
                containment_host=legal_section,
                upper_containment_host=legal_section,
                floor_containment_hosts=(
                    legal_section,
                    legal_section,
                    legal_section,
                    legal_section,
                ),
                floor_capacity_plan_hash="contained-stack-plan",
                target_floor_areas_m2=(180.0, 180.0, 180.0, 180.0),
                **context,
            )

        self.assertIsNone(materialized)
