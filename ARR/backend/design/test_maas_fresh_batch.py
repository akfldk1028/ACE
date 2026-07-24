from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import SimpleTestCase

from design.maas.agents.orchestrator.execution_collaboration import SPECIALIST_SEQUENCE
from design.maas.agents.shared.types import AgentEvidence
from design.maas.fresh_family_contracts import (
    build_family_contract_program,
    family_phenotype_issues,
)
from design.maas.fresh_batch import fresh_mass_specs, generate_fresh_mass_batch
from design.maas.geometry_language import compile_geometry_program


class FreshMassBatchTests(SimpleTestCase):
    def test_radial_family_contract_uses_one_unitbox_common_hub_and_radial_array(self):
        spec = next(
            item for item in fresh_mass_specs()
            if item.spec_id == "radial-cross"
        )

        program = build_family_contract_program(spec, variation_offset=317)

        self.assertIsNotNone(program)
        assert program is not None
        operators = [node.operator for node in program.topological_nodes()]
        self.assertEqual(operators.count("box"), 1)
        self.assertIn("radial_array", operators)
        self.assertIn("union", operators)
        self.assertNotIn("bend", operators)
        self.assertEqual(family_phenotype_issues(program, spec), ())

    def test_radial_family_contract_compiles_as_one_connected_manifold(self):
        spec = next(
            item for item in fresh_mass_specs()
            if item.spec_id == "radial-cross"
        )
        program = build_family_contract_program(spec, variation_offset=319)
        assert program is not None

        compilation = compile_geometry_program(program)

        self.assertEqual(compilation.status, "compiled")
        self.assertEqual(compilation.metrics["component_count"], 1)
        self.assertTrue(compilation.metrics["watertight"])
        self.assertTrue(compilation.metrics["manifold"])
        self.assertEqual(
            family_phenotype_issues(
                program,
                spec,
                compilation=compilation,
            ),
            (),
        )

    def test_fresh_mass_specs_cover_ten_distinct_architectural_relations(self):
        specs = fresh_mass_specs()

        self.assertEqual(len(specs), 10)
        self.assertEqual(len({item.family for item in specs}), 10)
        self.assertEqual(len({item.book_verbs for item in specs}), 10)
        self.assertTrue(all(item.scope_label == "1/1" for item in specs))
        self.assertTrue(all(item.intent_tags for item in specs))
        self.assertTrue(all(item.base_seeds for item in specs))

    def test_batch_accepts_ten_unique_geometry_hashes_before_image_generation(self):
        with TemporaryDirectory() as temporary:
            result = generate_fresh_mass_batch(
                temporary,
                batch_id="batch-test",
                building_type="neighborhood living",
                count=10,
                collaboration_executors=self._fast_collaboration_executors(),
            )

        self.assertEqual(result["accepted_count"], 10, result)
        self.assertEqual(len(set(result["program_hashes"])), 10)
        self.assertEqual(len(set(result["geometry_hashes"])), 10)
        self.assertEqual(result["paid_image_request_count"], 0)
        self.assertTrue(all(row["execution_mode"] == "fresh_synthesis" for row in result["executions"]))
        self.assertTrue(all(row["geometry_ready"] for row in result["executions"]))

    def test_batch_routes_radial_spec_through_focused_family_contract(self):
        with TemporaryDirectory() as temporary:
            result = generate_fresh_mass_batch(
                temporary,
                batch_id="radial-contract-batch",
                building_type="generic architectural form study",
                count=3,
                collaboration_executors=self._fast_collaboration_executors(),
            )
            radial = result["executions"][2]
            program_path = Path(temporary) / radial["execution_id"] / "program.json"
            program = json.loads(program_path.read_text(encoding="utf-8"))

        operators = [node["operator"] for node in program["nodes"]]
        self.assertEqual(radial["spec_id"], "radial-cross")
        self.assertIn("radial_array", operators)
        self.assertIn("union", operators)
        self.assertNotIn("bend", operators)
        self.assertEqual(
            program["metadata"]["family_contract"]["contract_id"],
            "common_hub_radial",
        )

    def test_management_command_writes_a_mass_only_batch_without_paid_calls(self):
        with TemporaryDirectory() as temporary:
            call_command(
                "generate_maas_fresh_batch",
                batch_id="command-test",
                count=1,
                building_type="neighborhood living",
                output_root=temporary,
                verbosity=0,
            )
            manifest = Path(temporary) / "command-test.batch.json"

            self.assertTrue(manifest.is_file())
            payload = json.loads(manifest.read_text(encoding="utf-8"))

        self.assertEqual(payload["accepted_count"], 1)
        self.assertEqual(payload["paid_image_request_count"], 0)

    def test_later_batch_rejects_geometry_already_present_in_archive(self):
        with TemporaryDirectory() as temporary:
            first = generate_fresh_mass_batch(
                temporary,
                batch_id="archive-first",
                building_type="generic",
                count=4,
                collaboration_executors=self._fast_collaboration_executors(),
            )
            second = generate_fresh_mass_batch(
                temporary,
                batch_id="archive-second",
                building_type="generic",
                count=4,
                collaboration_executors=self._fast_collaboration_executors(),
            )

        self.assertTrue(
            set(first["geometry_hashes"]).isdisjoint(second["geometry_hashes"])
        )

    @staticmethod
    def _fast_collaboration_executors():
        def executor(agent):
            def run(identity, accumulated):
                return AgentEvidence(
                    evidence_id=f"evidence:{agent}",
                    agent=agent,
                    status="needs_evidence" if agent != "maas_geometry_agent" else "passed",
                    summary=f"{agent} test evidence",
                    identity=identity,
                    evidence={"input_count": len(accumulated)},
                )

            return run

        return {agent: executor(agent) for agent in SPECIALIST_SEQUENCE}
