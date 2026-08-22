"""Handle-authenticated, no-follow reads for frozen development sources."""

from __future__ import annotations

from collections.abc import Callable
import ctypes
from ctypes import wintypes
import errno
import os
from pathlib import Path
import stat
import sys
from typing import Any, NamedTuple


_ReadObserver = Callable[[Path], None]
_NameObserver = Callable[[Path, str], None]


class AuthenticatedDirectoryEntry(NamedTuple):
    """One fully validated name from an authenticated directory handle."""

    name: str
    is_directory: bool


def _lexical_absolute(path: str | Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _normal_path(path: str | Path) -> str:
    value = os.fspath(path)
    if value.startswith("\\\\?\\UNC\\"):
        value = "\\\\" + value[8:]
    elif value.startswith("\\\\?\\"):
        value = value[4:]
    return os.path.normcase(os.path.normpath(value))


def _path_from_windows_final_name(value: str) -> Path:
    if value.startswith("\\\\?\\UNC\\"):
        return Path("\\\\" + value[8:])
    if value.startswith("\\\\?\\"):
        return Path(value[4:])
    return Path(value)


def _relative_parts(relative: str | Path, *, label: str) -> tuple[str, ...]:
    path = Path(relative)
    parts = path.parts
    if (
        path.is_absolute()
        or not parts
        or any(part in {"", ".", ".."} for part in parts)
        or (os.name == "nt" and any(":" in part for part in parts))
    ):
        raise ValueError(f"{label} must be a contained relative path")
    return parts


if os.name == "nt":
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _ntdll = ctypes.WinDLL("ntdll")
    _INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value

    _FILE_READ_DATA = 0x0001
    _FILE_LIST_DIRECTORY = 0x0001
    _FILE_READ_ATTRIBUTES = 0x0080
    _SYNCHRONIZE = 0x00100000
    _FILE_SHARE_READ = 0x00000001
    _OPEN_EXISTING = 3
    _FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
    _FILE_ATTRIBUTE_DIRECTORY = 0x00000010
    _FILE_ATTRIBUTE_DEVICE = 0x00000040
    _FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    _FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    _FILE_OPEN = 1
    _FILE_DIRECTORY_FILE = 0x00000001
    _FILE_NON_DIRECTORY_FILE = 0x00000040
    _FILE_SYNCHRONOUS_IO_NONALERT = 0x00000020
    _OBJ_CASE_INSENSITIVE = 0x00000040
    _FILE_ATTRIBUTE_TAG_INFO_CLASS = 9
    _FILE_STANDARD_INFO_CLASS = 1
    _FILE_DIRECTORY_INFORMATION_CLASS = 1
    _STATUS_NO_MORE_FILES = ctypes.c_long(0x80000006).value
    _STATUS_BUFFER_OVERFLOW = ctypes.c_long(0x80000005).value

    class _UnicodeString(ctypes.Structure):
        _fields_ = (
            ("Length", wintypes.USHORT),
            ("MaximumLength", wintypes.USHORT),
            ("Buffer", wintypes.LPWSTR),
        )

    class _ObjectAttributes(ctypes.Structure):
        _fields_ = (
            ("Length", wintypes.ULONG),
            ("RootDirectory", wintypes.HANDLE),
            ("ObjectName", ctypes.POINTER(_UnicodeString)),
            ("Attributes", wintypes.ULONG),
            ("SecurityDescriptor", wintypes.LPVOID),
            ("SecurityQualityOfService", wintypes.LPVOID),
        )

    class _IoStatusValue(ctypes.Union):
        _fields_ = (("Status", wintypes.LONG), ("Pointer", wintypes.LPVOID))

    class _IoStatusBlock(ctypes.Structure):
        _anonymous_ = ("value",)
        _fields_ = (("value", _IoStatusValue), ("Information", ctypes.c_size_t))

    class _FileAttributeTagInfo(ctypes.Structure):
        _fields_ = (("FileAttributes", wintypes.DWORD), ("ReparseTag", wintypes.DWORD))

    class _FileStandardInfo(ctypes.Structure):
        _fields_ = (
            ("AllocationSize", ctypes.c_longlong),
            ("EndOfFile", ctypes.c_longlong),
            ("NumberOfLinks", wintypes.DWORD),
            ("DeletePending", wintypes.BOOLEAN),
            ("Directory", wintypes.BOOLEAN),
        )

    _kernel32.CreateFileW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    _kernel32.CreateFileW.restype = wintypes.HANDLE
    _kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    _kernel32.CloseHandle.restype = wintypes.BOOL
    _kernel32.GetFileInformationByHandleEx.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    )
    _kernel32.GetFileInformationByHandleEx.restype = wintypes.BOOL
    _kernel32.GetFinalPathNameByHandleW.argtypes = (
        wintypes.HANDLE,
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
    )
    _kernel32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    _kernel32.ReadFile.argtypes = (
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    )
    _kernel32.ReadFile.restype = wintypes.BOOL
    _ntdll.NtCreateFile.argtypes = (
        ctypes.POINTER(wintypes.HANDLE),
        wintypes.DWORD,
        ctypes.POINTER(_ObjectAttributes),
        ctypes.POINTER(_IoStatusBlock),
        ctypes.c_void_p,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.ULONG,
        ctypes.c_void_p,
        wintypes.ULONG,
    )
    _ntdll.NtCreateFile.restype = wintypes.LONG
    _ntdll.NtQueryDirectoryFile.argtypes = (
        wintypes.HANDLE,
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.LPVOID,
        ctypes.POINTER(_IoStatusBlock),
        wintypes.LPVOID,
        wintypes.ULONG,
        ctypes.c_int,
        wintypes.BOOLEAN,
        ctypes.POINTER(_UnicodeString),
        wintypes.BOOLEAN,
    )
    _ntdll.NtQueryDirectoryFile.restype = wintypes.LONG
    _ntdll.RtlNtStatusToDosError.argtypes = (wintypes.LONG,)
    _ntdll.RtlNtStatusToDosError.restype = wintypes.ULONG
