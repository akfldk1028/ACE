# Law-Derived Floor Capacity Design

**Date:** 2026-07-27
**Scope:** BOOK portfolio MASS generation, exact shared-floor evidence, and elevation handoff

## Goal

Replace catalog-owned fixed floor counts with one law- and program-derived
floor capacity plan while preserving the existing UnitBox/BaseVolume, BOOK,
LLM/VLM, legal, parking, and elevation boundaries.

## Current defect

`program_catalog.py` currently supplies `(height, floors)` before the live PNU
legal context exists. `capacity_contract.py` then measures only those requested
floors, while `legal_envelope.py` can independently derive another floor stack.
The result has two floor authorities: a five-floor neighborhood fixture can
silently become the capacity ceiling even when FAR, height, sunlight, and the
program profile permit a different answer.

## Module boundary

Create `book_language/floor_capacity_plan.py` as the only pre-authoring
authority for occupiable floor count and target floor areas.

The module consumes:

- the immutable `LegalGenerationContext`;
- the live parcel polygon;
- the resolved program profile;
- the program/site capacity target;
- an optional brief height cap.

It returns an immutable, serializable plan containing:

- program ID and planning mode;
- typical floor height and legal/brief height cap;
- allowed and selected occupiable floor count;
- one exact legal section and legal area per selected floor;
- BCR footprint cap and statutory FAR area cap;
- feasible maximum and target GFA;
- deterministic target area per floor;
- status, derivation, and explicit failure reasons;
- a content hash used by generation, gates, replay, and elevation.

## Derivation

For ordinary occupiable-floor programs:

1. Resolve the program's `target_floor_range`.
2. Resolve typical floor height from the existing evaluator.
3. Clamp the candidate range by legal height and an explicit brief height cap.
4. Sample the live horizontal/sunlight field at every floor top.
5. Stop before a terminal sunlight section that fails the same minimum
   occupiable area or clear-depth rules used by the shared-floor hard gate;
   such a legal sliver or strip is envelope residue, not a floor or GFA target.
6. Apply the statutory BCR footprint cap and FAR total-area cap.
7. Compute the target GFA from the full law- and program-feasible stack, then
   select the smallest allowed floor count that can carry that full feasible
   capacity. This preserves the unused target-utilization share as real design
   reserve for courts, voids, terraces, and circulation instead of forcing the
   selected plates to be almost solid.
8. Allocate target GFA proportionally to each exact legal section so every
   selected floor retains the same design-reserve ratio; no floor target may
   exceed its legal section.
9. If the target is unreachable, return the maximum feasible plan with an
   explicit `target_unreachable` status. Do not fabricate extra floors or relax
   a gate.

For clear-span halls, occupiable floors and mass clear height remain distinct.
Existing subtype rules continue to own hall clear height; the new module only
derives occupiable levels within that program contract.

## Geometry contract

- One `1/1 UnitBox` remains primitive authority.
- BOOK BaseVolume selections (`1/1`, `3/8`, `1/2`, `1/4`, `1/8`, `1/16`) are
  derived UnitBox states.
- Translate, rotate, scale, mirror, and shear remain homogeneous 4x4 matrix
  operations from the base model onward.
- Boolean and nonlinear BOOK operations remain typed CSG/modifier nodes; they
  are not misrepresented as a single affine matrix.
- Floorwise legal placement uses composed 4x4 matrices and carries the exact
  floor capacity plan hash.

## Pipeline

`PNU law graph/context`
-> `floor_capacity_plan`
-> `UnitBox/BaseVolume`
-> `BOOK + LLM GeometryProgram/AST`
-> `compiler`
-> `shared-floor + law/FAR/BCR + parking hard gates`
-> `render`
-> `VLM typed review/repair`
-> `same hard gates`
-> `selector`
-> `frozen exact MASS`
-> `elevation agent`

Every downstream stage must consume the same plan identity. Realized
shared-floor geometry, not requested metadata, remains the final authority for
FAR and parking.

## Failure handling and cost

- Invalid or infeasible plans stop before paid model calls.
- Previously rejected exact geometry hashes remain excluded.
- Smoke verification performs at most one new LLM author request and one final
  VLM candidate review per iteration.
- A failed VLM candidate advances to a different exact hard-pass candidate; it
  does not lower thresholds or repeat the same paid image.

## Verification

Tests must prove:

- a catalog value of five cannot override a different law-derived result;
- legal height clamps the allowed floor range before capacity measurement;
- sunlight-shrinking upper plates affect selection and allocation;
- terminal sunlight slivers or strips below the shared occupiable area/depth
  minimum never become authored floors or GFA targets;
- target utilization remains a measurable design reserve in the selected
  stack, including sunlight-constrained sites;
- per-floor targets never exceed exact legal sections or statutory FAR;
- unreachable targets are explicit;
- hall clear height stays separate from occupiable floor count;
- the same plan hash reaches shared-floor, replay, and elevation evidence;
- UnitBox/BaseVolume matrix provenance is retained;
- one bounded live loop can produce an exact selected MASS before elevation.

The final acceptance requires focused backend tests, full relevant regressions,
an exact single-MASS replay, one bounded elevation proposal, and live
`/design/language` verification on port 5178 with no console errors.
