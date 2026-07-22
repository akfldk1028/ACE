# Open Validation Gaps

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

## P0 - full MAAS acceptance still awaits VLM

- The r199 one-MASS replay has evaluated site/capacity/law/parking/program,
  compiler/GATE/render and selector evidence, but VLM is `not_evaluated`.
- No paid VLM request was made during r199. This is intentional truthfulness,
  not a pass: `geometry_ready=true`, `full_flow_complete=false`, and
  `final_hard_pass=false`.
- A fresh paid call is permitted only for a requested new visual judgement
  after deterministic gates, using bounded candidates and exact image/prompt/
  model/program hash caching. Never fabricate VLM approval from retrieval.

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
