from dataclasses import replace
from hashlib import sha256
import unittest

from iclr2027.oacs_domain_census import (
    DomainCensusError,
    DomainCensusV1,
    DomainUnitV1,
    domain_census_bytes,
    validate_architecture_census,
    validate_jci_census,
    verify_domain_census_bytes,
)


class OacsDomainCensusTests(unittest.TestCase):
    """Synthetic, outcome-free fixtures for the two unpooled domains."""

    def _hash(self, label: str) -> str:
        return sha256(label.encode("utf-8")).hexdigest()

    def _census(
        self, units: tuple[DomainUnitV1, ...], label: str = "manifest"
    ) -> DomainCensusV1:
        return DomainCensusV1(
            schema="oacs-domain-census/v1",
            units=units,
            source_manifest_sha256=self._hash(label),
        )

    def _unit(
        self,
        domain: str,
        cluster: str,
        unit: str,
        partition: str,
        families: tuple[str, ...],
    ) -> DomainUnitV1:
        tag = f"{domain}|{cluster}|{unit}|{partition}|{'|'.join(families)}"
        return DomainUnitV1(
            domain=domain,
            cluster_id=cluster,
            unit_id=unit,
            partition=partition,
            obligation_families=families,
            public_packet_sha256=self._hash(f"public|{tag}"),
            evaluator_commitment_sha256=self._hash(f"commitment|{tag}"),
            source_rights_status="unrestricted",
            blind_overlap_sha256=self._hash(f"overlap|{tag}"),
        )

    def architecture_fixture(
        self, sites: int = 8, units: int = 64, audit_units: int = 24
    ) -> DomainCensusV1:
        rows: list[DomainUnitV1] = []
        for position in range(units):
            partition = "audit" if position < audit_units else "focal"
            cluster_number = (
                position % 3 + 1
                if partition == "audit"
                else 4 + ((position - audit_units) % max(1, sites - 3))
            )
            rows.append(
                self._unit(
                    "architecture",
                    f"cluster-{cluster_number:02d}",
                    f"unit-{position:03d}",
                    partition,
                    (f"family-{position % 5}",),
                )
            )
        return self._census(
            tuple(sorted(rows, key=lambda row: (row.cluster_id, row.unit_id)))
        )

    def jci_fixture(
        self, repositories: int = 8, prefixes: int = 80, resource_prefixes: int = 20
    ) -> DomainCensusV1:
        rows: list[DomainUnitV1] = []
        for position in range(prefixes):
            families = (
                ("resource",) if position < resource_prefixes else ("compatibility",)
            )
            rows.append(
                self._unit(
                    "jci",
                    f"cluster-{position % repositories + 1:02d}",
                    f"unit-{position:03d}",
                    "focal",
                    families,
                )
            )
        return self._census(
            tuple(sorted(rows, key=lambda row: (row.cluster_id, row.unit_id)))
        )

    def test_architecture_requires_8_clusters_and_64_units(self):
        with self.assertRaisesRegex(DomainCensusError, "architecture census"):
            validate_architecture_census(self.architecture_fixture(sites=7, units=64))
        valid = validate_architecture_census(
            self.architecture_fixture(sites=8, units=64, audit_units=24)
        )
        self.assertEqual(valid.cluster_count, 8)

    def test_architecture_requires_3_24_audit_and_5_40_focal_floors(self):
        with self.assertRaisesRegex(DomainCensusError, "architecture census"):
            validate_architecture_census(self.architecture_fixture(audit_units=23))
        rows = self.architecture_fixture().units
        with self.assertRaisesRegex(DomainCensusError, "architecture census"):
            validate_architecture_census(
                self._census(tuple(replace(row, partition="focal") for row in rows))
            )

    def test_additional_committed_units_are_allowed_above_each_floor(self):
        architecture = validate_architecture_census(
            self.architecture_fixture(units=65, audit_units=25)
        )
        jci = validate_jci_census(self.jci_fixture(prefixes=81, resource_prefixes=20))
        self.assertEqual(len(architecture.units), 65)
        self.assertEqual(len(jci.units), 81)

    def test_architecture_requires_five_obligation_families(self):
        rows = tuple(
            replace(row, obligation_families=("family-0",))
            for row in self.architecture_fixture().units
        )
        with self.assertRaisesRegex(DomainCensusError, "obligation families"):
            validate_architecture_census(self._census(rows, "family-reseal"))

    def test_jci_requires_8_repositories_80_prefixes_and_resource_floor(self):
        with self.assertRaisesRegex(DomainCensusError, "resource obligation"):
            validate_jci_census(
                self.jci_fixture(repositories=8, prefixes=80, resource_prefixes=19)
            )
        for repositories, prefixes in ((7, 80), (8, 79)):
            with self.subTest(repositories=repositories, prefixes=prefixes):
                with self.assertRaisesRegex(DomainCensusError, "jci census"):
                    validate_jci_census(self.jci_fixture(repositories, prefixes))

    def test_jci_allows_a_nine_repository_predeclared_census(self):
        valid = validate_jci_census(
            self.jci_fixture(repositories=9, prefixes=80, resource_prefixes=20)
        )
        self.assertEqual(valid.cluster_count, 9)

    def test_jci_resource_obligations_span_three_repositories(self):
        rows = []
        for position, row in enumerate(self.jci_fixture().units):
            families = ("resource",) if position < 20 else ("compatibility",)
            rows.append(replace(row, obligation_families=families))
        rows = tuple(sorted(rows, key=lambda row: (row.cluster_id, row.unit_id)))
        with self.assertRaisesRegex(DomainCensusError, "resource obligation"):
            validate_jci_census(self._census(rows, "resource-reseal"))

    def test_cluster_pairs_partitions_and_native_types_are_closed(self):
        rows = self.architecture_fixture().units
        overlapping = list(rows)
        focal = next(row for row in rows if row.partition == "focal")
        overlapping[rows.index(focal)] = replace(focal, cluster_id="cluster-01")
        overlapping = tuple(
            sorted(overlapping, key=lambda row: (row.cluster_id, row.unit_id))
        )
        with self.assertRaisesRegex(DomainCensusError, "audit and focal"):
            validate_architecture_census(self._census(overlapping, "overlap-reseal"))

        duplicate = list(rows)
        duplicate[1] = replace(duplicate[1], unit_id=duplicate[0].unit_id)
        duplicate = tuple(
            sorted(duplicate, key=lambda row: (row.cluster_id, row.unit_id))
        )
        with self.assertRaisesRegex(DomainCensusError, "cluster/unit"):
            validate_architecture_census(self._census(duplicate, "duplicate-reseal"))

        with self.assertRaisesRegex(DomainCensusError, "tuple"):
            replace(rows[0], obligation_families=["family-0"])  # type: ignore[arg-type]
        with self.assertRaisesRegex(DomainCensusError, "partition"):
            replace(rows[0], partition="holdout")

    def test_public_rows_reject_protected_channels_and_nonopaque_identifiers(self):
        base = self.architecture_fixture().units[0]
        for field, value in (
            ("cluster_id", "PNU-123"),
            ("cluster_id", "D:/private/source"),
            ("unit_id", "project-name"),
            ("unit_id", "gold-label"),
            ("unit_id", "outcome-pass"),
            ("unit_id", "mutation-branch"),
            ("unit_id", "expected-decision"),
            ("unit_id", "evaluator-feedback"),
        ):
            with self.subTest(field=field, value=value):
                with self.assertRaisesRegex(DomainCensusError, "protected"):
                    replace(base, **{field: value})

    def test_row_schema_rejects_malformed_rights_and_commitments(self):
        base = self.architecture_fixture().units[0]
        for field, value in (
            ("public_packet_sha256", "g" * 64),
            ("evaluator_commitment_sha256", "A" * 64),
            ("blind_overlap_sha256", "a" * 63),
            ("source_rights_status", "permission_pending"),
        ):
            with self.subTest(field=field):
                with self.assertRaises(DomainCensusError):
                    replace(base, **{field: value})
        with self.assertRaises(DomainCensusError):
            DomainCensusV1("oacs-domain-census/v1", (), "x" * 64)

    def test_canonical_bytes_round_trip_and_reject_noncanonical_forms(self):
        census = self.architecture_fixture()
        raw = domain_census_bytes(census)
        self.assertTrue(raw.endswith(b"\n"))
        self.assertEqual(verify_domain_census_bytes(raw), census)
        mutations = (
            raw[:-1],
            raw.replace(b'{"schema"', b'{ "schema"', 1),
            raw.replace(
                b'"schema":"oacs-domain-census/v1"',
                b'"schema_x":"oacs-domain-census/v1"',
                1,
            ),
            raw.replace(b'"cluster_id"', b'"cluster_x"', 1),
            raw.replace(
                b'"schema":"oacs-domain-census/v1",',
                b'"schema":"oacs-domain-census/v1","schema":"oacs-domain-census/v1",',
                1,
            ),
        )
        for mutated in mutations:
            with self.subTest(mutated=mutated[:40]):
                with self.assertRaises(DomainCensusError):
                    verify_domain_census_bytes(mutated)

    def test_resealed_partition_and_family_mutations_reject_after_canonical_parse(self):
        census = self.architecture_fixture()
        rows = list(census.units)
        cases = []
        cases.append(
            ("partition", tuple(replace(row, partition="focal") for row in rows))
        )
        cases.append(
            (
                "family",
                tuple(replace(row, obligation_families=("family-0",)) for row in rows),
            )
        )
        for name, mutated_rows in cases:
            with self.subTest(name=name):
                with self.assertRaises(DomainCensusError):
                    resealed = self._census(
                        tuple(
                            sorted(
                                mutated_rows,
                                key=lambda row: (row.cluster_id, row.unit_id),
                            )
                        ),
                        f"re-sealed-{name}",
                    )
                    validate_architecture_census(
                        verify_domain_census_bytes(domain_census_bytes(resealed))
                    )

    def test_parser_rejects_malformed_rights_and_commitments(self):
        census = self.architecture_fixture()
        raw = domain_census_bytes(census)
        malformed = (
            raw.replace(b'"unrestricted"', b'"permission_pending"', 1),
            raw.replace(
                b'"blind_overlap_sha256":"'
                + self._hash(
                    "overlap|architecture|cluster-01|unit-000|audit|family-0"
                ).encode(),
                b'"blind_overlap_sha256":"' + b"a" * 63,
                1,
            ),
            raw.replace(census.source_manifest_sha256.encode(), b"g" * 64, 1),
        )
        for mutated in malformed:
            with self.subTest(mutated=mutated[:64]):
                with self.assertRaises(DomainCensusError):
                    verify_domain_census_bytes(mutated)

    def test_parser_rejects_protected_identifier_in_canonical_bytes(self):
        raw = domain_census_bytes(self.architecture_fixture())
        with self.assertRaisesRegex(DomainCensusError, "protected"):
            verify_domain_census_bytes(raw.replace(b'"unit-000"', b'"outcome-pass"', 1))

    def test_valid_reseal_changes_canonical_census_bytes_and_digest(self):
        census = self.architecture_fixture()
        original_bytes = domain_census_bytes(census)
        first = census.units[0]
        replacement = replace(
            first,
            public_packet_sha256=self._hash("alternate-public-commitment"),
            evaluator_commitment_sha256=self._hash("alternate-evaluator-commitment"),
            source_rights_status="permission_granted",
            blind_overlap_sha256=self._hash("alternate-blind-overlap"),
        )
        resealed = DomainCensusV1(
            schema=census.schema,
            units=(replacement,) + census.units[1:],
            source_manifest_sha256=self._hash("alternate-source-manifest"),
        )
        resealed_bytes = domain_census_bytes(resealed)
        self.assertEqual(verify_domain_census_bytes(resealed_bytes), resealed)
        self.assertEqual(validate_architecture_census(resealed), resealed)
        self.assertNotEqual(resealed_bytes, original_bytes)
        self.assertNotEqual(
            sha256(resealed_bytes).hexdigest(), sha256(original_bytes).hexdigest()
        )

    def test_canonical_parser_rejects_ordering_and_jci_resource_reseal(self):
        census = self.architecture_fixture()
        reversed_rows = tuple(reversed(census.units))
        with self.assertRaisesRegex(DomainCensusError, "byte-sorted"):
            self._census(reversed_rows, "order-reseal")

        jci = self.jci_fixture(resource_prefixes=20)
        rows = tuple(
            replace(row, obligation_families=("compatibility",)) if index == 0 else row
            for index, row in enumerate(jci.units)
        )
        resealed = self._census(rows, "jci-resource-reseal")
        with self.assertRaisesRegex(DomainCensusError, "resource obligation"):
            validate_jci_census(
                verify_domain_census_bytes(domain_census_bytes(resealed))
            )


if __name__ == "__main__":
    unittest.main()
