from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class ProjectionIdentityCliTests(unittest.TestCase):
    def test_cli_creates_once_and_prints_only_path_and_commitment(self) -> None:
        from iclr2027.projection import ProjectionIdentity

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "identity.private.json"
            command = [
                sys.executable,
                "init_iclr2027_projection_identity.py",
                "--output",
                str(path),
            ]
            first = subprocess.run(
                command,
                cwd=Path(__file__).parents[1],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(first.returncode, 0, first.stderr)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(
                set(payload),
                {"schema_version", "secret_hex"},
            )
            self.assertEqual(len(payload["secret_hex"]), 64)
            commitment = ProjectionIdentity(
                bytes.fromhex(payload["secret_hex"])
            ).commitment
            self.assertEqual(
                first.stdout.splitlines(),
                [f"path={path}", f"identity_commitment={commitment}"],
            )
            self.assertNotIn(payload["secret_hex"], first.stdout)
            original = path.read_bytes()

            second = subprocess.run(
                command,
                cwd=Path(__file__).parents[1],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("already exists", second.stderr)
            self.assertEqual(path.read_bytes(), original)

    def test_invalid_secret_factory_leaves_no_partial_target(self) -> None:
        try:
            from iclr2027.release import create_projection_identity
        except ImportError as exc:
            self.fail(f"projection identity creator is missing: {exc}")

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "identity.private.json"
            with self.assertRaisesRegex(ValueError, "exactly 32 bytes"):
                create_projection_identity(
                    path,
                    secret_factory=lambda _length: b"x" * 31,
                )
            self.assertFalse(path.exists())

    def test_existing_symlink_is_never_followed_or_replaced(self) -> None:
        from iclr2027.release import create_projection_identity

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target.json"
            target.write_text("sentinel", encoding="utf-8")
            link = root / "identity.private.json"
            try:
                link.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            with self.assertRaisesRegex(FileExistsError, "already exists"):
                create_projection_identity(link)
            self.assertTrue(link.is_symlink())
            self.assertEqual(target.read_text(encoding="utf-8"), "sentinel")


if __name__ == "__main__":
    unittest.main()
