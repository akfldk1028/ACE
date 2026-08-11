# MASS verified state — 2026-08-10 (C175 / C176)

Agent-neutral. Codex and Claude both read this file first; it states only what
was measured, and it corrects earlier checkpoints that overclaimed.

## Straight answer: does it work?

**No — not yet.** Across every run to date, the number of masses passing the
combined hard gate is **zero**.

| Run | selected | `combined_hard_pass` | finalization hard gate |
|---|---|---|---|
| C173 | 3 | **False × 3** | False × 3 |
| C174 | 2 | **False × 2** | False × 2 |
| C175 / C176 | 16 | **False × 16** | False × 9, True × 7 |

The board title "16/20 floor-verified masses" and the card label
"SELECTED/WARN · program hard pass, clean mass pass" mean the floor and program
gates passed. They are **not** combined acceptance. Canonical publishable
remains **0/20**, and VLM is **not evaluated**.

## THE ACTUAL BLOCKER — found 2026-08-11, read before anything else

`combined_hard_pass = 0` is **not** a geometry, capacity or law-calculation
failure. Every real gate passes on all 16 selected candidates:

```
legal_projection               16/16 True
capacity_hard_gate             16/16 True
parking_hard_gate              16/16 True
semantic_projection_hard_gate  16/16 True
law_graph_evidence_hard_pass    0/16 False   <- this is what blocks it
```

The law-graph failures are all environmental:

```
law_agent_neo4j_unavailable
law_agent_search_unavailable
law_agent_article_ids_missing
law_agent_status_not_passed:needs_evidence
```

**Neo4j was not running.** Ports 7687 and 7474 both refused connections during
every run in this session. `.env` already carries `NEO4J_URI`, `NEO4J_USERNAME`,
`NEO4J_PASSWORD`, `NEO4J_DATABASE`; the service simply was not up. Memory
already records that Neo4j is local-only with no deployed instance.

So a whole session was spent on geometry, supply and ordering while the thing
holding the gate shut was a stopped database. **Check per-gate status first:**

```python
for key in ("legal_projection", "capacity_hard_gate", "parking_hard_gate",
            "semantic_projection_hard_gate"):
    ...  # plus row["law_graph_evidence_hard_pass"]
```

### The second blocker, once Neo4j is up

7 of 16 already pass finalization. The other 9 fail
`final_mesh_capacity_below_minimum` by **0.9%–3.6%**: achieved utilization
0.564–0.591 against a required 0.600, which is `feasible_minimum_utilization`.

That 0.6 is **not statutory**. FAR is a ceiling, not a floor; building less is
always lawful. This project's own recorded contract says so —
*"maximum legal capacity is not a statutory minimum"* — yet
`certify_final_mesh_actual_gfa_stop` raises a hard `FinalMeshFloorEvidenceError`
on underfill. The document and the code contradict each other. Making underfill
advisory (keeping every legal maximum hard) is what unblocks the remaining 9.

## What did improve, measured

- Visible-mesh producer: `legal_section_loft` 2/3 (C173) → **1/16** (C175).
- Geometry validity: **16/16** closed, single-component manifolds. Every
  undirected edge shared by exactly 2 triangles, every directed half-edge once,
  positive volume. 3 candidates are genus 1/1/2 and their `solid_genus`
  metadata matches the mesh.
- `selected_scope_count` 6/6 (was 4/6 in r318, 0 in r183).
- Finalization hard-pass count 0 → 7 of 16.

## What did not improve

Diversity is **label-only**. Metadata shows 16 distinct `design_concept`, 8
chassis families, 16 distinct visual hashes — the geometry does not carry it:

- 28³ voxel IoU over 120 pairs, each mesh normalized to its own bbox:
  min 0.365, **median 0.637**, max 0.867. 76/120 pairs ≥ 0.60.
- Every footprint is near-square (aspect 1.00–1.43) on the same ~12×12 m plan.
- Height takes two values (10.5 m ×6, 14.0 m ×9) plus one 12.82 m.
- **11 of 16 share one sloped-face normal** ≈ (±0.40, ∓0.74, ±0.53), i.e. the
  same north-sunlight cut, covering 25–63% of each mesh's sloped area.
- Direct board review: **12/16 read as "block cut by a sloped plane"**. Only 4
  are a different type (fin cluster, twin bars with a slot, one real courtyard,
  and one jagged loft artifact). Zero tower / podium+tower / bridge.
- The pipeline agrees with itself: `near_duplicate_pair_count = 5`, and 16
  further candidates were rejected `silhouette_near_duplicate`.

Fair caveat: 264 m² site, 3–4 storeys, 10.5–14 m. Tower, podium+tower and
bridge are physically unavailable here. Part of the narrowness is the site.

## Corrections to earlier memory — do not trust the old text

1. `08_C173_THREE_LANGUAGE_CHECKPOINT.md` says *"All three selected records
   pass geometry, law, capacity, parking, program, and selection stages."*
   **Wrong.** All three are `combined_hard_pass=False`; two fail
   `invalid_final_mesh_authority`.
