# r67-r68 first visible selected MASS checkpoint

## r67

- Full run completed without crash.
- Selected: 1/5, one BOOK operation.
- Certified geometry measured approximately 14.1 x 12.6 x 14.0m with 799m3
  volume, so it was not a thin sheet.
- Render still looked like a vertical plate because another preference-render
  path multiplied physical v2 Z by candidate height again.
- Final VLM cache also reused the old distorted r63 PNG.

## Fix

- All v2 physical-meter render paths preserve physical Z.
- Only explicit legacy normalized-Z artifacts scale by candidate height.
- Final VLM cache identity includes exact rendered PNG SHA-256 and renderer
  coordinate-contract version.
- Stale distorted PNG cache entries naturally miss without global deletion.

## r68

- Full live LLM/VLM run exited successfully.
- Portfolio result: 1/5 selected floor-verified MASS, one BOOK operation.
- Selected card renders visibly at normal proportions.
- Selected operation label: `shift`.
- Displayed capacity: FAR 113/126%, reserve 90% -> 90%.
- Status: SELECTED/WARN.

Visual evidence:

- `docs/playwright/design-route-live-verify/book-program-portfolios-legal-archive-target5-r68/maas-book-neighborhood-5.png`

## Remaining objective

- Portfolio is still incomplete at 1/5.
- Selected form remains stepped/terraced and does not satisfy the intended
  competition-grade diversity target by itself.
- Continue from the post-selection diversity/portfolio-completion funnel; do
  not reopen repaired authority, coordinate, or persistence paths unless their
  typed contracts fail again.
