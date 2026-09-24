"""Contract tests for the immutable AgentTelemetry intake boundary."""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import unittest

from iclr2027.estimand_receipt_external import (
    ExternalSourceReceipt,
    load_agenttelemetry_rows,
)


SOURCE_URL = (
    "https://raw.githubusercontent.com/Krishnachaitanyakc/AgentTelemetry/"
    "8ba0ae753d51cc2837f4ef2fa450e103c3be904a/src/agenttelemetry_inspect/data/traces_v1.jsonl"
)
LICENSE_URL = (
    "https://raw.githubusercontent.com/Krishnachaitanyakc/AgentTelemetry/"
    "8ba0ae753d51cc2837f4ef2fa450e103c3be904a/LICENSE"
)
COMMIT_SHA = "8ba0ae753d51cc2837f4ef2fa450e103c3be904a"
LICENSE_BYTES = b"Apache License\nVersion 2.0, January 2004\nhttps://www.apache.org/licenses/\n"
SAMPLE_METADATA = {
    "condition": "agenttelemetry",
    "framework": "custom",
    "fault_type": "none",
    "is_control": True,
    "task": "A task",
    "n_spans": 1,
    "oracle_detected": False,
    "oracle_false_fires": [],
    "ground_truth_events": 0,
    "run_error": None,
    "harness": {
        "seed": 42,
        "rate": 1.0,
        "max_iterations": 5,
        "persona": "claude-sonnet-4",
        "dataset_version": "v1",
    },
}


def sample_row(index: int) -> dict[str, object]:
    return {
        "id": f"row-{index:03d}",
        "input": "trace",
        "metadata": SAMPLE_METADATA,
        "target": "none",
    }


def source_from_rows(rows: list[dict[str, object]], *, spaced: bool = True) -> bytes:
    separators = (", ", ": ") if spaced else (",", ":")
    return b"".join(
        json.dumps(row, separators=separators).encode("utf-8") + b"\n" for row in rows
    )


SOURCE_BYTES = source_from_rows([sample_row(index) for index in range(170)])

INTAKE_ROOT = (
    Path(__file__).resolve().parents[2]
    / ".superpowers"
    / "sdd"
    / "2026-09-01-iclr2027-estimand-receipt-study"
    / "external-source-intake-v3"
)
_TRANSPORT_KEYS = {
    "schema_version",
    "source_receipt_sha256",
    "source_commit",
    "source_path",
    "source_row_id",
    "source_row_sha256",
    "payload_sha256",
}


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _reseal_transport(value: dict[str, object]) -> dict[str, object]:
    payload = dict(value)
    payload.pop("payload_sha256", None)
    return {**payload, "payload_sha256": _sha256_json(payload)}


def _materialize_transport(
    rows: tuple[dict[str, object], ...],
    *,
    receipt_sha256: str,
    source_commit: str,
    source_path: str,
) -> tuple[dict[str, object], ...]:
    output = []
    for row in rows:
        output.append(
            _reseal_transport(
                {
                    "schema_version": "agenttelemetry-schema-identity-row/v1",
                    "source_receipt_sha256": receipt_sha256,
                    "source_commit": source_commit,
                    "source_path": source_path,
                    "source_row_id": row["id"],
                    "source_row_sha256": _sha256_json(row),
                }
            )
        )
    output.sort(key=lambda item: item["source_row_id"].encode("utf-8"))
    return tuple(output)


def _verify_transport(
    rows: tuple[dict[str, object], ...],
    *,
    receipt_sha256: str,
    source_commit: str,
    source_path: str,
    identity_by_id: dict[str, str],
) -> bytes:
    if type(rows) is not tuple or len(rows) != 170:
        raise ValueError("external transport census")
    observed_ids = []
    for row in rows:
        if type(row) is not dict or set(row) != _TRANSPORT_KEYS:
            raise ValueError("external transport row")
        if row["schema_version"] != "agenttelemetry-schema-identity-row/v1":
            raise ValueError("external transport schema")
        payload = dict(row)
        observed_seal = payload.pop("payload_sha256")
        if observed_seal != _sha256_json(payload):
            raise ValueError("external transport seal")
        if (
            row["source_receipt_sha256"] != receipt_sha256
            or row["source_commit"] != source_commit
            or row["source_path"] != source_path
        ):
            raise ValueError("external source binding")
        row_id = row["source_row_id"]
        if type(row_id) is not str or identity_by_id.get(row_id) != row["source_row_sha256"]:
            raise ValueError("external row identity binding")
        observed_ids.append(row_id)
    if observed_ids != sorted(identity_by_id, key=lambda value: value.encode("utf-8")):
        raise ValueError("external transport identity closure")
    return _canonical_bytes(
        {
            "schema_version": "agenttelemetry-schema-identity-transport/v1",
            "rows": list(rows),
        }
    )


