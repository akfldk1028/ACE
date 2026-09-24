# Task 1 report: Closed target-roster contracts

Status: complete. Commits: none.

## Files changed

- `iclr2027/architecture_target_roster.py` (8,751 bytes; SHA-256 `a32b1f5bfb8acf772b870172e09431dd0a8be0934855a3fcb2b27567ef0b3879`)
- `tests/test_iclr2027_architecture_target_roster.py` (3,708 bytes; SHA-256 `900cb2f5fe71cae96f5e141eaf34a823414514ad0f757d9b0a50e96da92582a4`)

The implementation provides `TargetRosterV1.from_dict`, `canonical_sha256`,
`verify_target_roster`, and `TargetRosterError`. Validation closes the root,
site, source, and target schemas; requires exact built-in scalar types; checks
lowercase SHA-256 values, UTF-8 byte ordering, uniqueness, exact 3/34 and
12/11/11 allocation, `dev` split, sealing, and recursive protected identifier
rejection.

## RED

Command:

```powershell
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests -v
```

Output (exit 1):

```text
test_iclr2027_architecture_target_roster (unittest.loader._FailedTest.test_iclr2027_architecture_target_roster) ... ERROR

======================================================================
ERROR: test_iclr2027_architecture_target_roster (unittest.loader._FailedTest.test_iclr2027_architecture_target_roster)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_iclr2027_architecture_target_roster
Traceback (most recent call last):
  File "C:\Python313\Lib\unittest\loader.py", line 137, in loadTestsFromName
    module = __import__(module_name)
  File "D:\Data\25_ACE\AG\AG-Research\tests\test_iclr2027_architecture_target_roster.py", line 8, in <module>
    from iclr2027.architecture_target_roster import (
ModuleNotFoundError: No module named 'iclr2027.architecture_target_roster'

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
```

## GREEN

Command:

```powershell
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests -v
```

Output (exit 0):

```text
test_evidence_fields_and_conditions_cannot_inflate_targets (...) ... ok
test_exact_12_11_11_roster_is_accepted (...) ... ok
test_public_records_reject_protected_values_recursively (...) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.002s

OK
```

Ruff command:

```powershell
C:\Python313\python.exe -E -B -m ruff check iclr2027/architecture_target_roster.py tests/test_iclr2027_architecture_target_roster.py
```

Output (exit 0):

```text
All checks passed!
```

## Self-review

- Confirmed production code was added only after the independent test module
  failed from the expected missing import.
- Confirmed duplicate target-spec hashes fail even after resealing, so evidence
  and condition fields cannot increase the valid target count.
- Confirmed protected identifiers are found recursively before row-key errors,
  preserving the required public-record error contract.
- Re-ran the exact focused unittest and Ruff commands after the final strict
  scalar-type edit; both exited 0.

## Initial concern

The initial row-contract inference below was superseded by the binding model in
Fix Round 1. No commits were created.

## Fix Round 1

The independent review corrected the binding row model. The implementation now
has no public source rows: sites are exactly `{site_ref, area_bin}` and targets
are exactly `{target_ref, site_ref, program, subject_kind, attempt_stage,
route_kind, target_spec_sha256, source_ids}`. `source_ids` must be nonempty,
unique, and UTF-8 byte-ordinal. The recursive audit now rejects raw 19-digit
PNU, address, URI/URL, filesystem path, condition, decision/outcome, mutation,
gold/private/internal/secret, native/challenged categories, and path- or
URI-like strings while allowing `source_ids` and `target_spec_sha256`.

### RED

Command:

```powershell
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests -v
```

Output (exit 1):

```text
Ran 4 tests in 0.208s

FAILED (failures=16, errors=2)
```

The exact new-model acceptance tests errored with `TargetRosterError:
site_keys`; the prior validator expected the obsolete site/source model. The
protected-vocabulary subtests also failed because the prior recursive audit did
not recognize the reviewed protected names and values.

### GREEN

Command:

```powershell
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests -v
```

Output (exit 0):

```text
test_evidence_fields_and_conditions_cannot_inflate_targets (...) ... ok
test_exact_12_11_11_roster_is_accepted (...) ... ok
test_exact_public_rows_accept_source_ids_and_reject_legacy_fields (...) ... ok
test_public_records_reject_protected_values_recursively (...) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.011s

OK
```

Ruff command:

```powershell
C:\Python313\python.exe -E -B -m ruff check iclr2027/architecture_target_roster.py tests/test_iclr2027_architecture_target_roster.py
```

Output (exit 0):

```text
All checks passed!
```

### Final identities

- `iclr2027/architecture_target_roster.py`: 8,522 bytes; SHA-256 `11d7e304600ade22e0a5b9c192a2fa74cafed989edcf7ed7a4ecd7515ffa7b70`
- `tests/test_iclr2027_architecture_target_roster.py`: 4,915 bytes; SHA-256 `527eee6208d386e80cf5bd3cb454de6c24f4f8df6c205212d8668c82d835dcc8`

No commits were created. Concern: none remaining from the reviewed contract.