2. The same file's GFA table (199.392 / 201.140 / 229.574) lists **target**
   values, not achieved. C173's two loft candidates report
   `achieved_gfa_m2 = 0.0`.
3. The 2026-08-10 handoff line — *"final visible authority가
   authored-continuous인지 legal floorwise loft인지 구분해 확인"* — assumed the
   producer was indistinguishable in persisted evidence. It was not:
   `section_geometry_binding_hash` is populated only for the profiled-clip
   modes and is excluded for `floorwise_csg_section_loft`, so an empty hash
   already separated them. It was persisted and simply never read.

## Root cause, measured not inferred

Instrumented `select_legal_field_affine_projection` on the real parcel:

- **100%** of affine-fit failures are `no_screened_alternatives`. Compilation,
  floor sections and band meshes all pass.
- Inside screening, of 2640 pose attempts: `min_required_none` **2243 (85%)**,
  `min_required_exceeds_contained` 397 (15%). `_screen_matrix` is never reached.
- Of the 2243: only **21** are invalid placements. The rest are poses where the
  authored body, scaled to the lawful field's principal dimensions, covers
  0.1–1.0 of the required area, concentrated at **0.6–0.9**.

One sentence: **required GFA, the legal envelope, and an articulated form —
you can have two.** Filling capacity means filling the envelope, which is why
survivors converge on the envelope silhouette, and why 8 of 16 selected fail
`final_mesh_capacity_below_minimum`.

### Why the deterministic supply is the place to fix it

`universal_form_programs(variation_page: int = 0)` takes a page index and
nothing else — **no legal, capacity or envelope input at all**. C175 and C176
used no LLM authoring (`agent_authored_manifest_supply` empty); all 16 masses
came from this envelope-blind path. The envelope brief that does exist
(`normalized_legal_field_design_context`) only ever reached the live LLM author,
so it never applied to this board.

## Two dead ends — do not repeat them

1. **`minimum_aggregate_target_ratio` is not the lever.** Threading the capacity
   band (0.706 / 0.857 / 0.923 instead of a hard 0.995) reaches the function —
   verified by instrumentation — and changes nothing. C176 and C175 produced
   **byte-identical geometry-hash sets** (`67c0251bd925c0ce`). Reverted.
2. **`_contains_internal_horizontal_terrace` → tread-area ratio** *did* work
   (loft 2/3 → 1/16) and is worth keeping, but it lives in `source_bridge.py`,
   which currently holds ~3000 lines of uncommitted work from other sessions.
   It is **not committed**. Do not `git stash` in this tree — it silently
   reverts other sessions' work (this was hit and recovered once).

## What landed — commit `15a983e`

```
backend/design/maas/geometry_language/legal_envelope/
  __init__.py            public API; no coordinates / mesh / form names leave here
  design_context.py      legal floor sections -> normalized band relations
                         (extracted out of llm_adapter, now shared)
  seed_conditioning.py   band relations -> generic seed proportions
backend/design/test_maas_legal_envelope_context.py            6 tests
backend/design/test_maas_legal_envelope_seed_conditioning.py  9 tests
```

Additive only. **Not wired into the supply — no run output changes yet.**

Real parcel `1168011800104170004` now reads as:

```
plan_aspect               1.606
band_area_ratios          1.0 / 1.0 / 0.729 / 0.500
prism_efficiency_ceiling  0.807     a straight prism's maximum lawful share
taper_ratio               0.500
long_axis_retention       1.000
short_axis_retention      0.501
contraction_axis / side   short / min      <- the 정북일조 cut
centroid_drift_short      +0.250
```

Real data caught a defect synthetic boxes could not: a 0.003% axis wobble was
being read as a legal setback. Contraction is now judged at 1% of an axis.

## Next step

Wire `envelope_seed_conditioning` into `universal_form_programs` as an optional
argument. Lock "no conditioning ⇒ byte-identical output" **first**, then let the
conditioning bias seed proportions only.

Hard rules that still hold: no PNU coordinates, no completed form template, no
fixed roof script, no pinned operator probabilities in production.

## Reproduce

```bash
cd ARR/backend
python manage.py benchmark_maas_book_program_portfolios \
  --pnu 1168011800104170004 --program neighborhood --recursive-only \
  --diagnostic-target 20 --output-dir <run-dir>
# ~35 min, ends completed_with_failed_gate, selected 16, scope 6/6
python manage.py test design.test_maas_legal_envelope_context \
  design.test_maas_legal_envelope_seed_conditioning   # 15/15
```

Baseline caution: `design/test_maas_shared_floor_contract`,
`test_maas_final_mesh_floor_evidence` and `test_maas_diagnostic_morphology_policy`
already fail **40 + 16** in this tree before any new change — mostly stale mode
names (`floorwise_profiled_legal_clip` vs `floorwise_profiled_continuous_envelope_clip`,
`legal_csg_maximum_lower` vs `affine_maximum_contained_lower`). Diff failure
**sets**, never counts.

## Runtime cost — measured, and the agreed plan

A 20-mass run takes ~35 min. Measured phase split (C175):

