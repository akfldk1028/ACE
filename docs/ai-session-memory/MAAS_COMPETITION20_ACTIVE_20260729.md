# MAAS Competition-20 Active Handoff

Updated: 2026-07-29 (Asia/Seoul)

This is the canonical continuation note for the active MASS recovery. Read
this file first, then:

1. `docs/ai-session-memory/MAAS_R9_TARGET20_ROOT_CAUSE_20260729.md`
2. `docs/superpowers/specs/2026-07-29-competition-grade-20-mass-portfolio-design.md`
3. `docs/superpowers/plans/2026-07-29-competition-grade-20-mass-portfolio.md`
4. `.superpowers/sdd/2026-07-29-competition-grade-20-mass/progress.md`
5. `docs/ai-session-memory/MAAS_FRESH20_VISUAL_PREVIEW_20260729_1250.md`

## User-visible objective

- One PNU and one program must produce 20 legal MASS alternatives on one
  board, quickly enough for direct visual review.
- The 20 must show architectural-language diversity. Unique hashes alone are
  insufficient.
- Stepped masses are a minority option, not the default result.
- First acceptance PNU: `1168011800104170004`.
- First acceptance program: `neighborhood`.
- Neo4j law and parking evidence remain hard requirements.
- Do not use per-card paid VLM before the first numeric/legal PNG.
- Copy a board into `docs/mass` only after the complete publishable-20
  contract passes and the board is visually inspected.
- The user's supplied historical diversity reference was copied unchanged to
  `docs/mass/reference-original-diverse-mass-board.png`
  (SHA-256
  `7532E187FE84F3BA9F827CFE00247FB6777113ED385CD02D7A5DA26032C09D4F`).
  It is a visual reference, not new acceptance evidence.
- The 12 reference cards were deterministically cropped without generative
  changes into
  `docs/mass/reference-original-diverse-mass-cards/mass-01-*.png` through
  `mass-12-*.png` for direct inspection.

## Canonical generation model

```text
one canonical 1/1 UnitBox
-> derived BOOK BaseVolume occupancy states
   1/1, 1/2, 3/8, 1/4, 1/8, 1/16
-> long/short/vertical axis and proportional seed Matrix4
-> BOOK architectural verbs and variations
-> typed CSG/macros for non-affine operations
-> program/capacity projection
-> legal affine placement or intentional stepped legal CSG
-> exact law/program/capacity/parking/hash gates
-> certified-mesh diversity solver
-> selected 20 MASS
-> elevation
```

Affine scale/rotation/shear/translation/placement use homogeneous Matrix4.
Courtyard, void, union, difference, bend, curve, and similar non-affine
operations remain typed CSG/macros. The six BaseVolume labels are not six
independent primitive models; they are normalized occupancy/partition states
derived from the single public 1/1 UnitBox root.

Floor count is never a fixed 3/4/5-storey catalog choice. For ordinary
occupiable MASS it is an unresolved lawful `N` (including 7, 20, or more):
measure each PNU-bound legal floor section, author/project the actual floor
plate, accumulate certified GFA, and stop at the minimum `N` that reaches the
selected FAR/GFA target. The target is distributed through authored
parameters or a form-preserving affine fit and then remeasured from the final
mesh. Generic terminal-floor trimming is forbidden because it would rewrite
unrelated alternatives as stepped masses; a terminal residual plate is
allowed only for intentionally stepped/terraced typed language. Exhausting
the lawful height/section field before the target is a hard
`target_unreachable` result. Historical catalog floor hints and program
`target_floor_range` values are preferences, not legal/capacity ceilings,
unless an explicit program dimensional invariant (for example a clear-span
hall) requires one.

The shared legal-floor-field hash identifies the complete PNU legal field and
all usable floor sections; it must not impose one identical design floor count
on all 20 alternatives. Each alternative carries its own certified
actual-GFA-stop hash while binding that same trusted PNU legal-field hash.

The current declared axes contain 68,310 theoretical BOOK variant paths before
program conditioning:

```text
1 base model * 6 BaseVolumes * 3 orientations * 5 seeds
* 69 principles * 11 variations = 68,310
```

This count is diagnostic, not a demand to materialize the Cartesian product.
The publishable path must sample the lattice with quotas and cheap evidence.
Because many valid BOOK/CSG programs have no provable cheap envelope, an
`unknown_bounds` result is never called a cheap pass but may consume a
quota-protected `exact_required` slot inside the same 64-candidate exact cap.
Only exact compile/legal/capacity/parking/hash gates may then admit it. Invalid
ASTs and known cheap failures remain excluded.

## Why r9 collapsed

The architecture did not disappear. The r9 diagnostic control path:

- evaluated only 36 candidates;
- visited only `1/1`, `3/8`, and `1/2`;
- used one BOOK probe per genotype;
- therefore could not supply 20 legal alternatives;
- then applied floorwise legal projection broadly, which rewrote many
  surviving non-stepped authored meshes into stepped solids;
- selected with target-three caps that allowed one phenotype to occupy all
  three slots;
- treated silhouette distance 0.10 as adequate even though it only rejects
  near twins.

The r9 PNGs under `docs/mass/r9-pnu1-neo4j-target3-*.png` are
diagnostic/legal-only and must never be reported as competition portfolio
acceptance.

## Completed implementation

### Task 1: target-aware portfolio contract

Complete and independently reviewed.

- One fail-closed solver contract for targets 3, 10, and 20.
- Target 20 requires exactly 20 cards.
- Capacity bands require exactly 5/5/5/5.
- Scope/body/roof/chassis/plan/step/void/wing-curve/BOOK/gestalt constraints
  are enforced together.
- Target 3 regression requires three visibly distinct bodies with stepped at
  most one.
- No cap relaxation or score-only backfill.

### Task 2: authored legal preservation

Complete and independently reviewed.

- A contained authored legal program/mesh is preserved unchanged with its
  authoritative hash.
- Exact containment uses a closed, cap-inclusive clipped z-band solid check.
- Public floorwise CSG requires at least 0.995 capacity retention.
- Floorwise legal CSG is restricted to authored `setback`, `stepped_mass`, or
  `terrace` live-root programs.
- Twisted protrusion and intermediate legal-hole false certificates are
  covered by regressions.

### Task 3: certified-mesh gestalt

Complete and independently reviewed.

- Composite top/front/side/isometric/floor/roof/plan/void evidence comes from
  the certified final mesh.
- `visible_stepped`, `authored_stepped`, and `legal_seam_stepped` are separate.
- Pairwise minimum distance is 0.14; same-body or same-roof pairs require
  0.22.
- Continuous principal-frame normalization prevents rigid rotations from
  appearing falsely different.

## Active implementation

### Task 4: six-scope breadth scheduler

Implementer: `/root/competition_breadth_scheduler_impl`

Status at this checkpoint:

- implementation complete, fresh review active;
- focused tests: 9/9 pass;
- BOOK-language plus flow regressions: 144/144 pass;
- production modules pass `py_compile`;
- scoped diff check is clean except existing LF/CRLF warnings;
- cold-cache 48-record certified-mesh descriptors: 26.5731 seconds;
- breadth activates only for recursive, non-diagnostic, non-smoke full
  target-20 runs;
- target10 smoke, explicit diagnostic runs, and ordinary nonrecursive runs do
  not inherit target-20 budgets.

Required acceptance:

- first real breadth cycle visits all six scopes before any repeats;
- historical 36 cap is bypassed only in the publishable target-20 path;
- typed AST compiles once during cheap screening;
- exact shortlist stays within 48..64;
- body/roof/chassis/plan quota anchors cannot be evicted by score;
- failure evidence includes BOOK bind, authored compile, legal section,
  affine, exact CSG, capacity, parking, and hash-bridge stages;
- advance deterministic pages until 24..28 exact hard passes contain a
  feasible 20-set.

Fresh reviewer: `/root/competition_breadth_scheduler_review`.
Verdict: changes required. Fix round 1 is active with the original implementer.

Open Critical findings:

- production chooses 64 of 192 by index before exact authored/legal work;
  quota-aware scheduling runs afterward on already exact candidates, so rare
  morphology and failure evidence can be lost;
- the real replenishment page loop still uses legacy selected-count/scope
  stopping while competition evidence receives `feasible_portfolio=False`;
  the 24..28 exact hard-pass reserve plus feasible-20 result is not
  operational.

Open Important findings:

- the resolver has no explicit target argument and hardcodes target20, so a
  full target10 path may inherit the 192/64 budget;
- body/roof/chassis/plan minimum-distinct deficits are absent when the supply
  contains only one family on each axis;
- more than 28 exact hard passes still report ready even though the contract
  defines a bounded 24..28 reserve.

Review report:
`.superpowers/sdd/2026-07-29-competition-grade-20-mass/task-4-review.md`.
Fix round 1 implementation evidence:

