# Oblique West-Open Court v30B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist and one-shot validate one frozen v30B direct-authored west-open courtyard AST.

**Architecture:** A focused evidence JSON records the live-equivalent normalized legal context and rotated BOOK offer membership. A separate static fragment owns only the direct architectural AST and its authorship digests; existing packaging and production preflight scripts remain unchanged.

**Tech Stack:** JSON typed AST, Python 3 packaging/preflight scripts, Shapely/manifold production geometry stack.

## Global Constraints

- Freeze `Matrix4=[[1.606443,0,0,0],[0,1,0.34,0],[0,0,1,0],[0,0,0,1]]`, taper end `[1.0,0.56]`, courtyard margin `0.34`, and access side `west`.
- Bind exactly `book:path:5e65cbf8f45e8f38e4ab7729b0c502adbd9b3b1a07afd0101dbe3bd4fd3074bb` from v30 batch `1/3`, offset `20`, count `8`.
- Never encode parcel coordinates, legal polygons, legal floor heights, floor/band breakpoints, per-floor transforms, or fallback geometry.
- Run packaging once and production validation once; make no post-result morphology or path changes.

---

### Task 1: Persist the frozen authorship evidence and AST

**Files:**
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-b-v30/author-context-evidence.json`
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-b-v30/fragments/01-v30b_oblique_west_open_court.json`

**Interfaces:**
- Consumes: v50 normalized legal relations, full capacity-deficit list, rotated v30 offer, persisted WEST access.
- Produces: one static fragment accepted by `package_static_codex_mass_v11.py` without morphology synthesis.

- [x] **Step 1: Record the exact offer identity, normalized legal relations, selected path contract, and authored Matrix4.**
- [x] **Step 2: Write the typed source graph with `box -> scale -> matrix4 -> taper -> courtyard`.**
- [x] **Step 3: Compute the prompt/response/morphology SHA-256 values from canonical content and patch only those metadata fields before freeze.**
- [x] **Step 4: Confirm by read-only inspection that the fragment contains no legal coordinates, band z controls, steps, or pre-applied pinch node.**

### Task 2: Package and validate once

**Files:**
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-b-v30/.run-01/manifest.json`
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-b-v30/.run-01/admission.json`
- Create: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/v11-revisions-b-v30/evidence/01-v30b-result.md`

**Interfaces:**
- Consumes: the frozen fragment from Task 1.
- Produces: immutable package/admission artifacts and one production validation decision.

- [x] **Step 1: Package exactly one fragment with `package_static_codex_mass_v11.py --expected-count 1`.**
- [x] **Step 2: Run `validate_static_codex_mass_v11.py --maximum-programs 1` exactly once against the packaged pair.**
- [x] **Step 3: Record the unmodified pass/reject decision, measured utilization/areas when present, runtime, hashes, and the no-post-result-tuning statement.**