| phase | seconds | share |
|---|---:|---:|
| **exact_compile** | **1996.9** | **96%** |
| solver | 52.9 | 2.5% |
| parking / render | 15.0 / 15.0 | 1.4% |
| law (incl. VWorld) | 1.4 | 0.07% |
| cheap_screen | 0.9 | — |

Law and site lookup are **1.4 s**. The 35 min is not the legal pipeline.

`exact_compile` is ~8.3 s per evaluated candidate (1996.9 / 240). It is *not*
geometry compilation: compiling a form-bank program measures at **3 ms**
(86 programs in 0.2 s). The time goes into the per-candidate legal
materialization — affine pose search plus floorwise CSG.

**Not yet measured: how that 8.3 s splits between the affine search and the CSG
booleans. Profile before optimizing.** Three wrong guesses were made in one
session before instrumentation settled the earlier question; do not repeat that.

### Agreed order of work

1. Profile one target-3 run to attribute the 8.3 s. Do not run it concurrently
   with another benchmark — they contend for CPU and both numbers become junk.
2. **Parallelize candidate evaluation.** It is embarrassingly parallel: the
   legal floor field is fixed for the run, candidates do not read each other,
   and each result is deterministic in `(program_hash, legal_floor_field_hash)`.
   The machine has 24 cores and the run uses one. Realistic 8–12x, not 24x:
   workers must stay pure, with outcome-graph and run-state writes collected by
   the parent, and replenishment *cycles* stay sequential because they feed back.
3. **Monotone short-circuit in `_minimum_scale_multiplier`.** `achieved(scale)`
   is non-decreasing, yet the failing 85% run all 12 linear probes before
   returning None. Probing the top scale first ends them in one call. Caveat:
   `achieved()` returns 0.0 when `_placed_sections` fails, so it is not strictly
   monotone — 21 of 2243 cases. Correct form: check the top first; if it falls
   short *with a valid placement*, return None; if the placement was invalid,
   fall back to the full sweep. Results stay identical.
4. **Cache candidate evaluation** on `(program_hash, legal_floor_field_hash)`.
   Same parcel plus same seed is always the same result; today it is recomputed.
5. Only then the closed-form work: intersection area is piecewise quadratic in
   scale within a fixed clip topology, and "largest inscribed similar copy" is
   an LP for convex sections. This one *can* shift numerics, so it needs its own
   verification rather than the equality gate below.

### Equality gate for 2–4

Steps 2, 3 and 4 must not change output. Verify the way C175 and C176 were
compared: hash the sorted set of `projectedVisualGeometryHash` across the
selected rows and require the same digest (C175 = C176 = `67c0251bd925c0ce`).
Reordered computation with a stable final sort must reproduce it exactly.

### Deployment note

35 min is the cost of evaluating ~240 candidates to select 20. A single MASS is
~50 s (C173 exited in 47.5 s). Nothing here should run synchronously on a web
request: `/design/jobs/<id>/stream/` (SSE) and the `single_execution/` boundary
already exist for that. With step 4 in place, a repeat visit to the same parcel
is largely cache hits.

## Performance pass — what landed, and what the numbers are worth

Profiled one target-3 run (`cProfile`). Two warnings before reading any of it:

1. **The profile's top entry is misattributed.** `scipy...._highspy._highs` shows
   587 s tottime in 4 calls, but `portfolio_selection`, `portfolio_constraint_solver`
   and `run_replenishment_cycle` together total a few seconds, and the app's own
   timer puts `solver` at 15.3 s. The MILP is *not* a cost. Ignore that row.
2. **This machine's run-to-run variance exceeds the effects being measured.**
   Three target-3 runs of identical code gave 4.79 / 5.85 / 6.78 s per candidate.
   Any end-to-end claim under ~40% on a loaded machine is noise.

### Where the time actually is (profile, our code only)

```
select_legal_field_affine_projection      265.7s   46% of app-measured phase time
 └ _screen_affine_alternatives            264.3s
    ├ _maximum_contained_scale_multiplier 205.2s   <- largest single item
    │   └ contained() 56,127 calls
    │      └ _general_bands_contained     157.6s
    ├ _pose_matrix            92,720 calls  75.8s
    └ _minimum_scale_multiplier            54.8s
materialize_floorwise_legal_source          70.4s
```

Underneath: shapely `covers` 488k calls, `is_valid` 1.37M, and shapely's own
decorator calling `inspect.signature` **4.5M times** (230 s cumulative). The cost
is per-call Python overhead around GEOS, not GEOS itself.

### Applied (all four verified to leave output unchanged)

1. `validate_matrix4` fast path for already-canonical matrices, and `_multiply`
   with unrolled indexing. Isolated benchmark: **4.1x each** (0.93→0.23 s and
   2.62→0.64 s per 200k calls).
2. Dropped the redundant `shapely.is_valid` pass in `_general_bands_contained`
   (a 3-point ring cannot self-intersect; the area floor already removes
   degenerates).
3. **Thread-parallel pose screening** in `_screen_affine_alternatives`. The 48
   poses are independent and the work is GEOS/NumPy, which releases the GIL.
   Results are consumed in the original iteration order, so dedup and the
   returned set are identical. Workers = `min(8, cpu-1)`.
