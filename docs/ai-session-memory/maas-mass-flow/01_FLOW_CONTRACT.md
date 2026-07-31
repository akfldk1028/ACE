# Stable MASS Flow Contract

## Product-level canonical multi-agent flow

The target system produces a traceable competition-design proposal from a real
site. The following order is authoritative even though current runtime modules
still implement parts of it as separate pipelines:

```text
user brief + PNU + program
  -> design_orchestrator
  -> site/datum acquisition + law_graph_agent
  -> deterministic legal envelope
  -> authoritative floor plates + four capacity alternatives
  -> parking_agent pre-constraint
  -> optional reference-language distillation
  -> llm_architect_agent
  -> massdsl_agent
  -> GeometryProgram Compiler
  -> grammar + architectural-building gate
  -> exact capacity/legal/program/parking hard gates
  -> technical MASS render
  -> bounded preference/VLM critic
  -> typed graph or GeometryProgram repair request
  -> recompile and repeat every hard gate with a new geometry hash
  -> review_agent
  -> selector
  -> archive and freeze accepted identity
  -> freeze execution_id + program_hash + geometry_hash + PNU
  -> elevationAgent deterministic condition pack
  -> replaceable facade image provider
  -> deterministic and multimodal cross-view consistency gates
  -> final competition-design evidence package
```

### Authority by stage

- `design_orchestrator` owns routing and fail-closed workflow state. It does
  not calculate law or author geometry.
- `law_graph_agent` owns cited legal evidence from the law-domain service and
  the Neo4j law Graph DB. Deterministic ARR calculators turn those rules and
  site data into buildable footprint, height, setback, sunlight, BCR and FAR
  constraints.
- The legal envelope/floor-stack solver owns per-floor plate geometry and
  capacity accounting. Floor count cannot be metadata detached from those
  plates.
- `parking_agent` owns required-count and layout evidence. Parking first
  constrains the author brief, then rechecks each realized candidate and emits
  deterministic repair requests when infeasible.
- An optional Reference VLM distills precedent images into transferable
  language. It never copies geometry or approves law.
- `llm_architect_agent` owns site-, program-, capacity-, parking- and
  reference-conditioned architectural intent and typed component relations.
- `massdsl_agent` validates and lowers that intent into an executable typed
  program. It is not a post-hoc label attached after geometry already exists.
- The Geometry Compiler materializes the program and owns mesh truth, but a
  valid manifold solid alone is not a building. The current
  `maas_geometry_agent` is a post-compile metric/review-context agent; it does
  not compile geometry.
- Grammar, floor, program, capacity, law and parking gates are deterministic
  vetoes. No LLM, VLM, selector or attractive PNG can override them.
- VLM owns image-backed architectural criticism only after deterministic
  preflight. Actionable criticism must become a typed bounded edit, compile to
  a child identity and pass every gate again.
- Selector/review chooses only from the exact hard-pass universe. It cannot
  create missing quality or fill a portfolio with duplicates/rejects.
- `elevationAgent` starts only after MASS identity is frozen. It consumes the
  same floor plates, mesh, program, law, parking and site evidence and cannot
  alter MASS geometry or infer compliance from pixels.

### One shared floor truth

The canonical building representation must expose the same per-floor plates to
capacity, program, parking, compiler/building-legibility gates, selector and
elevation. `requested_floors`, sampled SourceVolume intersections, bounding-box
height and visual floor guides are supporting evidence; none may replace the
authoritative plates.

Capacity alternatives remain `spatial_reserve`, `balanced_yield`,
`brief_target` and `maximum_feasible`. They are site-derived performance
targets, not morphology families. Each candidate must pass its own measured
target while remaining within the exact legal envelope.

### Two repair loops

1. Parking/legal repair:
   candidate floor/use schedule -> required parking/layout -> typed repair
   request -> LLM/MassDSL/geometry regeneration -> full hard-gate replay.
2. Architectural critic repair:
   technical render + exact references -> VLM directive -> typed graph/AST
   child -> new program/geometry hash -> full hard-gate and VLM replay.

Textual advice that never changes a typed child is review evidence, not an
active generative loop.

### Execution-mode truth

- Portfolio benchmark: explores supply/diversity and may run site-derived
  preflight. Numeric 20/20 is not automatically a final design or VLM approval.
- `fresh_synthesis`: proves a new GeometryProgram/hash. Without resolved PNU,
  placement, capacity, law, parking, program and VLM evidence it is a form
  study, not a complete proposal.
- `exact_replay`: re-executes the immutable parent AST. It may add new evidence
  but is never a newly authored design.
- Single execution: fast compile/GATE/render of one explicit program. It does
  not imply that the LLM authoring or portfolio search stages ran.
- Elevation proposal: downstream evidence for one frozen MASS. It never counts
  as MASS generation or legal/capacity evidence.

The UI must display these modes explicitly and must not choose a newer partial
fixture over a complete product-path result. If no complete product-path result
exists, the UI must say so instead of presenting a diagnostic as final.

### Product acceptance

A competition-design proposal requires evaluated, identity-matching evidence
for site/PNU, cited law, datum, authoritative floor plates, capacity target,
program, parking, GeometryProgram/compiler, building-legibility GATE, technical
render, bounded MASS VLM and selector. The final presentation additionally
requires accepted elevation consistency evidence. `geometry_ready`,
`live_scored`, `accepted` from a pre-current contract, or an attractive
elevation image alone is insufficient.

## Historical BOOK/single-execution causal order

