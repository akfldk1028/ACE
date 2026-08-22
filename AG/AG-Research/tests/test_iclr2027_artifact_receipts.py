import copy
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from iclr2027.artifact_receipts import (
    canonical_artifact_receipt,
    verify_artifact_receipt,
)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_hash(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return _sha256(payload)


def _forged_receipt(
    *, files: dict[str, str], row_census: dict[str, int], bindings: dict[str, str]
) -> dict[str, object]:
    schema_version = "ace.iclr2027.test_receipt.v1"
    file_set_sha256 = _canonical_hash(files)
    row_census_sha256 = _canonical_hash(row_census)
    artifact_sha256 = _canonical_hash(
        {
            "bindings": bindings,
            "file_set_sha256": file_set_sha256,
            "files": files,
            "row_census": row_census,
            "row_census_sha256": row_census_sha256,
            "schema_version": schema_version,
        }
    )
    return {
        "schema_version": schema_version,
        "files": files,
        "file_set_sha256": file_set_sha256,
        "row_census": row_census,
        "row_census_sha256": row_census_sha256,
        "bindings": bindings,
        "artifact_sha256": artifact_sha256,
    }


class ArtifactReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "root"
        self.root.mkdir()
        self.file_a = self.root / "a.json"
        self.file_a.write_bytes(b"original\x00bytes")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_receipt_hashes_raw_bytes_and_sorts_relative_paths(self) -> None:
        nested = self.root / "nested"
        nested.mkdir()
        file_b = nested / "b.json"
        file_b.write_bytes(b"second")

        receipt = canonical_artifact_receipt(
            schema_version="ace.iclr2027.test_receipt.v1",
            files={"nested\\b.json": file_b, "a.json": self.file_a},
            row_census={"z_rows": 1, "a_rows": 2},
            bindings={"source": "a" * 64},
        )

        self.assertEqual(list(receipt["files"]), ["a.json", "nested/b.json"])
        self.assertEqual(receipt["files"]["a.json"], _sha256(b"original\x00bytes"))
        self.assertEqual(receipt["files"]["nested/b.json"], _sha256(b"second"))
        verify_artifact_receipt(receipt, root=self.root)

    def test_receipt_rejects_changed_file_or_row_census(self) -> None:
        receipt = canonical_artifact_receipt(
            schema_version="ace.iclr2027.test_receipt.v1",
            files={"a.json": self.file_a},
            row_census={"rows": 2},
            bindings={"source": "a" * 64},
        )

        self.file_a.write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "artifact hash mismatch"):
            verify_artifact_receipt(receipt, root=self.root)

        tampered = copy.deepcopy(receipt)
        tampered["row_census"]["rows"] = 3
        with self.assertRaisesRegex(ValueError, "row census hash mismatch"):
            verify_artifact_receipt(tampered, root=self.root)

    def test_receipt_rejects_file_set_and_binding_tampering(self) -> None:
        receipt = canonical_artifact_receipt(
            schema_version="ace.iclr2027.test_receipt.v1",
            files={"a.json": self.file_a},
            row_census={"rows": 2},
            bindings={"source": "a" * 64},
        )

        removed_file = copy.deepcopy(receipt)
        removed_file["files"] = {}
        with self.assertRaisesRegex(ValueError, "file-set hash mismatch"):
            verify_artifact_receipt(removed_file, root=self.root)

        changed_binding = copy.deepcopy(receipt)
        changed_binding["bindings"]["source"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "artifact hash mismatch"):
            verify_artifact_receipt(changed_binding, root=self.root)

    def test_receipt_rejects_malformed_binding_and_traversal_path(self) -> None:
        with self.assertRaisesRegex(ValueError, "binding"):
            canonical_artifact_receipt(
                schema_version="ace.iclr2027.test_receipt.v1",
                files={"a.json": self.file_a},
                row_census={"rows": 2},
                bindings={"source": "A" * 64},
            )

        outside = self.root.parent / "outside.json"
        outside.write_bytes(b"outside")
        receipt = _forged_receipt(
            files={"../outside.json": _sha256(b"outside")},
            row_census={"rows": 1},
            bindings={"source": "a" * 64},
        )
        with self.assertRaisesRegex(ValueError, "path outside root"):
            verify_artifact_receipt(receipt, root=self.root)

    def test_receipt_rejects_symlink_inside_root(self) -> None:
        outside = self.root.parent / "outside-link-target.json"
        outside.write_bytes(b"outside")
        link = self.root / "link.json"
        try:
            link.symlink_to(outside)
        except OSError as error:
            self.skipTest(f"symlinks unavailable: {error}")

        receipt = _forged_receipt(
            files={"link.json": _sha256(b"outside")},
            row_census={"rows": 1},
            bindings={"source": "a" * 64},
        )
        with self.assertRaisesRegex(ValueError, "symlink"):
            verify_artifact_receipt(receipt, root=self.root)

    def test_receipt_rejects_hardlink_before_outside_inode_bytes_are_read(self) -> None:
        outside = self.root.parent / "outside-hardlink-target.json"
        outside_bytes = b"outside-hardlink-bytes-must-not-be-read"
        outside.write_bytes(outside_bytes)
        linked = self.root / "hardlink.json"
        try:
            os.link(outside, linked)
        except OSError as error:
            self.skipTest(f"hard links unavailable: {error}")
        self.assertGreater(os.stat(linked).st_nlink, 1)
        receipt = _forged_receipt(
            files={"hardlink.json": _sha256(outside_bytes)},
            row_census={"rows": 1},
            bindings={"source": "a" * 64},
        )
        observed: list[tuple[Path, bytes]] = []
        original_read_bytes = Path.read_bytes

        def observe_read(path: Path) -> bytes:
            artifact = original_read_bytes(path)
            if path == linked:
                observed.append((path, artifact))
            return artifact

        caught: ValueError | None = None
        with mock.patch.object(Path, "read_bytes", observe_read):
            try:
                verify_artifact_receipt(receipt, root=self.root)
            except ValueError as error:
                caught = error
        if observed or caught is None or "link count" not in str(caught):
            self.fail(
                "hardlink must be rejected before its inode is read; "
                f"observed={observed!r}, error={caught!r}"
            )

    def test_receipt_creation_rejects_hardlink_before_hashing_outside_inode(self) -> None:
        outside = self.root.parent / "outside-create-target.json"
        outside_bytes = b"outside-create-bytes-must-not-be-hashed"
        outside.write_bytes(outside_bytes)
        linked = self.root / "create-hardlink.json"
        try:
            os.link(outside, linked)
        except OSError as error:
            self.skipTest(f"hard links unavailable: {error}")
        observed: list[tuple[Path, bytes]] = []
        original_read_bytes = Path.read_bytes

        def observe_read(path: Path) -> bytes:
            artifact = original_read_bytes(path)
            if path == linked:
                observed.append((path, artifact))
            return artifact

        caught: ValueError | None = None
        with mock.patch.object(Path, "read_bytes", observe_read):
            try:
                canonical_artifact_receipt(
                    schema_version="ace.iclr2027.test_receipt.v1",
                    files={"create-hardlink.json": linked},
                    row_census={"rows": 1},
                    bindings={"source": "a" * 64},
                )
            except ValueError as error:
                caught = error
        if observed or caught is None or "link count" not in str(caught):
            self.fail(
                "hardlink must be rejected before receipt hashing; "
                f"observed={observed!r}, error={caught!r}"
            )

    def test_receipt_rejects_windows_special_artifact_components(self) -> None:
        for relative_path in (
            "artifact.json:stream",
            "CON",
            "aux.txt",
            "nested/COM1.csv",
            "trailing.",
            "trailing ",
            "bad|name.json",
        ):
            with self.subTest(relative_path=relative_path):
                with self.assertRaisesRegex(ValueError, "non-portable artifact path"):
                    canonical_artifact_receipt(
                        schema_version="ace.iclr2027.test_receipt.v1",
                        files={relative_path: self.file_a},
                        row_census={"rows": 1},
                        bindings={"source": "a" * 64},
                    )

        receipt = _forged_receipt(
            files={"artifact.json:stream": _sha256(b"original\x00bytes")},
            row_census={"rows": 1},
            bindings={"source": "a" * 64},
        )
        with self.assertRaisesRegex(ValueError, "non-portable artifact path"):
            verify_artifact_receipt(receipt, root=self.root)
