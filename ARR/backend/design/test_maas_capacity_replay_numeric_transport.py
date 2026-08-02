import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

from django.test import SimpleTestCase
from shapely.geometry import shape

from design.maas.geometry_language.book_adapter import (
    apply_book_projection_to_geometry_program,
)
from design.maas.geometry_language.compiler import compile_geometry_program
from design.maas.geometry_language.gate import (
    GeometryGatePolicy,
    compilation_gate,
)
from design.maas.geometry_language.source_bridge import (
    compile_geometry_program_to_source_mass,
    floorwise_source_to_geometry_program,
    materialize_floorwise_legal_source,
)
from design.maas.geometry_language.universal_form_bank import (
    universal_form_programs,
)
from design.maas.grammar.verb_sequence import VerbCall, VerbSequence
from design.maas.program_massing.book_projection import (
    book_sentence_variants,
    compose_program_with_book_operations,
)


class CapacityReplayNumericTransportTests(SimpleTestCase):
    def test_real_pnu_c2bb_three_floor_replay_repairs_only_proven_seam(self):
        workspace_root = Path(__file__).resolve().parents[3]
        summary = json.loads((
            workspace_root
            / "docs/mass/subagent-floorwise-zoverlap"
            / "maas-book-programs-summary.json"
        ).read_text(encoding="utf-8"))
        plan = summary["programs"][0]["floor_capacity_plan"]
        legal_sections = tuple(
            shape(payload)
            for payload in plan["legal_floor_sections"][:3]
        )
        targets = (97.436, 97.436, 70.986)
        base = next(
            program
            for program in universal_form_programs(1)
            if program.program_hash()
            == "c2bb537e47e2cc02b5a57e394449d92d"
               "dde63b2ccbcf75414c1d6863d5c03789"
        )
        operations = book_sentence_variants(
            ("notch",),
            count=12,
        )[5]
        sequence = compose_program_with_book_operations(
            VerbSequence(
                name=base.name,
                label="c2bb real-PNU 3F transport regression",
                calls=(VerbCall("base", {}),),
            ),
            operations,
            name_suffix="1_1_notch",
            base_volume_label="1/1",
        )
        program = apply_book_projection_to_geometry_program(
            base,
            sequence,
        )
        self.assertEqual(
            program.program_hash(),
            "a83b159dca13a7bea98395be1474bb9b"
            "31f2c5f6fe3a5fb1362b88cf9f867d14",
        )
        source = compile_geometry_program_to_source_mass(
            program,
            legal_sections[0],
            target_plan_area=targets[0],
            max_raw_surfaces=None,
        )
        self.assertIsNotNone(source)
        assert source is not None
        source = replace(
            source,
            metadata={
                **deepcopy(source.metadata),
                "candidate_floor_context": {
                    "height_m": 10.5,
                    "floors": 3,
                },
            },
        )
        materialized = materialize_floorwise_legal_source(
            source,
            legal_sections=legal_sections,
            target_plan_coverage=0.9,
            floor_capacity_plan_hash=plan[
                "floor_capacity_plan_hash"
            ],
            target_floor_areas_m2=targets,
        )
        self.assertIsNotNone(materialized)
        assert materialized is not None
        self.assertEqual(len(materialized.surfaces), 152)
        self.assertAlmostEqual(
            sum(
                float(volume.footprint.area)
                for volume in materialized.volumes
            ),
            265.858,
            places=3,
        )

        replay = floorwise_source_to_geometry_program(
            materialized,
            height_m=10.5,
        )
        raw = compile_geometry_program(
            replace(replay, execution_contract={})
        )
        self.assertEqual(
            [issue.code for issue in compilation_gate(
                raw,
                GeometryGatePolicy(maximum_components=1),
            )],
            ["tiny_edge"],
        )
        clean = compile_geometry_program(replay)
        self.assertEqual(
            compilation_gate(
                clean,
                GeometryGatePolicy(maximum_components=1),
            ),
            (),
        )
        self.assertEqual((len(clean.vertices), len(clean.triangles)), (61, 118))
        evidence = clean.metrics[
            "capacity_replay_numeric_transport"
        ]
        self.assertEqual(
            evidence["raw_gate_failure_codes"],
            ["tiny_edge"],
        )
        self.assertTrue(evidence["repair_attempted"])
        self.assertTrue(evidence["clean_gate_hard_pass"])
        self.assertEqual(evidence["clean_gate_failure_codes"], [])
        self.assertEqual(evidence["floor_center_section_count"], 3)
        self.assertEqual(len(evidence["floor_center_sections"]), 3)
        self.assertLessEqual(
            evidence["max_3d_displacement_m"],
            evidence["collapse_threshold_m"],
        )
        self.assertNotEqual(
            evidence["raw_indexed_mesh_hash"],
            evidence["clean_indexed_mesh_hash"],
        )
        passport = clean.to_dict(include_mesh=False)[
            "execution_passport"
        ]
        self.assertEqual(
            passport["capacity_replay_numeric_transport"],
            evidence,
        )

        invalid_contract = deepcopy(replay.execution_contract)
        invalid_contract["capacity_replay_numeric_transport"][
            "collapse_threshold_m"
        ] = 1e-6
        rejected = compile_geometry_program(replace(
            replay,
            execution_contract=invalid_contract,
        ))
        self.assertEqual(rejected.status, "invalid_program")
        self.assertIn(
            "invalid_execution_contract",
            {issue.code for issue in rejected.issues},
        )

    def test_capacity_replay_transport_never_collapses_vertical_edges(self):
        from design.maas.geometry_language.capacity_replay_numeric_transport import (
            _collapse_edges,
        )

        vertices = (
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 5e-9),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        )
        triangles = (
            (0, 2, 3),
            (1, 3, 2),
        )
        self.assertIsNone(_collapse_edges(
            vertices,
            triangles,
            maximum_length=1e-8,
        ))