- all five findings addressed in code;
- adverse production tests 7/7 pass;
- late rare body plus BOOK witness test 1/1 pass;
- BOOK-language plus flow regressions 150/150 pass;
- `py_compile` and scoped diff check pass;
- no live or paid run started.

Fresh re-review confirmed all five prior findings are addressed in production
(focused 6/6 and neighbor 150/150). One new Important remains: cheap legal,
capacity, and affine evidence is currently derived once from the site envelope
and copied to all 192 candidates rather than being candidate-specific. Exact
correctness remains fail-closed, but cheap filtering and the 120-second
runtime contract are incomplete.

Fix round 2 made the screen candidate-specific and passed focused 5/5 and
neighbor 155/155. Its re-review found one narrower Important: cheap AST bounds
can under-estimate supported bend/sweep/loft and z-to-xy Matrix4 operators.
Actual swept-bar evidence was cheap 12.0 x 2.4 versus compiled
11.3648 x 7.0206. Fix round 3 is active; unsupported bounds must fail closed
or use conservative analytical bounds. No publishable live run yet.

### Task 5 Steps 1-3: publishable command and frontend identity

Agent: `/root/pnu20_publish_frontend_impl`

Status at this checkpoint:

- backend RED captured: `--publishable-20` was unknown;
- frontend RED captured: a visual-hash mismatch still bound the passport;
- first GREEN: publishable/diagnostic conflict fails before PNU lookup;
- frontend passport requires program, geometry, visual, and
  floor-capacity-plan hashes; focused frontend tests 6/6 pass;
- second backend RED captured: no independent publishable manifest builder;
- implementation complete and awaiting fresh review;
- the manifest independently recalculates 20 rows, solver certificate,
  capacity 5/5/5/5, six scopes 3..4, morphology quotas, BOOK >=10,
  law/downstream status, four hashes, four phase timings, and typed deficits;
- a failed publishable audit persists evidence and raises `CommandError`;
- a passing backend-selected 20-card run takes precedence over stale
  single-execution replay in the frontend;
- fresh tests: BOOK 112/112, flow plus single execution 79/79, frontend 8/8,
  Vite builds and TypeScript pass, `py_compile` and diff check pass.
- integration gap found: the frontend now requires `visual_hash`, but the
  backend passport/archive producers did not yet emit that field. The Task 5
  implementer is authorized to add it from the authoritative certified or
  projected visual geometry hash and cover producer-to-archive-to-frontend
  flow with tests. Missing evidence must fail closed; it must not be invented
  from an unrelated hash.
- integration gap fixed: certified visual identity now flows through backend
  passport, archive row, and frontend binding; missing or mismatched evidence
  fails closed.

Implementation report:
`.superpowers/sdd/2026-07-29-competition-grade-20-mass/task-5-steps1-3-report.md`.
No real PNU run was performed in Steps 1-3.

Preliminary fresh-review warnings, not yet resolved:

- publishable audit trusts `combined_hard_pass` rather than directly checking
  per-row site, program, capacity, and parking gates;
- void/courtyard, wing/curve, wedge, pyramid, and all 190 pairwise gestalt
  distances are not independently recalculated;
- missing `visual_hash` may fall back to `geometry_hash`, hiding absent
  certified visual identity;
- phase timing is too coarse and zero-valued phases may pass;
- frontend publishable preference checks count/top-level status but not a
  passing publishable manifest with empty deficits.
- Critical adversarial proof: twenty rows with one repeated
  `(program, geometry, visual)` identity and twenty different floor-capacity
  plan hashes still passed with zero deficits. Publishable audit therefore
  lacks unique MASS identity and shared floor-capacity-plan authority checks.

Final Task 5 review verdict: changes required.

Critical:

- repeated identical MASS identities and inconsistent floor-capacity-plan
  hashes can pass;
- full certified-mesh pair/shape/BOOK contract is not independently audited;
- per-row site/program/capacity/parking and Neo4j law payload are not directly
  audited.

Important:

- visual hash may fall back to geometry hash;
- required internal timings are absent or zero;
- frontend preference lacks publishable manifest status/deficits;
- legacy/single records lack visual identity needed by the stricter binder.

Review report:
`.superpowers/sdd/2026-07-29-competition-grade-20-mass/task-5-steps1-3-review.md`.
Fix round 1 is active. No live/paid run is authorized until a clean re-review.

### Task 5 fix round 1 implementation checkpoint

The Task 5 review findings have now been implemented locally; the earlier
warnings above are retained as review history, not current code behavior.

- duplicate program/final-geometry/visual identities fail closed;
- the 20 selected rows must share one floor-capacity-plan hash;
- complete certified-final-mesh descriptors are persisted and all 190 pair
  distances are independently recomputed (`0.14`, or `0.22` for shared
  body/roof language);
- visible step, void/courtyard, wing/curve, wedge, pyramid, and BOOK diversity
  are recounted from final selected rows;
- site/program/capacity/parking gates and law-agent payload hash, exact
  execution identity, and Neo4j availability are directly validated;
- visual hash fallback to geometry hash is removed;
- real breadth/cheap/exact/law/parking/solver/render timings are required and
  zero/missing/non-finite values fail;
- archive/frontend preference now requires a passing target-20 publishable
  manifest with empty deficits, while legacy browsing is explicitly scoped as
  non-certified.

Fresh local verification: BOOK registry `120/120`, flow plus single execution
`79/79`, frontend focused `16/16`, TypeScript and backend compile checks all
passed. No live PNU or paid call was made. Next action is a fresh independent
re-review; only after approval may the one neighborhood target-20 acceptance
run begin.

Do not treat a boolean command flag or summary status as acceptance. The
publishable manifest must independently validate all 20 rows.

## Still not done

- Task 4 fresh code review and any fix rounds.
- Task 5 Steps 1-3 fresh code review and any fix rounds.
- One real PNU target-20 neighborhood execution.
- Runtime evidence; target first board is 120 seconds.
- Exact checks:
  `selected_count=20`,
  law/program/capacity/parking/hash `20/20`,
  capacity `5/5/5/5`,
  BaseVolume scopes each `3..4`,
  body phenotypes at least 5 and at most 4 each,
  roof/section at least 7 and at most 3 each,
  chassis at least 6 and at most 4 each,
  plan families at least 5 and at most 4 each,
  visible stepped `1..3`,
  void/courtyard at least 3,
  winged/curved combined at least 3,
  BOOK principles at least 10,
  certified-mesh distance contract pass.
- Direct PNG inspection.
- Copy accepted PNG to `docs/mass`.
- Load that exact run in `http://127.0.0.1:5178/design/language`.
- Verify 20 cards, no broken images or console errors, and no passport mismatch.

## Latest freshly generated visual evidence

A rejected 20-geometry compiler/render preview exists:

`docs/mass/fresh20-unitbox-book-preview-20260729-1250.png`

- 20/20 geometry-ready;
- 20 unique program hashes;
- 20 unique geometry hashes;
- two fresh seeds across ten family contracts;
- 0 paid image calls and 0 paid VLM calls;
- canonical UnitBox/BOOK/compiler/gate/render exercised;
- BaseVolume scope is `1/1` only;
- PNU, program, capacity, parking, floor-plan hash, six-scope quotas, and
  publishable audit are not complete.
- Status is `rejected_wrong_generation_path`; it bypassed architectural
  storey/GFA generation and must not be reused as MASS evidence.
- Independent board review rejected competition readiness because the two
  batches collapse into ten related A/B families; keep/reject evidence is in
  `docs/mass/fresh20-preview-20260729-1250/visual-review.md`.

Canonical evidence:
`docs/ai-session-memory/MAAS_FRESH20_VISUAL_PREVIEW_20260729_1250.md`.

## Immediate continuation sequence

1. Wait for Task 4 implementer report.
2. Run a fresh Task 4 reviewer against implementation, spec, tests, and report.
3. Fix every Critical/Important finding and re-review.
4. Wait for Task 5 Steps 1-3 report.
5. Run a separate fresh reviewer for publishable manifest and four-hash
   frontend binding.
6. Fix every Critical/Important finding and re-review.
7. Verify arbitrary-lawful-N floor/GFA termination and remove hidden catalog
   or program-profile floor ceilings from capacity authority.
8. Run the real PNU target-20 neighborhood command with Neo4j evidence and no
   per-card paid VLM.
9. If it fails or misses 120 seconds, persist phase timing and typed deficits;
   do not lower gates.
10. If it passes, inspect the 20-card PNG directly.
10. Copy it to `docs/mass`, load the same run in the frontend, and save browser
    evidence.
11. Update this document and
    `docs/ai-session-memory/maas-mass-flow/current-checkpoint.json` with exact
    command, duration, run directory, hashes, counts, PNG paths, and any
    remaining limitation.

## 2026-07-29 14:30 KST active floor/GFA correction

- Do not choose a catalog floor count before form generation. One resolved PNU
  produces a target-independent, complete legal-floor field; every candidate
  chooses its own minimum lawful prefix `N` from that same field.