4. Monotone short-circuit in `_minimum_scale_multiplier` — **failure path only**.
   Intersected area grows with scale, so if the top of the range falls short
   nothing smaller reaches the target. Guarded: `achieved()` returns 0.0 for a
   failed placement, so it only concludes when the top pose actually placed.

**Verification gate used throughout:** the sorted set of
`projectedVisualGeometryHash` over the selected rows, hashed. Target-3 digest
`595018a1e25220c4` was identical across all four changes.

### Rejected after measuring

- A bbox early-out inside `_general_bands_contained`. `legal.bounds` costs a
  shapely property call per band per invocation (~224k extra) and the early-out
  almost never fires. Reverted — though note this judgement sits on the same
  noisy measurements.
- Short-circuiting `_maximum_contained_scale_multiplier` from either end.
  `contained()` is **not** guaranteed monotone: `_pose_matrix` applies a
  scale-dependent correction that translates the body, so a larger scale is not
  strictly less contained. The existing sweep only assumes monotonicity *after*
  the first contained probe. Do not "optimize" this without proving the property.

### The trap worth remembering

Fully unrolling `_multiply` into `a + b + c + d` looked equivalent and was not:
**CPython 3.12+ sums floats with Neumaier compensation**, so `sum()` and
left-to-right addition differ in the last digit — which moves every program
hash. `design/test_maas_affine_matrix_exactness.py` (commit `bc85cd4`) keeps the
pre-optimization implementations as oracles and caught it immediately. Any
future work on this kernel must run against that oracle.

### Not done

Candidate-level parallelism is where an 8–12x lives, and it is *not* started.
The loop is four levels deep in `candidate_generation.py`, mutates failure
sinks, counters and the outcome graph, and sits under ~3000 lines of another
session's uncommitted work. It needs the loop body extracted into a pure
function first, in a tree that has been committed.

## Proven: the pose is linear in the scale multiplier

`_pose_matrix(scale_multiplier=s, ...)` maps a fixed vertex to a position that
is **exactly affine in s**. Measured over 300 random `(s1, s2, t)` triples, the
gap between linear interpolation and the actual transform is `1.1e-12` — float
noise:

```
v(s) = P * s + Q
```

This unlocks a closed form for `_maximum_contained_scale_multiplier`, which is
the single largest cost in the pipeline (205 s of the 265 s affine stage) and
today runs a 24-sample sweep plus 14 bisection steps — up to 38 containment
tests per pose.

With linearity, each convex halfspace `n·x <= d` becomes one linear inequality
in s:

```
(n·P) s <= d - n·Q
```

so every vertex/halfspace pair yields an interval, and their intersection is
the exact maximum contained scale. Two matrix evaluations recover `P` and `Q`.
For the non-convex legal sections on this parcel, the convex hull gives a
strict upper bound — a necessary condition — which brackets the search tightly
and lets the 24-sample sweep be dropped safely.

Target: 38 containment tests per pose down to 1–3.

Watch the degenerate case `n·P == 0` (constraint independent of s: either
always satisfied or never).

Do **not** confuse this with monotonicity of `contained(s)`, which is *not*
proven and must not be assumed: linearity of the vertices does not make the
containment predicate monotone once the body leaves and re-enters a concave
legal boundary.

## 2026-08-11 — masses now clear the combined gate, and the real gap is named

`legal-mass-v36-c179-law-online-capacity-advisory`: **15 of 16 selected pass
`combined_hard_pass`**, against 0 of 16 before. `law_graph` 16/16. Capacity
modes: 8 `advisory_actual_gfa_underfill`, 7 `accepted_actual_gfa_minimum_band`.

All three blockers were identified and cleared:

| blocker | kind | fix |
|---|---|---|
| Neo4j not running | environment | started |
| law-domain-agents :8011 not running | environment | started (reads local Neo4j; the CF Worker reads Vectorize instead and would break article-id binding) |
| capacity underfill rejected as unlawful | **policy bug** | advisory, commit `5842c73` |

Commits: `15a983e` (legal_envelope package), `bc85cd4` (Matrix4 exactness
oracle), `5842c73` (capacity advisory).

### Second real-world test parcel

`경기도 의정부시 산곡동 684-1` → **PNU `4115011300106840001`**.
This is a live KG엔지니어링 설계1본부 project (주민센터 현상설계); reference
images in `docs/Ref/`. The stated purpose there is to check whether this system
produces anything useful on an in-progress real project.

### The quality gap, from the reference drawing (`docs/Ref/1-8_29_6.jpg`)

Practice massing on this site is **an assembly of a few clean orthogonal
volumes**: a plinth, a shifted middle block, a smaller upper block, setbacks
that become roof terraces, the ground floor **lifted on piloti** to give public
space underneath, all drawn inside a modelled urban context (neighbours, roads,
river, green corridor).

Our output is **one solid carved by the sunlight plane** — the user's phrase was
"그냥 다각형". The gap is not legality and not geometric validity, both of which
now pass. It is composition:

- several discrete clean volumes in relation, not one carved blob
- a lifted/piloti ground condition
- setback-derived terraces as an intended move rather than envelope residue
- surrounding context in the render

This, not the gate work, is what "현상설계급" requires next.

