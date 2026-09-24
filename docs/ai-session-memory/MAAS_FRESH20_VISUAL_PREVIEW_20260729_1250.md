# MAAS Fresh-20 Visual Preview — 2026-07-29 12:50 KST

## Ruling

This is a genuinely new 20-geometry execution created for immediate visual
inspection, but it used the wrong generation path. It is **not** an
architectural MASS portfolio and is **not** the six-scope, PNU-resolved,
law/capacity/parking publishable-20 acceptance.

Use this exact status:

`rejected_wrong_generation_path`

The user explicitly rejected it because `generate_maas_fresh_batch` bypassed
PNU law, program projection, floor-capacity planning, derived BaseVolume
scope breadth, and actual storey/GFA logic. Do not call it legal, PNU
accepted, architectural MASS, six-scope complete, or competition-ready.
Never use `generate_maas_fresh_batch` as a substitute for the competition-20
PNU pipeline again.

## Artifacts

- Combined board:
  `docs/mass/fresh20-unitbox-book-preview-20260729-1250.png`
- Board SHA-256:
  `30AA86E40F9A17D02F39011A01560202EA285EB9CD605CF6DC11CC20AC74139A`
- Individual cards:
  `docs/mass/fresh20-preview-20260729-1250/cards/mass-01-*.png`
  through `mass-20-*.png`
- Batch A manifest:
  `docs/mass/fresh20-preview-20260729-1250/fresh20a-20260729-1250.batch.json`
- Batch B manifest:
  `docs/mass/fresh20-preview-20260729-1250/fresh20b-20260729-1250.batch.json`
- Each execution directory contains `mass.png`, `execution.json`,
  `mass.png.passport.json`, and local elevation evidence.

## Exact commands

```powershell
cd D:\Data\25_ACE\ARR\backend
python manage.py generate_maas_fresh_batch `
  --batch-id fresh20a-20260729-1250 `
  --count 10 `
  --building-type "neighborhood living" `
  --output-root D:\Data\25_ACE\docs\mass\fresh20-preview-20260729-1250

python manage.py generate_maas_fresh_batch `
  --batch-id fresh20b-20260729-1250 `
  --count 10 `
  --building-type "neighborhood living" `
  --output-root D:\Data\25_ACE\docs\mass\fresh20-preview-20260729-1250
```

## Verified execution facts

- Batch A: requested 10, accepted 10.
- Batch B: requested 10, accepted 10.
- Total geometry-ready: 20/20.
- Distinct program hashes: 20/20.
- Distinct geometry hashes: 20/20.
- Rejected candidates before replacement: 2 in Batch B.
- Paid image requests: 0.
- Paid VLM requests: 0.
- Approximate wall-clock generation: 38.6 seconds for the two commands,
  excluding board assembly.
- Neo4j and the law-domain search service were reachable during execution,
  but PNU and floor-capacity-plan identity were unresolved; this does not
  constitute a legal pass.

## Flow actually exercised

```text
canonical 1/1 UnitBox
-> proportional base seed Matrix4
-> BOOK base-volume node, scope 1/1 only
-> BOOK/family typed operator or macro
-> UnitBox normalization
-> geometry compiler
-> manifold/watertight geometry gate
-> local multi-view render
-> single-execution passport/elevation evidence
```

The 20 programs use two fresh variation seeds across ten family contracts:

1. curved bar
2. open courtyard
3. radial cross
4. stepped setback
5. tapered leaning
6. diagonal cut
7. face attachment
8. profiled span
9. split bridge
10. nested offset

The Batch A and Batch B program/geometry hashes are distinct, but the family
contract is intentionally paired. This proves fresh synthesis and the
UnitBox/BOOK/compiler/render path; it does not prove 20 competition-grade
languages.

## Not exercised

- BaseVolume scopes `1/2`, `3/8`, `1/4`, `1/8`, `1/16`
- resolved PNU parcel placement
- neighborhood program projection
- shared floor-capacity-plan hash
- BCR/FAR capacity alternatives
- parking hard pass
- PNU-bound Neo4j law evidence
- target20 quota solver and all 190 certified-mesh pair distances
- publishable-20 manifest
- paid board VLM

## Direct visual inspection

The combined board was opened and inspected after assembly.

- 20 images render correctly with no missing card.
- Courtyard, radial, stepped, tapered, cut, profiled, split, nested, and curved
  families are visible.
- Only two cards are explicitly stepped-setback, so the preview is not
  all-stepped.
- Batch A/B pairs remain visibly related; this board is a supply preview, not
  the final diversity portfolio.

Independent visual-review report:
`docs/mass/fresh20-preview-20260729-1250/visual-review.md`.

Independent verdict: reject as competition-ready. The reviewer found ten
paired A/B families, obvious near-duplicates at 04/14, 05/15, and 10/20, and
excess stepped/slab repetition.

- Strict provisional keep:
  02, 03, 05, 08, 09, 11, 16, 17, 18, 19.
- Reject:
  01, 04, 06, 07, 10, 12, 13, 14, 15, 20.

This rejection is useful only as evidence that the geometry compiler and
renderer can produce images. It does not prove that the architectural MASS
generation path works. Merely changing variation seeds inside ten family
contracts is insufficient for a competition-grade 20-card portfolio.

## Required next execution

After Task 4 and Task 5 fixes receive clean re-review, run the actual
six-scope/PNU path without per-card VLM:

```powershell
cd D:\Data\25_ACE\ARR\backend
python manage.py benchmark_maas_book_program_portfolios `
  --pnu 1168011800104170004 `
  --program neighborhood `
  --recursive-only `
  --publishable-20 `
  --output-dir D:\Data\25_ACE\docs\mass\fresh-pnu20-<timestamp>
```

Then inspect the real board, run at most one board-level VLM audit, and update
the canonical competition-20 memory. Never substitute this preview for that
acceptance.