- `N` is not restricted to 3/4/5 or to the neighborhood profile's historical
  2..8 preference. Focused candidate-context evidence currently covers
  3, 7, and 23 storeys from one shared legal field.
- Per-floor area at MASS stage is only a horizontal-section compliance
  measurement of the final 3D mesh. It is not room-layout or detailed floor
  plan design.
- The candidate must reach its selected GFA/FAR target through authored or
  form-preserving parameters. A generic post-hoc terminal-floor trim is
  forbidden because it would make unrelated alternatives read as stepped
  masses. Stepped/terraced terminal articulation is allowed only when authored
  by the typed architectural language.
- Phase A is in fix round 5. The producer and validator must require the
  original trusted `expected_legal_floor_field_hash`; a shortened field cannot
  authorize itself merely by being consistently rehashed. A legal field is
  complete only when it reaches the legal height count or carries a non-empty,
  exact allowlisted terminal exclusion reason.
- Phase A fix 5 is now independently `APPROVED`: Floor/GFA 45/45,
  target-10/smoke 14/14, clear-span 1/1, and a separate 12-case authority
  attack all pass. Phase B still must supply the expected hash from an
  independent PNU/run authority rather than rereading candidate data.
- Phase B1 is active in `candidate_generation.py`: candidate height, floor
  count, exact legal-section prefix, floor tops, targets, materialization,
  measurement, sunlight fit, and program metadata must all use the same
  candidate-specific `N`. It is not final acceptance yet.
- Phase B1 fresh review is `CHANGES REQUIRED`: a forged one-floor 40,000m2
  prefix could retain the hash string and become the materialization host, and
  the initial production expected hash was tautologically read from the same
  mutable contract. The active fix anchors the validated field/hash from the
  run's authoritative floor-capacity plan and independently verifies exact
  prefix sections, tops, caps, target sums, and minimum reachable `N`.
- Historical note above is now closed. Phase B1 fix 4 is independently
  `APPROVED`: the run anchor and exact prefix are enforced; authoritative
  runs cannot enter legacy fallback; base/candidate/sibling fields are
  deep-copy isolated; numeric aliases reject coercion and NaN/Inf before
  comparison; exact plain-container/GeoJSON validation blocks overloaded
  list/dict equality. Fresh suites pass 71/71 and 52/52, with 3/7/23 and
  clear-span 3/18m preserved.
- Phase B2A is active but not approved. Its first fresh review found three
  blockers: eight-decimal endpoint rounding could erase a 4e-9m legal escape,
  jointly edited candidate/semantic targets could override the capacity target
  aliases, and missing candidate floor context could fall back to global
  15m/5 floors.
- Source export is also in fix round 2. The first fix removed 2048-surface
  truncation and closed incomplete surface export, but review found a separate
  64-band truncation, silent missing-band success, small valid MultiPolygon
  part deletion, and missing proxy-volume payload identity. No accepted PNG
  may be produced until these are closed.
- Phase B2 remains blocked until Phase A and B1 receive fresh approval. It must
  remeasure the final mesh, issue `candidate_actual_gfa_stop_hash`, and bind
  both that hash and the shared `legal_floor_field_hash` through capacity,
  execution passport/archive, publish audit, elevation, and frontend evidence.
- Task 4 breadth scheduling is approved. Task 5 artifact measurement Part A is
  approved, but the whole publishable-20 contract is not approved until Phase
  B2 replaces the obsolete one-shared-candidate-floor-plan assumption.
- Two remaining semantic-handoff failures have been diagnosed as invalid
  positive fixtures under exact closed-band containment. Production semantic
  and containment gates must not be weakened; only the fixtures may be
  corrected, with their original geometries retained as explicit negatives.
- No new real PNU run, accepted PNG, paid per-card VLM, or frontend acceptance
  has occurred. The next visual board must come only from the reviewed
  six-scope PNU/program/capacity/parking/publishable command.

## Completion rule

No agent may say “MASS fixed,” “20 complete,” or “competition-ready” until the
real PNU board and frontend run satisfy every item above. If the run fails,
report the exact typed deficit and continue from the failing stage without
relaxing legal or diversity gates.

## 2026-07-29 17:49 KST verified real-PNU single MASS

- New bounded run:
  `docs/mass/mass-pnu1-verified-20260729-174913`.
- Runtime was 11.7 seconds. No paid VLM was requested.
- One real architectural MASS was freshly generated from the canonical
  UnitBox/Matrix4/BOOK path and the live PNU legal floor field.
- The accepted candidate is 3 floors / 10.5m with target GFA 232.625m2 and
  certified actual GFA 232.625001m2.
- Capacity target, downstream legal gate, Neo4j/law-search evidence, parking,
  and the combined hard gate are all true. Parking is 2 required / 2 provided
  by `piloti_ground`.
- The exact artifact now persists
  `geometry_artifact.floorwiseLegalMatrixStack.floors[*].matrix4` for all
  three floors and
  `geometry_artifact.projectedVisualMesh.triangles[*].vertices_m`
  (40 triangles / 120 vertices).
- Individual exact render:
  `docs/mass/mass-pnu1-verified-20260729-174913/mass-01.png`.
- This is only a target-1 diagnostic and therefore correctly remains
  `diagnostic_only`; it is not evidence that the competition target-20
  portfolio is complete.
- Fixed two summary-contract false negatives before this run:
  an optional law display-status field no longer overrides boolean legal
  evidence, and a rounded square-metre capacity target is compared in its
  authoritative area unit rather than against an unrounded ratio.
- Next action: run `--publishable-20` without live VLM, enforce exactly 20
  distinct candidates and diversity caps, then inspect the final board.

## 2026-07-29 18:29 KST target-20 scheduler/materializer checkpoint

- Fresh no-VLM publishable run:
  `docs/mass/mass-pnu20-publishable-20260729-182713`.
- It terminated normally at the fail-closed portfolio contract in 114.7s,
  after all 7 replenishment cycles. The pool improved from the previous
  single surviving candidate to 8, but exact-20 selection correctly remained
  0 and the rendered board is an empty failure board, not acceptance evidence.
- All eight pool survivors were still `recursive:stepped`; this is not the
  requested diverse MASS portfolio.
- Candidate scheduling correction:
  cheap screening now visits every UnitBox/BaseVolume parent once before
  repeating BOOK mutations, and the exact stage consumes only the exact
  descriptor keys selected by the cheap stage. The temporary
  executable-core priority helper was removed.
- Code hygiene performed during this correction: removed the unused
  `_legacy_cheap_ast_bounds` implementation (185 lines) instead of continuing
  to append scheduling exceptions to `candidate_generation.py`.
- Competition-focused regression evidence: 39/39 tests pass.
- Immediate remaining failure is upstream of law/parking selection:
  non-stepped core forms fail floorwise legal materialization mainly at
  post-CSG tiny-edge/tiny-face replay and exact section reconciliation on the
  skewed PNU. Do not relax law, GFA, containment, hash, or diversity gates.
- A source-bridge-only TDD fix is active: tolerance-safe CSG normalization
  plus post-CSG exact GFA/containment and authored phenotype-retention hard
  gates. No paid VLM request has occurred.
- Process hygiene: the first retry left duplicate PID 5644 alive after a
  terminal timeout; it was explicitly terminated at 116.3 CPU seconds.
  Its output folder `mass-pnu20-publishable-20260729-182650` is preserved.

## 2026-07-29 18:39 KST balanced BOOK retry

- Fresh no-VLM run:
  `docs/mass/mass-pnu20-balanced-20260729-183645`.
- Runtime 113.3s, replenishment 7/7, pool 8, selected 0. The result still
  fails closed and its empty board is not acceptance evidence.
- Cheap budget is now divided evenly by parent count: page 0 gives each
  UnitBox/BaseVolume two BOOK witnesses and later 64-parent pages give three.
  Cheap-selected descriptor keys are the only keys admitted to exact work.
  Competition-focused tests pass 40/40.
- The target-20 solver now consumes the contract minimum pair distance 0.14
  instead of the generic 0.10 default. The prior
  `solver.compatibility_threshold_mismatch` deficit disappeared.
- Supply did not improve beyond 8, and the visible pool still collapses to
  stepped duplicates. Scheduler expansion is therefore paused.
- Direct real-PNU 21-program evidence is in
  `docs/mass/subagent-floorwise-direct21`: only bar+spatial-reserve passes.
  Cross/grid spatial-reserve candidates reach replay but fail tiny-edge/
  tiny-face; void/wing candidates cannot retain phenotype and exact target
  under the current floor-prism projection.
- Active split:
  one agent is isolating the replay sliver without gate relaxation; another
  is reviewing the existing authored indexed-visual-mesh/loft path so legal
  floor volumes can remain the compliance authority without every visible
  MASS becoming a stepped prism stack.

## 2026-07-29 19:30 KST section-loft and code-organization checkpoint