else:
    _AT_EMPTY_PATH = 0x1000
    _AT_SYMLINK_NOFOLLOW = 0x0100
    _STATX_MNT_ID = 0x00001000

    class _StatxTimestamp(ctypes.Structure):
        _fields_ = (
            ("tv_sec", ctypes.c_int64),
            ("tv_nsec", ctypes.c_uint32),
            ("reserved", ctypes.c_int32),
        )

    class _Statx(ctypes.Structure):
        _fields_ = (
            ("mask", ctypes.c_uint32),
            ("block_size", ctypes.c_uint32),
            ("attributes", ctypes.c_uint64),
            ("link_count", ctypes.c_uint32),
            ("uid", ctypes.c_uint32),
            ("gid", ctypes.c_uint32),
            ("mode", ctypes.c_uint16),
            ("spare0", ctypes.c_uint16),
            ("inode", ctypes.c_uint64),
            ("size", ctypes.c_uint64),
            ("blocks", ctypes.c_uint64),
            ("attributes_mask", ctypes.c_uint64),
            ("access_time", _StatxTimestamp),
            ("birth_time", _StatxTimestamp),
            ("change_time", _StatxTimestamp),
            ("modify_time", _StatxTimestamp),
            ("rdev_major", ctypes.c_uint32),
            ("rdev_minor", ctypes.c_uint32),
            ("dev_major", ctypes.c_uint32),
            ("dev_minor", ctypes.c_uint32),
            ("mount_id", ctypes.c_uint64),
            ("direct_io_memory_alignment", ctypes.c_uint32),
            ("direct_io_offset_alignment", ctypes.c_uint32),
            ("spare3", ctypes.c_uint64 * 12),
        )

    _libc = ctypes.CDLL(None, use_errno=True)
    _statx = getattr(_libc, "statx", None)
    if _statx is not None:
        _statx.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_uint,
            ctypes.POINTER(_Statx),
        )
        _statx.restype = ctypes.c_int


def _linux_mount_id(handle: int, *, label: str) -> int:
    """Return mount identity from retained handle metadata, or fail closed."""

    if _statx is not None:
        details = _Statx()
        result = _statx(
            handle,
            b"",
            _AT_EMPTY_PATH | _AT_SYMLINK_NOFOLLOW,
            _STATX_MNT_ID,
            ctypes.byref(details),
        )
        if result == 0 and details.mask & _STATX_MNT_ID:
            return int(details.mount_id)
        if result != 0 and ctypes.get_errno() not in {
            errno.EINVAL,
            errno.ENOSYS,
            errno.EOPNOTSUPP,
        }:
            raise ValueError(f"{label} mount identity cannot be authenticated")

    fdinfo = f"/proc/self/fdinfo/{handle}"
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    try:
        metadata_handle = os.open(fdinfo, flags)
        try:
            chunks: list[bytes] = []
            while True:
                chunk = os.read(metadata_handle, 4096)
                if not chunk:
                    break
                chunks.append(chunk)
        finally:
            os.close(metadata_handle)
        for line in b"".join(chunks).splitlines():
            if line.startswith(b"mnt_id:"):
                return int(line.split(b":", 1)[1].strip())
    except (OSError, ValueError) as error:
        raise ValueError(
            f"{label} mount identity cannot be authenticated"
        ) from error
    raise ValueError(f"{label} mount identity cannot be authenticated")


