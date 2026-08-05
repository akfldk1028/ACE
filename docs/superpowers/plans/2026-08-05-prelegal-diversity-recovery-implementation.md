# Pre-Legal MASS Diversity Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore an auditable same-PNU twenty-card pre-legal MASS board from cached plus fresh LLM-authored GeometryPrograms, with exact per-stage PASS counts and graceful partial completion after HTTP 429.

**Architecture:** Extend the existing `generate_maas_creative_100` pre-legal path instead of adding behavior to the full BOOK portfolio benchmark. Preserve `creative_program_author.py` as the cache/author normalization boundary, add one focused hybrid-supply coordinator, make `creative_floor_portfolio.py` expose a tolerant typed report using the existing `creative_morphology` distance decision while retaining its current strict wrapper, and persist one bounded stage/rejection ledger beside the existing board and candidate research bundles.

**Tech Stack:** Python 3, Django management commands, existing GeometryProgram compiler/gate, immutable dataclasses, Pillow board rendering, unittest-style Django tests, JSON evidence, PowerShell, pytest.

## Global Constraints

- Target PNU is exactly `1168011800104170004`; program context is `neighborhood`.
- The diagnostic target is exactly 20 retained pre-legal candidates.
- Fresh LLM author transport is allowed, with at most 3 attempts per invocation.
- Paid VLM request count is exactly 0 for this diagnostic.
- Cache lookup does not consume a fresh author attempt.
- The first HTTP 429 opens an invocation-scoped circuit; all later fresh attempts are deferred without sleeping.
- Cached programs, already returned fresh programs and valid carried inputs continue through canonical compilation after a 429.
- Candidate admission requires the existing canonical compiler plus connected, watertight and manifold evidence.
- Program hash, geometry hash and normalized authored-mesh hash must be unique.
- Existing morphology-distance thresholds remain unchanged.
- Named families are post-hoc evidence only; named-family quotas, recipe fallback, candidate cloning and forced stepped replay are prohibited.
- If 20 candidates cannot be retained, persist an explicit `partial` board and exact supply/rejection evidence; do not raise before artifacts are written.
- Output is labeled `PRE-LEGAL / NOT LAW, PARKING, CAPACITY OR VLM ACCEPTED`.
- Preserve existing payload, LLM, cache-pool and explicit `recipe_fixture` command modes.
- Do not modify law, parking, capacity, final VLM, selector, profiled-mesh repair or full BOOK benchmark behavior.
- All edits in the inner repository must be isolated from the existing dirty/untracked dependency stack with pre-task snapshots and task-only patch review.

---

### Task 1: Capture the baseline and replace the unreadable MAAS entry map

**Files:**
- Modify: `ARR/backend/design/maas/README.md`
- Test without modification: `ARR/backend/design/test_maas_creative_floor_portfolio.py`
- Test without modification: `ARR/backend/design/test_maas_creative_floor_portfolio_command.py`
- Test without modification: `ARR/backend/design/test_maas_creative_morphology.py`
- Test without modification: `ARR/backend/design/test_maas_creative_program_author.py`

**Interfaces:**
- Consumes: the current `generate_maas_creative_100 -> build_creative_floor_portfolio -> compile_geometry_program -> compilation_gate` path.
- Produces: an AI-readable ownership map and immutable baseline output for later PASS-count comparisons.

- [ ] **Step 1: Snapshot every planned inner file before editing**

Run from `D:\Data\25_ACE\ARR`:

```powershell
$taskRoot = 'D:\Data\25_ACE\.superpowers\sdd\prelegal-diversity'
New-Item -ItemType Directory -Force $taskRoot | Out-Null
$files = @(
  'backend/design/maas/README.md',
  'backend/design/maas/creative_program_author.py',
  'backend/design/maas/creative_floor_portfolio.py',
  'backend/design/management/commands/generate_maas_creative_100.py',
  'backend/design/test_maas_creative_program_author.py',
  'backend/design/test_maas_creative_floor_portfolio.py',
  'backend/design/test_maas_creative_floor_portfolio_command.py'
)
foreach ($path in $files) {
  $name = $path.Replace('/', '__')
  Copy-Item -LiteralPath $path -Destination (Join-Path $taskRoot "$name.before")
}
git status --short -- $files
```

