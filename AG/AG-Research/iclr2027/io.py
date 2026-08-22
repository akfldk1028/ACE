"""Canonical and atomic serialization for research artifacts."""

from __future__ import annotations

import dataclasses
import csv
import hashlib
import io
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


def _jsonable(value: Any) -> Any:
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return _jsonable(to_dict())
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return _jsonable(dataclasses.asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def canonical_json(value: Any) -> str:
    """Serialize a JSON-compatible value deterministically."""

    return json.dumps(
        _jsonable(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_json(value: Any) -> str:
    """Return the SHA-256 of the canonical UTF-8 JSON representation."""

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def write_json_atomic(path: Path, value: Any) -> None:
    """Atomically write one canonical JSON record."""

    _write_text_atomic(path, canonical_json(value) + "\n")


def write_jsonl_atomic(path: Path, rows: Iterable[Any]) -> None:
    """Atomically write canonical JSON Lines records."""

    lines = [canonical_json(row) for row in rows]
    _write_text_atomic(path, "".join(f"{line}\n" for line in lines))


def write_csv_atomic(
    path: Path,
    rows: Iterable[Mapping[str, Any]],
    *,
    fieldnames: Sequence[str],
) -> None:
    """Atomically replace a CSV with one header and canonical field order."""

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row[field] for field in fieldnames})
    _write_text_atomic(path, buffer.getvalue())


_FORBIDDEN_PUBLIC_KEYS = {"expected_decision", "mutation_family", "gold_record"}


def assert_public_gold_separation(value: Any, path: str = "packet") -> None:
    """Fail if a public payload contains fields reserved for gold records."""

    if isinstance(value, Mapping):
        for raw_key, item in value.items():
            key = str(raw_key)
            lowered = key.lower()
            if lowered in _FORBIDDEN_PUBLIC_KEYS or lowered.startswith("gold_"):
                raise ValueError(f"forbidden public field at {path}.{key}")
            assert_public_gold_separation(item, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            assert_public_gold_separation(item, f"{path}[{index}]")