## Capacity intent is already program-aware — use the right program

`design/maas/capacity_policy.py::resolve_massing_capacity_policy` resolves FAR
intent from the program label, and it already encodes the practice rule that
commercial programs fill their allowance while civic ones often do not:

```
neighborhood  -> balanced     min 0.35 / target 0.75
cultural      -> design-led   min 0.20 / target 0.55
gymnasium     -> design-led   min 0.20 / target 0.55
```

`DESIGN_LED_PROGRAM_TOKENS` covers 미술관·박물관·문화·체육·**공공**·도서관·
학교·civic·library·pavilion; `CAPACITY_FIRST_PROGRAM_TOKENS` covers 근린생활·
상가·주거·업무 and drops to a 0.60 floor on sites under 1000 m².

**The 의정부 산곡동 684-1 주민센터 is a civic program.** Running it as
`--program neighborhood` puts it on the fill-the-envelope track and is wrong;
use `--program cultural` (design-led, 0.20 floor). The CLI only offers
`neighborhood | gymnasium | cultural`, so `cultural` is the civic stand-in until
a dedicated 주민센터/공공청사 program exists.

### Correction to the earlier "policy bug" claim

The 0.6 floor that rejected 8 of 16 Gangnam candidates was **not** an arbitrary
mistake — for 근린생활 on a small site it is the intended capacity-first value.
Only half of that earlier claim holds: the real defect was treating a shortfall
against that floor as *unlawful* and hard-rejecting it. FAR remains a ceiling,
so underfill stays advisory (`5842c73`), but the floor itself is a deliberate,
program-aware design target and must not be flattened.

## What the practice reference actually shows (`docs/Ref/1-8_29_6.jpg`, `_10.jpg`)

Two mass alternatives for the same competition site. Shared moves:

1. three or four discrete clean orthogonal volumes, stacked and shifted
2. ground lifted on piloti, giving public space underneath
3. setbacks read as intended roof terraces, not envelope residue
4. **the mass occupies roughly 40% of the parcel** — the rest is left open for
   approach and yard; one alternative adds a large external entry stair
5. composition follows program: public base, smaller volumes above
6. neighbours, roads, river and green corridor are modelled as context

Our masses are one solid carved by the sunlight plane. The parts exist in the
language — `union`, `matrix_array`, `terrace`, `setback`, and
`clip_and_certify_projected_piloti_visual` — but none reach a selected board,
because every gate has preferred filling the envelope. Point 4 is the one that
today's advisory change plus a design-led program finally makes reachable.

### The low-rate exotic seeds never survive

`rare_unitbox_capability_programs()` adds four page-zero parents (triangular
clip, oblique clip, elliptical circularize, interlocking elliptical plates) at
4/86 = 4.65%, added specifically so Qatar-Library-like outcomes were possible.
In C179 they appear **zero times** anywhere in the run; selected `base_seed` is
`slab 6 / block 8 / bar 1 / tower 1`, all rectilinear. Measure where they die
before theorising — the affine reject histogram method works for this.

## C181 — Uijeongbu civic parcel, first live VLM verdict

`legal-mass-v38-c181-uijeongbu-civic-live-vlm`, PNU `4115011300106840001`,
`--program cultural` (design-led, 0.20 floor), `--live-vlm`.

Site is far tighter than Gangnam: **BCR 20% / FAR 100%**, 2499.7 m² parcel with
1922.2 m² generation area.

```
evaluated 240 | program-passed 167 (Gangnam: 114) | pool 0 | selected 0
VLM requests 4
```

Design-led capacity clearly works — program pass rate rose from 45% to 69%.
But **selection took nothing**, and the first named failure is:

```
portfolio_vlm_visual_diversity_hard_gate_failed
selected_count_below_target_20
book_operation_count_below_required_target
visual_language_count_below_required_target
ground_strategy_count_below_3
```

**The live VLM rejected the portfolio for visual diversity** — independently
reaching the same conclusion measured on the Gangnam board (12 of 16 read as one
sloped-plane cut, voxel-IoU median 0.637). Law and geometry are no longer the
constraint; sameness is.

### Where candidates die (outcome graph histogram)

```
372  stage=program_gate
116  stage=geometry_gate
 63  authored_profiled_legal_clip_failed
 60  profiled_legal_clip_legal_revalidation_failed
 24  authored_visual_projection_revalidation_failed
 21  revalidation_floor_section_area_mismatch
```

Every one of the 372 program-gate records carries
`source_seed=program_cultural_court_bridge` — `cultural` runs on only 3 base
role seeds (`base_role_seed_count: 3`), so the court/bridge assembly seed
dominates that stage. **Not yet established: how many of those 372 are
rejections versus observations.** Determine that before drawing conclusions —
the same discipline that settled the affine question.

### Standing conclusion

The parts for practice-grade massing exist in the language (`union`,
`matrix_array`, `terrace`, `setback`, piloti certification) and the reference
drawings show exactly what to aim for, but no assembled multi-volume candidate
has ever reached a selected board on either parcel. That, not the gates, is the
remaining work.

## ROOT CAUSE OF THE DIVERSITY FAILURE — one seed