Expected: snapshots exist outside the inner repository. The creative source/test files are recorded as existing untracked dependencies; no index changes.

- [ ] **Step 2: Run the existing focused baseline and record exact counts**

```powershell
Set-Location D:\Data\25_ACE\ARR\backend
$env:DJANGO_SETTINGS_MODULE='config.settings'
python -m pytest `
  design/test_maas_creative_program_author.py `
  design/test_maas_creative_morphology.py `
  design/test_maas_creative_floor_portfolio.py `
  design/test_maas_creative_floor_portfolio_command.py -q 2>&1 |
  Tee-Object D:\Data\25_ACE\.superpowers\sdd\prelegal-diversity\baseline-tests.txt
```

Expected: capture the exact passed/failed count and runtime in `D:\Data\25_ACE\.superpowers\sdd\prelegal-diversity\baseline-tests.txt`. If any test fails, preserve the traceback and distinguish pre-existing failure from later task changes.

- [ ] **Step 3: Replace the mojibake README with the executable ownership map**

The rewritten `ARR/backend/design/maas/README.md` must contain these sections and exact routing facts:

```markdown
# ARR MAAS

## Start here
## Production paths
## Pre-legal creative path
## Full BOOK legal portfolio path
## Geometry authority
## Generated evidence and memory
## Tests by owner
## Rules for AI changes
```

Under `Pre-legal creative path`, document:

```text
generate_maas_creative_100
-> creative_program_author
-> creative_floor_portfolio
-> geometry_language.compiler / geometry_language.gate
-> creative_morphology
-> immutable candidate JSON + PNG board
```

Under `Rules for AI changes`, state that generated artifacts are not source, family labels are not generation quotas, the full BOOK benchmark is not the pre-legal command, and source/test files currently absent from clean `HEAD` must not be staged wholesale.

- [ ] **Step 4: Audit the documentation-only change**

```powershell
git diff --check -- backend/design/maas/README.md
git diff --no-index -- `
  D:\Data\25_ACE\.superpowers\sdd\prelegal-diversity\backend__design__maas__README.md.before `
  backend/design/maas/README.md
```

Expected: readable UTF-8 documentation only; no Python behavior change.

---

### Task 2: Add cache-first hybrid author supply with a typed 429 circuit

**Files:**
- Create: `ARR/backend/design/maas/creative_author_supply.py`
- Modify: `ARR/backend/design/maas/creative_program_author.py`
- Modify: `ARR/backend/design/test_maas_creative_program_author.py`
- Create: `ARR/backend/design/test_maas_creative_author_supply.py`

**Interfaces:**
- Consumes: `CreativeAuthoredProgram`, accepted v3 author-cache JSON, and a supplied fresh-author callback.
- Produces: `cached_authored_programs(cache_root: Path, *, limit: int) -> tuple[CreativeAuthoredProgram, ...]` and `collect_creative_author_supply(*, target_count: int, cached_programs: Iterable[CreativeAuthoredProgram], fresh_author: FreshAuthor, retained_count: RetainedCount, max_fresh_requests: int = 3) -> CreativeAuthorSupplyResult`.

- [ ] **Step 1: Write RED tests for non-strict cache scanning**

Add to `test_maas_creative_program_author.py`:

```python
def test_cache_scan_returns_available_unique_programs_without_exact_count(self):
    with TemporaryDirectory() as temporary:
        cache_root = Path(temporary)
        first, second = self._accepted_cache_programs()
        self._write_accepted_cache(cache_root, (first, second))

        programs = creative_program_author.cached_authored_programs(
            cache_root,
            limit=20,
        )

    self.assertEqual(len(programs), 2)
    self.assertTrue(all(item.author_evidence["cache_hit"] for item in programs))
```

