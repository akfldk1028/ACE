# Authored Site-perimeter Intersection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist and one-shot validate one direct-authored five-edge perimeter/intersection mass.

**Architecture:** One JSON fragment owns the complete AST and content hashes. Packaging adds execution evidence only; canonical production validation decides acceptance without modifying source geometry.

**Tech Stack:** JSON typed geometry AST, Python static v11 packager, canonical `neighborhood_living` v10 preflight, PowerShell.

## Global Constraints

- Persist the five-edge operand directly in the AST; no runtime polygon builder.
- Use exactly one canonical UnitBox BaseVolume plus one typed polygon operand.
- Use body families composition plus deformation and exactly one terminal threshold.
- Preserve points with `.18`, taper end scale `.90/.86`, and notch `.28/.38/.58` after freeze.
- Use no legal-floor coordinates or z breakpoints.
- Bind `book:path:fda21c3dd4b1e6a2699ca4f80b6eecb223bd56e35a296e2358674d2b77d6a28e`; do not pre-apply extrude.
- Validate once; do not commit or mutate shared unrelated work.

---

### Task 1: Persist, freeze, validate, and archive the authored mass

**Files:**
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-a2/03-v11a2_03_perimeter_taper_corner.json`
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-a2/evidence/03-perimeter-taper-corner-result.md`

**Interfaces:**
- Consumes: static fragment schema and canonical `neighborhood_living` production context.
- Produces: one content-addressed direct-authored fragment and one immutable validation result.

- [ ] **Step 1:** Write the approved UnitBox/operand/intersection/taper/notch graph exactly.
- [ ] **Step 2:** Canonically hash the frozen morphology and `{"program": program}` response payload; assert one UnitBox, five operand points, body2+threshold1, no source extrude, and no law-floor keys.
- [ ] **Step 3:** Package it in `v11-revisions-a2/.run-03` with `package_static_codex_mass_v11.py --expected-count 1`.
- [ ] **Step 4:** Run `validate_static_codex_mass_v11.py --maximum-programs 1` once against the isolated run.
- [ ] **Step 5:** Retain an accepted fragment in the A2 root or archive a rejected fragment as `rejected/03-rejected-production-validation.json`; write exact result evidence and make no numeric revision.
