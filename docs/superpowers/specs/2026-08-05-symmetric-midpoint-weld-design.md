# Symmetric Midpoint Weld Design

**Date:** 2026-08-05  
**Status:** Approved design specification  
**Evidence source:** `D:\Data\25_ACE\docs\superpowers\plans\2026-08-05-r85-r87-profiled-mesh-metric-proof.md`

## 1. Purpose

Add a generic, deterministic symmetric midpoint weld to the existing profiled indexed-mesh numeric-repair path. The weld addresses canonical `tiny_edge` failures that cannot be removed by the existing one-sided endpoint collapse within its displacement budget, but whose two endpoint representative groups can both move to the physical midpoint within that same budget.

The design does not make a failed mesh legal by tolerance or exception. It creates a candidate repaired indexed mesh and submits that mesh to the unchanged canonical compiler gate and every existing downstream authority gate. Failure at any stage remains terminal and typed.

The r85-r87 evidence establishes only a bounded opportunity: six of seven residual `tiny_edge` witnesses may fit a symmetric two-endpoint displacement budget. It does not establish that any will pass mesh topology, emitted-section equivalence, law, capacity, parking, program scoring, final VLM, or portfolio selection.

## 2. Scope

### In scope

- Canonical identification of current representative edges responsible for `tiny_edge`.
- Deterministic one-sided endpoint collapse followed by narrowly eligible symmetric midpoint welds.
- Per-original-vertex cumulative physical displacement enforcement.
- Fixed-point representative-edge rebuilding after every successful weld.
- Complete canonical compiler and authority revalidation of the emitted repaired mesh.
- Additive typed, bounded attempt and operation evidence.
- Focused TDD for geometry, determinism, displacement, component preservation, gate alignment, and evidence propagation.
- One r88 diagnostic benchmark with measured funnel and PNG evidence.

### Out of scope

- Repairing `tiny_face` through a new operation.
- Changing Hausdorff, section area, containment, legal, capacity, parking, program, VLM, manifold, watertight, component, or self-intersection thresholds.
- Family-, site-, PNU-, principle-, scope-, candidate-, or run-specific repair logic.
- New fallback geometry, candidate fabrication, or promotion of an uncertified repair.
- Changes to author/provider retry, quota, cache, cooldown, or replenishment behavior.
- A guaranteed five-candidate portfolio.

## 3. Existing authority and constants

The existing canonical authority remains unchanged:

- `compilation_gate(result, GeometryGatePolicy())` determines whether the indexed mesh is acceptable.
- `GeometryGatePolicy.minimum_edge_length == 1e-5` is the compact-coordinate `tiny_edge` predicate.
- `MAXIMUM_CLEANUP_DISPLACEMENT_M == 5e-7` is the absolute physical displacement cap for every original vertex.
- The five existing attempt thresholds remain exactly `(1e-8, 3e-8, 1e-7, 3e-7, 5e-7)` metres.
- Physical distance uses XY directly and normalized Z multiplied by `effective_height_m`.

The compact-coordinate gate and physical displacement budget are intentionally separate metrics. An edge is a repair candidate because its current representative endpoints violate the canonical compact-coordinate predicate. Whether and how it may be welded is decided using physical displacement.

## 4. Architecture

The implementation remains inside the existing profiled mesh numeric-repair boundary.

### 4.1 Canonical edge classifier

A small internal classifier operates on the current representative mesh. For every non-degenerate triangle edge it computes:

- compact-coordinate edge length;
- physical edge length using `effective_height_m`;
- deterministic representative-group identities;
- one-sided relocation cost for each possible retained representative;
- symmetric midpoint relocation cost for every original vertex in both groups.

An edge enters the repair queue only when its compact-coordinate length is strictly below `GeometryGatePolicy().minimum_edge_length`. The repair code must use the policy value, not duplicate `1e-5` as an independent literal.

### 4.2 Representative groups

Each representative group owns:

- a deterministic retained representative identifier;
- the immutable set of original vertex indices in the group;
- the current representative coordinate;
- each original vertex's immutable raw coordinate;
- the maximum cumulative physical displacement from raw coordinate to proposed representative coordinate.

Union identity and representative coordinate are separate. A symmetric weld retains one deterministic representative identifier while relocating that representative's coordinate to the physical midpoint. The discarded representative points to the retained identifier, but no original coordinate is overwritten.

The retained identifier is selected by the existing deterministic representative ordering evaluated before relocation. If the existing ordering cannot be reused directly, the equivalent ordering is `(representative coordinate tuple, minimum original vertex index)`. The choice cannot depend on set iteration order, triangle order, process hash seed, or the newly computed midpoint.

### 4.3 Weld operation modes

Every selected canonical tiny edge is evaluated in this order:

1. `endpoint_collapse`
2. `symmetric_midpoint_weld`
3. typed rejection

`endpoint_collapse` preserves existing behavior. It is eligible when one representative group can be relocated onto the other endpoint and every original vertex in the moved group remains within both the current attempt threshold and `MAXIMUM_CLEANUP_DISPLACEMENT_M`. At the maximum attempt, this includes physical edges at or below `5e-7m`, subject to cumulative group displacement.

`symmetric_midpoint_weld` is eligible only when all of the following are true:

- The current edge violates the canonical compact-coordinate `tiny_edge` predicate.
- No deterministic one-sided endpoint collapse can satisfy the current attempt's cumulative displacement budget.
- The physical midpoint is finite.
- Every original vertex in the left group can move from its raw coordinate to the midpoint within the current attempt threshold and the absolute `5e-7m` cap.
- Every original vertex in the right group can move from its raw coordinate to the midpoint within the current attempt threshold and the absolute `5e-7m` cap.
- The two groups are distinct.

For a linear normalized-Z coordinate, the physical midpoint is represented by the coordinate-wise midpoint. Physical validation still scales the Z delta by `effective_height_m`; no normalized-coordinate shortcut may replace that validation.

An edge longer than `1e-6m` cannot be assumed nonrepairable solely from endpoint distance when groups already have displacement history. The authoritative decision is the per-original-vertex check against the proposed midpoint. The r87 `>2cap` fixture must demonstrate the simple two-singleton case where midpoint movement exceeds `5e-7m` for both endpoints.

### 4.4 Fixed-point loop

After every successful endpoint collapse or symmetric midpoint weld, the implementation must:

- remap all triangles through current representative groups;
- remove triangles whose remapped indices are degenerate;
- rebuild the complete representative edge set;
- recompute compact and physical metrics from current representative coordinates;
- deterministically select the next canonical tiny edge;
- repeat until no canonical tiny edge remains or a fail-closed condition occurs.

The edge queue must not be reused after a weld. Rebuilding is mandatory because each weld can create a new sub-threshold representative edge.

Candidate ordering is deterministic by:

```text
compact edge length,
physical edge length,
left representative coordinate,
right representative coordinate,
left minimum original index,
right minimum original index
```

Endpoint orientation is canonicalized using the same representative ordering before evidence is emitted.

## 5. Attempt semantics and evidence migration

The existing maximum of five attempt records is preserved. No sixth synthetic attempt is introduced.

For each threshold, one attempt may contain multiple ordered weld-operation records. The threshold is the maximum permitted cumulative physical displacement per original vertex for that attempt, additionally capped by `MAXIMUM_CLEANUP_DISPLACEMENT_M`.

The existing repair evidence schema migrates additively from `arr.maas.profiled_mesh_numeric_repair.v1` to `arr.maas.profiled_mesh_numeric_repair.v2` when symmetric-weld fields are present. Readers must accept both versions:

- v1 means endpoint-collapse evidence without typed per-operation records.
- v2 retains all v1 top-level fields and adds bounded operation records and typed symmetric-weld rejection details.
- A v2 producer always emits exactly five attempt records when numeric repair is attempted across the complete threshold ladder, including attempts that cannot produce a mesh.
- Existing top-level `collapse_count` remains the total number of successful union operations in the attempt.
- Existing `max_chain_displacement_m` remains the maximum cumulative physical displacement over every original vertex represented in the attempt.
- Existing `selected_as_final` remains true for at most one attempt.

Each bounded operation record contains only:

- `operation_type`: `endpoint_collapse` or `symmetric_midpoint_weld`;
- canonical endpoint representative indices;
- bounded original-group sizes;
- midpoint coordinate as three finite numeric values for a symmetric weld;
- left and right group maximum cumulative displacement in metres;
- resulting combined-group maximum cumulative displacement in metres;
- compact and physical edge lengths before the operation;
- operation status: `applied` or `rejected`;
- typed rejection code when rejected.

Operation evidence is capped at 24 records per attempt. If more operations occur, evidence adds `operation_record_count`, `operation_records_truncated=true`, and aggregate counts by operation type/status. Truncation affects diagnostics only and cannot affect repair execution or gate results.

Coordinates are mesh-local numeric evidence, not parcel/provider payloads. Values must be finite and passed through the existing bounded sanitizer. No source prompt, provider body, URL, secret, candidate prose, or unrestricted nested payload may enter this evidence.

## 6. Data flow