Extract the existing `first_builder` and `second_builder` setup from
`test_cache_pool_reads_only_unique_accepted_exact_llm_programs` into
`_accepted_cache_programs(self) -> tuple[GeometryProgram, GeometryProgram]`.
Add `_write_accepted_cache(self, cache_root: Path, programs: tuple[GeometryProgram, ...])`
that creates the directory and writes one accepted v3 cache JSON containing
`[program.to_dict() for program in programs]`, model `cache-pool-model` and
response ID `resp-cache-pool`. Reuse these helpers in the old and new tests so
the cache contract is defined once.

Retain the existing strict `authored_programs_from_cache_pool(..., expected_count=20)` behavior and its shortage error.

- [ ] **Step 2: Run the cache RED test**

```powershell
python -m pytest design/test_maas_creative_program_author.py `
  -k cache_scan_returns_available -q
```

Expected: FAIL because `cached_authored_programs` does not exist.

- [ ] **Step 3: Extract the existing cache scan without changing validation**

Implement in `creative_program_author.py`:

```python
def cached_authored_programs(
    cache_root: Path,
    *,
    limit: int,
) -> tuple[CreativeAuthoredProgram, ...]:
    """Return up to limit unique compiler-clean accepted cached programs."""
```

Move the existing accepted-schema, canonical UnitBox, compiler, connected,
watertight, manifold, program-hash and geometry-hash checks into this function.
Make `authored_programs_from_cache_pool` call it and preserve its exact shortage
exception when `len(selected) < expected_count`.

- [ ] **Step 4: Run the cache GREEN tests**

```powershell
python -m pytest design/test_maas_creative_program_author.py -q
```

Expected: all existing and new tests pass; strict cache mode remains unchanged.

- [ ] **Step 5: Write RED hybrid-supply tests**

Create `test_maas_creative_author_supply.py` with these focused cases:

```python
def test_cache_is_consumed_before_any_fresh_request(self):
    result = collect_creative_author_supply(
        target_count=20,
        cached_programs=self.authored_programs(20, cache_hit=True),
        fresh_author=self.fail_if_called,
        retained_count=lambda programs: len(programs),
        max_fresh_requests=3,
    )
    self.assertEqual(len(result.programs), 20)
    self.assertEqual(result.counts["fresh_transport_attempted"], 0)
    self.assertEqual(result.counts["cache_programs_accepted"], 20)

def test_first_429_opens_circuit_and_preserves_cached_supply(self):
    result = collect_creative_author_supply(
        target_count=20,
        cached_programs=self.authored_programs(7, cache_hit=True),
        fresh_author=self.raise_geometry_author_429,
        retained_count=lambda programs: len(programs),
        max_fresh_requests=3,
    )
    self.assertEqual(len(result.programs), 7)
    self.assertEqual(result.status, "partial")
    self.assertEqual(result.counts["fresh_transport_attempted"], 1)
    self.assertEqual(result.counts["fresh_transport_deferred"], 2)
    self.assertEqual(result.counts["http_429"], 1)

def test_fresh_batches_deduplicate_program_hashes_without_fixture_fallback(self):
    result = collect_creative_author_supply(
        target_count=3,
        cached_programs=self.authored_programs(1, cache_hit=True),
        fresh_author=self.fresh_batches_with_one_duplicate,
        retained_count=lambda programs: len(programs),
        max_fresh_requests=3,
    )
    self.assertEqual(len(result.programs), 3)
    self.assertEqual(result.status, "complete")
    self.assertEqual(result.counts["duplicate_program_hash"], 1)
    self.assertNotIn("recipe_fixture", json.dumps(result.evidence()))
```

Define `authored_programs`, `fail_if_called`, `raise_geometry_author_429` and
`fresh_batches_with_one_duplicate` as local deterministic helpers in the new
test class. The 429 helper raises `GeometryAuthorError` with typed
`provider_error.category=rate_limited` and `provider_error.http_status=429`.

- [ ] **Step 6: Run the hybrid-supply RED tests**

```powershell
python -m pytest design/test_maas_creative_author_supply.py -q
```

Expected: collection fails because the module and types do not exist.

- [ ] **Step 7: Implement the typed hybrid-supply coordinator**

Create `creative_author_supply.py` with immutable types:

```python
FreshAuthor = Callable[[int, int], Iterable[GeometryProgram]]
RetainedCount = Callable[[tuple[CreativeAuthoredProgram, ...]], int]

