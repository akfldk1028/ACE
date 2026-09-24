# North-Drift Split-Market C21 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to execute this plan with the stated freeze checkpoint.

**Goal:** Persist and one-shot validate one direct LLM-authored C21 mass whose
new topology is a north-drifting pair of long living wings joined by a low
WEST-access ground spine.

**Architecture:** The artifact is a single static typed GeometryProgram, not a
generator. Its source lineage is UnitBox, canonical BAR scale, one authored
Matrix4, one continuous z taper, and one terminal WEST split-wing relation.
The existing BOOK adapter inserts the offered `1/8` long-axis compress before
that protected suffix. The existing packager and v11 validator remain the only
schema, legal-fit, capacity, and runtime authorities.

**Tech Stack:** JSON typed GeometryProgram AST, Python v11 static packager and
validator, MAAS recursive BOOK adapter, exact legal-field affine selector.

## Global constraints

- Use v30 batch count `3`, batch index `0`, variation offset `80`, count `8`,
  depth `2`, reserve `0`.
- Include only A puncture, B pinch, C16 measured top-band, C17 runtime, C18
  whole-fit, and the complete persisted v50 capacity deficits.
- Bind only
  `book:path:ded25d4fbc561ae9a9c64070cf62bc43a624de027391e8c1d891dc88784f5966`.
- Use canonical UnitBox and BAR `[2.8,0.62,0.48]`, followed by exactly one
  authored Matrix4.
- Use no floor index, z breakpoint, legal band value, copied legal polygon,
  step, terrace, or per-floor transform.
- Terminal program relation is `split_wing(access_side=west)` with a ground
  spine. No second threshold relation is allowed.
- Package once and invoke the canonical validator once. Never post-tune or
  rerun after exact/capacity evidence exists.
- Do not commit.

---

### Task 1: Persist context evidence and the frozen static response

**Files:**

- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-c/v30-round3-c21/author-context-evidence.json`
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-c/v30-round3-c21/response-evidence.json`
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/tmp-v11-c/21-v11c_21_north_drift_split_market.json`

- [ ] Persist the exact request identity, current five-record typed causal set,
      full v50 deficit list, complete 32-path offer, and selected path.
- [ ] Persist this frozen source lineage:

```text
UnitBox
  -> scale([2.8, .62, .48])
  -> matrix4([[.96,-.14,0,0],[.10,.99,.16,0],[0,0,1,0],[0,0,0,1]])
  -> taper(axis=z, start=[1,1], end=[.88,.58], subdivisions=5)
  -> split_wing(axis=y, layout=split, gap=.21,
                ground_spine=true, spine_width=.31, spine_height=.19,
                access_side=west)
```

- [ ] Run source-only decode/compiler contract checks. Before hashing, correct
      only a declared parser/type/name/range mismatch. Record any discarded
      draft; do not react to legal-fit or capacity.
- [ ] Compute the canonical morphology hash and write it unchanged to both
      `direct_llm_authorship.response_sha256` and
      `program_morphology_sha256`.

### Task 2: Package and run the sole canonical validation

**Files:**

- Modify: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-c/report.md`
- Create on pass: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-c/21-v11c_21_north_drift_split_market.json`
- Create on failure: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/tmp-v11-c/21-v11c_21_north_drift_split_market.json.rejected`
- Create when returned: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-c/v30-round3-c21/validation-result.json`

- [ ] Package the sole active fragment with
      `package_static_codex_mass_v11.py --expected-count 1`.
- [ ] Invoke `validate_static_codex_mass_v11.py --maximum-programs 1` exactly
      once. A parser, compiler, exact-fit, capacity, or runtime failure is
      terminal.
- [ ] Preserve the unchanged frozen artifact as promoted or `.rejected`, append
      exact/capacity evidence to the report, and verify no active JSON remains
      in `tmp-v11-c`.
- [ ] Run `git diff --check` over the C21 spec, plan, evidence, and report. This
      is formatting verification only, not a second morphology validation.