This section records the older implemented lane and must not override the
product-level flow above. In particular, it contains post-compile specialist
review rather than the full law/parking-conditioned authoring transaction.

1. Parcel input: PNU, parcel polygon and jurisdiction.
2. Legal generation context: buildable footprint, height-dependent sunlight
   field, BCR/FAR limits and setbacks.
3. Canonical Base Model: exactly one normalized `1/1 UnitBox`. BOOK ratios
   such as `3/8`, `1/2`, `1/4`, `1/8` and `1/16` are derived occupancy or
   partition states of that host, never sibling Base Model primitives.
4. Universal recursive Geometry Program: primitive, transform, modifier,
   boolean, pattern, cutting, profile/sweep and architectural macro nodes.
5. BOOK language projection: one ordered operative, combination, aggregation
   or case-study lineage. BOOK pages are language provenance, never final MASS
   image evidence.
6. Use/program projection: access threshold, public-space relation, section and
   program role controllers. Program projection is downstream of universal
   geometry and BOOK language.
7. Capacity alternatives: spatial reserve, balanced yield, brief target and
   maximum feasible. Each candidate must pass its own measured capacity target.
8. Compiler and geometry GATE: mesh/kernel validity, non-trivial volume,
   complexity/component/extent budgets and tiny-geometry checks. Inhabitable
   floors, program fit, capacity and architectural morphology require separate
   downstream hard gates.
9. Hash-bound post-compile specialist review on the same compiled MASS:
   `design_orchestrator -> maas_geometry_agent -> law_graph_agent ->
   parking_agent -> review_agent -> selector`. `law_graph_agent` owns calls to
   the existing law-domain/MCP and Neo4j adapters; the orchestrator may not
   bypass the agent with a direct scalar pass.
10. Actual MASS render and immutable program/geometry hashes.
11. Reference retrieval: ArchDaily images may be retrieved and displayed as
    pending context. Retrieval alone is not VLM input.
12. VLM critic: active only when a recorded request actually submits the MASS
    render and reference images. `not_evaluated` is never PASS.
13. Portfolio selector: exact hard-pass universe, silhouette compatibility and
    typed coverage solved as a portfolio set problem. This is distinct from
    the shorter single-execution review selector already listed in step 9.
14. Outcome memory: exact geometry-hash observation stored for the next bounded
    Author/Critic/Repair/Selector cycle.

## Graph contract

- One `LanguageNetworkCanvas`; do not add a second causal graph.
- `FULL GRAPH` and `SELECTED MASS PATH` are two queries over stable IDs.
- Selecting one MASS activates only the materialized edges in that passport.
- The right sidebar and bottom gallery use actual archived run renders.
- BOOK raster requests and BOOK raster DOM nodes must remain zero.
- Retrieved ArchDaily nodes use pending edges unless `used_by_vlm=true` is
  recorded in the passport.
- The graph is causal execution evidence for an Agent, not hidden neural state.
- Specialist agents, source attempts, resolved articles and handoffs are nodes
  in this same graph. Never create a parallel law or agent graph.
- Every handoff repeats the exact execution ID, program hash, geometry hash and
  PNU. Any mismatch fails closed.

## Base-Model-relative parametric invariant

- Base authority is singular: `1/1 UnitBox`. The frontend, compiler and Agent
  graph must not present `3/8`, `1/2`, `1/4`, `1/8` or `1/16` as independent
  base primitives. They are traceable derived states below the base node.
- Every affine state is representable by a homogeneous 4x4 matrix in the live
  local frame: translation, rotation, non-uniform scale, reflection and shear.
  Matrix composition is the canonical transform stack and must remain relative
  to the current Solid, not parcel coordinates.
- A 4x4 affine matrix is not the entire geometry language. It cannot by itself
  create a void, change topology, branch, bend non-linearly or repeat solids.
  Boolean, cutting, modifier, pattern and composition nodes remain recursive
  Solid-to-Solid operations whose inputs ultimately descend from the one
  `1/1 UnitBox` authority.
- BOOK p.3 ratios are recorded as matrix/partition/occupancy derivations so an
  Agent can explain how `1/2` or `3/8` emerged from `1/1`; they must never be
  hardcoded as unrelated final building templates.
- Every downstream operator consumes the evaluated current Solid and derives
  its coordinate frame from live bounds/axes/faces/topology.
- `Attach` stores a host face plus normalized local anchor, guest extent,
  engagement and rotation. The compiler resolves actual guest size and
  position from that live host face. Engagement is a fraction of the resolved
  guest projection, never the full host depth.
- Profile families such as triangular, trapezoidal and chamfered use the same
  `extruded_polygon` Primitive. They are parameterized plan profiles, not new
  one-off building primitives.
- Synthesis may contain named, dimensionless exploration policies. It must not
  contain parcel coordinates, absolute final dimensions or reference-image
  vertex copies.
- A VLM reference may propose capability constraints such as triangular plan,
  oblique cut or face attachment. It never writes unchecked geometry directly;
  the resulting explicit AST must still compile and pass all hard gates.

## Cost boundary

- Non-live geometry exploration may use bounded form-bank pages 0-7.
- A single-MASS VLM review uses at most three distinct ArchDaily images: one
  program precedent, one formally similar precedent and one counterfactual.
  Exact image bytes are deduplicated and nested `program_projection` identity
  must be resolved before generic fallback.
- Live VLM keeps an explicit configured request budget; default is one cycle.
- Never enable paid VLM merely to make a status appear complete.