@dataclass(frozen=True)
class CreativeAuthorAttempt:
    attempt_index: int
    source: str
    status: str
    requested_count: int
    returned_count: int
    provider_executed: bool
    http_status: int | None = None
    category: str = ""

    def evidence(self) -> dict[str, Any]:
        return {
            "attempt_index": self.attempt_index,
            "source": self.source,
            "status": self.status,
            "requested_count": self.requested_count,
            "returned_count": self.returned_count,
            "provider_executed": self.provider_executed,
            "http_status": self.http_status,
            "category": self.category,
        }

@dataclass(frozen=True)
class CreativeAuthorSupplyResult:
    status: str
    programs: tuple[CreativeAuthoredProgram, ...]
    attempts: tuple[CreativeAuthorAttempt, ...]
    counts: dict[str, int]

    def evidence(self) -> dict[str, Any]:
        return {
            "schema_version": "arr.maas.creative_author_supply.v1",
            "status": self.status,
            "program_count": len(self.programs),
            "attempts": [item.evidence() for item in self.attempts],
            "counts": dict(sorted(self.counts.items())),
        }

def collect_creative_author_supply(
    *,
    target_count: int,
    cached_programs: Iterable[CreativeAuthoredProgram],
    fresh_author: FreshAuthor,
    retained_count: RetainedCount,
    max_fresh_requests: int = 3,
) -> CreativeAuthorSupplyResult:
    """Merge cache-first authored supply and stop transport after typed 429."""
```

Use `GeometryAuthorError.diagnostics["provider_error"]` as the only 429
authority. Never parse arbitrary exception prose. Before each transport call,
invoke `retained_count` on the current unique supply; stop when it reaches the
target. Normalize fresh programs through `normalize_authored_programs`,
deduplicate by program hash, and emit one deferred record for every unused
attempt after 429. This callback lets the command count actual morphology-
retained meshes rather than assuming twenty raw programs equal twenty cards.

- [ ] **Step 8: Run the hybrid-supply GREEN tests**

```powershell
python -m pytest `
  design/test_maas_creative_program_author.py `
  design/test_maas_creative_author_supply.py -q
```

Expected: all tests pass and the synthetic 429 path reports `7` usable cached,
`1` attempted transport, `2` deferred transports and `0` fabricated programs.

---

### Task 3: Add tolerant portfolio compilation with exact stage PASS counts

**Files:**
- Modify: `ARR/backend/design/maas/creative_floor_portfolio.py`
- Modify: `ARR/backend/design/test_maas_creative_floor_portfolio.py`

**Interfaces:**
- Consumes: an oversupplied iterable of `GeometryProgram | CreativeAuthoredProgram`.
- Produces: `build_creative_floor_portfolio_report(*, target_count: int, capacity_ceiling_m2: float, authored_programs: Iterable[GeometryProgram | CreativeAuthoredProgram]) -> CreativeFloorPortfolioReport`; the existing `build_creative_floor_portfolio(...) -> dict[str, Any]` remains strict and backward compatible.

- [ ] **Step 1: Write RED tests for a mixed valid/invalid/duplicate stream**

Add focused cases to `test_maas_creative_floor_portfolio.py`:

```python
def test_report_counts_each_stage_and_retains_valid_candidates_after_rejections(self):
    report = module.build_creative_floor_portfolio_report(
        target_count=2,
        capacity_ceiling_m2=332.322,
        authored_programs=(
            self.valid_authored("first"),
            self.disconnected_authored("invalid"),
            self.valid_authored("first"),
            self.valid_authored("second"),
        ),
    )
    self.assertEqual(report.status, "complete")
    self.assertEqual(report.stage_counts["author_input"], 4)
    self.assertEqual(report.stage_counts["unique_program_hash"], 3)
    self.assertEqual(report.stage_counts["canonical_compile_pass"], 3)
    self.assertEqual(report.stage_counts["structural_pass"], 2)
    self.assertEqual(report.rejection_counts["duplicate_program_hash"], 1)
    self.assertEqual(report.stage_counts["morphology_retained"], 2)
    self.assertEqual(len(report.candidates), 2)

