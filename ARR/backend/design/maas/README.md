# ARR MAAS

## Start here

MAAS turns typed `GeometryProgram` inputs into auditable MASS geometry. Keep
generation, canonical geometry, legal review, visual review, and selection as
separate authorities. A rendered image or a semantic family label is never a
substitute for the compiled indexed mesh.

For the current product contract and unresolved gaps, read:

- `docs/ai-session-memory/maas-mass-flow/00_READ_FIRST.md`
- `docs/ai-session-memory/maas-mass-flow/03_MODULE_MAP.md`
- `docs/ai-session-memory/maas-mass-flow/04_VALIDATION_GAPS.md`

## Production paths

There are two different portfolio paths. Do not merge them implicitly.

- Pre-legal creative choice pool: fast geometry/diversity diagnosis without
  law, parking, capacity, program-fit, or VLM acceptance.
- Full BOOK legal portfolio: complete PNU-derived generation, law, parking,
  program, final-VLM, and selection flow.

Single-MASS request-time execution is separately owned by `single_execution/`.

## Pre-legal creative path

```text
generate_maas_creative_100
-> creative_program_author
-> affine_normalization (one 1/1 UnitBox -> explicit Matrix4 BaseVolume)
-> creative_book_supply (6 scopes, executable 30/20/9 BOOK schedule)
-> creative_floor_portfolio
-> geometry_language.compiler / geometry_language.gate
-> creative_morphology
-> immutable candidate JSON + deterministic PNG board
```

Ownership:

- `creative_program_author.py`: normalize exact LLM programs and read accepted
  author-cache entries.
- `creative_book_supply.py`: assign canonical BOOK principles and prove their
  materialization from executable AST nodes rather than family metadata.
- `creative_floor_portfolio.py`: compile physical candidates and require one
  connected, watertight, manifold mesh. Deterministic `count=100` uses a
  compatibility matching pass so all 30 base operatives, 20 combinations, and
  9 aggregations occur before any principle repeats.
- `creative_morphology.py`: scale-invariant mesh descriptor, pair distance,
  and near-duplicate decision.
- `generate_maas_creative_100.py`: CLI options and immutable artifact writing.
  Hybrid runs write pre-legal ledger v2 with BOOK coverage plus UnitBox,
  Matrix4, and affine-shorthand audit counts.

This path must label every result `PRE-LEGAL / NOT EVALUATED`. The explicit
`recipe_fixture` mode is for regression tests and demos only. Production
authorship uses exact payload, cache, or LLM-authored `GeometryProgram` values.

## Full BOOK legal portfolio path

```text
management/commands/benchmark_maas_book_program_portfolios.py
-> book_language/portfolio_benchmark.py
-> book_language/candidate_generation.py
-> book_language/portfolio_replenishment.py
-> book_language/downstream_hard_gate.py
-> book_language/final_vlm_cycle.py
-> book_language/portfolio_selection.py
```

The full path owns PNU law, capacity, parking, program-fit, final VLM, and
selection authority. `book_language/quality_diversity_archive.py` stores full
BOOK `_Candidate` values; it is not the pre-legal creative archive.

## Geometry authority

`geometry_language/` owns the only canonical AST, compiler, mesh gate, and
typed geometry repair path. Admission claims must be derived from the exact
compiled vertices and triangles. Never accept a MASS from metadata, a PNG, or
an earlier mesh hash when canonical geometry fails.

Every creative MASS starts from exactly one canonical 1/1 UnitBox. Its direct
BaseVolume authority is an explicit homogeneous `matrix4`; affine shorthand
(`scale`, `rotate`, `translate`, `mirror`, `shear`) is lowered before the final
program is admitted. BOOK scope labels are `1/1`, `3/8`, `1/2`, `1/4`, `1/8`,
and `1/16`. Architectural references such as Qatar National Library are
capability references only and never recipe names, operators, or quotas.

## Generated evidence and memory

- `docs/playwright/`: run-scoped PNG/JSON evidence, not executable source.
- `docs/ai-session-memory/`: reviewed checkpoints and cache evidence, not a
  place to add production branching.
- `backend/tmp_mass_check/`: disposable diagnostics only.

Historical artifacts are immutable. A new run writes a new directory rather
than overwriting prior evidence.

## Tests by owner

- Author/cache normalization: `design/test_maas_creative_program_author.py`
- Pre-legal morphology: `design/test_maas_creative_morphology.py`
- Pre-legal compilation: `design/test_maas_creative_floor_portfolio.py`
- Pre-legal command/artifacts:
  `design/test_maas_creative_floor_portfolio_command.py`
- Full BOOK flow: focused `design/test_maas_*` and task-specific BOOK tests
  listed in `docs/ai-session-memory/maas-mass-flow/07_FULL_TEST_CONTRACT.md`

## Rules for AI changes

1. Trace the existing entry point and owner before creating a module.
2. Write a failing focused test before changing behavior.
3. Report input, compile, structural, uniqueness, morphology, and retained
   counts separately; do not report only the final number.
4. Named family labels are diagnostic evidence, never generation quotas.
5. Never recover a rejected form with a forced stepped replay, cloned mesh,
   fixture fallback, or weakened gate.
6. A provider 429 may stop new transport, but cached and already-authored
   programs must continue through local compilation.
7. Generated artifacts are not source files and must not be imported by
   production code.
8. The full BOOK benchmark is not the pre-legal command; changes must stay in
   their owning path unless an explicit integration plan says otherwise.
9. Most current creative source/test files are absent from clean inner `HEAD`.
   Do not stage whole untracked files or absorb unrelated user work. Build and
   audit task-only patches against explicit pre-task snapshots.