Resolved from the C181 outcome graph. The 372 program-gate records were not
rejections:

```
program_gate observations 186 -> hard_pass True 167 / False 19
passing seeds : program_cultural_court_bridge  167
failing seeds : program_cultural_court_bridge   19
```

**Every one of the 240 evaluated candidates for `cultural` descends from a
single seed, `program_cultural_court_bridge`.** The program gate passes 90% of
them; it was never the bottleneck.

That is the whole diversity story. Two hundred and forty variants of one seed
resemble each other no matter which operators are applied, which is exactly what
the live VLM rejected as `portfolio_vlm_visual_diversity_hard_gate_failed`.
Gangnam has the same shape: `base_role_seed_count: 3`, selected base seeds only
slab/block/bar/tower, and the four rare capability parents appearing zero times.

```
1 seed -> 240 derivatives -> all alike -> VLM rejects the portfolio
```

This explains why every attempt made in this session to create diversity
downstream failed — affine ratio band (no-op), nearest-proportion supply order
(throughput up, spread down), dispersed supply order (throughput down). **You
cannot select diversity that was never generated.**

### The next two questions, in order

1. `program_seed_sequences(building_type)` — why does `cultural` run on one
   seed? How many does each program have, and what governs that?
2. `rare_unitbox_capability_programs()` — the four elliptical/triangular parents
   were added deliberately so Qatar-Library-like outcomes were reachable, and
   they never enter the `cultural` (or `neighborhood`) candidate path. Find
   where the supply is filtered to a single program seed.

Fix generation, not selection.

### Where the seeds are lost — start here next session

`program_profiles.v1.json` defines per-program seeds:

```
housing 20 | gymnasium 6 | neighborhood_living 4 | cultural 3 | cafe 2
office 1 | retail 1
```

`cultural` has **three** seeds — `court_bridge`, `carved_gallery_spine`,
`split_gallery_ramp` — and all three pass `VerbSequence.validate()` cleanly
(returns `[]`), so `program_seed_sequences("cultural")` hands back all three.
Yet every one of C181's 240 candidates carries
`source_seed=program_cultural_court_bridge`.

**The seeds are truncated downstream, not at the profile.** One confirmed
truncation site:

```python
# candidate_generation.py, inside _agent_mutated_seeds
for source_index, source in enumerate(tuple(originals.values())[:2]):
```

`[:2]` caps the seeds fed into the universal-program cross product. Find every
such cap between `program_seed_sequences()` and the candidate loop, and check
whether a later stage collapses to `originals` first entry.

This is the highest-value fix available: the portfolio's whole diversity budget
is set here, and the live VLM is already rejecting on exactly this. Do not edit
blind — the tree currently produces 15/16 combined hard passes on Gangnam and
that result must survive. Verify with the geometry-hash digest method and rerun
both parcels.

## 2026-08-11 (later) — the truncation is fixed, and the deeper cause is named

### Truncation: measured on a real run artifact, not inferred

`tmp_mass_check/law-on/maas-book-programs-summary.json` records which supply a
finished run actually touched. Every row is
`program_neighborhood_active_bar__universal_0_<n>_...` with **n in 0..20** —
one program seed (source index 0) and a contiguous head of 15 distinct forms
out of 86.

Three caps stacked:

| axis | in the bank | reached | why |
|---|---|---|---|
| program seed | 3 (cultural) | **1** | `[:2]` plus source-major order |
| form | 86 | **first ~21** | exact-compile cap truncates a contiguous head |
| rare lane (ellipse/triangle) | idx 82-85 | **0** | tail of the list |
| lift / terrace / setback / bridge | idx 14-68 | 2-3 | past the cut; the 5-strong families repeated 3x inside the head |

Fixed in `81bfa9e`: `stratified_form_supply_order` round-robins the bank's own
declared families and then spreads lanes by fair share inside each round, and
the cross product runs form-major with the program seed rotating over *all*
seeds. Same programs, same pairings, different order. A 21-head now holds 21
distinct families, 2 multi-volume compositions and 2 rare probes.

Failure set across the four affected suites was captured before and after by
reverting the two edits in place (never `git stash` in this tree) — identical,
24 pre-existing, 0 new.

### The deeper cause: the bank was a one-body language

Ordering alone could not have produced competition massing, because the supply
had nothing to reach:

```
programs by (union + attach + matrix_array) count, page 0
  0 ops : 80 / 86
  1 op  :  5
  2 ops :  1
```

93% of the bank is one box with one modifier. The reference drawings are three
or four clean orthogonal volumes stacked and shifted, ground lifted on piloti,
setbacks read as terraces. That is not a gate problem and never was.

Two mechanical reasons, both verified:
1. `synthesis.py::_OPERATOR_KIND` contains **no boolean operator at all**. The
   only multi-input operator the 64-program synthesis lane can emit is
   `attach`, and `universal_form_bank.py`'s single-primitive filter then
   discards every `attach` program, because its guest is a second primitive.
   So the largest lane is single-volume by construction *and* by filter.
2. The other two lanes are hand-written literal lists.