def test_report_returns_partial_instead_of_raising_when_supply_is_short(self):
    report = module.build_creative_floor_portfolio_report(
        target_count=3,
        capacity_ceiling_m2=332.322,
        authored_programs=(self.valid_authored("only"),),
    )
    self.assertEqual(report.status, "partial")
    self.assertEqual(report.stage_counts["morphology_retained"], 1)
    self.assertEqual(report.deficit, 2)

def test_report_rejects_geometry_near_duplicate_despite_different_family_label(self):
    report = module.build_creative_floor_portfolio_report(
        target_count=2,
        capacity_ceiling_m2=332.322,
        authored_programs=self.same_mesh_different_metadata_programs(),
    )
    self.assertEqual(report.status, "partial")
    self.assertEqual(
        report.rejection_counts["duplicate_normalized_authored_mesh_hash"],
        1,
    )
```

Define the four test helpers with `GeometryProgramBuilder`: `valid_authored`
creates one canonical UnitBox with a supplied unique cut-corner ratio;
`disconnected_authored` applies a two-item linear array with vector
`[3.0, 0.0, 0.0]`; `same_mesh_different_metadata_programs` returns two programs
whose node graphs are identical but metadata family labels differ. Wrap each
program with `CreativeAuthoredProgram` and the existing v1 author evidence.

- [ ] **Step 2: Run the portfolio-report RED tests**

```powershell
python -m pytest design/test_maas_creative_floor_portfolio.py `
  -k 'report_counts or report_returns_partial or report_rejects_geometry' -q
```

Expected: FAIL because `build_creative_floor_portfolio_report` is missing.

- [ ] **Step 3: Implement typed report and bounded rejection records**

Add to `creative_floor_portfolio.py`:

```python
@dataclass(frozen=True)
class CreativePortfolioRejection:
    input_index: int
    stage: str
    reason_code: str
    program_hash: str = ""
    geometry_hash: str = ""

    def evidence(self) -> dict[str, Any]:
        return {
            "input_index": self.input_index,
            "stage": self.stage,
            "reason_code": self.reason_code,
            "program_hash": self.program_hash,
            "geometry_hash": self.geometry_hash,
        }

@dataclass(frozen=True)
class CreativeFloorPortfolioReport:
    status: str
    target_count: int
    candidates: tuple[dict[str, Any], ...]
    stage_counts: dict[str, int]
    rejection_counts: dict[str, int]
    rejections: tuple[CreativePortfolioRejection, ...]

    @property
    def deficit(self) -> int:
        return max(0, self.target_count - len(self.candidates))

    def evidence(self) -> dict[str, Any]:
        return {
            "schema_version": "arr.maas.creative_floor_portfolio_report.v1",
            "status": self.status,
            "target_count": self.target_count,
            "candidate_count": len(self.candidates),
            "deficit": self.deficit,
            "stage_counts": dict(sorted(self.stage_counts.items())),
            "rejection_counts": dict(sorted(self.rejection_counts.items())),
            "rejections": [item.evidence() for item in self.rejections],
        }

def build_creative_floor_portfolio_report(
    *,
    target_count: int,
    capacity_ceiling_m2: float,
    authored_programs: Iterable[GeometryProgram | CreativeAuthoredProgram],
) -> CreativeFloorPortfolioReport:
    """Compile oversupplied authored programs and retain up to target_count."""
```

Record these exact monotonically non-increasing stage counters:

```text
author_input
normalized_program
unique_program_hash
canonical_compile_pass
structural_pass
physical_candidate_pass
unique_geometry_hash
unique_normalized_mesh_hash
morphology_retained
```

Also record rejection counters by typed reason, including compiler exception,
geometry gate, disconnected, non-watertight, non-manifold, physical candidate,
duplicate program hash, duplicate geometry hash, normalized mesh duplicate and
morphology distance. Store no arbitrary exception body.

- [ ] **Step 4: Preserve the strict public wrapper**

