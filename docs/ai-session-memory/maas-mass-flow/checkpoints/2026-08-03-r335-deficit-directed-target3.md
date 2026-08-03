# r335 Deficit-Directed Target-3 - 2026-08-03 KST

## Run

```text
run: book-program-portfolios-r335-deficit-directed-target3
PNU: 1168011800104170004
program: neighborhood
mode: progressive target 3, live LLM author, base/exact/final VLM
elapsed: 98.1 seconds command / 94.1 seconds program
result: fail, 0/3
```

Official PNG:

`docs/playwright/design-route-live-verify/book-program-portfolios-r335-deficit-directed-target3/maas-book-neighborhood-3.png`

Direct PNG review: the board contains only the title strip and no MASS geometry. This is a truthful empty diagnostic board, not a successful portfolio.

## Exact attrition

```text
LLM-authored active seeds: 16
exact compile/materialization invocations: 16 / cumulative limit 24
terminal materialization failures: 11
materialized candidates: 5
floor/program/shared-floor hard-pass candidates: 1
base VLM reviewed: 1
base VLM hard-pass: 0
released descendants: 0
exact final VLM scored: 0
selected: 0/3
```

Terminal materialization reasons:

```text
authored_identity_collapse: 2
authored_visual_authority: 5
floor_affine_fit: 4
```

Legal-fit deficit events:

```text
whole_solid_affine_fit_infeasible: 16
```

The event count is not a terminal-candidate count. Task 5 count-unit metadata correctly distinguishes the two populations.

## Base VLM result

The only floor/program hard-pass candidate was `llm_taper_notch`, scope `1/16`. Base VLM rejected it with:

```text
book_base_operative_vlm_too_fragmented
book_base_operative_vlm_weak_primary_mass
book_base_operative_hierarchy_below_development_floor
```

The VLM returned typed geometry edits for a public-threshold courtyard and a cleaner dominant gesture. The hard visual gate was therefore operating, not bypassed.

## Provider ledger evidence

```text
provider limit: 15
used: 3
geometry author: 2 / 2
base candidate VLM: 1 / 3
exact candidate VLM: 0 / 9
portfolio board VLM: 0 / 1
remaining total: 12
```

The final board reserve worked. The failure occurred before exact/final VLM.

## Newly confirmed blocker

Replenishment had eight exact compile opportunities remaining, but produced zero new seeds because the initial stage consumed the entire author quota. Logs show repeated:

```text
paid_provider_request_quota_exhausted:kind=geometry_author:quota=author:2/2
```

The replenishment cycle therefore had:

```text
exact compile limit: 8
exact compile invocations: 0
new LLM-authored seeds: 0
stop reason: cycle_budget_exhausted
```

Do not fix this by changing a shared author quota from 2 to 3. The initial synthesis already attempts another author request and can consume the added slot. The next change must hard-partition:

```text
initial geometry author quota: 2
replenishment geometry author reserve: 1
```

Also verify that the rejected base VLM audit's typed critic actions and geometry edits reach the replenishment author context. VLM/legal/GFA/parking thresholds remain unchanged.