1. Floorwise profiled legal clipping produces an indexed mesh.
2. Raw canonical compilation and `compilation_gate` run unchanged.
3. Numeric repair is eligible only when raw gate codes remain within the existing numeric-repairable set. Structural failures do not enter weld logic.
4. For each of the five thresholds, repair starts from the immutable raw indexed mesh and fresh representative groups.
5. The fixed-point loop classifies current canonical tiny edges, prefers endpoint collapse, and uses symmetric midpoint weld only when endpoint collapse cannot satisfy the current displacement budget but midpoint relocation can.
6. The attempt compacts the representative mesh deterministically.
7. The complete canonical compiler and `compilation_gate` rerun on the compacted mesh.
8. A gate-clean result must preserve raw component count and all structural metrics before it can become `certified_vertices` and `certified_triangles`.
9. The selected certified mesh is converted to emitted surfaces.
10. Emitted component volumes and counts are remeasured.
11. Floor-midplane topology, area, containment, symmetric difference, and Hausdorff certificates rerun unchanged.
12. Source bridge materialization, legal projection, capacity, parking, program scoring, final VLM, and selection continue unchanged.
13. Any failure is propagated through the existing terminal certificate, candidate report, stage outcome, and outcome graph.

No authority may certify pre-weld CSG inputs in place of the emitted repaired mesh.

## 7. Invariants

The following invariants are mandatory:

- The raw vertex and triangle payload is immutable for all five attempts.
- Every attempt starts from the same raw payload, not a prior attempt's output.
- Every original vertex maps to exactly one current representative group.
- Every representative group retains the complete immutable membership of its original vertices.
- Every original vertex's cumulative physical displacement is measured from its raw coordinate, never from the preceding representative coordinate.
- No original vertex exceeds the current attempt threshold or `5e-7m`.
- Symmetric weld never runs when a valid endpoint collapse is available under the same attempt budget.
- Representative identity is deterministic and independent of iteration order.
- Triangle and edge rebuilding reaches a fixed point or fails with a typed bounded reason.
- Degenerate remapped triangles may be removed; disappearance or merger of a raw connected component remains a hard failure.
- Component count, watertightness, closed-solid status, manifold status, outward normals, and kernel self-intersection evidence must pass after repair.
- Canonical `compilation_gate` must return no issue codes before the mesh is selectable as a numeric repair.
- A post-repair `tiny_face` is not accepted or converted into success.
- Emitted-surface and downstream authority gates remain unchanged.
- A clean numeric repair is not equivalent to a complete candidate hard pass.

## 8. Error handling

### `symmetric_weld_displacement_exceeded`

This code is emitted when a canonical tiny edge cannot use endpoint collapse and at least one original vertex in either representative group would exceed `MAXIMUM_CLEANUP_DISPLACEMENT_M` at the proposed midpoint. The attempt returns no candidate mesh and fails closed. Because later attempts cannot exceed the same absolute cap, the repair may preserve the remaining attempt evidence as rejected diagnostics but cannot certify that edge.

When midpoint displacement exceeds only the current lower threshold but remains within the absolute cap, the current attempt records `symmetric_weld_threshold_not_reached`; the next existing threshold may retry from the immutable raw mesh. This diagnostic is not a terminal repair code.

### Other typed failures

- `symmetric_weld_nonfinite_midpoint`: midpoint or displacement is non-finite.
- `symmetric_weld_same_group`: the selected edge resolves to one representative group; the edge set is rebuilt rather than mutated.
- `numeric_repair_displacement_exceeded`: retained for endpoint-collapse chain overflow and compatibility.
- `numeric_repair_component_count_mismatch`: unchanged hard failure after canonical revalidation.
- Existing canonical gate issue codes, including `tiny_edge` and `tiny_face`, remain authoritative when a completed attempt still fails.

Unexpected internal inconsistency must return typed failed repair evidence. It must not return the partially mutated representative mesh.

## 9. Testing strategy

Tests use the real canonical gate wherever the assertion concerns acceptance. Mocking is limited to evidence propagation boundaries that cannot otherwise isolate serialization behavior.

### 9.1 Closed-manifold symmetric weld

Construct a small closed manifold indexed solid with one compact-coordinate tiny edge whose physical length is greater than the endpoint relocation budget for the selected attempt but whose midpoint keeps both singleton endpoints within budget. Assert:

- endpoint collapse is not selected;
- symmetric midpoint weld is selected;
- the deterministic retained representative is relocated to the midpoint;
- every original vertex remains within budget;
- the repaired mesh remains closed, watertight, manifold, outward-normal valid, and canonical-gate clean.

### 9.2 Cumulative chain budget

Construct two representative groups with prior weld displacement. Make the current edge's endpoint midpoint appear locally eligible while one original group member would exceed the cumulative cap. Assert `symmetric_weld_displacement_exceeded`, no certified mesh, and exact left/right group maximum displacement evidence.

### 9.3 Greater-than-two-cap nonrepairable edge

Use singleton endpoints separated by more than `1e-6m` physically while retaining compact-coordinate length below the canonical `1e-5` threshold. Assert midpoint movement exceeds `5e-7m`, typed rejection survives, and no later threshold certifies the mesh.

