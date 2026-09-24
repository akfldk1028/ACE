# Task 3 report — offline builder and freeze receipt v2

## Scope and changed files

- `build_iclr2027_architecture_target_roster.py` — offline input validator, fresh-root builder transaction, and CLI.
- `iclr2027/architecture_target_roster.py` — exact-key `LegacyBindingsV1`, `IndependentReviewV1`, and `FreezeReceiptV2` constructors.
- `tests/test_iclr2027_architecture_target_roster.py` — synthetic on-disk intake fixtures and builder transaction tests.

No commits were created.

## TDD evidence

### RED

Command:

```text
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterBuilderTests -v
```

Exact result before implementation:

```text
ImportError: cannot import name 'FreezeReceiptV2' from 'iclr2027.architecture_target_roster'
Ran 1 test in 0.000s
FAILED (errors=1)
```

This was the expected missing Task-3 receipt interface.

### GREEN

Command:

```text
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterBuilderTests -v
```

Exact result:

```text
test_builder_leaves_no_partial_release_on_failure ... ok
test_builder_writes_only_to_fresh_output_and_emits_exact_receipt ... ok
test_release_records_require_exact_fields_and_bindings ... ok

Ran 3 tests in 0.839s

OK
```

Additional focused-module verification:

```text
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster -v
Ran 20 tests in 0.968s
OK
```

## CLI, capability, and lint checks

```text
C:\Python313\python.exe -E -B build_iclr2027_architecture_target_roster.py --help
exit 0
```

The help lists required `--input-root` and `--output-root` arguments.

```text
rg -n "requests|urllib|httpx|Claude|OpenAI|subprocess|heldout|test_registry|os\.environ" build_iclr2027_architecture_target_roster.py iclr2027/architecture_target_roster.py
NO_MATCHES
```

```text
C:\Python313\python.exe -E -B -m ruff check build_iclr2027_architecture_target_roster.py iclr2027/architecture_target_roster.py tests/test_iclr2027_architecture_target_roster.py
All checks passed!
```

## AST and raw-file pins

| File | Raw SHA-256 | AST SHA-256 |
| --- | --- | --- |
| `build_iclr2027_architecture_target_roster.py` | `f882a4c8e073ac2aab0dc4f75699b6ebc900fb0f6abc48bf97f62b4af7d1114e` | `9d15bca944a07db864975a12dcd1447e294b102cb6e793a6ea67c09769c01862` |
| `iclr2027/architecture_target_roster.py` | `7d08608c8af8801cf79e679ce74e08807909dd5945e0850ed0299ac4b814dc18` | `3944ec0db93e92b39cc4e091055b7b0ca20145ff452c3605b27def3f9b9f4809` |
| `tests/test_iclr2027_architecture_target_roster.py` | `62a014815303d53ee83866d2ee9e8638953b57f7bfbee5ee7c9c0b249feea74b` | `1f0d7569e5a4f2c0e8dd28d76d003c88c011bba8f0fa10f745a853f939dd81fc` |

AST pins are SHA-256 over `ast.dump(ast.parse(utf8_source), annotate_fields=True, include_attributes=False)` UTF-8 bytes.

## Self-review and concerns

- The builder accepts only an absolute, non-reparse input directory with the exact specified regular-file layout and source-object names; it rejects a pre-existing or nested output root before creating a temporary release directory.
- Source object byte length and SHA-256 are rechecked before `verify_admission_inputs()`; a failed validation creates no output root.
- The temporary directory is freshly created as a resolved sibling under the verified output parent and only that fresh directory is eligible for cleanup. Each JSON file uses the existing canonical LF/final-LF atomic writer, then the completed directory is renamed into place.
- The fixtures are synthetic. Passing them verifies the offline transaction and schema bindings only; it does not claim real candidate admission.
- Windows does not permit `os.fsync()` on a directory descriptor (`PermissionError: 13` in this environment). The existing atomic JSON writer fsyncs every release file before its atomic replacement; the complete staging directory is then renamed on the same verified parent volume.

## Fix round 1/5 — durable no-replace publication

The prior final directory replacement was replaced with a Windows-only no-replace publication primitive. `_publish_fresh_directory()` calls `MoveFileExW(staging, output, 0x8)`: `0x8` is `MOVEFILE_WRITE_THROUGH`, and `MOVEFILE_REPLACE_EXISTING` (`0x1`) is deliberately absent. A destination collision (including a destination created after the early freshness check) produces `publication_destination_exists`; other API failures produce `publication_failed`. Unsupported platforms produce `publication_unsupported` rather than using a racy fallback.

The staging cleanup remains constrained to the freshly created resolved sibling; a competing destination is never removed or modified.

### Fix-round RED

Command:

```text
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterBuilderTests -v
```

Exact result before the new primitive:

```text
Ran 11 tests in 3.469s
FAILED (errors=3)
```

Each failure was the expected missing `_windows_move_file_ex_w` helper, reached by the injected-publication-failure, race-created-destination, and write-through/no-replace flag-witness tests.

### Fix-round GREEN

```text
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterBuilderTests -v
Ran 11 tests in 3.456s
OK

C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster -v
Ran 28 tests in 3.881s
OK

C:\Python313\python.exe -E -B build_iclr2027_architecture_target_roster.py --help
exit 0

rg -n "requests|urllib|httpx|Claude|OpenAI|subprocess|heldout|test_registry|os\.environ" build_iclr2027_architecture_target_roster.py iclr2027/architecture_target_roster.py
NO_MATCHES

C:\Python313\python.exe -E -B -m ruff check build_iclr2027_architecture_target_roster.py iclr2027/architecture_target_roster.py tests/test_iclr2027_architecture_target_roster.py
All checks passed!
```

The builder tests now cover: sentinel preservation for a pre-existing output; input/output nesting rejection; unexpected files, directories, and a safely constructible link; review validation before staging; injected publication failure cleanup; race-created destination preservation; a complete file/directory release census; and the focused Windows flag witness.

### Final pins after fix round 1

| File | Raw SHA-256 | AST SHA-256 |
| --- | --- | --- |
| `build_iclr2027_architecture_target_roster.py` | `7e8e39e58083f60cc27603b708ebbeac52dcfb4d6df0c3d0cef7f15b57d3f86b` | `c3f21471ca5aaafcdc695f8f330166ebc5719defa2f1d2237da7b87bf8aa2e76` |
| `iclr2027/architecture_target_roster.py` | `7d08608c8af8801cf79e679ce74e08807909dd5945e0850ed0299ac4b814dc18` | `3944ec0db93e92b39cc4e091055b7b0ca20145ff452c3605b27def3f9b9f4809` |
| `tests/test_iclr2027_architecture_target_roster.py` | `9e7c6a36ca2482eaf2e62d3f2faf45f4e1b26ff46ac3df803d1a7cec21d95468` | `a003c58e69bbb655e6123e414559ef64e8a5898c2e88f677c244bdfbec44ab98` |

The same AST pin method from the initial report was used. No commits were created.

### Deferred concern

The requested raw-`OSError` handling issue was not changed in this round. The new wrapper maps only the publication API's failure result and setup failure to stable publication blockers.