- Do not expand the scheduler further. The latest real-PNU target-20 failure
  is no longer a parent/BOOK scheduling shortage: all core families reached
  exact work, while the final eight survivors still collapsed to stepped
  floor prisms.
- `candidate_generation.py` is already oversized in the shared dirty
  worktree (`git diff --numstat`: +2738/-250 as of this checkpoint). This is
  accumulated work, not a justification for further appending. The obsolete
  `_legacy_cheap_ast_bounds` block was removed, the temporary priority helper
  was removed, and the new CSG-to-visual-mesh work lives in the separate
  `geometry_language/floorwise_section_loft.py` module.
- Root cause confirmed: compliance-authority `occupied` floor polygons were
  produced after Matrix4 and legal CSG, but visual projection previously saw
  only the pre-CSG Matrix4. CSG designs therefore fell back to a terminal
  floor-prism replay and appeared stepped.
- Task 6 now has an exact occupied-section loft implementation. On the
  bounded real-PNU probe, `lofted_envelope` newly passed materialization,
  visual projection, clean-mass, and containment; it then failed only the
  `site_coverage` program gate.
- The site-coverage failure was a measurement-context bug: final floorwise
  candidates used the XY union of every height band, so shifted upper floors
  could report coverage 1.0. Task 6B changes only final floorwise authority
  to use the lowest occupied band for the hard gate, preserves the all-height
  ratio as advisory evidence, and leaves thresholds/ranges unchanged.
- Task 6B focused/neighbor tests are 4/4 green plus py_compile/diff-check.
  Its full program-massing module exceeded 184 seconds and was terminated;
  no full-suite pass is claimed. Independent review is active.
- Task 6 remains unaccepted until the reviewer findings are fixed:
  exact visual-hash mode must reject small vertex tampering, all
  plan/matrix/capacity/authority bindings must be recomputed at consumption,
  the stepped fallback must carry the same bindings, and missing/mismatched
  evidence plus multipart/hole cases must fail closed. The original
  implementer is performing this narrow TDD fix.
- No paid VLM was used. Do not start target-20 yet. Next gate is one fresh,
  single-process, real-PNU target-3 run proving at least one non-stepped form
  passes geometry, containment, program, law, capacity, and parking. Only
  then run exact target-20 and export individual PNG/JSON.

## 2026-07-29 19:45 KST independent review checkpoint

- Task 6B ground-band site coverage is independently APPROVED after a test
  fix. The fixtures now distinguish legal-ground host 100, benchmark 200,
  and all-height union 300, and separately prove benchmark fallback when the
  legal-floor-area evidence is unavailable. Final-floorwise uses legal
  ground first; ordinary candidates retain the historical all-height union.
- Task 6 exact authority fix1 passed its six focused tests but the fresh
  reviewer found two remaining fail-open cases:
  1. overlapping capacity plates in one band can union to the occupied
     polygon while their individually summed GFA doubles;
  2. certification mode/visible operation/fallback identity is not yet bound,
     so a loft can be relabeled as a prism.
- Task 6 fix2 is active and limited to those two findings. Do not run live
  PNU until a fresh re-review accepts both.
- `candidate_generation.py` organization audit:
  current size is 4,598 lines / 203 KB. The first safe extraction after the
  target-3/target-20 baseline is the roughly 1,050-line breadth cheap-screen
  cluster. Floor authority (~550 lines), seed authorship (~600), and directed
  materialization (~485) follow later. Do not move the ~1,600-line
  `_program_pool` exact/legal/capacity/QD transaction core before the live
  baseline. Two production-dead helpers were identified:
  `_eligible_smoke_floor_candidate` and
  `_capacity_retry_result_is_selectable`.
- Audit document:
  `.superpowers/sdd/2026-07-29-competition-grade-20-mass-portfolio/candidate-generation-modularization-audit.md`.

## 2026-07-29 20:00 KST target-3 and allocation instrumentation

- Task 6 C2/I1/I2/I3 fixes are independently APPROVED after three adversarial
  rounds. Exact `1e-9` surface tampering, component/combined hash tampering,
  missing/incomplete Matrix4 or plan evidence, overlapping capacity-plate
  GFA inflation, loft/prism relabeling, and unknown-mode downgrade all fail
  closed. The final combined focused run is 11/11 green, including Task 6B.
- Fresh real-PNU target-3:
  `docs/mass/mass-pnu3-section-loft-verified-20260729-194600`.
  It completed in 38.3 seconds but selected 0/3, so it is failure evidence,
  not an accepted MASS board.
- Initial supply: 36 evaluated, 2 compiled/clean, one bar full hard-pass.
  `lofted_envelope` passes materialization, visual projection, clean closed
  mass, and containment; its only failure is `site_coverage`.
- Selection universe remained one, so exact-3 plus three distinct body and
  body/roof signatures is proven infeasible with maximum cardinality one.
- Runtime-only instrumentation (no production mutation) disproved the earlier
  timing hypothesis:
  - both source and bridge geometry authority are
    `final_floorwise_legal_geometry_program`;
  - `coverage_measurement_mode=lowest_occupied_floor_band`;
  - ground numerator `102.931`, legal-host denominator `102.931`, ratio `1.0`.
  The measurement fix works; the ground floor really fills the whole host.
- Exact floor allocation diagnosis for that loft:
  - planned `[85.256, 85.256, 62.113]`;
  - legal caps `[102.931, 102.931, 74.989]`;
  - authored ratios `[1.0, 0.7673, 0.6525]`;
  - current allocated `[102.931, 80.0808, 49.6133]`;
  - total remains `232.625`;
  - explicit target plan coverage `0.7`.
- Direct cause: `_allocate_profiled_floor_targets` multiplies the already
  proportional capacity vector by the authored vertical profile and
  water-fills against full legal caps, consuming all ground reserve.
- Task 6D is active in `geometry_language/source_bridge.py`, not candidate
  generation: preserve the ground design cap
  `min(legal0, max(planned0, legal0 * target_plan_coverage))`, retain authored
  redistribution on upper floors, keep exact total GFA, and fail closed when
  bounded caps cannot carry the total. Do not encode or relax the program
  0.92 boundary.

## 2026-07-29 16:15 KST real-PNU runtime diagnosis

- Full target-20 command started in
  `docs/mass/fresh-pnu20-20260729-160958` with PID 54588.
- It was terminated deliberately after 140.3 seconds and 157.4 CPU seconds.
  At termination it was still `replenishment` cycle 4/7 with
  `selection_pool_count=0`, `selected_mass_count=0`, and no final PNG.
  Logs and `maas-run-state.json` were preserved.
- The bounded same-PNU diagnostic in
  `docs/mass/diag-pnu1-20260729-161459` completed in about 12 seconds with
  `evaluated_count=12`, `compiled_count=0`, `program_passed_count=0`,
  and `selected_mass_count=0`.
- All 12 recursive BOOK sequences compiled, but all 12 failed at
  `directed_geometry_materialization`; law, parking, selection, and final
  rendering never received a candidate. This rules out Neo4j/PNU law as the
  immediate zero-supply cause.
- The real legal section field is four occupiable floors with areas
  102.931, 102.931, 74.989, and 51.471 m2 and a target GFA of 299.089 m2.
  A single whole-program affine pose must fit the smallest upper section on
  every floor, so ordinary constant/profiled authored programs cannot reach
  the aggregate target. The only current non-affine fallback is restricted to
  `is_intentional_floorwise_stepped_program`, which conflicts with the required
  diverse non-stepped portfolio.
- Active root-cause boundary:
  `candidate_generation._materialize_directed_geometry` calls
  `select_legal_field_affine_projection`; general authored forms need a
  form-preserving floorwise legal-field placement/projection that keeps their
  indexed-mesh identity and exact band containment. Do not weaken law, GFA,
  containment, or hash gates, and do not turn all forms into terminal steps.
- No paid VLM call occurred. The diagnostic PNG is an empty failed-gate board
  and is not MASS acceptance evidence.

## 2026-07-29 21:05 KST exact loft hard-gate and modularization checkpoint

- Task 6D ground-reserve allocation and Task 6E bounded exact-ring compaction
  are independently approved. The allocation now preserves the intended
  ground design reserve while carrying the same exact total GFA; ring
  simplification is only accepted after validity, hole, area-delta, and
  symmetric-difference proofs within the existing `1e-6` tolerance.
- Fresh real-PNU target-3 evidence:
  `docs/mass/mass-pnu3-exact-compact-verified-20260729-205000`.
  It completed in 22.6 seconds (program duration 18.358 seconds), evaluated
  36 candidates, compiled/cleaned 2, and produced 2 full preselection
  candidates that pass program, legal, geometry, capacity, parking, and the
  combined gate. `lofted_envelope` now passes the full hard-gate path.
- Selection is still 0/3, so the PNG remains an empty failure board and must
  not be presented as accepted MASS output. The final pool has only 2
  candidates and both are reported as `recursive:stepped`; the target-3
  solver proves maximum achievable cardinality 1 under the one-stepped cap.
