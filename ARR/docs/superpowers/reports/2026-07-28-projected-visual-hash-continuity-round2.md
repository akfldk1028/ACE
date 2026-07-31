# Projected Visual Hash Continuity — Round 2

## Review Findings Addressed

1. Certified projected meshes store Z in normalized coordinates. Exact replay
   now derives the physical Z origin and height from the validated capacity
   compilation bounds, creates a physical render/elevation mesh, and retains
   the certified visual hash as its immutable identity. Metrics declare both
   coordinate spaces and the physical scale.
2. Single-execution replay validates the requested and every intermediate
   program, passport, manifest, and geometry identity before any legacy
   capacity early return. Missing provenance, cycles, incomplete source
   identities, and tampering fail closed.
3. HTTP and CLI now share the same bounded single-execution provenance
   resolver. CLI supports exact replay chains and the same missing, cycle, and
   tamper rejection behavior as HTTP.
4. Production projected archive hydration retains
   `capacity_geometry_hash` separately from the certified visual hash.
5. Render observations require a schema-valid certificate, a nonempty
   projected surface tuple, exact projected surface count, a recomputed Task-1
   visual hash, and matching board render evidence.

## TDD Evidence

The Round 2 RED tests reproduced:

- flattened normalized-Z elevation (`front` projected height 1.0 instead of
  5.0 m);
- bogus passport program hash accepted by the capacity-hash early return;
- CLI routing a `single-execution:*` run to the portfolio archive reader;
- CLI missing provenance, cycle, and intermediate tamper not receiving the
  shared fail-closed checks;
- missing production `capacity_geometry_hash`;
- fabricated empty certified surface evidence accepted by the outcome graph.

All eight tests passed after the minimal implementation.

## Fresh Verification

```text
python manage.py test \
  design.test_maas_single_execution \
  design.test_maas_outcome_render_memory \
  design.test_maas_flow_regressions

Found 59 test(s).
Ran 59 tests in 6.342s
OK
```

This run includes the previously failing authored visual
board/archive/elevation regression after the independently owned Task 1
certificate handoff landed.
