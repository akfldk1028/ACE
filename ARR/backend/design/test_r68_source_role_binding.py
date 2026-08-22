from copy import deepcopy
from dataclasses import replace

from django.test import SimpleTestCase
from shapely.geometry import Polygon

from design.maas.geometry_language import base_seed_program
from design.maas.program_massing import program_seed_sequences
from design.maas.program_massing.semantic_carriers import (
    REQUIRED_RELATIONS,
    bind_source_role_scaffold_to_program,
)
from design.maas.source_geometry import compile_sequence_to_source_mass


class R68SourceRoleBindingTests(SimpleTestCase):
    def test_proven_book_section_band_descendant_binds_but_unrelated_role_rejects(self):
        site = Polygon(((0, 0), (42, 0), (42, 30), (0, 30)))
        seed = next(
            sequence
            for sequence in program_seed_sequences("neighborhood_living")
            if sequence.name == "program_neighborhood_active_bar"
        )
        source = compile_sequence_to_source_mass(site, seed)
        self.assertIsNotNone(source)
        assert source is not None
        graph = deepcopy(source.metadata["component_graph"])
        graph["name"] = (
            "program_neighborhood_active_bar__synth_1_4_0_"
            "llm_cut_corner_notch_274d09d141__book_combination_09_"
            "shift+shift__search_v5"
        )
        band_index = 0
        descendant_volumes = []
        for volume in source.volumes:
            if volume.role == "neighborhood_primary_active_bar":
                volume = replace(
                    volume,
                    role=(
                        "neighborhood_primary_active_bar__"
                        "program_section_band__book_shift_shift_"
                        f"{band_index}"
                    ),
                )
                band_index += 1
            descendant_volumes.append(volume)
        source = replace(
            source,
            volumes=tuple(descendant_volumes),
            metadata={**source.metadata, "component_graph": graph},
        )
        descendant_roles = tuple(
            volume.role
            for volume in source.volumes
            if "__program_section_band__book_" in volume.role
        )
        self.assertTrue(descendant_roles)

        failures = []
        bound = bind_source_role_scaffold_to_program(
            base_seed_program("slab"),
            source,
            program_id="neighborhood_living",
            failure_sink=failures,
        )
        self.assertIsNotNone(bound, failures)
        relations = {
            node.parameters["source_role_relation_binding"]["source_relation"]
            for node in bound.topological_nodes()
            if node.semantic_role == "source_role_relation_binding"
        }
        self.assertEqual(
            relations,
            set(REQUIRED_RELATIONS["neighborhood_living"]),
        )

        unrelated = replace(source, volumes=tuple(
            replace(
                volume,
                role="unrelated_role__program_section_band__book_shift_0",
            )
            if index == next(
                candidate_index
                for candidate_index, candidate in enumerate(source.volumes)
                if "__program_section_band__book_" in candidate.role
            )
            else volume
            for index, volume in enumerate(source.volumes)
        ))
        unrelated_failures = []
        self.assertIsNone(bind_source_role_scaffold_to_program(
            base_seed_program("slab"),
            unrelated,
            program_id="neighborhood_living",
            failure_sink=unrelated_failures,
        ))
        self.assertTrue(any(
            reason.startswith("untrusted_source_component_role:unrelated_role")
            for reason in unrelated_failures[-1]["scaffold_failures"]
        ))
