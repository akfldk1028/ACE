# Task 6 independent review

## Verdict

FIX REQUIRED — one Important finding.

## Important

`run_exp08_architecture.py` created `checkpoint_dir` before
`validate_run_manifest()` and `_existing_compatible_manifest()`. An independent
dry witness supplied valid verified sidecars with manifest-invalid model value
`private-model`; the command raised `ValueError` but left an empty checkpoint
directory. Existing coverage exercised sidecar-specific failures but not this
later manifest-validation failure.

Required correction: move directory creation after manifest validation and
compatibility checking, add the regression, and rerun Task 6 gates.

## Fresh evidence

- Exact Task-6 command: 35/35 passed in 33.294 seconds.
- Ruff check passed; Ruff format check reported all three files formatted.
- Independent fresh-root dry-run: exit 0, zero
  `ExperimentRunner.run_single` calls, schema v3, counts 30/30/64, exactly
  three v3-only fields, and independently valid receipt self-hash.
- All reported raw and normalized-AST pins matched.
- No file edit, model call, network access, git action, or protected-data access
  occurred during review.