Nothing in the geometry layer blocked composition: a plinth + shifted middle +
smaller upper + `lift` compiles to **one closed component, no gate issues**,
from `box`/`translate`/`union`/`lift` alone.

`b7810d3` adds `geometry_language/stacked_volume_bank.py` — six composition
figures (offset stack, alternating stack, lifted stack, plinth and upper, twin
volume with bridge, pinwheel) over a parameter grid of plan aspect, level scale
and volume count. Measured: **48/48** compile to one closed component across
two pages; **72/72** survive BOOK projection against all three cultural seeds,
the same rate as the existing bank. Every volume is a Matrix4 placement of the
one canonical UnitBox, so each program still has exactly one primitive and the
bank's single-primitive rule is intact.

Unplanned benefit: the lane is **0/24 near-square** against the old bank's
40/86, median plan aspect 1.333 vs 1.160, against a lawful ground of 1.606.
Memory already recorded mis-proportioned supply as why poses fail to cover the
required area.

### Traps found here

- A union of *touching* volumes is fine, but plain `union` does **not**
  auto-connect: an alternating stack whose shift walked a level clear of the
  one below returned 2-3 components. Shifts must be cumulative from the level
  below and bounded to keep plan overlap.
- `program_projection.py::_LIFT_HAZARDS` contains `union`, so BOOK will not
  *add* a lift to a union-rooted program. Harmless here (the lifted figures
  carry their own `lift`), but it means union-rooted supply gets no automatic
  threshold operator.
- `test_maas_universal_form_rare_capabilities` pinned page zero at exactly 86.
  Any new lane breaks it. It now bounds the total against the contract's
  declared lane counts instead.

### Rendering the supply

