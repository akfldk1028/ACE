from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from design.maas.agents.maas_geometry_agent.version_memory import (
    write_version_snapshot,
)
from design.maas.geometry_language.run_state import (
    tracked_mass_command,
    update_run_progress,
)


class MaasVersionMemoryTests(SimpleTestCase):
    def test_progress_updates_create_idempotent_append_only_checkpoints(self):
        with TemporaryDirectory() as directory:
            output_dir = Path(directory) / "c112-progress"
            progress = {
                "phase": "candidate_generation",
                "program": "neighborhood",
                "diagnostic_target": 3,
                "evaluated_count": 1,
                "compiled_count": 1,
                "program_passed_count": 1,
            }

            update_run_progress(output_dir, **progress)
            update_run_progress(output_dir, **progress)

            memory_dir = output_dir / "memory"
            checkpoints = sorted(memory_dir.glob("*--cp-*.json"))
            self.assertEqual(len(checkpoints), 1)
            first = json.loads(checkpoints[0].read_text(encoding="utf-8"))
            self.assertEqual(first["stage"], "progress:candidate_generation")
            self.assertEqual(first["payload"]["evaluated_count"], 1)

            update_run_progress(
                output_dir,
                **{**progress, "evaluated_count": 2},
            )

            checkpoints = sorted(memory_dir.glob("*--cp-*.json"))
            self.assertEqual(len(checkpoints), 2)
            run_state = json.loads(
                (output_dir / "maas-run-state.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(run_state["evaluated_count"], 2)
            self.assertTrue(Path(run_state["progress_checkpoint_path"]).is_file())

    def test_snapshot_is_append_only_hash_bound_and_credential_free(self):
        with TemporaryDirectory() as directory:
            output_dir = Path(directory)
            snapshot = write_version_snapshot(
                output_dir,
                version_id="c53-b01-provider-v2",
                parent_version_id="c53-b01-provider-v1",
                stage="provider_response",
                payload={
                    "requested_count": 20,
                    "artifact_hashes": {"request": "a" * 64},
                    "OPENAI_API_KEY": "must-not-survive",
                    "nested": {"authorization": "Bearer secret"},
                },
            )

            stored = json.loads(snapshot.read_text(encoding="utf-8"))
            self.assertEqual(
                stored["schema_version"],
                "arr.maas.version_memory.v1",
            )
            self.assertEqual(stored["version_id"], "c53-b01-provider-v2")
            self.assertEqual(
                stored["parent_version_id"],
                "c53-b01-provider-v1",
            )
            self.assertEqual(stored["stage"], "provider_response")
            self.assertEqual(stored["payload"]["requested_count"], 20)
            self.assertEqual(len(stored["payload_sha256"]), 64)
            serialized = json.dumps(stored, sort_keys=True)
            self.assertNotIn("must-not-survive", serialized)
            self.assertNotIn("Bearer secret", serialized)

            self.assertEqual(
                write_version_snapshot(
                    output_dir,
                    version_id="c53-b01-provider-v2",
                    parent_version_id="c53-b01-provider-v1",
                    stage="provider_response",
                    payload={
                        "requested_count": 20,
                        "artifact_hashes": {"request": "a" * 64},
                        "OPENAI_API_KEY": "different-secret",
                        "nested": {"authorization": "different-secret"},
                    },
                ),
                snapshot,
            )

            with self.assertRaisesRegex(
                ValueError,
                "version memory snapshot already exists with different content",
            ):
                write_version_snapshot(
                    output_dir,
                    version_id="c53-b01-provider-v2",
                    parent_version_id="c53-b01-provider-v1",
                    stage="provider_response",
                    payload={"requested_count": 19},
                )

    def test_tracked_command_binds_final_version_snapshot_to_run_state(self):
        with TemporaryDirectory() as directory:
            output_dir = Path(directory)

            @tracked_mass_command
            def command(_self, **_options):
                return {
                    "status": "pass",
                    "programs": [{"selected_count": 20}],
                }

            command(
                object(),
                output_dir=str(output_dir),
                pnu="1168011800104170004",
                program=["neighborhood"],
                recursive_only=True,
                live_vlm=False,
                progressive_target=None,
                outcome_graph=None,
                parent_version_id="c53-b01-provider-v2",
            )

            run_state = json.loads(
                (output_dir / "maas-run-state.json").read_text(
                    encoding="utf-8"
                )
            )
            memory_path = Path(run_state["version_memory_path"])
            self.assertTrue(memory_path.is_file())
            self.assertEqual(
                run_state["parent_version_id"],
                "c53-b01-provider-v2",
            )
            snapshot = json.loads(memory_path.read_text(encoding="utf-8"))
            self.assertEqual(snapshot["stage"], "completed")
            self.assertEqual(snapshot["payload"]["selected_mass_count"], 20)