- Runtime instrumentation corrected the first interpretation: both survivors
  are actually certified as
  `floorwise_matrix_prism_exact_containment` with
  `visible_step_fallback=true`. Their measured step transitions are real, so
  the phenotype classifier and one-stepped cap must not be weakened.
- The pre-fallback certificate proves the exact failure. Both the
  `base_seed_bar` and `lofted_top_bottom_mass` candidates reach
  `floorwise_csg_section_loft` and fail with
  `section_loft_degenerate_profile`. Their bottom profiles are valid, simple,
  CCW, positive-area polygons with 16 and 21 unique boundary points, but
  `_ear_clip` returns `None`; each top cap triangulates successfully. The
  union of corner fractions across aligned floor rings inserts collinear
  boundary samples that the cap triangulator cannot finish.
- Task 6F must fix cap triangulation while retaining every boundary segment
  required by closed directed-edge topology. Naively deleting collinear
  vertices is invalid unless cap triangles are split to restore the exact
  side-boundary edges. Keep hole/multipart cases fail-closed.
- `candidate_generation.py` is frozen against further feature growth. It is
  currently 4,598 lines / 203 KB with a dirty delta of +2738/-250. New
  geometry or phenotype logic belongs in dedicated modules. After a stable
  target-3/target-20 baseline, extract the already-audited breadth
  cheap-screen cluster first; do not move `_program_pool` before that
  baseline. This is an incremental extraction policy, not an all-at-once
  rewrite.
- No paid VLM was used. Next gate: focused TDD for exact cap triangulation,
  fresh review, then one single-process real-PNU target-3.

## 2026-07-29 21:10 KST Task 6F approved and live target-3

- Task 6F exact cap triangulation is approved after one review fix round.
  The first implementation exposed a hidden zero-area terminal triangle.
  The final strict path validates the terminal cross and coverage, then tries
  deterministic full-index cyclic starts before the validated core/fan
  fallback. It never drops original cap boundary edges.
- Tests/review evidence: focused 16/16 green; two independent reviews
  approved; an independent 1,296-case subdivided-rectangle sweep reported
  `bad=0`, `none=0`; concave and shifted-profile regressions pass.
- Fresh real-PNU target-3:
  `docs/mass/mass-pnu3-cap-triangulation-verified-20260729-210500`.
  Wall time was 29.5 seconds and program duration 24.878 seconds. It still
  selected 0/3, so its PNG is failure evidence, not an accepted MASS board.
- The live result confirms the all-stepped collapse changed: the two final
  hard-pass candidates are now one `recursive:prismatic` and one
  `recursive:stepped`. The previous `visible_stepped:max_1` and
  `body_phenotype:stepped:max_1` deficits disappeared.
- Both candidates pass program, legal, geometry retention, capacity, parking,
  and the combined preselection hard gate. The remaining selection deficits
  are exact count 3, one incompatible silhouette pair, and fewer than three
  distinct body/body-roof signatures. Maximum achievable cardinality remains
  one because only two eligible candidates exist.
- Supply is now the active problem: initial generation evaluated 36 typed
  programs but only 2 directed geometries materialized; replenishment
  evaluated another 36 but materialized/compiled 0 and grew the selection
  pool by 0. Diagnose that boundary before any target-20 run.
- `candidate_generation.py` remains frozen; Task 6F changed only the separate
  geometry module and its focused tests. No paid VLM was used.

## 2026-07-29 21:40 KST exact-loft supply boundary and file-growth policy

- Low-overhead boundary instrumentation supersedes the earlier generic
  `directed_geometry_materialization_failed` diagnosis. Six candidates earn
  `floorwise_csg_section_loft` with `visible_step_fallback=false`, return a
  `SourceMass`, and match their allocated floor targets within roughly
  `1e-7`.
- One exact loft survives. Five certified exact lofts fail later, when
  `_materialize_directed_geometry` rebuilds the capacity volumes as a separate
  extruded-polygon execution replay. All five replay compilations are
  `compiled`, closed, manifold, and component-count one; the only gate issue is
  `tiny_edge`. Hash and semantic gates are not reached.
- The five recoverable authored routes are attached+branch, tower+carve,
  slab+branch, tower+branch, and slab+expand. Evidence:
  `docs/mass/mass-pnu3-post-source-trace-20260729-213500`.
- Fix boundary is `geometry_language/source_bridge.py` replay-ring transport,
  preferably through a small shared proof-bounded normalization module. Keep
  the `1e-5` geometry-gate threshold unchanged; preserve true corners, holes,
  bands, area, symmetric difference, containment, capacity authority, visual
  surfaces, Matrix4 evidence, and all authority hashes. Do not add the fix to
  `candidate_generation.py`.
- `candidate_generation.py` is 4,598 lines and its dirty diff is
  `+2738/-250`. The highlighted unique `+47` hunk is
  `_shared_floor_capacity_measurement`, a trusted floor-anchor/candidate-floor
  binding with fail-closed evidence. It belongs eventually in
  `candidate_floor_authority.py`, but moving only those 47 lines would split
  its signature and consumers. No new feature logic may be added there.
- Safe extraction order after a stable target-3/target-20 baseline:
  breadth cheap-screen cluster (~1,050 lines), floor authority (~550),
  seed/VLM authorship (~600), directed materialization (~485). Do not move the
  `_program_pool` transaction core (~1,600) before the baseline.
- No paid VLM was used. Next acceptance gate remains one fresh real-PNU
  target-3 with at least three materialized/combined hard-pass candidates and
  exactly three selected before any target-20 run.

## 2026-07-29 21:50 KST Task 6H approved; supply 2 to 4

- Task 6H added the dedicated
  `geometry_language/replay_ring_transport.py`; it did not add logic to
  `candidate_generation.py` and did not change the `1e-5` geometry-gate
  threshold.
- Two independent blocking reviews found and fixed: (1) a shallow inward
  breakpoint could expand outside the occupied polygon and depend on cyclic
  ring start; (2) a valid two-hole polygon could fail due to local-to-world
  floating-point roundtrip. The final transport canonicalizes ring/origin,
  accepts only an occupied-subset candidate, reconstructs and proves the actual
  payload in compiler-local coordinates, prefers proven 7-decimal transport,
  and otherwise uses a proven full-precision local fallback.
- Final independent checks: 15/15 combined Task 6F/6H tests green; a separate
  12-variant cyclic/reversed/hole-order probe produced one origin and one
  payload with validity, two holes, CCW exterior, and CW holes preserved.
- Fresh real-PNU target-3:
  `docs/mass/mass-pnu3-replay-transport-verified-20260729-214500`.
  Wall time 31.8 seconds; program duration 27.615 seconds; paid VLM count zero.
- Initial generation still supplied two combined hard-passes, but bounded
  replenishment supplied two more. The final hard-pass selection pool is four
  unique fingerprints and four distinct geometry hashes; all four pass
  capacity, legal, geometry-retention, parking, and combined gates.
- Selection remains 0/3, so both PNGs are still empty fail-closed summary
  images and are not MASS acceptance. The current pool has only measured body
  phenotypes `prismatic` and `stepped`; the competition target-3 contract
  requires three distinct body and body/roof signatures with maximum one of
  each. The solver therefore proves maximum selectable cardinality one.
- The active boundary moved from geometry materialization to measured
  morphology/selection supply. Diagnose whether the four distinct exact
  meshes are genuinely only two body types or whether final-mesh morphology
  descriptors are stale/incomplete. Do not weaken diversity caps and do not
  run target-20 yet.
- Runtime reproduction confirms the descriptor is not stale. Exact pairwise
  silhouette distances are `0.04265..0.15931`, all below the `0.16`
  compatibility threshold. Candidate facts are:
  - prism-fallback skew: stepped, sloped ratio 0, 40 triangles;
  - exact-loft lift: prismatic, sloped 0.1062, 290 triangles;
  - recovered exact-loft tower/carve: prismatic, sloped 0.1668, 360
    triangles, wedge-like but genus zero and no retained void;
  - recovered exact-loft tower/skew: stepped, sloped 0, 60 triangles.
- This is actual two-family/silhouette-collapsed supply, not a selector bug.
  The tower/carve candidate is the nearest honest third type but remains below
  the measured generic-oblique threshold 0.24 and has no surviving
  slice/clip intent. The next narrow target is a genuinely stronger oblique
  exact mesh (preferably recover an existing `agent_slice`/clip path), not
  phenotype relabeling or threshold relaxation.

## 2026-07-29 22:10 KST Task 6J oblique-loss boundary fixed

- The existing `agent_slice` programs do compile as authored UnitBox/BOOK
  solids. The first loss is not candidate generation: it is
  `materialize_floorwise_legal_source`.
- `project_floorwise_visual_mesh` applies the floor Matrix4 field but does not
  reapply the same legal CSG used by the capacity plates, so both traced slice
  meshes escape the irregular live-PNU section and fail closed.
