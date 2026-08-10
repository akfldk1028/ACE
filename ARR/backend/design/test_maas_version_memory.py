from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from design.maas.agents.maas_geometry_agent.version_memory import (
    write_version_snapshot,
)
from design.maas.geometry_language.run_state import tracked_mass_command


class MaasVersionMemoryTests(SimpleTestCase):
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