Refactor `build_creative_floor_portfolio` so authored mode delegates to the
report. When the report is partial, raise the same category of `RuntimeError`
used by current callers. Recipe-fixture mode keeps its current balanced schedule
and tests. Existing exact-100 behavior must remain byte-for-byte equivalent in
its public evidence fields except deterministic ordering of internal code.

- [ ] **Step 5: Run portfolio GREEN and regression tests**

```powershell
python -m pytest `
  design/test_maas_creative_floor_portfolio.py `
  design/test_maas_creative_morphology.py -q
```

Expected: all existing strict tests and new tolerant-report tests pass.

---

### Task 4: Wire hybrid supply and partial evidence into the existing command

**Files:**
- Modify: `ARR/backend/design/management/commands/generate_maas_creative_100.py`
- Modify: `ARR/backend/design/test_maas_creative_floor_portfolio_command.py`

**Interfaces:**
- Consumes: `cached_authored_programs`, `collect_creative_author_supply`, and `build_creative_floor_portfolio_report`.
- Produces: `--author-mode hybrid`, `--max-fresh-author-requests 0..3`, a board for complete or partial results, and `maas-prelegal-stage-ledger.json`.

- [ ] **Step 1: Write RED command-option and 429 tests**

Add to `test_maas_creative_floor_portfolio_command.py`:

```python
def test_hybrid_mode_writes_partial_board_and_stage_ledger_after_429(self):
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        cache_root = self.write_valid_cache(root / "cache", count=2)
        with patch(
            "design.management.commands.generate_maas_creative_100."
            "author_geometry_programs_with_openai",
            side_effect=self.geometry_author_429(),
        ):
            call_command(
                "generate_maas_creative_100",
                count=20,
                pnu="1168011800104170004",
                output_root=str(root / "out"),
                run_id="hybrid-429",
                author_mode="hybrid",
                author_cache_root=str(cache_root),
                max_fresh_author_requests=3,
            )
        payload = json.loads(
            (root / "out" / "hybrid-429" / "maas-creative-portfolio.json")
            .read_text(encoding="utf-8")
        )
    self.assertEqual(payload["status"], "partial")
    self.assertEqual(payload["candidate_count"], 2)
    self.assertEqual(payload["author_supply"]["counts"]["http_429"], 1)
    self.assertEqual(
        payload["author_supply"]["counts"]["fresh_transport_deferred"], 2
    )
    self.assertEqual(payload["paid_vlm_request_count"], 0)

def test_hybrid_mode_prints_exact_stage_pass_counts(self):
    output = StringIO()
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        cache_root = self.write_valid_cache(root / "cache", count=2)
        call_command(
            "generate_maas_creative_100",
            count=2,
            pnu="1168011800104170004",
            output_root=str(root / "out"),
            run_id="hybrid-complete",
            author_mode="hybrid",
            author_cache_root=str(cache_root),
            max_fresh_author_requests=3,
            stdout=output,
        )
    result = json.loads(output.getvalue())
    self.assertEqual(result["author_input"], 2)
    self.assertEqual(result["morphology_retained"], 2)
    self.assertEqual(result["candidate_count"], 2)
```

Add `write_valid_cache(root: Path, *, count: int) -> Path` and
`geometry_author_429() -> GeometryAuthorError` as deterministic test helpers in
the command test class. The cache helper writes accepted v3 payloads containing
the existing connected UnitBox and cut-corner test programs;
the 429 helper sets `provider_error.category=rate_limited` and
`provider_error.http_status=429`.

- [ ] **Step 2: Run the command RED tests**

```powershell
python -m pytest design/test_maas_creative_floor_portfolio_command.py `
  -k hybrid_mode -q