- The following section-loft fallback uses occupied mid-floor sections and a
  generic horizontal cap; it does not use the authored terminal slice surface.
  The last prism replay also cannot be called oblique. This is why adding more
  slice seeds or repairing only `tiny_edge` would not create a third phenotype.
- Direct traces:
  - `0087797471ac...` bar + slice + BOOK taper 3/8: authored compile/gate pass,
    projection outside legal, exact loft topology incompatible, prism fallback
    `tiny_face`.
  - `c2bb537e47e2...` slab + slice + BOOK notch 1/1: authored compile/gate pass,
    projection outside legal, exact loft outside legal envelope, prism fallback
    `tiny_edge`.
- Approved repair boundary: a separate
  `geometry_language/floorwise_profiled_legal_clip.py` module must project the
  authored indexed mesh through the existing Matrix4 field, intersect it with
  the identical stacked legal solids, cap new cut boundaries, and revalidate
  the actual closed/manifold mesh. Capacity volumes, floor areas, lawful floor
  count, Matrix4 stack, and floor-capacity-plan hash remain unchanged; visual
  and authority hashes bind the resulting mesh. Ambiguous holes, multipart,
  non-manifold, containment, or tiny-feature cases fail closed.
- `candidate_generation.py` stays frozen; no classifier relabel and no
  silhouette/geometry threshold change. One focused RED/GREEN test and
  independent review precede exactly one fresh target-3 run. No target-20 and
  no paid VLM until target-3 produces three real individual MASS PNG/JSON
  artifacts.

## 2026-07-29 22:55 KST Task 6J implementation checkpoint; live witnesses still fail

- A dedicated `floorwise_profiled_legal_clip.py` now applies the existing
  continuous piecewise Matrix4 field to the complete authored indexed mesh,
  intersects it once with the canonical-winding stacked legal solids, and
  revalidates manifold/component/gate/midplane/containment evidence. The first
  per-band-constant prototype was rejected because it produced a false 60 m2
  seam terrace.
- Matrix arguments must exactly equal the stack matrices used by the authority
  hash. Holes/multipart/incomplete exports fail closed. Legal setback terraces
  use half-open band ownership. A piloti cut reaching the first floor-capacity
  sample is rejected rather than reusing a contradictory capacity hash.
- Canonical `shape_13_diagonal_slice` proof is green: 74 final triangles,
  physical-height sloped ratio 0.1974, actual retained diagonal plane,
  candidate-equivalent body phenotype `oblique`, no visible step. The exact
  certificate binds the authored program hash and retained slice-plane
  area/hash to the exact surface and four legal/capacity authorities. Replay
  overwrite passes; AST, bridge-hash, certificate, and surface tamper controls
  revert to prismatic/fail closed. A fully clipped-away slice-plane control is
  prismatic.
- Focused verification after these changes: 25/25 relevant section-loft,
  exact-authority, profiled-clip and visual-projection tests pass. The unrelated
  pre-existing direct visual-shift test remains 0.095238 below its existing
  0.10 silhouette expectation and was not weakened.
- The two persisted real-PNU slice witnesses are not yet recovered, so no full
  target-3 was run:
  - `008779...`: new clip reaches a closed/manifold/single-component mesh but
    the unchanged gate reports `tiny_face`; fallback is prismatic, sloped
    0.1669.
  - `c2bb...`: new clip fails exact midplane matching; fallback is prismatic,
    sloped 0.1636.
  Both still match GFA 299.09 m2 and the four legal floor targets.
- Independent review also rejected an over-broad first lineage matcher because
  it treated every authored sloped face as the terminal slice plane. The next
  fix must identify only the terminal root slice plane from the compiled AST
  and its stored host-fit Matrix4. Separately, kernel simplification may remove
  the 008 numerical sliver only if the unchanged gate, exact midplanes,
  containment, lineage and hashes all re-pass. Do not delete faces or relax
  thresholds.

## 2026-07-29 23:08 KST Task 6J contract simplification and module freeze

- `candidate_generation.py` is frozen at 4,598 lines / 203,045 bytes,
  filesystem mtime `18:34:50`, SHA-256
  `23A801303E37135BD69444EE02D2E2AAA9046707B36F403556CF7EFBBB266675`.
  No Task 6J geometry feature logic was added there.
- The highlighted `+47` belongs to one 587-line floor-authority transaction:
  `_capacity_pack_retry_eligible`, `_capacity_retry_required`,
  `_shared_floor_capacity_measurement`, `_candidate_floor_context`, and
  `_compact_candidate_capacity_evidence`. It must later move atomically to
  `candidate_floor_authority.py`, not be peeled out alone.
- The complete extraction map is
  `.superpowers/sdd/2026-07-29-competition-grade-20-mass-portfolio/candidate-generation-extraction-map.md`.
  After a stable target-3/target-20 hash baseline, four leaf clusters can
  reduce the file by roughly 2,580-2,685 lines while `_program_pool` remains
  the orchestration transaction.
- Independent adversarial review proved that AST bypass/plane matching
  over-attributed downstream taper side walls to a slice. That causal-slice
  contract was rejected and its dead helper code is being removed.
- Replacement contract: certify the current final exact profiled mesh's
  physical non-axis sloped subset, not an inferred operator label. The
  producer and classifier share one measurement/hash helper. Its evidence is
  bound to effective physical height, exact surface payload, authored program
  and bridge hashes, section profile, capacity volumes, floor-capacity plan,
  and Matrix4 stack. The classifier does not inject `slice`; it may use the
  verified exact sloped mesh only as the prior for the existing measured
  oblique gate.
- Legal stacked-prism CSG creates only horizontal or vertical new faces, so a
  surviving non-axis final face is actual visible profiled/Matrix-field
  geometry. A fully clipped-away sloped body remains prismatic; a surviving
  taper or cut may honestly be oblique without pretending its face came from a
  particular slice node.
- Numeric recovery remains separate. Validation-only Shapely snapping was
  rejected because it did not change the hashed emitted mesh. Any 008/c2bb
  cleanup must alter the actual deterministic manifold, then re-run the
  unchanged mesh gate, raw midplane `1e-6` comparison, containment, and hashes.
- No target-3 or paid VLM call is allowed until at least one persisted real-PNU
  witness passes the new exact mode and candidate-equivalent morphology as a
  genuine oblique body.

## 2026-07-30 00:10 KST Task 6J geometry green; live seed supply is now the blocker

- `candidate_generation.py` is now 4,605 lines / 203,279 bytes. The only
  post-freeze production change is a seven-line orchestration bridge that
  copies the already-validated `candidate_floor_context` into the freshly
  compiled authored source. No geometry repair was added to this file.
- Exact profiled legal clipping and numeric repair live in focused modules:
  `floorwise_profiled_legal_clip.py`, `profiled_mesh_numeric_repair.py`, and
  `capacity_replay_numeric_transport.py`.
- The actual 3-floor c2bb/notch witness now passes deterministic full
  `_materialize_directed_geometry`: 152 visual surfaces, three capacity
  volumes, GFA 265.858 m2, certified `floorwise_profiled_legal_clip`, and an
  oblique measured body.
- The profiled mesh repair is physical-unit bounded: raw failure is only
  `tiny_edge`, selected threshold is 5e-7 m, maximum displacement is
  3.63578e-7 m, and all three floor-center section proofs pass.
- The capacity replay has a separate hash-bound execution contract. Its raw
  120-triangle stacked-floor CSG has one 9.999999939e-9 m same-Z seam edge.
  The transport collapses only that proven seam at the first 1e-8 m threshold,
  produces 61 vertices / 118 triangles, passes the unchanged geometry gate,
  and certifies all three floor-center sections against the authoritative
  capacity polygons. Visual geometry is not substituted for the capacity
  graph. The rejected global decimal-7 rounding path was completely removed.
- Verification: seven shared-floor/hash/oblique tests pass; the dedicated
  capacity replay transport tests pass 2/2 from `ARR/backend`. The dedicated
  fixture path was made independent of the current working directory.
- Fresh live run
  `docs/mass/mass-pnu3-finalcheck-20260730-000930` still selects 0/3, but this
  is no longer the c2bb geometry failure. The live scheduler never supplies
  c2bb: all 78 observations use `program_neighborhood_active_bar`; six
  hard-gate-eligible survivors are all prismatic, so the exact-three diversity
  solver proves maximum cardinality one. The next task is seed scheduling:
  supply oblique, stepped, and prismatic anchors before variant expansion,
  preferably outside `candidate_generation.py`.
- No paid VLM request was made. The generated 0/3 PNG is a fail-closed empty
  diagnostic board and is not MASS acceptance.

## 2026-07-30 01:15 KST Candidate-generation extraction and target-3 reserve diagnosis

- Unbounded growth in `candidate_generation.py` is no longer allowed.
  The complete competition breadth/cheap-screen cluster (11 helpers) moved
  verbatim to `competition_candidate_screen.py`. The old module directly
  re-exports the same function objects for compatibility.