`tmp_mass_check/render_lane.py` draws a contact sheet of any program supply
(axonometric, painter's algorithm). Use it before theorising about shape —
`python tmp_mass_check/render_lane.py lane|head`.

## 2026-08-11 (later still) — why every mass came out a flat plate

The supply work above was necessary and not sufficient. With the truncation
fixed and a composed supply in place, a target-5 Uijeongbu run still selected
**0 of 47 archived masses**, and rendering the archive showed why: every one
was a wide flat plate with an overhang. `tmp_mass_check/render_archive.py`
draws any run's archive - use it before theorising, it found this in one look.

The cause was in the floor plan, not the geometry.

### Coverage was applied to the ground plate only

건축법 시행령 제119조 제1항 제2호 defines 건축면적 as the horizontal projection
of the **building**, and 제4항 binds every other 수평투영면적 to the same method.
An upper plate that overhangs the one below therefore governs coverage.

Three files clamped index 0 only (`floor_capacity_plan.py`,
`legal_floor_field.py`, `candidate_floor_authority.py`). Wrong twice over: it
let upper plates exceed the limit, and because the clamped vector is also the
*weight* vector of a proportional allocator, it shrank the ground floor's share
rather than its size and pushed the difference upward.

```
PNU 4115011300106840001, BCR 20%, FAR 100%, 2499.69 m2
caps    = [499.938, 1922.226, 1922.226]     coverage on index 0 only
util    = 1374.830 / 4344.390 = 0.316461
targets = [158.211, 608.310, 608.310]       4x cantilever; 608 > 499.938
```

Side effect: realized per-plate utilization was 0.316 while the payload
advertised `design_reserve_ratio: 0.45`.

After (`f74554b`): **5 floors x 274.966 m2 at 15 m, utilization 0.55**, every
plate inside the coverage capacity.

**No test caught it because every fixture in `test_maas_floor_capacity_plan`
sits on a site whose coverage cap exceeds its floor section — the clamp was a
no-op in all 15.** `CoverageBoundsEveryPlateTests` adds fixtures where it
binds. Check that a new fixture actually exercises the branch it is aimed at.

### The payload disagreed with its own validator

Applying the fix made every run die at
`authoritative_run_legal_floor_field_invalid` before generating anything.
`validate_legal_floor_field` recomputes `height_field_capacity_m2` from the
per-floor capacities the payload carries, but the payload summed the raw
values and stored the rounded total. That gap survived only while the plates
differed and their rounding errors cancelled. Sixteen identical 499.938 plates
made it coherent: sum 7999.008 vs stored 7999.01, i.e. 0.0020000000004 against
a 0.002 tolerance. Fixed in `858f30c` by rounding once and summing the stored
values.

Generalisable: **any aggregate a validator recomputes must be summed from the
stored values, not the raw ones.**

### Debugging note

Do not verify a CLI benchmark through `call_command(...)` with keyword
arguments — the run completed in 2 seconds having done nothing, and the
"validator passes" conclusion drawn from it was worthless. Use
`execute_from_command_line` with a real `sys.argv`, which parses exactly as
the CLI does.

### The fix opened a branch that had never run

Fixing the floor plan made affine placement start succeeding. Memory records
that **100% of affine-fit failures were `no_screened_alternatives`**, so every
candidate had always taken the repair path. The success branch
(`compile_site_bound_geometry_program_to_source_mass`) had therefore never
delivered a certified artifact — and it carries Z in a different frame.

`_compile_geometry_program_to_source_mass` has two identity exports
(source_bridge.py:2528-2551):

| mode | Z frame |
|---|---|
| `normalized_authored_identity` | divided by the compiled vertical span, [0, 1] |
| `site_bound_matrix4` | compiled vertices passed through, **metres** |

`canonical_metric_surface_payload` assumed the normalized frame
unconditionally and multiplied by the physical height — metres times metres on
a site-bound source, with the range guard firing first and killing the run at
`certified final visual source Z is not normalized`. Fixed in `2f1ceb6` by
reading the export's own declared `legal_fit_mode` instead of guessing from
coordinate magnitudes.

**The lesson worth keeping:** when a long-failing stage starts passing, the
code downstream of its success path has never been exercised. Expect one
defect per newly reachable branch, and look for the *frame* or *unit*
assumptions first — they are what a never-taken branch gets wrong.

### First masses that are buildings, not plates

Target-3 run `c195-probe` (all fixes): **3 selected**, `combined_hard_pass`
6/9, FAR 48-56%. Three distinct concepts — a carved block, a **two-volume
split**, and a clean prism. Proportions are a building, against the flat
plates of every earlier run. Full target-20 verification still outstanding.

### Environment note

Vworld intermittently times out (`VWorld parcel boundary is required`, `PNU
zoning lookup returned no executable zone`). Three consecutive runs died on it
within 10-30 s. It is not a code fault — retry. There is no synthetic
fallback by design.

## 2026-08-11 (end of session) — coverage was never a placement constraint

Fixing the floor plan (`f74554b`) made the *plan* lawful. It did not make the
*mass* lawful, because nothing carried coverage into placement. Measured by
projecting every archived mass's surfaces to XY and unioning them:

```
PNU 4115011300106840001, coverage capacity 499.938 m2
23 of 28 archived masses exceed it, worst 969.7 m2 (1.94x)
lawful: 401.8 / 415.2 / 432.9 / 465.3 / 465.3   (5 of 28)
```

The `bcr_limit_exceeded` hard gate at `downstream_hard_gate.py:707` **does
exist and does work** — the three selected candidates all passed it. It simply
catches violations *after* a full legal materialization each, so the lawful
pool stays thin and `selected_scope_count` stays at 1 of 3.

Two corrections to claims made earlier in this session, both from sloppiness:

1. **`GFA / floors` is not 건축면적.** Coverage is the horizontal projection of
   the building, so L-shapes, courtyards and stepped bodies have unequal
   plates. The first estimate said 16/28; the correct union-projection
   measurement says 23/28.
2. **"Add a coverage hard gate" was wrong — one already exists.** And
   "enforce the plan's floor count" was wrong too: a wide two-storey building
   and a slim five-storey one are equally lawful if coverage and FAR hold. The
   plan's floor count is one solution, not a requirement. Do not count a mass
   as defective for choosing a different stack.

`289084c` bounds the pose search itself. The pose scales the body in plan and
otherwise only translates it, so the projected area is exactly quadratic in
the multiplier:

```
s_max = sqrt(coverage_capacity / projected_area_at_scale_1)
```

applied as a `min` on the `scale_upper` the search already computes. One union
area per pose; can only tighten. The capacity comes from the trusted legal
floor field. Passing None leaves the search byte-identical.

**Not verified on a live run.** VWorld timed out on all three endpoints for
the last hour of the session and there is no synthetic fallback by design.
`test_maas_coverage_bounded_placement` verifies it instead, including the
premise that an unbounded placement really does exceed.

### Where the literature actually is (searched 2026-08-11)

The paper the user supplied is **EvoMass** (Wang, Janssen, Ji — CAADRIA 2020,
*Frontiers of Architectural Research* 2024). Its formulation is better than
this project's on one specific point: **subtraction is a first-class generator
with its own count and boundary constraint** (voids on the edge / voids
inside), and its parameter set is only five numbers — additive mass count
(4/6/8), horizontal size range, vertical size range, subtractor count (6/4/2),
boundary constraint. Its Fig. 3 argues that additive+subtractive spans one
*unified* design space, where typology enumeration (which is what this bank's
`family` list is) only produces disjoint islands.

That matters here: `_VOID_MACROS` was excluded from composition because voids
severed the body. EvoMass avoids that by bounding subtractor size relative to
the host instead of excluding it. **Re-introducing subtraction that way is the
next supply improvement.**

Newer work, from search only — **none of these were read in full, do not cite
them as settled**:

| year | work |
|---|---|
| 2026 | DQN building arrangement under sunlight/spacing constraints (*Scientific Reports*); high-rise residential layout RL (Springer); multimodal LLM floor-plan tokenization |
| 2025 | LLM-based floor plan automation (*Automation in Construction*); generative-AI conceptual design scoping review |
| 2024 | EvoMass follow-up; Building-Agent (LLM + graph 3D form); eCAADe LLM-CAD; Autodesk Forma x Zoneomics zoning-responsive envelopes |

The pattern: top-venue generative AI went to **2D floor plans**, and 3D massing
went to **RL placement**. "Statute -> lawful 3D mass" remains largely empty.
Treat that as a working hypothesis, not a finding — it rests on search
summaries, not on reading the papers.
