# Open Validation Gaps

## P0 - one full legal-to-competition-design transaction does not yet exist

- The declared agent order is `law -> parking -> LLM Architect -> MassDSL ->
  geometry -> grammar -> preference -> review`, but the public legal-variants
  runtime generates LLM candidates before candidate parking, attaches
  MassDSL/grammar evidence after selection and emits mostly post-hoc agent
  reviews.
- The BOOK portfolio has stronger PNU/capacity/program/downstream selection,
  while single execution has stronger immutable passport/VLM/elevation
  evidence. They are not composed as one request and identity.
- Add one orchestration contract that carries the same PNU, site, law sources,
  capacity alternative, parking strategy, LLM author evidence, typed program,
  authoritative floors and hashes through every generation and repair stage.
- Agent results must become the next agent's typed input. Rendering the same
  `AgentContext` through a review registry is evidence narration, not
  collaboration.
- The public legal-variants endpoint currently builds its envelope from
  caller-supplied constraints while carrying PNU separately for identity and
  later parking paths. Connect PNU -> cited law Graph DB evidence ->
  deterministic constraints -> envelope in the same fail-closed transaction.
- Reconcile the declared `grammar -> preference -> review` flow with
  `GrammarCriticAgent.next_agent=review_agent`; the executable handoff contract
  must have one unambiguous order.

## P0 - authoritative floor plates are split from GeometryProgram truth

- `legal_envelope.py` owns real per-floor legal plates. BOOK capacity currently
  samples SourceVolume intersections using requested floor context, while the
  compiler only proves mesh topology.
- A requested floor count, FAR proxy or bounding-box level count cannot prove
  an inhabitable building. This is the direct path by which ribs, radial
  sculptures and continuous solids can pass as "MASS."
- Define one floor schema consumed by capacity, program, parking, building
  legibility, selector and elevation. Each rendered floor datum must trace to
  one authoritative plate; elevation must not invent guides from height alone.
- Add hard checks for usable plate area/depth, plate continuity, support/core
  relation, access/egress reservation and floor-count agreement. Program-
  specific exceptions such as halls remain explicit.

## P0 - frontend must distinguish product acceptance from partial evidence

- r230 is a `PNU_UNRESOLVED` geometry/elevation fixture and its multi-view
  proposal is failed. r200 is a legacy exact archived-AST replay of r196
  MASS04, created before `execution_mode` and live-VLM-accepted under a
  pre-current collaboration contract. Neither is a complete competition-design
  proposal.
- Default selection needs an explicit product-acceptance predicate rather than
  using recency, `geometry_ready`, or historical `accepted + VLM` alone.
- If no product-complete run exists, show `NO FULL COMPETITION DESIGN ACCEPTED`
  and let the user inspect the best partial lane without implying finality.
- Clear passport, outcome and elevation state atomically on run changes. The
  selected old r200 sidebar currently has no matching card in the up-to-24-item
  newest deduplicated single-execution rail.
- Technical six-view extraction currently lacks the identity guard used by
  legacy and multi-view creative proposals. Selection swaps archive data before
  the later passport-clearing effect, and outcome state is not cleared
  immediately, so prior technical views/outcomes can appear transiently under
  a newly selected MASS.
- Timeline text says `CLICK TO REPLAY`, but clicking performs only GET
  selection. Actual replay is a separate POST action; relabel the timeline so
  evidence inspection is not confused with execution.

## P0 - render provenance is not sufficient for a default artifact

- The same program/geometry hash can render differently after renderer fixes.
  Preserve historical PNGs, but record renderer contract/version and do not use
  an obsolete render as the current visual-quality authority.
- A current-view regeneration must create new render evidence without mutating
  the historical execution identity or copying old VLM acceptance to new image
  bytes.

## P0 - fresh synthesis must not be confused with exact replay

- `source_run_id/source_mass_index` always means immutable exact AST replay.
  It may create new evidence and a new execution ID, but the geometry hash is
  expected to remain identical.
- New design claims require `execution_mode=fresh_synthesis`, a persisted
  synthesis request/variation seed, and a geometry hash different from the
  selected parent. Keep this as an admission gate when a request-time fresh
  generation endpoint is added.
- r222 proves the offline fresh synthesis + BOOK + compiler path, but the
  frontend currently exposes the replay action only. Add a separate
  `GENERATE NEW MASS` endpoint/button; never overload the replay action again.

## P0 - local UnitBox to parcel placement authority

- Never infer site fit from `pnu`, `inside_site` or a copied legacy site gate.
  They can describe the original SourceMass while the replayed GeometryProgram
  remains in local UnitBox coordinates.
- A replayed/generated single MASS is `site_bound` only with resolved PNU,
  exact parcel geometry and an evaluated 4x4 local-to-parcel placement matrix.
  Road/access geometry should use that same frame.
- r219 is intentionally `source_gate_only`; do not claim its new compiler
  render itself fits the parcel until the placement adapter exists.
- r219 has no legacy `capacityAlternative`. Recompute capacity from placed
  world geometry and current law; do not fabricate a pass from missing data.

## P0 - selected-MASS critic does not yet close the repair loop (r218c)

- The one-MASS endpoint now compiles, gates, renders, calls specialists,
  materializes six elevation views and records a bounded VLM judgement in one
  hash-bound passport.
- A VLM failure currently stops at `critic_actions`. It does not yet generate
  a typed repair AST, compile the child, require a new geometry hash, re-run
  gates and compare parent/child evidence inside the selected-MASS UI.
