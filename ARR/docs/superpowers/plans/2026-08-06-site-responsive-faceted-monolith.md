# Site-responsive Faceted Monolith Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce and one-shot validate one direct-authored, site-responsive faceted `neighborhood_living` monolith.

**Architecture:** Add one standalone static AST fragment in the A2 revision lane. The packager may add only execution evidence; the source geometry remains one UnitBox lineage with two body-rule families and one terminal public threshold.

**Tech Stack:** JSON typed geometry AST, Python v11 static packager, canonical v10 production preflight, PowerShell orchestration.

## Global Constraints

- The only site-derived authored quantity is the normalized `12.865:8.009` host aspect ratio in Matrix4.
- Facet, continuous slice, and notch values are direct architectural choices, not law-floor coordinates.
- Use exactly one canonical UnitBox lineage.
- Use no `z`, floor-index, legal-section, or fixed section-breakpoint controls.
- Use at most two body-rule families and exactly one terminal access threshold.
- Bind unused non-`extrude` BOOK path `book:path:a09ad744acb3b85c7d71cf6ba4741d96e0ea09caafce5df56a3755d87552375f` and do not pre-apply `rotate` in source.
- Freeze the fragment before validation; run the latest canonical pipeline once and do not numerically revise afterward.
- Do not commit from this shared dirty working tree.

---

### Task 1: Author, freeze, and validate the single fragment

**Files:**
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-a2/02-v11a2_02_faceted_market_corner.json`
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-a2/evidence/02-faceted-market-corner-result.md`
- Read: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/package_static_codex_mass_v11.py`
- Read: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/validate_static_codex_mass_v11.py`

**Interfaces:**
- Consumes: fragment schema `arr.maas.codex_oauth_static_ast_fragment.v1` and canonical program context `neighborhood_living`.
- Produces: one content-addressed direct-authored fragment plus an immutable accept/reject record.

- [ ] **Step 1: Create the direct-authored AST**

  Write one unary graph with these nodes and no additional geometry: UnitBox, canonical block scale, diagonal Matrix4 `[12.865/8.009, 1, 1]`, southwest `cut_corner` ratio `0.11`, oblique `slice` normal `[0.18, -0.32, 1.0]` with `offset_ratio: 0.14`, and terminal south `notch` ratios `0.28/0.38/0.58`.

- [ ] **Step 2: Freeze content-addressed evidence**

  Canonically hash every morphology field required by `morphology_payload()`. Set `response_sha256` to the canonical hash of `{"program": program}`. Assert the only UnitBox primitive count is one, source has no `rotate`, source has no law/floor control keys, and the selected BOOK path is absent from all other v11 fragments at freeze time.

- [ ] **Step 3: Package the frozen fragment**

  Run:

  ```powershell
  python .superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/package_static_codex_mass_v11.py --fragments .superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-a2/.run-02/fragments --manifest .superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-a2/.run-02/manifest.json --admission .superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-a2/.run-02/admission.json --expected-count 1
  ```

  Expected: exit `0`, one manifest, and one admission record.

- [ ] **Step 4: Run the canonical one-shot production validation**

  Run:

  ```powershell
  python .superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/validate_static_codex_mass_v11.py --fragments .superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-a2/.run-02/fragments --manifest .superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-a2/.run-02/manifest.json --admission .superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-a2/.run-02/admission.json --maximum-programs 1
  ```

  Expected acceptance: static authorship pass, exact feasible candidate, capacity utilization at least `0.70`, no production-context violation, and wall time at most `120 s`.

- [ ] **Step 5: Record the immutable decision**

  If accepted, retain the fragment in the A2 root. If rejected, move it to `v11-revisions-a2/rejected/02-rejected-production-validation.json` and record the exact reason inside the evidence report. In either case record exact counts, floor areas, utilization, runtime, hashes, and the fact that no post-validation numeric revision was made.