### 9.4 Determinism

Run the same mesh with permuted triangle order and repeat the repair multiple times. Assert identical retained representative identity, midpoint, operation order, compacted vertices/triangles, hashes, attempt evidence, and final gate result.

### 9.5 Component preservation

Use a valid multi-component closed mesh where one component has an eligible edge. Assert both components survive with identical component count. Add a case where welding would merge or erase component authority and assert hard failure.

### 9.6 Canonical gate alignment

Use `GeometryGatePolicy().minimum_edge_length` to create edges immediately below and at the threshold. Assert only the strictly-below edge is classified as canonical tiny. Assert the repaired output is accepted only when the real `compilation_gate` no longer emits `tiny_edge` or another issue.

### 9.7 Endpoint precedence

Create an edge for which one-sided endpoint collapse is cumulatively within the current threshold. Assert endpoint collapse remains selected and no symmetric operation is recorded.

### 9.8 Tiny-face and structural non-relaxation

Assert a post-repair `tiny_face`, nonmanifold mesh, non-watertight mesh, self-intersection failure, or component mismatch remains rejected with its original gate code and cannot be masked by symmetric-weld success.

### 9.9 Full authority revalidation

Pass a canonical-clean symmetric weld through floorwise profiled clip and source bridge. Assert emitted component measurement, floor topology, area, containment, symmetric difference, and Hausdorff checks execute against the repaired surfaces. Include a clean mesh that then fails Hausdorff and remains terminal.

### 9.10 Sanitizer and propagation

Assert v2 operation evidence survives:

- profiled clip failure witness;
- source bridge terminal failure sink;
- candidate-generation terminal record;
- `StageOutcome` evidence;
- outcome-graph observation.

Assert operation records are capped, truncation is typed, midpoint contains exactly three finite numbers, endpoint pairs contain exactly two bounded indices, and arbitrary nested data is removed.

### 9.11 Five-attempt compatibility

Assert every complete numeric repair emits exactly five ordered attempt records with the existing thresholds. Assert at most one `selected_as_final`, v1 evidence remains readable, and v2 retains all existing top-level fields.

## 10. r88 diagnostic acceptance

r88 is a measured diagnostic, not a guaranteed success run. It uses the same live benchmark controls as r87 and a new output directory ending in `book-program-portfolios-legal-archive-target5-r88`.

The acceptance report must record:

- command and runtime;
- evaluated, compiled, materialized, clean, program-pass, combined-hard-pass, final-VLM, and selected counts;
- raw and post-repair gate-code histograms;
- endpoint-collapse and symmetric-midpoint operation counts;
- every typed symmetric rejection count;
- component/manifold/watertight outcomes;
- immediate downstream rejection for every newly canonical-clean repair;
- provider cache, paid request, 429, and cooldown context;
- absolute board, witness, summary, and legal-archive PNG paths.

Minimum implementation acceptance is focused test success plus truthful r88 evidence showing unchanged hard gates. r88 may remain `1/5`. An increased clean or downstream count is useful evidence but is not required to claim that the implementation obeys this contract.

No result may be described as `5/5`, complete, or competition-grade unless five distinct candidates independently pass every existing hard gate and the recorded final selection contract.

## 11. Rollout

1. Implement behind the existing numeric-repair entry point; do not add a parallel materialization path.
2. Land focused tests before enabling symmetric weld in production repair selection.
3. Preserve v1 evidence reading and emit v2 only when the new producer fields are available.
4. Run focused geometry and propagation suites.
5. Review the exact staged diff for only numeric-repair, profiled-clip, propagation, and focused-test scope.
6. Run r88 once after focused review.
7. Compare r88 to the frozen r85-r87 checkpoint without changing thresholds in response to the result.

## 12. Rollback

Rollback disables selection of `symmetric_midpoint_weld` while retaining:

- the existing endpoint-collapse path;
- the five thresholds;
- v1/v2 evidence readers;
- typed evidence already persisted in artifacts;
- every canonical and downstream gate.

Rollback must not delete or reinterpret historical v2 evidence. A v2 record remains an immutable report of the operation executed in that run. No database or artifact migration is required because the schema change is additive and persisted JSON readers accept both versions.

## 13. Success and non-claims

The design succeeds when symmetric midpoint welding is deterministic, cumulatively bounded per original vertex, fully revalidated, typed on failure, and observable through terminal artifacts without changing any acceptance threshold.

This specification does not claim:

- that six budget-eligible r87 witnesses are actually repairable;
- that a repaired mesh will pass Hausdorff or another authority gate;
- that r88 will improve the funnel;
- that r88 will select five candidates;
- that any current output is competition-grade.