- `candidate_generation.py` changed from 4,515 to 3,467 physical lines,
  a net reduction of 1,048 lines. Verification: extraction parity 1/1,
  existing competition regressions 40/40, diagnostic cap/capacity scheduling
  2/2, `py_compile`, and `git diff --check` passed. Two wider pre-existing
  R9 materialization failures remain outside this extraction; no full-suite
  green claim is made.
- The bounded real-PNU 4F/high-yield typed probe evaluated 28 exact recipes.
  Only three stepped-family candidates materialized, and their mutual
  silhouette distances were 0.003865533 to 0.016914531. This is genuine
  collapse, not a stale-cache or selector artifact.
- The failed courtyard/void/cross programs compile as valid single-component
  authored solids. Their first useful loss is the floorwise legal fit:
  fixed-pose Matrix4 + typed legal CSG can achieve only about 83/81/54 m2
  respectively against a 92.638 m2 per-floor high-yield target. The exact
  area gate correctly rejects the underfill instead of filling authored voids.
- This PNU has four usable lawful floor sections only (tops 3.5, 7.0, 10.5,
  14.0 m). The fifth floor and above fail `insufficient_clear_floor_depth`;
  forcing a fifth floor is forbidden.
- Root cause: `capacity_alternatives._apply_candidate_floor_prefix` collapses
  the law-derived four-floor design-reserve stack to the minimum legal
  three-floor prefix for the `spatial_reserve` target before authored
  morphology is fitted. `_candidate_floor_context` then enforces that
  legal-only minimum. The post-fit shortfall has no authority feedback.
- A diagnostic four-floor spatial-reserve distribution totaling 232.625 m2
  recovered an exact three-way geometry/materialization witness:
  prismatic vs oblique 0.211571503, prismatic vs stepped 0.240466064,
  oblique vs stepped 0.173582034. All exceed the unchanged 0.16 threshold.
  The typed stepped witness is `agent_stepped_mass` plus
  `book:operative:expand`, canonical master-lattice variant 7, short axis.
- This witness is diagnostic, not accepted MASS: its temporary diagnostic
  capacity hash is not a Neo4j/law-agent-issued product passport and no PNG
  is published as acceptance. The production fix must preserve the lawful
  four-floor spatial-reserve authority, bind it to the real plan/legal hashes,
  then run exact target-3 and render three individual PNG/JSON artifacts.
- Next structural step is already active: move the complete 587-line floor
  authority transaction to `candidate_floor_authority.py` before changing
  the spatial-reserve contract. No new feature branch belongs in
  `candidate_generation.py`.

## 2026-07-30 02:15 KST target-3 final-mesh checkpoint

- `candidate_generation.py` is no longer growing without extraction. It is
  now 2,911 lines versus the 4,515-line baseline, a net reduction of 1,604
  lines. The breadth screen, floor authority transaction, and diagnostic
  anchor schedule live in `competition_candidate_screen.py`,
  `candidate_floor_authority.py`, and `diagnostic_anchor_scheduler.py`.
- Fresh real-PNU diagnostic:
  `docs/mass/mass-pnu3-final-verified-20260730-021046`.
  It selected and rendered three real candidates. All three pass the
  downstream law graph, parking, semantic projection, final mesh containment,
  and actual-GFA stop gates. No paid VLM request was made.
- The final board is
  `maas-book-neighborhood-3-smoke.png`. Direct review rejects it as a
  diversity acceptance: cards 1 and 3 still read as stepped relatives.
- The certified final-mesh pair distances are 0.11294129, 0.14510441, and
  0.10370896. Only one of three pairs passes its final requirement. The
  selected classifier labels oblique/prismatic/stepped, but authoritative
  certified body morphology is prismatic/prismatic/stepped.
- Root cause is an authority-order bug, not insufficient generator functions.
  Initial and replenishment selection use `_silhouette_distance`; authoritative
  certification later uses `competition_gestalt_distance`, then records the
  failed pair audit without reselection. The final certificate also hardcodes
  0.22/0.14 while target-3 selection uses the contract's 0.16.
- Required next change is outside `candidate_generation.py`: certify the
  bounded hard-pass pool, derive certified morphology and gestalt keys, and
  rerun the selector with one shared contract-owned pair-distance policy.
  Do not add another anchor branch before fixing selection/certification
  authority parity.
- Numeric finalization fixes are bounded and regression-tested:
  nanometre-deep legal overlay requires both area and mean-depth limits;
  actual-GFA mesh overlay tolerance is capped at 0.00001 m2 and 0.00002 m2
  remains fail-closed. The final-mesh plus actual-GFA suites pass 55/55.
- Neo4j mirror was disabled in this run. Portable law-graph evidence was
  materialized and hard-passed, so this run must not be reported as a live
  Neo4j-backed execution.

## 2026-07-30 02:26 KST selection-authority correction

- Initial and replenishment selection now use the same
  `competition_gestalt_distance` formula through
  `portfolio_selection.build_gestalt_compatibility_analysis`. No change was
  made to `candidate_generation.py`.
- Fresh real-PNU check:
  `docs/mass/mass-pnu3-gestalt-select-20260730-021920`.
  The six-candidate hard-pass pool now correctly produces 0/3 instead of the
  visually misleading three-card board. The exact solver evaluated all 15
  unordered pairs and proved maximum achievable cardinality two at the
  unchanged 0.16 threshold.
- A bounded `1/2 + split_wing + BOOK offset` diagnostic probe was tested in
  `docs/mass/mass-pnu3-winged-probe-20260730-022304`. It did not add a
  hard-pass winged survivor and cardinality remained two. The experimental
  fourth anchor and its test changes were removed; ineffective generator
  branches were not retained.
- Current truth: three individually lawful/GFA/parking-passing meshes exist,
  but they are not an acceptable diverse trio. The selector no longer hides
  that fact.
- Next architectural seam remains final-mesh authority ordering: certify a
  bounded hard-pass shortlist before the solver, derive morphology and gestalt
  from those exact artifacts, then select. In parallel, the third survivor
  must be a real non-wedge/non-step architectural form that survives the
  unchanged parking and legal gates, not another label over a similar mesh.

## 2026-07-30 11:30 KST creative authored 100 choice-pool checkpoint

- The immediate product was changed from another max-capacity target-3/20 loop
  to a bounded **pre-legal authored choice pool of 100 MASS candidates**.
  This is the pool a user or architect will later choose from in the frontend
  graph; it is not a law-approved final portfolio.
- Production run:
  `docs/mass/maas-creative-100-authored-book-floors-20260730-1130`.
  The overview board is `maas-creative-board.png`; 100 individual four-view
  PNGs are under `renders/`, and 100 full candidate JSON files are under
  `candidates/`.
- The portfolio has ten measured families with exactly ten candidates each:
  bent, carved_void, courtyard, cross, grid, inflated, notch, radial,
  split_wing, and stepped. Stepped is therefore capped at 10/100 rather than
  dominating the pool.
- Capacity is not maximum-only. `spatial_reserve`, `balanced_yield`,
  `brief_target`, and `maximum_target` each have 25 candidates, and every
  family contains all four bands. The 332.322 m2 ceiling is explicitly
  `user_supplied_prelegal_target`, not a law-agent feasibility claim.
- All 100 candidates have unique program hashes, final geometry hashes, and
  scale-invariant authored mesh hashes. All 100 compiled as one connected,
  watertight, manifold solid.
- The executable lineage is real, not a label:
  one canonical UnitBox authority, a derived Matrix4 scope, active BOOK
  projection with one of `1/1, 1/2, 3/8, 1/4, 1/8, 1/16`, a physical Matrix4,
  and 3-6 explicit occupied-floor-plate intersection nodes derived from
  UnitBox Matrix4 cutters. Compiler-trace positive volumes bind the typed
  contact witness and each floor plate.
- Storey distribution is 3F:24, 4F:27, 5F:25, 6F:24. These are authored
  pre-legal horizontal-section/storey contracts with
  `legal_certified=false`; Neo4j/law/parking have not approved them.
- No paid VLM request was made. `paid_vlm_request_count=0`, and every legal
  review status is `not_evaluated`.
- Focused verification:
  `python manage.py test design.test_maas_creative_floor_portfolio
  design.test_maas_creative_floor_portfolio_command -v 2` passed 12/12.
  Artifact verification found 100 candidate JSON, 100 render PNG, 100
  passport sidecars, BOOK active 100/100, explicit plate counts 3-6, and
  connected/watertight/manifold 100/100.
- Root cause of the earlier step/prism collapse is now recorded precisely:
  nonuniform legal fields routed every survivor through floorwise replay and
  the final renderer mesh was rebuilt by `floorwise_profiled_legal_clip`.
  The single-ring topology gate also structurally disadvantaged holes and
  split-wing sections. The law itself did not require visible steps.
