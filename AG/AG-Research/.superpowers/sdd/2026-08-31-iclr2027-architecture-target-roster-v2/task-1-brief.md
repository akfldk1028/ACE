### Task 1: Closed target-roster contracts

**Files:**
- Create: `iclr2027/architecture_target_roster.py`
- Create: `tests/test_iclr2027_architecture_target_roster.py`

**Interfaces:**
- Produces: `TargetRosterV1.from_dict()`.
- Produces: `canonical_sha256(value: Mapping[str, object], *, omit: frozenset[str] = frozenset()) -> str` and `verify_target_roster(roster: Mapping[str, object]) -> TargetRosterV1`.
- Consumes later: every builder/integration task imports these exact constructors and validators.

- [ ] **Step 1: Write the independent failing schema tests**

```python
class TargetRosterSchemaTests(unittest.TestCase):
    def test_exact_12_11_11_roster_is_accepted(self) -> None:
        roster = make_roster(allocation=(12, 11, 11))
        parsed = verify_target_roster(roster)
        self.assertEqual((parsed.site_count, parsed.target_count), (3, 34))

    def test_evidence_fields_and_conditions_cannot_inflate_targets(self) -> None:
        roster = make_roster(allocation=(12, 11, 11))
        roster["targets"][1]["target_spec_sha256"] = roster["targets"][0]["target_spec_sha256"]
        with self.assertRaisesRegex(TargetRosterError, "target_spec_duplicate_or_mutated"):
            verify_target_roster(reseal(roster, "roster_sha256"))

    def test_public_records_reject_protected_values_recursively(self) -> None:
        for key, value in protected_public_mutations():
            with self.subTest(key=key):
                with self.assertRaisesRegex(TargetRosterError, "protected_identifier"):
                    verify_target_roster(make_roster(extra_target_field={key: value}))
```

- [ ] **Step 2: Run RED**

Run: `C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests -v`

Expected: import failure for `iclr2027.architecture_target_roster`.

- [ ] **Step 3: Implement exact records and canonical validators**

```python
TARGET_ROSTER_SCHEMA = "ace.iclr2027.architecture_target_roster.v1"
ALLOCATION = (12, 11, 11)
EVIDENCE_FAMILIES = ("geometry", "law", "parking", "program", "site")

class TargetRosterError(ValueError):
    pass

def canonical_sha256(value: Mapping[str, object], *, omit: frozenset[str] = frozenset()) -> str:
    payload = {key: item for key, item in value.items() if key not in omit}
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

@dataclass(frozen=True, slots=True)
class TargetRosterV1:
    schema_version: str
    roster_version: str
    projection_identity_commitment: str
    split: str
    site_count: int
    target_count: int
    allocation: tuple[int, ...]
    sites: tuple[Mapping[str, object], ...]
    targets: tuple[Mapping[str, object], ...]
    roster_sha256: str
```

Enforce exact root/row key sets, exact built-in scalar types, lowercase 64-hex hashes, byte-ordinal site/target/source ordering, three unique sites, 34 unique target refs/spec hashes, allocation by site, `split == "dev"`, and recursive protected-name/value rejection.

- [ ] **Step 4: Run GREEN and Ruff**

Run: `C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests -v`

Run: `C:\Python313\python.exe -E -B -m ruff check iclr2027/architecture_target_roster.py tests/test_iclr2027_architecture_target_roster.py`

Expected: both exit 0.

- [ ] **Step 5: Record Task-1 file sizes and SHA-256 pins in the report; do not commit the dirty shared tree**

