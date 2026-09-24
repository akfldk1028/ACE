# Deep South-to-North Public-Roof Replenishment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist and one-shot validate one direct LLM-authored C18 mass with a single deep south-to-north roof/ramp, terminal west threshold, and the newly offered simple taper path.

**Architecture:** The artifact is a static typed GeometryProgram, not a runtime generator. Its source lineage is one UnitBox, one block BaseVolume, one host-aspect Matrix4, one continuous oblique slice, and one terminal west notch; the existing BOOK adapter inserts the selected `1/2` taper before the protected access suffix. Existing deterministic packaging and v11 preflight remain the only compliance authorities.

**Tech Stack:** JSON typed GeometryProgram AST, Python v11 static packager/validator, existing MAAS BOOK adapter and exact legal-field affine selector.

## Global Constraints

- Use v30 request batch count `3`, batch index `0`, variation offset `60`, requested count `8`.
- Use the full persisted v50 capacity-deficit list verbatim.
- Include typed A puncture, B pinch, C17 runtime, and C16 top-band feedback exactly as approved.
- Source slice is frozen at `normal=[0,1,-0.72]`, `offset_ratio=0.36`, `keep_side=positive`.
- Terminal west notch is frozen at `ratio=0.30`, `width_ratio=0.42`, `height_ratio=0.64`.
- Bind only `book:path:9cb42d9be8b7d3ae296513612f8869645a71f0a27938e27399f45cdd253fd6ba`.
- No floor index, z breakpoint, legal-band replay, copied legal polygon, or stepped operator.
- Package once and validate once; never tune a value or path after validation begins.
- Do not create another git commit.

---

### Task 1: Persist the frozen author evidence and static fragment

**Files:**
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-c/v30-round2-c18/author-context-evidence.json`
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-c/v30-round2-c18/response-evidence.json`
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/tmp-v11-c/18-v11c_18_deep_public_roof_ramp.json`

**Interfaces:**
- Consumes: v50 summary capacity deficits, A/B/C17/C16 immutable result artifacts, selected v30 BOOK path, persisted west access context.
- Produces: one hash-bound `arr.maas.codex_oauth_static_ast_fragment.v1` file accepted by `package_static_codex_mass_v11.py`.

- [ ] **Step 1: Persist exact context evidence**

Write the approved request identity, four typed feedback records, normalized legal design context, complete 32-path rotated offer, and selected path to `author-context-evidence.json`. Do not include parcel coordinates in the authored program.

- [ ] **Step 2: Persist the direct response and AST**

Use this exact source graph:

```text
UnitBox
  -> scale([1,1,1])
  -> matrix4(diag(12.865/8.009, 1, 1, 1))
  -> slice(normal=[0,1,-0.72], offset_ratio=.36, keep_side=positive)
  -> notch(side=west, ratio=.30, width_ratio=.42, height_ratio=.64)
```

Bind `book:path:9cb42d9be8b7d3ae296513612f8869645a71f0a27938e27399f45cdd253fd6ba` and state that its taper is absent from the source.

- [ ] **Step 3: Bind immutable morphology hashes**

Run:

```powershell
python -c "import json,sys; from pathlib import Path; sys.path.insert(0,'.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass'); from package_static_codex_mass_v11 import _canonical_hash,morphology_payload; p=Path('.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/tmp-v11-c/18-v11c_18_deep_public_roof_ramp.json'); d=json.loads(p.read_text(encoding='utf-8')); print(_canonical_hash(morphology_payload(d['program'])))"
```

Expected: one 64-character SHA-256 digest. Put the same digest in `direct_llm_authorship.response_sha256` and `program_morphology_sha256` without changing morphology.

- [ ] **Step 4: Package the single fragment**

Run from `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass`:

```powershell
python package_static_codex_mass_v11.py --fragments tmp-v11-c --manifest tmp-v11-c-manifest.json --admission tmp-v11-c-admission.json --expected-count 1
```

Expected: JSON naming `tmp-v11-c-manifest.json` and `tmp-v11-c-admission.json`.

### Task 2: Execute the sole canonical validation and preserve its result

**Files:**
- Modify: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-c/report.md`
- Create on pass: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-c/18-v11c_18_deep_public_roof_ramp.json`
- Create on failure: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/tmp-v11-c/18-v11c_18_deep_public_roof_ramp.json.rejected`
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-c/v30-round2-c18/validation-result.json` when validator returns JSON.

**Interfaces:**
- Consumes: the packaged manifest/admission and immutable fragment from Task 1.
- Produces: one terminal pass or rejection record; no second validation input.

- [ ] **Step 1: Run the validator exactly once**

Run from `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass`:

```powershell
python validate_static_codex_mass_v11.py --fragments tmp-v11-c --manifest tmp-v11-c-manifest.json --admission tmp-v11-c-admission.json --maximum-programs 1
```

Expected on pass: `hard_pass: true` and minimum capacity utilization at least `0.70`. Any parser, compiler, whole-fit, capacity, or 120-second runtime failure is terminal.

- [ ] **Step 2: Preserve the immutable terminal artifact**

On pass, move the unchanged JSON into `v11-revisions-c`. On failure, rename the unchanged JSON with `.rejected`. Persist returned JSON when available and append the exact outcome to `report.md`.

- [ ] **Step 3: Verify no accidental second candidate or morphology mutation**

Run:

```powershell
Get-ChildItem tmp-v11-c -Filter '*.json'
git diff --check -- docs/superpowers/specs/2026-08-06-deep-south-north-public-roof-replenishment-design.md docs/superpowers/plans/2026-08-06-deep-south-north-public-roof-replenishment.md .superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-c
```

Expected: no active extra fragment and no whitespace errors.
