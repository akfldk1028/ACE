# MAAS BOOK Architectural-Language Corpus Audit — 2026-07-15

## Why this exists

The user is a licensed/practising architect intending to use ARR/MAAS in a
real design office. The 69 scanned pages under `docs/260506/BOOK/` are not
decorative references. They are a supplied architectural-language corpus and
must become traceable design evidence rather than another hidden prompt prior.

## Verified facts

- `docs/260506/BOOK/` contains 69 sequential JPEG pages.
- Every page is 1190 x 1684 pixels and is readable as an image asset.
- Repository-wide search on 2026-07-15 found no runtime code or corpus manifest
  that references `docs/260506/BOOK`, `스캔_smallpdf`, or its pages.
- Therefore the current claim must be: **the BOOK was supplied, but it has not
  yet been systematically distilled or connected to generation**.
- The current Mass-Brain PNU graph is seed-centric:
  - 64 `massdsl_seed` nodes;
  - one `seed_generation` stage;
  - 2,016 pair relations (706 `same_family`, 1,310 `contrasts`);
  - the relation set is effectively all feature pairs, so the raw GRL canvas is
    visually over-connected and is not a useful presentation of learned design
    reasoning.
- Current Mass-Brain DB metrics for PNU `1168011800104170004`:
  - 2 append-only versions;
  - 94 executable proposals and 6 experimental proposals;
  - 28 recorded outcomes;
  - promotion remains `shadow`, `slots=0`.
- v100 still compiled/VLM-evaluated only 2 of 14 exact Mass-Brain proposals.
  This is not evidence that BOOK-derived knowledge improves geometry.
- `ARR/backend/design/maas/grammar/data/maas_terms.v0.json` and parts of
  `maas_sequences.v0.json` contain mojibake in Korean labels. Do not use the
  damaged strings as evidence that the Korean architectural vocabulary was
  preserved correctly.

## Required systematic corpus contract

Every BOOK page must receive a stable record, not only a caption:

1. `source_id`, page number, checksum and local provenance.
2. OCR/transcription with a manual-correction field for Korean terms.
3. Image regions for diagram, text and built-reference evidence.
4. Generalized relation profile using coordinate-free primitives such as
   `preserve`, `carve`, `step`, `bend`, `bridge`, `cluster`, and `fold`.
5. Typed component-graph fragment with declared parameter schema and program/
   site applicability conditions.
6. Counterexample and failure risks: fragmentation, unusable depth, false
   ground contact, excessive surface count, legal repair loss.
7. Executable compile evidence, VLM evidence, FAR/capacity result and hard-gate
   result before it becomes an eligible Mass-Brain parent.
8. Architect approval/correction as first-class feedback, never overwritten by
   a model score.

Raw page coordinates and a named precedent silhouette must never be copied into
parcel coordinates. The system should learn a transformable relationship and
its applicability conditions.

## Correct runtime flow

```text
BOOK page / ArchDaily image / architect text
  -> VLM + OCR evidence extraction
  -> architect-correctable relation card
  -> typed component subgraph + parameter schema
  -> program/site-conditioned graph proposal
  -> ARR geometry compile on real PNU
  -> clean-mass + FAR/BCR/height/parking hard gates
  -> VLM pairwise review + architect decision
  -> append-only Mass-Brain outcome
  -> only evaluated, hard-pass parents become eligible for recombination
```

## Acceptance criteria before claiming BOOK integration

- 69/69 pages have stable manifest records and checksums.
- Korean architectural terms round-trip without mojibake.
- Every extracted principle links to its page/region evidence.
- At least one executable typed graph and one counterexample are attached per
  accepted principle; abstract text alone is insufficient.
- A blind baseline-vs-BOOK-derived PNU benchmark shows compile survival, visual
  preference and hard-gate parity separately.
- The 20-card board preserves language-cell diversity and does not replace one
  box family with 20 variants of one BOOK diagram.
- Promotion remains shadow until the existing Mass-Brain thresholds are met.

## Presentation evidence

- `docs/mass-brain-presentation-20260715.html`
- `docs/mass-brain-presentation-20260715.png`
- `docs/mass-brain-pnu-1168011800104170004-20260715.png`

The first two are a Korean 16:9 presentation view. The third is the real GRL
debug UI. Keep them distinct: the presentation explains the intended and
partially connected loop; the debug screenshot exposes the current dense graph.
