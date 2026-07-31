# Shared Floor Full-Flow MASS Smoke Design

## Goal

Produce one architectural, multi-storey MASS whose PNU, legal envelope, floor
plates, FAR, parking, typed GeometryProgram, compiler geometry, MASS VLM review,
selection and elevation handoff share one immutable evidence identity.

## Verified failure

The current compiler and capacity path accepts a thin annular sculpture as a
building. `source_bridge._mesh_section_polygon()` polygonizes the outer and
inner section rings, then `unary_union()` fills the inner void. Capacity and
parking subsequently sample at most three `SourceVolume` bands as if they were
inhabitable floors. Elevation invents guides every 3.3 m from mesh bounds.

## Design

1. Preserve nested section voids when converting compiled mesh sections to
   `SourceMass`.
2. Materialize one `arr.maas.shared_floor_contract.v1` after legal generation.
   Every plate records floor/bottom/top height, legal and occupied geometry,
   gross/usable area, clear-depth evidence, support ratio and failures.
3. Reject plates without a usable clear-depth core and upper plates without
   adequate support. A thin ring/rib/sculpture must fail; a five-storey block,
   courtyard or sufficiently deep wing may pass.
4. Compute floor count, total floor area, FAR and capacity utilization only
   from accepted contract plates. Capacity, downstream law/parking and
   elevation must carry the same `floor_contract_hash`.
5. Product acceptance requires the shared-floor hard pass. Compiler mesh
   validity remains necessary but is no longer sufficient.
6. Elevation runs only for a MASS that passed the shared-floor and downstream
   gates. Its floor guides come from the exact plate elevations.
7. A bounded smoke entrypoint may author a small candidate set in one LLM
   response, run deterministic gates, send only the best hard-pass MASS to one
   paid MASS VLM call, freeze that exact identity, then generate elevation.
   No large portfolio VLM batch is permitted in smoke mode.

## Testing

- RED: thin annular sculpture currently passes compiler/capacity; shared-floor
  gate must reject it with `insufficient_clear_floor_depth`.
- GREEN: five-storey rectangular building must expose five continuous plates,
  meet the requested FAR band and pass support/clear-depth checks.
- Regression: nested mesh section void area remains a void.
- Integration: capacity, downstream parking and elevation expose the same
  floor-contract hash and exact floor guides.
- Runtime: generate one local hard-pass MASS, optionally make one paid MASS VLM
  request, then verify `/design/language` at port 5178 with zero console/request
  errors.

## Cost and safety

No paid call occurs before deterministic hard gates pass. Smoke mode permits at
most one paid MASS VLM request. GPT Image elevation is excluded from the first
MASS acceptance smoke and may run only with separate explicit approval.