class ExternalSourceReceiptTests(unittest.TestCase):
    def test_loads_valid_spaced_rows_but_public_factory_rejects_unpinned_bytes(self) -> None:
        self.assertEqual(len(load_agenttelemetry_rows(SOURCE_BYTES)), 170)
        with self.assertRaises(ValueError):
            ExternalSourceReceipt.from_bytes(
                SOURCE_BYTES,
                LICENSE_BYTES,
                url=SOURCE_URL,
                commit_sha=COMMIT_SHA,
                retrieved_on=date(2026, 9, 1),
            )

    def test_rejects_non_finite_json_constants(self) -> None:
        for token in (b"NaN", b"Infinity", b"-Infinity"):
            source = SOURCE_BYTES.replace(b'"rate": 1.0', b'"rate": ' + token)
            with self.subTest(token=token), self.assertRaises(ValueError):
                load_agenttelemetry_rows(source)

    def test_public_factory_rejects_structurally_valid_unpinned_source_and_license(self) -> None:
        with self.assertRaises(ValueError):
            ExternalSourceReceipt.from_bytes(
                SOURCE_BYTES,
                LICENSE_BYTES,
                url=SOURCE_URL,
                commit_sha=COMMIT_SHA,
                retrieved_on=date(2026, 9, 1),
            )

    def test_public_factory_rejects_source_and_license_raw_byte_drift(self) -> None:
        changed_source = SOURCE_BYTES.replace(b"row-169", b"row-170")
        changed_license = LICENSE_BYTES + b"notice\n"
        for source, license_bytes in (
            (changed_source, LICENSE_BYTES),
            (SOURCE_BYTES, changed_license),
        ):
            with self.subTest(source=source is changed_source), self.assertRaises(ValueError):
                ExternalSourceReceipt.from_bytes(
                    source,
                    license_bytes,
                    url=SOURCE_URL,
                    commit_sha=COMMIT_SHA,
                    retrieved_on=date(2026, 9, 1),
                )

    def test_public_factory_receipt_fields_are_exercised_by_frozen_v3_revalidation(self) -> None:
        """The exact 612,561-byte fixture is revalidated read-only outside unit tests."""
        self.assertEqual(
            ExternalSourceReceipt.__dataclass_fields__.keys(),
            {
                "schema_version", "repository", "source_commit", "source_path", "source_sha256",
                "source_bytes", "source_rows", "canonical_rows_sha256", "license_spdx",
                "license_sha256", "retrieved_on",
            },
        )


    def test_rejects_unpinned_urls_commits_and_repository_redirects(self) -> None:
        for url, commit_sha in (
            (SOURCE_URL.replace("Krishnachaitanyakc", "other"), COMMIT_SHA),
            (SOURCE_URL.replace(COMMIT_SHA, "main"), "main"),
            (SOURCE_URL.replace("raw.githubusercontent.com", "github.com"), COMMIT_SHA),
            (SOURCE_URL + "?redirect=https://example.invalid", COMMIT_SHA),
            (SOURCE_URL, COMMIT_SHA[:-1]),
            (SOURCE_URL, "0" * 40),
        ):
            with self.subTest(url=url, commit_sha=commit_sha), self.assertRaises(ValueError):
                ExternalSourceReceipt.from_bytes(
                    SOURCE_BYTES, LICENSE_BYTES, url=url, commit_sha=commit_sha,
                    retrieved_on=date(2026, 9, 1)
                )

    def test_rejects_encoding_duplicate_keys_and_wrong_row_count(self) -> None:
        malformed = (
            b"\xef\xbb\xbf" + SOURCE_BYTES,
            SOURCE_BYTES.replace(b"\n", b"\r\n"),
            SOURCE_BYTES[:-1],
            b"".join(SOURCE_BYTES.splitlines(keepends=True)[:-1]),
            SOURCE_BYTES.replace(
                b'"id": "row-000"', b'"id": "row-000", "id": "second"', 1
            ),
        )
        for source in malformed:
            with self.subTest(source=source[:20]), self.assertRaises(ValueError):
                load_agenttelemetry_rows(source)

    def test_rejects_duplicate_ids_and_wrong_root_or_metadata_schema(self) -> None:
        duplicate_ids = source_from_rows([
            sample_row(0) if index == 169 else sample_row(index) for index in range(170)
        ])
        wrong_root = [sample_row(index) for index in range(170)]
        wrong_root[0] = {**wrong_root[0], "unexpected": True}
        wrong_metadata = [sample_row(index) for index in range(170)]
        wrong_metadata[0] = {
            **wrong_metadata[0],
            "metadata": {**SAMPLE_METADATA, "n_spans": "one"},
        }
        for source in (duplicate_ids, source_from_rows(wrong_root), source_from_rows(wrong_metadata)):
            with self.subTest(source=source[:50]), self.assertRaises(ValueError):
                load_agenttelemetry_rows(source)

    def test_rejects_missing_or_non_apache_license(self) -> None:
        for license_bytes in (b"", b"MIT License\n", b"Apache License\nVersion 2.1\n"):
            with self.subTest(license_bytes=license_bytes), self.assertRaises(ValueError):
                ExternalSourceReceipt.from_bytes(
                    SOURCE_BYTES, license_bytes, url=SOURCE_URL,
                    commit_sha=COMMIT_SHA, retrieved_on=date(2026, 9, 1)
                )