```

Expected: FAIL because `hybrid` and `--max-fresh-author-requests` are unknown.

- [ ] **Step 3: Add bounded hybrid CLI arguments**

Extend `add_arguments`:

```python
parser.add_argument(
    "--author-mode",
    required=True,
    choices=("payload", "llm", "cache_pool", "hybrid", "recipe_fixture"),
)
parser.add_argument(
    "--max-fresh-author-requests",
    default=3,
    type=int,
)
```

Reject values outside `0..3`. Require `--author-cache-root` for hybrid mode.
Reject `--vlm-pilot` in hybrid pre-legal diagnostic mode so paid VLM remains
exactly zero.

- [ ] **Step 4: Run hybrid acquisition and tolerant compilation**

For hybrid mode:

1. Load up to 60 valid cached programs with `cached_authored_programs`.
2. Pass a callback around the existing `author_geometry_programs_with_openai`.
3. Pass a pure retained-count callback that invokes
   `build_creative_floor_portfolio_report` and returns candidate count.
4. Collect at most three fresh batches, stopping as soon as the retained-count
   callback reaches 20.
5. Feed all unique author supply to `build_creative_floor_portfolio_report`.
6. Persist candidates even when the report is partial.

Do not route hybrid mode through `_resolve_authored_programs`, because that
function intentionally preserves the strict behavior of the four existing
modes.

- [ ] **Step 5: Persist exact stage and rejection evidence**

Write `maas-prelegal-stage-ledger.json` with:

```json
{
  "schema_version": "arr.maas.prelegal_stage_ledger.v1",
  "status": "complete_or_partial",
  "target_count": 20,
  "candidate_count": 0,
  "deficit": 20,
  "author_supply": {},
  "stage_counts": {},
  "rejection_counts": {},
  "rejections": [],
  "morphology_histograms": {},
  "paid_vlm_request_count": 0,
  "acceptance_scope": "pre_legal_not_evaluated"
}
```

Populate `morphology_histograms` from retained certified candidates, including
post-hoc family, capacity band, visible-stepped where available, and morphology
distance distribution. The JSON stdout summary must include every stage count
so PASS counts are visible without opening the artifact.

- [ ] **Step 6: Make board persistence partial-safe**

Allow `_write_board` to receive `1..20` retained items. For zero retained
candidates, write a deterministic one-card failure board labeled
`PRE-LEGAL PARTIAL 0/20` rather than raising. Every board title and manifest
must retain the not-evaluated disclaimer.

- [ ] **Step 7: Run command GREEN and adjacent suites**

```powershell
python -m pytest `
  design/test_maas_creative_floor_portfolio_command.py `
  design/test_maas_creative_author_supply.py `
  design/test_maas_creative_program_author.py `
  design/test_maas_creative_floor_portfolio.py `
  design/test_maas_creative_morphology.py -q
```

Expected: all suites pass. Capture exact test count and runtime.

---

### Task 5: Audit isolation and run the bounded same-PNU diagnostic

**Files:**
- Audit: every file changed in Tasks 1-4
- Create through command: `docs/playwright/design-route-live-verify/prelegal-diversity-r1/`
- Create: `docs/ai-session-memory/maas-mass-flow/checkpoints/2026-08-05-prelegal-diversity-r1.md`

**Interfaces:**
- Consumes: focused GREEN tests and configured author cache/provider credentials.
- Produces: one immutable complete or partial r1 artifact set and a truthful PASS-count checkpoint.

- [ ] **Step 1: Build and inspect task-only diffs**

Run from `D:\Data\25_ACE\ARR`:

```powershell
$taskRoot = 'D:\Data\25_ACE\.superpowers\sdd\prelegal-diversity'
git diff --check
git status --short -- `
  backend/design/maas/README.md `
  backend/design/maas/creative_program_author.py `
  backend/design/maas/creative_author_supply.py `
  backend/design/maas/creative_floor_portfolio.py `
  backend/design/management/commands/generate_maas_creative_100.py `
  backend/design/test_maas_creative_program_author.py `
  backend/design/test_maas_creative_author_supply.py `
  backend/design/test_maas_creative_floor_portfolio.py `
  backend/design/test_maas_creative_floor_portfolio_command.py
```

Generate no-index patches against every `.before` snapshot. Reviewer must
confirm no law, parking, VLM, selector, BOOK benchmark, threshold or recipe
fallback change is present.

- [ ] **Step 2: Run the focused verification once more**

```powershell
Set-Location D:\Data\25_ACE\ARR\backend
$env:DJANGO_SETTINGS_MODULE='config.settings'
python -m pytest `
  design/test_maas_creative_program_author.py `
  design/test_maas_creative_author_supply.py `
  design/test_maas_creative_morphology.py `
  design/test_maas_creative_floor_portfolio.py `
  design/test_maas_creative_floor_portfolio_command.py -q
```

