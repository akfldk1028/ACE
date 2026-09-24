# MAAS Cumulative Candidate Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reuse exact MASS artifacts across compatible runs, produce a deterministic five-candidate recovery board without another LLM call, and preserve strict publishable-gate truth.

**Architecture:** Add one focused archive-pool module that discovers exact-artifact archives, normalizes the current artifact schema, validates exact surface hashes, groups candidates by PNU/legal-floor-field/floor-capacity-plan, and deduplicates final geometry. Add a thin Django management command that writes a machine-readable ledger and flow journal, then renders a five-card exact-surface board through the existing legal archive renderer. `mass_eligible` and `publishable` remain separate states; missing law/finalization evidence is never promoted.

**Tech Stack:** Python 3.13, Django management commands, existing MAAS exact geometry artifacts, PIL archive renderer, unittest/Django test runner.

## Global Constraints

- Preserve all existing dirty-worktree changes.
- No new LLM/provider call is required to recover archived candidates.
- Only candidates with the same PNU, legal-floor-field hash, and floor-capacity-plan hash may share a pool.
- Deduplicate by exact final legal geometry hash; never add raw run counts.
- Validate the canonical exact surface payload hash before rendering.
- Require clean MASS, legal, parking, and program hard passes for `mass_eligible`.
- Require candidate finalization and law graph evidence in addition to mass eligibility for `publishable`.
- Do not weaken the existing publishable-20 contract or label a recovery board as canonical.
- Flow counters, exclusions, malformed archives, identities, and output hashes must be recorded.

---

### Task 1: Compatible cumulative archive pool

**Files:**
- Create: `ARR/backend/design/maas/book_language/cumulative_candidate_pool.py`
- Create: `ARR/backend/design/test_maas_cumulative_candidate_pool.py`

**Interfaces:**
- Produces: `build_cumulative_candidate_pool(archive_roots: Sequence[Path], *, pnu: str, legal_floor_field_hash: str = "", floor_capacity_plan_hash: str = "") -> dict[str, Any]`.
- Produces: `select_recovery_records(pool: Mapping[str, Any], *, target_count: int) -> list[dict[str, Any]]`.
- Each selected record is compatible with `render_legal_mass_archive_board` and contains canonical `final_authored_surface_payload` plus its verified hash.

- [ ] **Step 1: Write the failing pool tests**

```python
def test_pool_deduplicates_geometry_and_excludes_incompatible_context(tmp_path):
    write_archive(tmp_path / "run-a", geometry_hash="g1", scope="1/1", family="ribbon")
    write_archive(tmp_path / "run-b", geometry_hash="g1", scope="1/2", family="bar")
    write_archive(tmp_path / "run-c", geometry_hash="g2", pnu="other")
    pool = build_cumulative_candidate_pool([tmp_path], pnu="site")
    assert pool["mass_eligible_unique_count"] == 1
    assert pool["duplicate_record_count"] == 1
    assert pool["incompatible_record_count"] == 1

def test_pool_does_not_promote_missing_publishable_evidence(tmp_path):
    write_archive(tmp_path / "run-a", geometry_hash="g1", finalization=False, law_graph=False)
    pool = build_cumulative_candidate_pool([tmp_path], pnu="site")
    assert pool["mass_eligible_unique_count"] == 1
    assert pool["publishable_unique_count"] == 0
    assert pool["candidates"][0]["status"] == "needs_recertification"

def test_recovery_selection_prefers_scope_and_family_diversity(tmp_path):
    # Literal fixtures contain two repeated families followed by distinct ones.
    pool = build_fixture_pool(tmp_path)
    selected = select_recovery_records(pool, target_count=3)
    assert [row["geometry_hash"] for row in selected] == ["g1", "g3", "g4"]
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python manage.py test design.test_maas_cumulative_candidate_pool -v 2`

Expected: import failure because `cumulative_candidate_pool` does not exist.

- [ ] **Step 3: Implement the minimal pool module**

```python
def build_cumulative_candidate_pool(archive_roots, *, pnu, legal_floor_field_hash="", floor_capacity_plan_hash=""):
    # Discover exact artifacts, parse with quarantine, normalize geometry_artifact,
    # validate context/gates/surface hash, and retain the first exact geometry.
    return ledger

def select_recovery_records(pool, *, target_count):
    # Deterministic greedy score: unseen scope, unseen family, unseen BOOK principle,
    # then utilization and stable identity.
    return records
```

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run: `python manage.py test design.test_maas_cumulative_candidate_pool -v 2`

