# r327 Progressive Target-3 Timeout - 2026-08-02 KST

## Exact Run

```text
PNU: 1168011800104170004
program: neighborhood
command: python manage.py benchmark_maas_book_program_portfolios
  --pnu 1168011800104170004
  --program neighborhood
  --progressive-target 3
  --output-dir .../book-program-portfolios-r327-progressive-target3
memory/design commit: e79c3df
working-tree patch SHA-256 before run:
  3e1729c5b8ee735a74554ee35412638cdabcc1989ef95391e6841320ee4d98cb
```

The external command reached its 45-minute limit and returned exit 124. Its
Python child survived the shell timeout and was explicitly terminated by exact
matching output-path command line. No unrelated Python process was stopped.

## Persisted Stage State

- run-state phase: `initial_selection`
- selection pool: `2`
- selected: `0/3`
- required scopes: `3`
- selected scopes: `0`
- official summary: not written
- official selected board: not written
- base VLM preview PNGs: `8`
- final VLM preview PNGs: `7`

The run-state field `live_vlm_requested=false` is stale/incorrect. Fifteen
distinct actual final-book VLM cache records and response IDs were written and
are the stronger execution evidence.

## Provider-Budget Failure

The progressive command used `setdefault` for
`MAAS_PAID_PROVIDER_MAX_REQUESTS`. The pre-existing `.env` value therefore won
and the intended target-3 total ceiling of six was not applied.

- actual VLM cache records / unique response IDs: `15/15`
- recent geometry-author cache records / unique response IDs: `16/16`
- observed provider responses: at least `31`
- intended target-3 budget: LLM author batches `2` plus VLM maximum `4`

This is a pipeline budget defect, not permission to repeat the run.

## VLM Result Distribution

- program-fit pass/fail: `6/9`
- `needs_carved_void`: `14`
- `wrong_program_typology`: `9`
- `weak_form_continuity`: `6`
- `too_box_like`: `4`
- `good_step_mass`: `5`
- `good_void`: `1`

Visual review shows bend, cut-corner, cross and rotate variants, but the board
is still dominated by low bar, terrace and stepped silhouettes. Base and final
previews are nearly unchanged, so typed repair did not materially transform
the final legal MASS in this interrupted run.

## Direct Visual Evidence

```text
docs/playwright/design-route-live-verify/
book-program-portfolios-r327-progressive-target3/
r327-interrupted-vlm-witness-15.png
SHA-256:
ad9c3f06842c8a357324255bcbfb80c8435c38ff4f1df198b71f38d274dc2a54
```

The board is labelled `INTERRUPTED`, `NOT SELECTED`, and `NOT PUBLISHABLE`.

## Single Next Change

- Replace environment `setdefault` with direct in-memory
  `configure_paid_provider_budget(6)`.
- Do not start another replenishment cycle after 40 percent of the runtime
  budget has elapsed.
- Reuse r327 author/VLM caches in r328; do not pay to repeat identical inputs.

