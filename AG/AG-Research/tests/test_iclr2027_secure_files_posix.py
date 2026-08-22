from __future__ import annotations

import importlib.util
import inspect
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "iclr2027/secure_files.py"


def _load_secure_files_module():
    spec = importlib.util.spec_from_file_location("_ace_secure_files_posix_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("secure-files test module cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(os.name == "posix", "POSIX no-follow regression")
class PosixAuthenticatedTreeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.secure_files = _load_secure_files_module()

    def _ancestor_alias_fixture(self, root: Path) -> tuple[Path, list[Path]]:
        actual = root / "actual"
        source = actual / "source"
        source.mkdir(parents=True)
        (source / "declared.json").write_bytes(b"outside-alias-bytes")
        alias = root / "ancestor-alias"
        alias.symlink_to(actual, target_is_directory=True)
        return alias / "source", []

    def _assert_mount_boundary_rejected(
        self,
        source: Path,
        *,
        sentinel: bytes,
        outside_name: str,
    ) -> None:
        observed_names: list[tuple[Path, str]] = []
        observed_reads: list[Path] = []
        returned: bytes | None = None
        list_error: ValueError | None = None
        read_error: ValueError | None = None
        publication_error: ValueError | None = None
        publication_renames: list[tuple[Path, Path]] = []

        with self.secure_files.AuthenticatedTree(
            source,
            label="POSIX mounted source",
            name_observer=lambda directory, name: observed_names.append(
                (directory, name)
            ),
        ) as tree:
            try:
                tree.list_directory("declared", label="POSIX mounted directory")
            except ValueError as error:
                list_error = error

        with self.secure_files.AuthenticatedTree(
            source,
            label="POSIX mounted source",
            read_observer=observed_reads.append,
        ) as tree:
            try:
                returned = tree.read_bytes(
                    "declared/input.bin", label="POSIX mounted file"
                )
            except ValueError as error:
                read_error = error

        candidate = source.parent / "candidate-publication"
        published = source.parent / "published"
        candidate.mkdir()
        with self.secure_files.AuthenticatedTree(
            source,
            label="POSIX publication preflight source",
            name_observer=lambda directory, name: observed_names.append(
                (directory, name)
            ),
            read_observer=observed_reads.append,
        ) as tree:
            try:
                for entry in tree.list_directory(
                    "declared", label="POSIX publication mounted directory"
                ):
                    if not entry.is_directory:
                        tree.read_bytes(
                            f"declared/{entry.name}",
                            label="POSIX publication mounted file",
                        )
            except ValueError as error:
                publication_error = error
            else:
                os.replace(candidate, published)
                publication_renames.append((candidate, published))

        failures: list[str] = []
        for operation, error in (
            ("list", list_error),
            ("read", read_error),
            ("publication", publication_error),
        ):
            if error is None:
                failures.append(f"{operation} accepted the mounted tree")
        outside_names = [name for _directory, name in observed_names]
        if outside_name in outside_names:
            failures.append(f"outside name was observed: {outside_name}")
        if observed_reads:
            failures.append(f"read observer count was {len(observed_reads)}")
        if returned == sentinel:
            failures.append("exact outside sentinel bytes were returned")
        if publication_renames:
            failures.append(
                f"publication rename count was {len(publication_renames)}"
            )
        if failures:
            self.fail(
                "; ".join(failures)
                + f"; list_error={list_error!r}; read_error={read_error!r}; "
                + f"publication_error={publication_error!r}; "
                + f"observed_names={outside_names!r}; returned={returned!r}"
            )

    def test_symlink_ancestor_is_rejected_before_child_read(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ace-posix-ancestor-") as temporary:
            source, observed = self._ancestor_alias_fixture(Path(temporary))
            with self.assertRaisesRegex(
                ValueError, "symlink|authenticated|outside the frozen tree"
            ):
                with self.secure_files.AuthenticatedTree(
                    source,
                    label="POSIX ancestor source",
                    read_observer=observed.append,
                ) as tree:
                    tree.read_bytes("declared.json", label="POSIX declared file")
            self.assertEqual(observed, [])

    def test_no_proc_fallback_rejects_symlink_ancestor_from_handle_chain(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ace-posix-no-proc-") as temporary:
            source, observed = self._ancestor_alias_fixture(Path(temporary))
            with (
                mock.patch.object(self.secure_files.Path, "exists", return_value=False),
                self.assertRaisesRegex(ValueError, "symlink|authenticated"),
            ):
                with self.secure_files.AuthenticatedTree(
                    source,
                    label="POSIX fallback ancestor source",
                    read_observer=observed.append,
                ) as tree:
                    tree.read_bytes("declared.json", label="POSIX fallback file")
            self.assertEqual(observed, [])

    def test_hardlink_is_rejected_before_read_observer(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ace-posix-hardlink-") as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            outside = root / "outside.json"
            outside.write_bytes(b"outside-hardlink-bytes")
            linked = source / "declared.json"
            try:
                os.link(outside, linked)
            except OSError as error:
                if error.errno in {1, 13, 18, 45, 95}:
                    self.skipTest(f"hard links unsupported by test filesystem: {error}")
                raise
            observed: list[Path] = []
            with self.secure_files.AuthenticatedTree(
                source,
                label="POSIX hardlink source",
                read_observer=observed.append,
            ) as tree:
                with self.assertRaisesRegex(ValueError, "link count"):
                    tree.read_bytes("declared.json", label="POSIX hardlink file")
            self.assertEqual(observed, [])

    def test_post_file_validation_rename_returns_original_handle_bytes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ace-posix-post-file-") as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            expected = source / "declared.json"
            original_bytes = b"POSIX-original-handle-bytes"
            expected.write_bytes(original_bytes)
            replacement = root / "replacement.json"
            replacement.write_bytes(b"POSIX-replacement-bytes")
            moved = source / "moved.json"
            hook_calls: list[Path] = []

            def replace_after_validation(final: Path) -> None:
                hook_calls.append(final)
                expected.replace(moved)
                expected.symlink_to(replacement)

            with self.secure_files.AuthenticatedTree(
                source,
                label="POSIX post-file source",
                post_file_validation_hook=replace_after_validation,
            ) as tree:
                observed = tree.read_bytes(
                    "declared.json", label="POSIX post-file declared file"
                )
            self.assertEqual(observed, original_bytes)
            self.assertEqual(len(hook_calls), 1)

    def test_post_directory_validation_rename_retains_original_directory_handle(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="ace-posix-post-dir-") as temporary:
            root = Path(temporary)
            source = root / "source"
            component = source / "declared"
            component.mkdir(parents=True)
            (component / "input.json").write_bytes(b"POSIX-original-directory-bytes")
            replacement = root / "replacement"
            replacement.mkdir()
            (replacement / "input.json").write_bytes(b"POSIX-replacement-directory")
            moved = source / "moved-declared"
            hook_calls: list[Path] = []
            read_calls: list[Path] = []

            def replace_after_validation(final: Path) -> None:
                hook_calls.append(final)
                component.replace(moved)
                component.symlink_to(replacement, target_is_directory=True)

            with self.secure_files.AuthenticatedTree(
                source,
                label="POSIX post-directory source",
                read_observer=read_calls.append,
                directory_validation_hook=replace_after_validation,
            ) as tree:
                with self.assertRaisesRegex(ValueError, "outside the frozen tree"):
                    tree.read_bytes(
                        "declared/input.json", label="POSIX post-directory file"
                    )
            self.assertEqual(len(hook_calls), 1)
            self.assertEqual(read_calls, [])

    def test_static_symlink_directory_rejects_before_any_name_observer(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ace-posix-list-static-link-") as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            outside = root / "outside"
            outside.mkdir()
            (outside / "outside-name.json").write_bytes(b"outside")
            (source / "linked").symlink_to(outside, target_is_directory=True)
            if (
                "name_observer"
                not in inspect.signature(
                    self.secure_files.AuthenticatedTree
                ).parameters
            ):
                self.fail("authenticated directory name observer is missing")
            observed: list[tuple[Path, str]] = []
            with self.secure_files.AuthenticatedTree(
                source,
                label="POSIX static link enumeration",
                name_observer=lambda directory, name: observed.append(
                    (directory, name)
                ),
            ) as tree:
                list_directory = getattr(tree, "list_directory", None)
                if list_directory is None:
                    self.fail("authenticated directory enumeration is missing")
                with self.assertRaisesRegex(ValueError, "symlink|reparse"):
                    list_directory(None, label="POSIX source directory")
            self.assertEqual(observed, [])

    def test_post_validation_directory_swap_never_observes_replacement_names(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="ace-posix-list-swap-") as temporary:
            root = Path(temporary)
            source = root / "source"
            component = source / "declared"
            component.mkdir(parents=True)
            (component / "inside-original.json").write_bytes(b"inside")
            outside = root / "outside"
            outside.mkdir()
            outside_name = "outside-name-must-not-be-observed.json"
            (outside / outside_name).write_bytes(b"outside")
            moved = source / "moved-declared"
            observed: list[tuple[Path, str]] = []
            replaced = False

            def replace_after_validation(final: Path) -> None:
                nonlocal replaced
                if final.name != "declared":
                    return
                component.replace(moved)
                component.symlink_to(outside, target_is_directory=True)
                replaced = True

            if (
                "name_observer"
                not in inspect.signature(
                    self.secure_files.AuthenticatedTree
                ).parameters
            ):
                self.fail("authenticated directory name observer is missing")
            with self.secure_files.AuthenticatedTree(
                source,
                label="POSIX directory swap enumeration",
                name_observer=lambda directory, name: observed.append(
                    (directory, name)
                ),
                directory_validation_hook=replace_after_validation,
            ) as tree:
                list_directory = getattr(tree, "list_directory", None)
                if list_directory is None:
                    self.fail("authenticated directory enumeration is missing")
                with self.assertRaisesRegex(ValueError, "outside the frozen tree"):
                    list_directory("declared", label="POSIX declared directory")
            self.assertTrue(replaced)
            self.assertNotIn(outside_name, [name for _directory, name in observed])

    def test_same_filesystem_bind_mount_rejects_outside_names_and_bytes(
        self,
    ) -> None:
        if os.environ.get("ACE_AUTHENTICATED_MOUNT_TESTS") != "1":
            self.skipTest("requires the isolated Linux mount-namespace harness")
        with tempfile.TemporaryDirectory(
            prefix="ace-posix-same-mount-", dir="/tmp"
        ) as temporary:
            root = Path(temporary)
            source = root / "source"
            declared = source / "declared"
            declared.mkdir(parents=True)
            outside = root / "outside"
            outside.mkdir()
            sentinel = b"same-filesystem-bind-outside-sentinel"
            outside_name = "outside-name-must-not-be-observed.bin"
            (outside / "input.bin").write_bytes(sentinel)
            (outside / outside_name).write_bytes(b"outside name sentinel")
            subprocess.run(
                ["mount", "--bind", os.fspath(outside), os.fspath(declared)],
                check=True,
                capture_output=True,
                text=True,
            )
            try:
                self._assert_mount_boundary_rejected(
                    source,
                    sentinel=sentinel,
                    outside_name=outside_name,
                )
            finally:
                subprocess.run(
                    ["umount", os.fspath(declared)],
                    check=True,
                    capture_output=True,
                    text=True,
                )

    def test_tmpfs_bind_mount_rejects_outside_names_and_bytes(self) -> None:
        if os.environ.get("ACE_AUTHENTICATED_MOUNT_TESTS") != "1":
            self.skipTest("requires the isolated Linux mount-namespace harness")
        with tempfile.TemporaryDirectory(
            prefix="ace-posix-tmpfs-mount-", dir="/tmp"
        ) as temporary:
            root = Path(temporary)
            source = root / "source"
            declared = source / "declared"
            declared.mkdir(parents=True)
            outside = root / "outside-tmpfs"
            outside.mkdir()
            subprocess.run(
                ["mount", "-t", "tmpfs", "tmpfs", os.fspath(outside)],
                check=True,
                capture_output=True,
                text=True,
            )
            try:
                sentinel = b"tmpfs-bind-outside-sentinel"
                outside_name = "tmpfs-name-must-not-be-observed.bin"
                (outside / "input.bin").write_bytes(sentinel)
                (outside / outside_name).write_bytes(b"outside tmpfs name sentinel")
                subprocess.run(
                    ["mount", "--bind", os.fspath(outside), os.fspath(declared)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                try:
                    self._assert_mount_boundary_rejected(
                        source,
                        sentinel=sentinel,
                        outside_name=outside_name,
                    )
                finally:
                    subprocess.run(
                        ["umount", os.fspath(declared)],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
            finally:
                subprocess.run(
                    ["umount", os.fspath(outside)],
                    check=True,
                    capture_output=True,
                    text=True,
                )


if __name__ == "__main__":
    unittest.main()
