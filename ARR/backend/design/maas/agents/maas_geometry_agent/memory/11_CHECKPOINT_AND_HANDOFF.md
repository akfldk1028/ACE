# Checkpoint and handoff protocol

This file exists because session loss previously caused successful MASS
evidence to be forgotten and broad runs to be repeated. Every agent must keep
the numbered memory bundle current while work is in progress, not only at the
end of a long run.

## Mandatory checkpoint triggers

Append a concise checkpoint to `09_CURRENT_STATE.md` and persist the run's
append-only version memory when any of these occurs:

1. a bounded run completes or fails;
2. three new authored candidates have been evaluated;
3. thirty minutes of active MASS investigation has elapsed without a run
   boundary;
4. a root cause, policy threshold, or validation authority changes;
5. before a commit, context handoff, usage-limit stop, or session end.

Do not rewrite the failure ledger to make a result look better. Move superseded
explanations to history only when the replacement evidence and commit are
named.

`update_run_progress` enforces the execution-side half of this rule. Each
distinct phase/counter payload creates one hash-bound append-only checkpoint;
repeating the identical state reuses the same file rather than producing
noise. The human-readable 09 checkpoint is still required at the triggers
above because a JSON counter cannot explain the architectural root cause.

## Checkpoint payload

Record only enough information to resume safely:

- timestamp, branch, commit, version/output directory;
- exact immutable manifest/admission identity and whether a paid call occurred;
- evaluated, compiled, individual hard-pass, compatible-selected, and
  canonical-publishable counts as separate numbers;
- current phase and the first typed blocking reason;
- capacity hard-floor and preferred-target values;
- final-mesh phenotype/island counts, stepped and wedge counts, minimum pair
  distance, PNG path and SHA-256 when rendered;
- exact next command or smallest next experiment;
- explicit statements of what must not be rerun or weakened.

Never store API keys, OAuth tokens, cookies, raw authorization headers, parcel
coordinates, or enormous candidate payloads in agent memory.

## Next-session start procedure

1. Read `manifest.json` and every required file in order.
2. Read `git log -5 --oneline` and `git status --short`; preserve unrelated
   dirty changes.
3. Inspect the newest append-only run memory and its PNG before generating.
4. State the four counters explicitly. `canonical 0/20` never erases a valid
   diagnostic `3/3` or individual hard-pass pool.
5. Resume the exact next bounded experiment from `09_CURRENT_STATE.md`.

## Current handoff

- Latest committed recovery contract: `ae44c10`.
- Latest bounded proof: C112, about 50 seconds,
  `5 evaluated -> 4 compiled -> 4 individual hard-pass -> 3 compatible`.
- C112 stepped count is zero; wedge-like count is three. Its minimum selected
  final-mesh pair distance is `0.15224147` against required `0.10`.
- Capacity-first policy is `0.60` hard floor and `0.70` preferred target.
- PNG:
  `docs/playwright/design-route-live-verify/legal-mass-v31-c112-diverse3-cap60/maas-book-neighborhood-3.png`.
- Canonical publishable status remains `0/20`; this is a release certificate,
  not the generator success counter.
- Target-five selection now enforces four measured body phenotype islands,
  maximum two cards per phenotype, four body/roof signatures, maximum one
  visible step, and pair distance `>= 0.10`; the measured wedge cap is three.
- Next bounded action: build that five-card final-mesh phenotype-island supply
  from valid survivors and request only missing non-wedge islands. Do not run a
  broad target-20 batch and do not relax law, parking, topology, or identity.
