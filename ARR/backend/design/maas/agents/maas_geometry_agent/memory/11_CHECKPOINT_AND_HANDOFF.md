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

- Latest committed paper-island checkpoint: `69f6d8b`.
- C112 and C113-C115 are superseded as visual success claims. Direct PNG
  inspection found wedge/block convergence, and the legal CSG retention audit
  proved that some apparent survivors replaced most authored form with the
  legal host silhouette.
- The fixed fitter enforces authored plan retention `>=0.78`; it may no longer
  enlarge a cross/void symbol and keep only its host intersection. Source
  bridge regressions are `5/5` green.
- Latest honest bounded replays: C116
  `11 evaluated -> 5 compiled -> 0 individual hard-pass`, and C117
  `15 evaluated -> 4 compiled -> 0 individual hard-pass`. The clean C117
  sources reach only about `2.6-3.7%` feasible utilization before dishonest
  projection; the admitted cache is not a site-feasible 3D supply.
- Capacity-first policy is `0.60` hard floor and `0.70` preferred target.
- Canonical publishable status remains `0/20`, and no C113-C117 PNG is an
  accepted diverse board. C114/C115 boards are retained only as visual failure
  evidence.
- Next bounded action: change the site-aware GeometryProgram author/admission
  contract so a seed must compile at four legal Z sections, genuinely vary in
  section, reach aggregate utilization `>=0.60`, and retain authored material
  `>=0.78` before BOOK/production. Then author/revise one seed and render one
  ISO proof before attempting three or twenty.
- Do not run another broad cached-manifest replay, weaken the identity or law
  gates, restore host-replacement CSG, or confuse phenotype-island selection
  with valid architectural supply.

## Current handoff update: C124

- Latest bounded production proof is C124: `1 evaluated / 1 compiled / 1
  individual hard-pass / 1 compatible selected`; canonical remains `0/20`.
- C124 GFA is `217.718 m2`, feasible utilization `0.6551`, FAR `82.43%`.
  Law, parking, semantic projection, clean mesh and final binding pass.
- ISO PNG is
  `docs/playwright/design-route-live-verify/legal-mass-v31-c124-continuous-fold1/maas-book-neighborhood-1.png`
  with SHA-256
  `032818651c3fe230029543b08070f58fed5922a18e5d7c19a68346dafba10a22`.
  It is continuous/non-stepped but still wedge-like, so it is not a diverse
  portfolio claim.
- Resume with one fresh non-wedge site-feasible AST using the same full-stack
  `0.60` capacity contract and exact `0.995` direct affine acceptance. Prefer
  a void, wing, curved or multi-axis continuous phenotype; inspect its ISO
  before requesting three. Do not rerun C118-C124 or launch target 20.