- Frontend limitation: arbitrary `docs/mass` portfolio JSON is not currently
  discovered by `ExecutedMassManifest`; the rail is capped at 24 and compact
  outcome attributes drop capacity/storey/legal facets. The portable
  creative graph is emitted, but live 100-card selection still needs an
  archive adapter, pagination/virtualization, facet pass-through, and honest
  pre-legal pending passport semantics.
- Implementation plan:
  `docs/superpowers/plans/2026-07-30-creative-authored-100-mass-preview.md`.
  The next legal task is relation-late projection:
  legal floor Matrix4 first, then typed courtyard/split/slice relation and
  post-CSG GFA/containment certification. Generic floorwise prism replay is
  forbidden for non-stepped authorship; preservation failure rejects rather
  than silently rewriting the design.
## 2026-07-30 12:04 KST — strict UnitBox diverse-100 implementation plan

### User-approved direction

- Maintain one canonical `1/1 UnitBox` authority.
- Treat Matrix4 as the affine coordinate/placement layer.
- Treat clipping, circularization, lofting, CSG, arrays, and bridges as typed
  architectural language that consumes UnitBox-derived solids.
- Preserve module maintainability; do not append creative-family logic to the
  already oversized `book_language/candidate_generation.py`.
- Resolve triangular/faceted, oblique crystal, disc cluster, interlocking
  tilted-disc, and long-span alternatives in addition to the existing ten
  families.
- Keep stepped mass as one balanced alternative, not the universal survivor.

### Current truthful status

- The current 100-card artifact exists at
  `docs/mass/maas-creative-100-authored-book-floors-20260730-1130/`.
- It is a real 100-file choice pool, but it repeats ten hard-coded families and
  is not yet accepted as competition-grade diversity.
- The compiler already supports most required language. Strict UnitBox disc
  lineage still needs a topology-changing `circularize` modifier; independent
  tilted arrays need `matrix_array`; non-horizontal curved/oblique spans need a
  real 3D sweep.
- The ArchDaily corpus currently reports 13 collections, 313 unique items, and
  375 images.
- Image inputs provide per-request VLM context. The project will use retrieval,
  structured critique, and preference memory rather than pretending that a
  prompt permanently trains the model.
- Current design outcome Neo4j mirroring can use the same default database as
  law. The approved plan introduces fail-closed `MAAS_DESIGN_MEMORY_NEO4J_*`
  configuration so design writes cannot silently enter the law database.
- The frontend graph renderer has no inherent 24-node cap. The visible limit is
  `archive-selection-policy.ts` using a default recent-card limit of 24.
  Creative portfolio membership will be adapted separately so all 100 remain
  reachable while the recent execution timeline may retain 24.

### Canonical documents

- Design:
  `docs/superpowers/specs/2026-07-30-strict-unitbox-diverse-mass-design.md`
- Implementation:
  `docs/superpowers/plans/2026-07-30-strict-unitbox-diverse-mass-implementation.md`

### Execution order

1. Family contract and registry.
2. Strict UnitBox operators.
3. Fifteen isolated family recipes.
4. Scale-invariant morphology/topology diversity gate.
5. Law/design-memory Neo4j separation.
6. Reference/VLM/preference event truth.
7. Creative archive/API adapter.
8. Full 100 frontend rail and graph.
9. Real 100 generation, visual inspection, bounded VLM pilot, browser check.
10. Independent review, regression, and final memory checkpoint.

The implementation had not started at this checkpoint.

## 2026-07-30 13:54 KST strict UnitBox Tasks 1-4 recovery checkpoint

- The interrupted main session was recovered from Codex history and rollout
  logs. It had completed Tasks 1-3 and stopped during Task 4 morphology work.
- Tasks 1-3 are complete: one canonical UnitBox authority, strict Matrix4
  affine lineage, typed `circularize`, `matrix_array`, and
  `profile_sweep_3d`, plus 15 registered architectural families.
- The five new families are `triangular_shard`, `oblique_crystal`,
  `thin_disc_cluster`, `interlocking_tilted_discs`, and
  `long_span_bridge`. They are not separate primitive exceptions: every one
  starts from the canonical UnitBox and uses Matrix4 plus typed
  clip/circularize/array/CSG/bridge/sweep language.
- Task 4 first reproduced a strict 92 accepted / 8 rejected morphology audit.
  The cause was a 60-card context cycle combined with tightly clustered legacy
  source selection and low-amplitude triangular/grid/radial parameters.
- The correction did not lower thresholds and did not add runtime retry or
  index-only scale noise. It uses deterministic source spreading and material
  BaseVolume-derived clip, grid-spacing, radial-count, and radial-angle
  variation.
- Fresh focused verification passed 40/40. The 100-card in-memory portfolio
  now has 15 family quotas at 7/6, four capacity bands at 25 each, stepped 7,
  morphology 100 accepted / 0 rejected, and 100 unique program, geometry, and
  normalized authored-mesh hashes.
- Morphology thresholds remain global 0.015 and within-family 0.025. The fresh
  nearest-distance distribution is minimum 0.025169155285, median
  0.119277555862, and maximum 0.259384437771.
- No paid VLM request was made. No law, parking, or legal certification is
  claimed by this pre-legal choice pool.
- SDD ledger:
  `.superpowers/sdd/2026-07-30-strict-unitbox-diverse-mass-implementation/progress.md`.
- Next plan item: Task 5, fail-closed separation of design-memory Neo4j from
  the law database.

## 2026-07-30 14:03 KST Task 5 design-memory isolation checkpoint

- The pre-fix RED proved that `MAAS_OUTCOME_NEO4J=1` could instantiate and
  connect the same `graph_db.services.Neo4jService` used by law/default graph
  paths. The RED graph was empty, so no node or relationship was written.
- Design-memory writes now require all of:
  `MAAS_DESIGN_MEMORY_NEO4J_ENABLED`, `_URI`, `_USER`, `_PASSWORD`, and
  `_DATABASE`. No design write falls back to `NEO4J_*`.
- The law URI and database are read only for collision detection. Equal
  normalized URI+database disables mirroring with
  `reason=law_database_collision`.
- The adapter passes the design database explicitly to `Neo4jService` and
  emits only `MaasDesignNode` and `MAAS_DESIGN_RELATION`. The old
  `MaasGeometryOutcomeNode` / `MAAS_GEOMETRY_RELATION` write path is removed
  from `GeometryOutcomeGraph`.
- `GeometryOutcomeGraph.save()` remains portable JSON authority. Disabled,
  incomplete, collided, invalid-payload, unavailable-service, and query
  failures cannot block geometry diagnostics.
- Focused verification passed 12/12. Combined design-memory, law identity,
  and authored/projected identity verification passed 37/37 without a live
  Neo4j dependency.
- Next plan item: Task 6 reference/VLM/preference truth events. Paid VLM calls
  remain zero by default.

## 2026-07-30 14:17 KST Task 6 reference/VLM truth checkpoint

- Five immutable, schema-versioned event kinds now separate retrieval,
  submitted visual evidence, VLM judgement, typed edit proposals, and human
  pairwise choices.
- Strict truth-policy tests retrieve five and submit two; only the two
  submission events set `used_by_vlm=true`. Each submitted reference carries
  image identity, SHA-256, input order, response ID, program hash, and geometry
  hash.
- Pairwise JSONL records retain reviewer, session, reason, both candidate IDs,
  and both geometry hashes. Portable outcome graphs store event/reference
  metadata and never embed image bytes.
- Executed archives retain local/remote reference identity, digest, source URL,
  collection, rights, and provenance. Cached critic results are rebound to
  current response/program/geometry identities.
- The creative command adds explicit `--vlm-pilot`: one morphology medoid per
  family, maximum three references, low image detail, and maximum 15 paid
  requests. Default generation remains zero-cost.
- Mock-only verification passed 64/64, including the default creative command
  reporting `paid_vlm_request_count=0`. No live provider call was made.
- Next plan item: Task 7, complete 100-card archive persistence/API exposure.

## 2026-07-30 14:26 KST Task 7 creative archive/API checkpoint

- A dedicated `creative_portfolio_catalog` validates the stored AST, replayed
  program/geometry hashes, stored mesh hash, unique identity tuple, and
  run-confined artifact paths.
- The read-only `/design/maas/creative-portfolios/` endpoint does not coerce
  creative candidates into the executed-mass schema. Candidate PNGs are served
  only after selected-member validation under the configured `docs/mass` root.
- The 100-member persistence contract passed: 100 JSON, 100 PNG, one board, 15
  family facets, four capacity facets, morphology 100 accepted, legal
  `not_evaluated`, paid calls 0.
- Task 7/adjacent boundary verification passed 9/9. The broader
  single-execution suite still has seven pre-existing elevation certificate
  failures, independently reproduced as
  `elevationAgent final geometry identity mismatch`; Task 7 did not modify or
  overwrite those dirty-worktree changes.
- Next plan item: Task 8, show/filter all 100 candidates in the frontend.