Expected: all pass with exact count and runtime recorded.

- [ ] **Step 3: Run the bounded live-author pre-legal command once**

Run from `D:\Data\25_ACE\ARR\backend`:

```powershell
python manage.py generate_maas_creative_100 `
  --count 20 `
  --pnu 1168011800104170004 `
  --capacity-ceiling-m2 332.322 `
  --output-root D:\Data\25_ACE\docs\playwright\design-route-live-verify `
  --run-id prelegal-diversity-r1 `
  --author-mode hybrid `
  --author-cache-root D:\Data\25_ACE\docs\ai-session-memory\reference-corpus\geometry-author-cache `
  --max-fresh-author-requests 3
```

Do not add `--vlm-pilot`. Do not rerun merely to obtain a prettier provider
sample. A normal complete or partial command exit with persisted artifacts is
valid diagnostic execution; a process crash is not.

- [ ] **Step 4: Print the exact PASS funnel and diversity evidence**

```powershell
@'
import json
from pathlib import Path

root = Path(r"D:\Data\25_ACE\docs\playwright\design-route-live-verify\prelegal-diversity-r1")
ledger = json.loads((root / "maas-prelegal-stage-ledger.json").read_text(encoding="utf-8"))
print(json.dumps({
    "status": ledger["status"],
    "target_count": ledger["target_count"],
    "candidate_count": ledger["candidate_count"],
    "deficit": ledger["deficit"],
    "author_supply": ledger["author_supply"]["counts"],
    "stage_counts": ledger["stage_counts"],
    "rejection_counts": ledger["rejection_counts"],
    "morphology_histograms": ledger["morphology_histograms"],
    "paid_vlm_request_count": ledger["paid_vlm_request_count"],
}, indent=2, sort_keys=True))
'@ | python -
```

Expected: exact measured numbers. The acceptance line is `PASS 20/20` only if
the ledger independently reports twenty retained distinct candidates. Any
smaller value is reported as `PARTIAL N/20` with its top rejection reasons.

- [ ] **Step 5: Verify artifact integrity**

```powershell
$root = 'D:\Data\25_ACE\docs\playwright\design-route-live-verify\prelegal-diversity-r1'
Get-ChildItem -LiteralPath $root -File -Recurse |
  Select-Object FullName,Length
Get-ChildItem -LiteralPath $root -Filter '*.png' -File -Recurse |
  Get-FileHash -Algorithm SHA256 |
  Select-Object Path,Hash
```

Expected: nonzero board/candidate artifacts and recorded PNG hashes. The board
is inspected directly for stepped-only repetition; JSON counters alone do not
establish visual quality.

- [ ] **Step 6: Write the r1 checkpoint**

Create `docs/ai-session-memory/maas-mass-flow/checkpoints/2026-08-05-prelegal-diversity-r1.md` with these exact sections:

```markdown
# Pre-Legal Diversity r1 - 2026-08-05 KST

## Command and runtime
## Test PASS count
## Author cache/fresh/429 funnel
## Compile and structural PASS funnel
## Duplicate and morphology rejection funnel
## Retained phenotype/body/section/plan evidence
## Board path and SHA-256
## Comparison with r87
## Acceptance decision
## Explicit non-claims
```

Record exact measured values only. Do not call a pre-legal board lawful,
parking-complete, VLM-approved or competition-grade.

- [ ] **Step 7: Issue the safe-commit decision**

Because most creative files are currently untracked relative to inner `HEAD`,
do not stage whole files. Attempt clean-HEAD patch applicability for each
task-only diff. End with exactly one decision:

```text
APPROVED: task-only patches are dependency-complete against clean HEAD, focused
tests pass, and the pre-legal artifact truthfully reports N/20.
```

or:

```text
BLOCKED: required creative source/test dependencies are absent from HEAD or
overlap unrelated work; implementation is verified in the shared worktree but
no unsafe inner commit was made.
```

Never absorb unrelated untracked creative modules into a task commit.
