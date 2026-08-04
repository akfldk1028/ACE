# r55-r56 final VLM authority checkpoint

## Objective

Restore the exact post-BOOK final VLM path without weakening law, capacity,
parking, semantic projection, or competition-quality gates.

## r55 failure

- Generated/evaluated: 62
- Clean: 12
- Program pass: 8
- Legal archive: 12
- BASE reviewed/approved: 5/4
- Program routing: 7 input, 5 preselection, 4 downstream hard pass
- Final VLM: 4 routed, 0 scored, 0 hard pass
- Selection: 0/5
- Failure: canonical v2 physical-meter `source_surfaces` were overwritten by
  normalized-Z source materialization before preview validation.

## Fix

`materialize_source_feature_surfaces()` now recognizes a canonical v2 final
authority artifact, validates it through `CertifiedMassArtifact.load()`, checks
the feature surface/core-hash binding, and returns without reserializing source
geometry. Legacy v1 behavior remains unchanged. Missing or tampered bindings
remain hard failures.

## Regression evidence

- Focused provenance regression: pass
- r56 full live LLM/VLM run: exit 0
- Final VLM: 4 routed, 4 scored, 0 provider failures
- Authority validation failures: 0

## Remaining first loss

r56 has a genuine competition-quality rejection rather than an integration
failure:

- Final VLM hard pass: 0/4
- Typed repairs requested: 4
- Repair clean/reprojected: 2/2
- Repair accepted: 0
- Main VLM reasons: program appropriateness 4, arbitrary tier silhouette 3,
  weak gesture/hierarchy/program fit 3, too box-like 3, weak continuity 3,
  wrong program typology 3.
- Repair terminal reasons: program hard gate 2, authored profiled legal clip 1,
  repaired source materialization 1.

Next action: preserve the typed subreason currently collapsed into
`repaired_source_materialization_failed`, then fix the earliest repair defect.
Do not lower final VLM competition thresholds and do not rerun the full
portfolio until that first repair failure is understood.

## Visual evidence

- `docs/playwright/design-route-live-verify/book-program-portfolios-legal-archive-target5-r56/maas-book-neighborhood-0-legal-archive.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios-legal-archive-target5-r56/maas-book-neighborhood-5.png`