Expected: all cumulative pool tests pass.

### Task 2: Recovery command, exact board, and flow journal

**Files:**
- Create: `ARR/backend/design/management/commands/rebuild_maas_cumulative_candidate_pool.py`
- Extend: `ARR/backend/design/test_maas_cumulative_candidate_pool.py`

**Interfaces:**
- CLI: `python manage.py rebuild_maas_cumulative_candidate_pool --archive-root <path> --output-dir <path> --pnu <pnu> --target-count 5`.
- Produces: `maas-cumulative-candidate-ledger.json`, `maas-cumulative-flow-journal.json`, and `maas-book-neighborhood-5-cumulative-recovery.png`.

- [ ] **Step 1: Write the failing command test**

```python
def test_command_writes_ledger_journal_and_exact_board(tmp_path):
    archive_root = make_three_candidate_archive_root(tmp_path)
    call_command("rebuild_maas_cumulative_candidate_pool", archive_root=[str(archive_root)], output_dir=str(tmp_path / "out"), pnu="site", target_count=3)
    ledger = json.loads((tmp_path / "out/maas-cumulative-candidate-ledger.json").read_text())
    journal = json.loads((tmp_path / "out/maas-cumulative-flow-journal.json").read_text())
    assert ledger["selected_recovery_count"] == 3
    assert journal["stages"][-1]["stage"] == "exact_board_rendered"
    assert Path(ledger["recovery_board"]["png_path"]).is_file()
```

- [ ] **Step 2: Run the command test and verify RED**

Run: `python manage.py test design.test_maas_cumulative_candidate_pool.CumulativeCandidatePoolCommandTests -v 2`

Expected: unknown command failure.

- [ ] **Step 3: Implement the thin command**

```python
pool = build_cumulative_candidate_pool(roots, pnu=options["pnu"], ...)
selected = select_recovery_records(pool, target_count=options["target_count"])
board = render_legal_mass_archive_board(..., archive_records=selected)
write_json_atomic(output_dir / "maas-cumulative-candidate-ledger.json", {**pool, "recovery_board": board})
```

- [ ] **Step 4: Run the focused command test and verify GREEN**

Run: `python manage.py test design.test_maas_cumulative_candidate_pool -v 2`

Expected: all cumulative pool and command tests pass.

### Task 3: Real archive recovery and recorded evidence

**Files:**
- Modify: `ARR/backend/design/maas/agents/maas_geometry_agent/memory/09_CURRENT_STATE.md`
- Runtime output: `docs/playwright/design-route-live-verify/legal-mass-cumulative-recovery-v1/`

**Interfaces:**
- Consumes both workspace exact-artifact roots without provider calls.
- Produces measured compatible/unique/eligible/publishable counts, five exact MASS cards, PNG SHA-256, and exclusion reasons.

- [ ] **Step 1: Run the real cumulative recovery command**

Run: `python manage.py rebuild_maas_cumulative_candidate_pool --archive-root D:/Data/25_ACE/docs/playwright/design-route-live-verify --archive-root D:/Data/25_ACE/ARR/docs/playwright/design-route-live-verify --output-dir D:/Data/25_ACE/docs/playwright/design-route-live-verify/legal-mass-cumulative-recovery-v1 --pnu 1168011800104170004 --target-count 5`

- [ ] **Step 2: Validate output identities and PNG**

Run: `python -m json.tool D:/Data/25_ACE/docs/playwright/design-route-live-verify/legal-mass-cumulative-recovery-v1/maas-cumulative-candidate-ledger.json > NUL`

Run: `python -m json.tool D:/Data/25_ACE/docs/playwright/design-route-live-verify/legal-mass-cumulative-recovery-v1/maas-cumulative-flow-journal.json > NUL`

- [ ] **Step 3: Inspect the five-card PNG**

Open the generated board and reject visible empty cards, repeated geometry hashes, or an all-staircase set.

- [ ] **Step 4: Record measured state only**

Append the command, context hashes, all stage counts, selected identities, PNG path/hash, and remaining publishable blockers to `09_CURRENT_STATE.md`.

- [ ] **Step 5: Run affected regressions**

Run: `python manage.py test design.test_maas_cumulative_candidate_pool design.test_legal_mass_archive_board design.test_maas_book_language -v 1`

Expected: exit 0 with no failures.