class ExternalTransportGateTests(unittest.TestCase):
    def test_frozen_agenttelemetry_schema_identity_transport(self) -> None:
        source_bytes = (INTAKE_ROOT / "traces_v1.jsonl").read_bytes()
        license_bytes = (INTAKE_ROOT / "LICENSE").read_bytes()
        frozen_receipt_bytes = (INTAKE_ROOT / "external_source_receipt.json").read_bytes()

        self.assertEqual(len(source_bytes), 612_561)
        self.assertEqual(
            hashlib.sha256(source_bytes).hexdigest(),
            "99a3e63f5a7a2eb25f5c1fd9ea62f80181f44e2d5a0d1096877c18f4cbd7cb49",
        )
        self.assertEqual(len(license_bytes), 11_239)
        self.assertEqual(
            hashlib.sha256(license_bytes).hexdigest(),
            "87e71eab2d4ec25ebe384daf6436a9c8afb54a26bc7f22bcc0642075d64bda10",
        )
        self.assertEqual(
            hashlib.sha256(frozen_receipt_bytes).hexdigest(),
            "b999218d09790ff934e3fafb0fbf84212d31b938db572f6d4db8c7bcdfb11626",
        )

        frozen_receipt = json.loads(frozen_receipt_bytes.decode("utf-8"))
        self.assertEqual(frozen_receipt_bytes, _canonical_bytes(frozen_receipt) + b"\n")
        receipt = ExternalSourceReceipt.from_bytes(
            source_bytes,
            license_bytes,
            url=SOURCE_URL,
            commit_sha=COMMIT_SHA,
            retrieved_on=date.fromisoformat(frozen_receipt["retrieved_on"]),
        )
        self.assertEqual(receipt.canonical_json_bytes(), frozen_receipt_bytes)

        parsed_rows = tuple(dict(row) for row in load_agenttelemetry_rows(source_bytes))
        identity_by_id = {row["id"]: _sha256_json(row) for row in parsed_rows}
        self.assertEqual(len(parsed_rows), 170)
        self.assertEqual(len(identity_by_id), 170)
        self.assertEqual(
            hashlib.sha256(
                b"".join(_canonical_bytes(row) + b"\n" for row in parsed_rows)
            ).hexdigest(),
            "ea6c3f74202dae212da5c51e684f49e1bbe206311013e8b97fa2ce9700ec08ef",
        )

        receipt_sha256 = hashlib.sha256(frozen_receipt_bytes).hexdigest()
        transport_rows = _materialize_transport(
            parsed_rows,
            receipt_sha256=receipt_sha256,
            source_commit=frozen_receipt["source_commit"],
            source_path=frozen_receipt["source_path"],
        )
        reverse_transport_rows = _materialize_transport(
            tuple(reversed(parsed_rows)),
            receipt_sha256=receipt_sha256,
            source_commit=frozen_receipt["source_commit"],
            source_path=frozen_receipt["source_path"],
        )
        self.assertEqual(transport_rows, reverse_transport_rows)
        transport_bytes = _verify_transport(
            transport_rows,
            receipt_sha256=receipt_sha256,
            source_commit=frozen_receipt["source_commit"],
            source_path=frozen_receipt["source_path"],
            identity_by_id=identity_by_id,
        )

        first, second = transport_rows[:2]
        tampered_rows = []
        for changes in (
            {"source_row_sha256": second["source_row_sha256"]},
            {"source_row_id": second["source_row_id"]},
            {"source_receipt_sha256": "0" * 64},
            {"source_commit": "0" * 40},
            {"source_path": "src/agenttelemetry_inspect/data/other.jsonl"},
        ):
            tampered = _reseal_transport({**first, **changes})
            candidate = (tampered, *transport_rows[1:])
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                _verify_transport(
                    candidate,
                    receipt_sha256=receipt_sha256,
                    source_commit=frozen_receipt["source_commit"],
                    source_path=frozen_receipt["source_path"],
                    identity_by_id=identity_by_id,
                )

        gate_receipt = {
            "schema_version": "external-transport-gate-receipt/v1",
            "claim_scope": "schema_identity_transport_only",
            "source_rows": len(parsed_rows),
            "source_sha256": receipt.source_sha256,
            "license_sha256": receipt.license_sha256,
            "canonical_rows_sha256": receipt.canonical_rows_sha256,
            "source_receipt_sha256": receipt_sha256,
            "transport_bytes": len(transport_bytes),
            "transport_sha256": hashlib.sha256(transport_bytes).hexdigest(),
            "fully_resealed_binding_tampers_rejected": 5,
            "outcome_claim": False,
            "causal_claim": False,
            "architecture_claim": False,
        }
        print("EXTERNAL_TRANSPORT_GATE_RECEIPT=" + _canonical_bytes(gate_receipt).decode())



if __name__ == "__main__":
    unittest.main()
