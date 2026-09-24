# C20 West-Anchored Lantern Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist one independently authored C20 AST from the exact v30 rotated BOOK offer, freeze its morphology, and perform exactly one production validator invocation.

**Architecture:** The source is a canonical UnitBox/BaseVolume chain with one normalized host-aspect/4-degree plan-pose Matrix4, one continuous NW-anchored anisotropic taper, and one terminal WEST notch. The exact offered vertical BOOK notch is not preapplied; deterministic packaging lowers it before the terminal access suffix and validation may only accept or reject the frozen artifact.

**Tech Stack:** JSON static AST fragments, Python v11 packager/validator, production `design.maas` geometry/compiler pipeline, PowerShell orchestration.

## Global Constraints

- Use `neighborhood_living`, production depth `2`, reserve `0`, and terminal access side `west`.
- Author request is exactly `author_batch_count=3`, `author_batch_index=2`, `author_variation_offset=60`, `count=8`.
- Select only the production-helper reconstructed offer index `0`, path `book:path:a6b706fdd1d75fe1f2073219e3148878a9aa68d0dcfbed9f933bed1413de5452`; do not vary any existing candidate path, shape, or numbers.
- Keep legal floor/z/profile values outside the AST. The source taper is an individual C20 decision, not a reusable recipe or inverse legal transform.
- Use one dedicated evidence directory and one separate fragment directory. Allow only parser-contract correction before freeze.
- After the morphology hash is frozen, invoke the validator exactly once; no morphology tuning and no rerun regardless of result.
- Do not commit.

---

### Task 1: Persist the complete author context

**Files:**
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-c/v30-round2-c20/author-context-evidence.json`

**Interfaces:**
- Consumes: v50 production program dimensions, normalized legal design context, three exact capacity deficit records, typed A/B/C16/C17/C18 feedback, and the exact 32-path rotated offer slice.
- Produces: immutable evidence for the prompt context and selected offer.

- [ ] **Step 1: Create the C20 evidence and fragment directories**

Run:

```powershell
New-Item -ItemType Directory -Force -Path '.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-c/v30-round2-c20'
New-Item -ItemType Directory -Force -Path '.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/tmp-v11-c20'
```

- [ ] **Step 2: Write the complete author-context evidence**

Write a single JSON object containing the exact request parameters, dimensions, normalized context, all three v50 capacity deficits, all five typed feedback records, all 32 production-helper rotated offers, selected path/lowering evidence, frozen morphology decision, and one-shot policy. The selected lowering is `book_notch(axis="x", corner="nw", ratio=0.4008)` with `source_preapplies_operation=false`.

- [ ] **Step 3: Check context cardinality and selected identity without invoking validation**

Run:

```powershell
@'
import json
from pathlib import Path
p=Path(r'.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-c/v30-round2-c20/author-context-evidence.json')
d=json.loads(p.read_text(encoding='utf-8'))
assert len(d['capacity_authoring_deficits']) == 3
assert len(d['legal_fit_repair_feedback']) == 5
assert len(d['offered_book_paths']) == 32
assert d['selected_offer_path']['offer_index'] == 0
assert d['selected_offer_path']['path_id'] == 'book:path:a6b706fdd1d75fe1f2073219e3148878a9aa68d0dcfbed9f933bed1413de5452'
print('context-contract-ok')
'@ | python -
```

Expected: `context-contract-ok`.

### Task 2: Author and freeze the C20 static fragment

**Files:**
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/tmp-v11-c20/20-v11c_20_west_spine_lantern.json`
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-c/v30-round2-c20/response-evidence.json`

**Interfaces:**
- Consumes: Task 1 author context and the approved frozen design.
- Produces: one static AST fragment with morphology SHA-256 and direct-authorship evidence.

- [ ] **Step 1: Write the complete AST fragment**

The node order and exact frozen parameters are:

```text
c2020_unit box [1,1,1]
c2020_block scale [1,1,1]
c2020_pose matrix4 [[1.602405,-0.069756,0,0],[0.112051,0.997564,0,0],[0,0,1,0],[0,0,0,1]]
c2020_lantern taper axis=z start=[1,1] end=[0.96,0.30] pivot=[-0.069756,0.997564,0] subdivisions=4
c2020_threshold notch side=west ratio=0.28 width_ratio=0.38 height_ratio=0.58
```

The root is `c2020_threshold`, and `book_composition_path_id` is the exact selected path. No floor index, legal-band extent, or law-derived z breakpoint may occur in the program.

- [ ] **Step 2: Perform parser-contract-only static inspection before freeze**

Inspect JSON decoding, required field presence, node SSA ordering, exactly one UnitBox and Matrix4, terminal WEST suffix, and forbidden floor/legal-profile tokens. Do not compile geometry, run the packager, or invoke the validator.

- [ ] **Step 3: Compute and persist the prompt and morphology hashes**

Use `package_static_codex_mass_v11._canonical_hash(morphology_payload(program))` to compute the response/morphology digest. Compute the prompt digest from the production `_author_prompt` over the exact author context. Patch only metadata hash fields, then record the frozen digest and source file SHA-256 in `response-evidence.json`.

- [ ] **Step 4: Confirm freeze integrity**

Recompute the morphology hash and assert it equals all three declared response/morphology/freeze hashes. Record `frozen_before_packaging=true` and `post_result_tuning_allowed=false`.

### Task 3: Package once and invoke the validator once

**Files:**
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-c/v30-round2-c20/.run-01/manifest.json`
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-c/v30-round2-c20/.run-01/admission.json`
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-c/v30-round2-c20/validation-result.json`
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-c/v30-round2-c20/result.md`

**Interfaces:**
- Consumes: the single frozen Task 2 fragment.
- Produces: immutable one-shot production validation evidence with exact legal/capacity outcome.

- [ ] **Step 1: Package the one frozen fragment**

Run:

```powershell
python '.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/package_static_codex_mass_v11.py' --fragments '.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/tmp-v11-c20' --manifest '.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-c/v30-round2-c20/.run-01/manifest.json' --admission '.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-c/v30-round2-c20/.run-01/admission.json' --expected-count 1
```

Expected: one manifest and one admission file; morphology remains byte-derived from the frozen fragment.

- [ ] **Step 2: Invoke the production validator exactly once and capture both streams**

Run one PowerShell `Start-Process -Wait -PassThru` invocation of `validate_static_codex_mass_v11.py`, redirecting stdout and stderr into `.run-01`, with `--maximum-programs 1`. Record this single process invocation in `validation-result.json`. Do not run that command again.

- [ ] **Step 3: Preserve and summarize the immutable outcome**

If exit code is zero, retain the `.json` fragment. If nonzero, rename it once to `.json.rejected` after evidence capture so it cannot enter later packages. Write `result.md` with morphology hash, exact selected path, static-authorship integrity, direct-fit/legal result, final GFA, feasible maximum, utilization, minimum threshold, per-floor GFA/deficits, fallback count, and the statement that validator invocation count is one.

### Task 4: Final evidence audit

**Files:**
- Inspect: all C20 evidence, fragment, manifest, admission, and result files.

**Interfaces:**
- Consumes: Tasks 1-3 outputs.
- Produces: a concise parent report; no repository mutation.

- [ ] **Step 1: Audit file existence, hashes, and invocation count**

Run read-only JSON/hash checks proving the context counts, selected path, frozen morphology identity, fragment/manifest agreement, and `validator_invocation_count=1`.

- [ ] **Step 2: Report without claiming more than the captured evidence**

State PASS or FAIL, exact/capacity figures, fallback status, paths to evidence, and that no post-result tuning, rerun, or commit occurred.