- The portfolio Author/Critic/Repair loop exists separately. Reuse its typed
  repair contract through a small adapter; do not copy portfolio search into
  request-time execution and do not mutate an immutable execution directory.

## P0 - repository-wide full test is still red (2026-07-24 r218c audit)

- Backend discovered 770 design tests and emitted multiple failures before the
  long-running audit was stopped. The current MASS-focused suite is 223/223.
- Frontend build completed and Vitest ran 415 tests: 71 failed, all in existing
  `ChatBox`, `SearchInput`, `Terminal` and `useInstallationSetup` suites. MASS
  focused tests remain green and TypeScript passes.
- This supersedes older counts but not the conclusion: do not claim an
  engineering full-test pass until the global owners repair those suites.

## P0 - repository-wide full test is red (2026-07-22 r199 audit)

- Backend full command `python manage.py test design --verbosity 1` executed
  742 tests and ended with 22 failures plus 2 errors. Current failures include
  BOOK-language visual selection/audit regressions (`surfaces` missing and an
  undefined `program`), stale outcome-graph/public-threshold expectations,
  multiple export/selection invariants, geometry-language projection counts,
  and mass-brain principle-count drift. The new single-MASS focused suite is
  green, but that does not make the repository suite green.
- Frontend `npm test` build completed, then Vitest executed 403 tests: 331
  passed, 71 failed, 1 pending. Failing files are existing global areas:
  `ChatBox.test.tsx`, `SearchInput.test.tsx`, `Terminal.test.tsx`, and
  `useInstallationSetup.test.ts`. The focused single-MASS UI/API tests pass 3/3
  and `npm run type-check` passes.
- Do not label the current branch "full tested" or "complete" until both full
  suites are green. Preserve this failure ledger across sessions; repair each
  owner module with isolated tests instead of weakening assertions globally.

## P0 - one MASS is accepted; portfolio and cost closure remain open

- r200 closes the exact single-MASS flow: deterministic/downstream stages and a
  bounded paid VLM all passed, so its hash-bound passport is genuinely accepted.
- This does not approve r196 as a portfolio; r196 remains 15/20 and its board
  diversity failures remain. Elevation may consume the accepted MASS hash, but
  approval-grade law and the elevation condition-pack adapter are still open.
- The r200 candidate call used 27,819 tokens despite only two reference images.
  Before scaling paid review, compact the causal prompt projection and add a
  token budget gate. Do not reduce evidence binding or increase image count.

## P0 — viable geometry supply

- r194 is 15/20. The maximum compatible set cannot reach 20 from current
  hard-pass supply without violating BOOK coverage or roof diversity.
- No triangular plan candidate reached final supply. Fix authoring/projection
  and deterministic geometry validity before adding a selector-only quota.
- Increase genuinely distinct courtyard, split bridge, bent/cross, terrace and
  carve-void programs. Parameter jitter on one box/bar chassis is not a family.
- Preserve Base-Model-relative dimensions and existing hard gates. Do not fix
  counts by absolute-coordinate recipes, per-candidate exceptions or relaxed
  law/parking/capacity thresholds.

## P0 — geometry proof

- The depth-buffer renderer removed false painter-order fragments, but selected
  MASSes still need deterministic manifold, self-intersection, degenerate-face,
  coplanar-Boolean and multi-view silhouette checks.
- Produce stable isometric, plan, section and street views per MASS. One board
  thumbnail is insufficient evidence for hidden connectivity or usable voids.
- Add rendered connected-component/noise metrics as supporting evidence while
  keeping exact indexed-mesh topology authoritative.

## P0 — VLM truth

- r194 has one paid board critic only; it has no individual reference-conditioned
  VLM evaluations. Graph fields correctly show 5 retrieved and 0 used.
- Keep board critic, individual reference critic and deterministic GATE as
  different node roles. Record submitted image hashes, response IDs, model,
  cache state and cost for every paid call.
- Do not spend hundreds of calls. Use bounded stage triggers after deterministic
  preflight and cache by image/prompt/model/program hash.
- r182 was not VLM reviewed; r184 spent 24 calls and produced no final MASS.

## P0 — legal and elevation authority

- Current site/legal/parking output is preflight only. Verify official ordinance
  source URL, article/appendix, effective date, exceptions and parsed-text hash.
- Road/building lines, district plan, fire access, evacuation, accessibility,
  landscaping, use restrictions and current parking rules remain incomplete.
- Implement and test GeometryProgram indexed mesh -> elevation condition pack.
  No facade/elevation result is final before an accepted MASS hash is frozen.
- Current single execution invokes elevation before collaboration/selector
  completion and supplies only compiled mesh. Move this behind an explicit
  accepted-MASS guard and pass the identity-matching floor/program/site/law/
  parking condition pack.

## P1 — runtime and modularity

- The one-MASS deploy path now runs an exact archived AST in about 38-41 ms and
  materializes source/program/passport/PNG/latency evidence. Content-hash cache
  reuse across different execution IDs is still open; do not add portfolio
  search to request-time execution.
- r195/r197 prove that even a bounded 600–840 MB worker cannot safely finish
  while workstation free memory fluctuates below 1 GB. Add a cooperative
  resource guard/checkpoint between generation pages and resume from saved
  page archives instead of restarting the whole run.
- Keep one public benchmark orchestrator, one AST/compiler and one graph. Put
  rendering, run state, VLM and selection mechanics in their owning modules.
- Run-local causal graphs are the default. Cross-run shared memory must be an
  explicit, bounded input and never an implicit 469 MB load.