class AuthenticatedTree:
    """Read declared files relative to one retained, authenticated root handle.

    ``list_directory`` is intentionally narrow: it exists only for the exact
    frozen transaction and publication-tree callers that cannot obtain their
    finite names from a receipt.  It enumerates a retained directory handle,
    validates every returned child before exposing any name, and revalidates
    the directory identity after enumeration.  On POSIX, each descendant's
    retained handle must also match the authenticated root mount (Linux mount
    ID, with a conservative device fallback on other POSIX systems).  It is
    not a general filesystem traversal API.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        label: str,
        read_observer: _ReadObserver | None = None,
        post_file_validation_hook: _ReadObserver | None = None,
        directory_validation_hook: _ReadObserver | None = None,
        name_observer: _NameObserver | None = None,
    ) -> None:
        self.root = _lexical_absolute(root)
        self.label = label
        self._read_observer = read_observer
        self._post_file_validation_hook = post_file_validation_hook
        self._directory_validation_hook = directory_validation_hook
        self._name_observer = name_observer
        self._root_handle: Any = None
        self._root_mount_identity: tuple[str, int] | None = None
        self._ancestor_handles: list[Any] = []
        self._directory_handles: dict[tuple[str, ...], Any] = {}

    def __enter__(self) -> AuthenticatedTree:
        if self._root_handle is not None:
            raise RuntimeError("authenticated tree is already open")
        root_handle = self._open_root()
        try:
            self._root_mount_identity = self._mount_identity(
                root_handle,
                label=self.label,
            )
        except BaseException:
            self._close(root_handle)
            for handle in reversed(self._ancestor_handles):
                self._close(handle)
            self._ancestor_handles.clear()
            raise
        self._root_handle = root_handle
        self._directory_handles[()] = self._root_handle
        return self

    def __exit__(self, *_exc: object) -> None:
        handles = list(self._directory_handles.values())
        self._directory_handles.clear()
        self._root_handle = None
        self._root_mount_identity = None
        for handle in reversed(handles):
            self._close(handle)
        for handle in reversed(self._ancestor_handles):
            self._close(handle)
        self._ancestor_handles.clear()

    def read_bytes(self, relative: str | Path, *, label: str) -> bytes:
        if self._root_handle is None:
            raise RuntimeError("authenticated tree is not open")
        parts = _relative_parts(relative, label=label)
        parent = self._directory_handle(parts[:-1], label=label)
        expected = self.root.joinpath(*parts)
        handle = self._open_relative(parent, parts[-1], directory=False, label=label)
        try:
            final = self._validate_handle(
                handle,
                expected=expected,
                directory=False,
                label=label,
            )
            if self._post_file_validation_hook is not None:
                self._post_file_validation_hook(final)
            if self._read_observer is not None:
                self._read_observer(final)
            return self._read_handle(handle, label=label)
        finally:
            self._close(handle)

    def list_directory(
        self,
        relative: str | Path | None,
        *,
        label: str,
    ) -> tuple[AuthenticatedDirectoryEntry, ...]:
        """Return validated immediate children anchored to one retained handle."""

        if self._root_handle is None:
            raise RuntimeError("authenticated tree is not open")
        parts = () if relative is None else _relative_parts(relative, label=label)
        handle = self._directory_handle(parts, label=label)
        expected = self.root.joinpath(*parts)
        final = self._validate_handle(
            handle,
            expected=expected,
            directory=True,
            label=label,
        )
        if not parts and self._directory_validation_hook is not None:
            self._directory_validation_hook(final)
            self._validate_handle(
                handle,
                expected=expected,
                directory=True,
                label=label,
            )
        raw_entries = self._list_handle(handle, label=label)
        entries: list[AuthenticatedDirectoryEntry] = []
        for name, is_directory in raw_entries:
            child = self._open_relative(
                handle,
                name,
                directory=is_directory,
                label=label,
            )
            try:
                self._validate_handle(
                    child,
                    expected=expected / name,
                    directory=is_directory,
                    label=label,
                )
            finally:
                self._close(child)
            entries.append(
                AuthenticatedDirectoryEntry(
                    name=name,
                    is_directory=is_directory,
                )
            )
        self._validate_handle(
            handle,
            expected=expected,
            directory=True,
            label=label,
        )
        entries.sort(key=lambda entry: entry.name)
        if self._name_observer is not None:
            for entry in entries:
                self._name_observer(expected, entry.name)
        return tuple(entries)

    def _directory_handle(self, parts: tuple[str, ...], *, label: str) -> Any:
        current: tuple[str, ...] = ()
        handle = self._directory_handles[current]
        for part in parts:
            current = (*current, part)
            cached = self._directory_handles.get(current)
            if cached is None:
                cached = self._open_relative(handle, part, directory=True, label=label)
                try:
                    final = self._validate_handle(
                        cached,
                        expected=self.root.joinpath(*current),
                        directory=True,
                        label=label,
                    )
                    if self._directory_validation_hook is not None:
                        self._directory_validation_hook(final)
                except BaseException:
                    self._close(cached)
                    raise
                self._directory_handles[current] = cached
            handle = cached
        return handle

    if os.name == "nt":

        @staticmethod
        def _mount_identity(
            _handle: Any,
            *,
            label: str,
        ) -> tuple[str, int] | None:
            del label
            return None

        def _open_root(self) -> Any:
            handle = _kernel32.CreateFileW(
                str(self.root),
                _FILE_LIST_DIRECTORY | _FILE_READ_ATTRIBUTES | _SYNCHRONIZE,
                _FILE_SHARE_READ,
                None,
                _OPEN_EXISTING,
                _FILE_FLAG_BACKUP_SEMANTICS | _FILE_FLAG_OPEN_REPARSE_POINT,
                None,
            )
            if handle == _INVALID_HANDLE_VALUE:
                error = ctypes.get_last_error()
                raise ValueError(f"{self.label} cannot be authenticated ({error})")
            try:
                self._validate_handle(
                    handle,
                    expected=self.root,
                    directory=True,
                    label=self.label,
                )
            except BaseException:
                _kernel32.CloseHandle(handle)
                raise
            return handle

        @staticmethod
        def _open_relative(
            parent: Any,
            name: str,
            *,
            directory: bool,
            label: str,
        ) -> Any:
            buffer = ctypes.create_unicode_buffer(name)
            unicode_name = _UnicodeString(
                len(name.encode("utf-16-le")),
                len(name.encode("utf-16-le")) + 2,
                ctypes.cast(buffer, wintypes.LPWSTR),
            )
            attributes = _ObjectAttributes(
                ctypes.sizeof(_ObjectAttributes),
                parent,
                ctypes.pointer(unicode_name),
                _OBJ_CASE_INSENSITIVE,
                None,
                None,
            )
            io_status = _IoStatusBlock()
            handle = wintypes.HANDLE()
            desired = (
                (_FILE_LIST_DIRECTORY if directory else _FILE_READ_DATA)
                | _FILE_READ_ATTRIBUTES
                | _SYNCHRONIZE
            )
            options = (
                (_FILE_DIRECTORY_FILE if directory else _FILE_NON_DIRECTORY_FILE)
                | _FILE_SYNCHRONOUS_IO_NONALERT
                | _FILE_FLAG_OPEN_REPARSE_POINT
            )
            status = _ntdll.NtCreateFile(
                ctypes.byref(handle),
                desired,
                ctypes.byref(attributes),
                ctypes.byref(io_status),
                None,
                0,
                _FILE_SHARE_READ,
                _FILE_OPEN,
                options,
                None,
                0,
            )
            if status < 0:
                error = _ntdll.RtlNtStatusToDosError(status)
                raise ValueError(f"{label} cannot be authenticated ({error})")
            return handle

        @staticmethod
        def _validate_handle(
            handle: Any,
            *,
            expected: Path,
            directory: bool,
            label: str,
        ) -> Path:
            tag = _FileAttributeTagInfo()
            if not _kernel32.GetFileInformationByHandleEx(
                handle,
                _FILE_ATTRIBUTE_TAG_INFO_CLASS,
                ctypes.byref(tag),
                ctypes.sizeof(tag),
            ):
                raise ValueError(f"{label} attributes cannot be authenticated")
            if tag.FileAttributes & _FILE_ATTRIBUTE_REPARSE_POINT or tag.ReparseTag:
                raise ValueError(f"{label} contains a symlink or reparse point")
            standard = _FileStandardInfo()
            if not _kernel32.GetFileInformationByHandleEx(
                handle,
                _FILE_STANDARD_INFO_CLASS,
                ctypes.byref(standard),
                ctypes.sizeof(standard),
            ):
                raise ValueError(f"{label} type cannot be authenticated")
            if bool(standard.Directory) is not directory or standard.DeletePending:
                kind = "directory" if directory else "regular file"
                raise ValueError(f"{label} must be a stable {kind}")
            if not directory and standard.NumberOfLinks != 1:
                raise ValueError(f"{label} file link count must be exactly one")
            size = 32_768
            buffer = ctypes.create_unicode_buffer(size)
            length = _kernel32.GetFinalPathNameByHandleW(handle, buffer, size, 0)
            if not length or length >= size:
                raise ValueError(f"{label} final path cannot be authenticated")
            final = _path_from_windows_final_name(buffer.value)
            if _normal_path(final) != _normal_path(expected):
                raise ValueError(f"{label} final path is outside the frozen tree")
            return final

        @staticmethod
        def _read_handle(handle: Any, *, label: str) -> bytes:
            chunks: list[bytes] = []
            while True:
                buffer = ctypes.create_string_buffer(1024 * 1024)
                count = wintypes.DWORD()
                if not _kernel32.ReadFile(
                    handle,
                    buffer,
                    len(buffer),
                    ctypes.byref(count),
                    None,
                ):
                    error = ctypes.get_last_error()
                    raise ValueError(f"{label} cannot be read from authenticated handle ({error})")
                if count.value == 0:
                    return b"".join(chunks)
                chunks.append(buffer.raw[: count.value])

        @staticmethod
        def _list_handle(handle: Any, *, label: str) -> tuple[tuple[str, bool], ...]:
            entries: list[tuple[str, bool]] = []
            restart = True
            while True:
                buffer = ctypes.create_string_buffer(64 * 1024)
                io_status = _IoStatusBlock()
                status = _ntdll.NtQueryDirectoryFile(
                    handle,
                    None,
                    None,
                    None,
                    ctypes.byref(io_status),
                    buffer,
                    len(buffer),
                    _FILE_DIRECTORY_INFORMATION_CLASS,
                    False,
                    None,
                    restart,
                )
                restart = False
                if status == _STATUS_NO_MORE_FILES:
                    break
                if status not in {0, _STATUS_BUFFER_OVERFLOW}:
                    error = _ntdll.RtlNtStatusToDosError(status)
                    raise ValueError(
                        f"{label} names cannot be authenticated ({error})"
                    )
                length = int(io_status.Information)
                if length <= 0:
                    break
                offset = 0
                while offset < length:
                    next_offset = wintypes.ULONG.from_buffer(buffer, offset).value
                    attributes = wintypes.ULONG.from_buffer(buffer, offset + 56).value
                    name_length = wintypes.ULONG.from_buffer(buffer, offset + 60).value
                    name = bytes(buffer[offset + 64 : offset + 64 + name_length]).decode(
                        "utf-16-le"
                    )
                    if name not in {".", ".."}:
                        if attributes & _FILE_ATTRIBUTE_REPARSE_POINT:
                            raise ValueError(
                                f"{label} contains a symlink or reparse point"
                            )
                        if attributes & _FILE_ATTRIBUTE_DEVICE:
                            raise ValueError(f"{label} contains an unsupported entry")
                        entries.append(
                            (name, bool(attributes & _FILE_ATTRIBUTE_DIRECTORY))
                        )
                    if next_offset == 0:
                        break
                    offset += next_offset
            return tuple(entries)

        @staticmethod
        def _close(handle: Any) -> None:
            _kernel32.CloseHandle(handle)

    else:

        @staticmethod
        def _mount_identity(handle: int, *, label: str) -> tuple[str, int]:
            if sys.platform.startswith("linux"):
                return ("linux-mount-id", _linux_mount_id(handle, label=label))
            return ("portable-device", int(os.fstat(handle).st_dev))

        def _open_root(self) -> int:
            flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
            flags |= getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
            anchor = Path(self.root.anchor)
            handles: list[int] = []
            try:
                handle = os.open(anchor, flags)
                handles.append(handle)
                self._validate_handle(
                    handle,
                    expected=anchor,
                    directory=True,
                    label=self.label,
                )
                expected = anchor
                for component in self.root.parts[1:]:
                    handle = self._open_relative(
                        handle,
                        component,
                        directory=True,
                        label=self.label,
                    )
                    handles.append(handle)
                    expected /= component
                    self._validate_handle(
                        handle,
                        expected=expected,
                        directory=True,
                        label=self.label,
                    )
            except OSError as error:
                for opened in reversed(handles):
                    os.close(opened)
                raise ValueError(f"{self.label} cannot be authenticated") from error
            except BaseException:
                for opened in reversed(handles):
                    os.close(opened)
                raise
            self._ancestor_handles = handles[:-1]
            return handles[-1]

        @staticmethod
        def _open_relative(
            parent: int,
            name: str,
            *,
            directory: bool,
            label: str,
        ) -> int:
            flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
            flags |= getattr(os, "O_NOFOLLOW", 0)
            if directory:
                flags |= getattr(os, "O_DIRECTORY", 0)
            try:
                return os.open(name, flags, dir_fd=parent)
            except OSError as error:
                raise ValueError(
                    f"{label} contains a symlink or cannot be authenticated"
                ) from error

        def _validate_handle(
            self,
            handle: int,
            *,
            expected: Path,
            directory: bool,
            label: str,
        ) -> Path:
            observed = os.fstat(handle)
            if self._root_mount_identity is not None:
                mount_identity = self._mount_identity(handle, label=label)
                if mount_identity != self._root_mount_identity:
                    raise ValueError(
                        f"{label} crosses the authenticated mount boundary"
                    )
            correct_type = stat.S_ISDIR(observed.st_mode) if directory else stat.S_ISREG(
                observed.st_mode
            )
            if not correct_type:
                kind = "directory" if directory else "regular file"
                raise ValueError(f"{label} must be a stable {kind}")
            if not directory and observed.st_nlink != 1:
                raise ValueError(f"{label} file link count must be exactly one")
            descriptor_path = Path(f"/proc/self/fd/{handle}")
            if descriptor_path.exists():
                final = Path(os.readlink(descriptor_path))
                if _normal_path(final) != _normal_path(expected):
                    raise ValueError(f"{label} final path is outside the frozen tree")
            else:
                final = expected
            return final

        @staticmethod
        def _read_handle(handle: int, *, label: str) -> bytes:
            try:
                os.lseek(handle, 0, os.SEEK_SET)
                chunks: list[bytes] = []
                while True:
                    chunk = os.read(handle, 1024 * 1024)
                    if not chunk:
                        return b"".join(chunks)
                    chunks.append(chunk)
            except OSError as error:
                raise ValueError(f"{label} cannot be read from authenticated handle") from error

        @staticmethod
        def _list_handle(handle: int, *, label: str) -> tuple[tuple[str, bool], ...]:
            try:
                names = os.listdir(handle)
                entries: list[tuple[str, bool]] = []
                for name in names:
                    observed = os.stat(name, dir_fd=handle, follow_symlinks=False)
                    if stat.S_ISLNK(observed.st_mode):
                        raise ValueError(f"{label} contains a symlink or reparse point")
                    if stat.S_ISDIR(observed.st_mode):
                        entries.append((name, True))
                    elif stat.S_ISREG(observed.st_mode):
                        entries.append((name, False))
                    else:
                        raise ValueError(f"{label} contains an unsupported entry")
                return tuple(entries)
            except ValueError:
                raise
            except OSError as error:
                raise ValueError(
                    f"{label} names cannot be authenticated"
                ) from error

        @staticmethod
        def _close(handle: int) -> None:
            os.close(handle)


def read_authenticated_file(path: str | Path, *, label: str) -> bytes:
    """Read one lexical pathname through an authenticated parent/file handle pair."""

    candidate = _lexical_absolute(path)
    with AuthenticatedTree(candidate.parent, label=f"{label} parent") as tree:
        return tree.read_bytes(candidate.name, label=label)


__all__ = (
    "AuthenticatedDirectoryEntry",
    "AuthenticatedTree",
    "read_authenticated_file",
)
