# r326 Lawful Competition MASS Recovery Plan - 2026-08-02 KST

## Product Goal

The product is not a geometry gallery. It must generate diverse,
competition-grade MASS alternatives for the same real PNU and program while
obeying law, FAR, BCR, floor, parking, geometry identity, and exact-render VLM
acceptance. Elevation follows only after MASS is frozen.

## Confirmed Regression

- The historical successful supply used 121 raw LLM candidates, 90 compiled
  variants, and a 155-candidate pool.
- Current live authorship is capped at 12 while base and final VLM stages are
  fail-closed.
- Non-stepped floorwise replay is now correctly rejected, but no sufficient
  morphology-preserving repair supply replaced it.
- Strict selection can hide useful hard-pass evidence behind an empty board.

## Chosen Recovery

Use broad LLM-authored AST supply, principal-frame whole-solid legal placement,
typed legal and developmental-VLM repair, exact-final VLM acceptance, and
certified-mesh diversity selection. Do not restore dishonest stepped fallback
or weaken deterministic hard gates.

## Run Rules

- Promotion sequence: 3, 10, 20.
- Never repeat an identical command and configuration after failure.
- Change one subsystem per diagnostic run.
- Record command, environment names, commit, stage counts, failure histogram,
  model/response/request/cache evidence, PNG paths and SHA-256, elapsed time,
  hypothesis result, and the next single change.
- A failed strict board must still preserve a separately labelled witness board.

## Status

`implementation_focused_tests_pass`; no new LLM, VLM, or portfolio run has
occurred at this checkpoint.

## Implemented Recovery Boundaries

- Progressive budgets are immutable: target 3=`36/24/4/2700s`, target
  10=`90/70/13/5400s`, target 20=`160/120/24/10800s` for
  raw/compiled/VLM/runtime.
- The hidden provider-side 12-program cap is removed. LLM authorship is split
  into at-most-24-program batches: target 3 uses `24+12`; target 20 uses seven
  batches totalling 160.
- Base BOOK VLM is now developmental: reviewed failures retain critic actions
  and geometry edits and release descendants for the exact repair cycle.
  Unreviewed parents remain withheld. Final exact VLM remains authoritative.
- Principal-frame placement failures persist recipe-free `LegalFitDeficit`
  records and feed the next replenishment LLM context.
- Certified final gestalt measurements produce label-free cluster IDs. The
  uniform maximum is `ceil(target*0.25)`.
- Failed strict selection persists a separate non-publishable witness PNG and
  JSON with hashes and failure reasons.
- `--progressive-target 3|10|20` requires actual LLM authorship and actual VLM
  and applies a process-wide provider budget.

## Focused Verification

```text
CLI help/import: pass
Focused Django tests: 20/20 pass
System check during tests: no issues
```

Covered contracts: progressive budget, LLM batching, all-selected LLM
authorship, legal-fit deficit, morphology preservation, developmental base
VLM release, certified-mesh cluster key, and failure witness persistence.
