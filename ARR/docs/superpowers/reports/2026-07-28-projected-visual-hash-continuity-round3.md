# Projected Visual Hash Continuity — Round 3

## Final Trust-Boundary Corrections

Independent review found that the projected visual certificate was valid while
its archived capacity compilation metadata could still be altered. A modified
stored capacity hash or a 100 m stored Z bound could therefore control physical
render scale without changing the visual certificate.

Projected archive hydration now:

- freshly compiles the archived capacity `GeometryProgram`;
- requires the stored capacity geometry hash to equal the fresh compilation;
- requires critical stored metrics, including bounds and solid validity, to
  equal the fresh compilation;
- exposes the fresh capacity hash and fresh capacity metrics as the sole
  physical render/elevation authority.

The shared single-execution provenance resolver also now requires:

- `source_mass_index == 1` for every `single-execution:*` edge;
- `source_mass_index == 0` for every terminal execution without an origin.

## TDD Evidence

Four RED tests demonstrated that the previous implementation accepted:

- a replaced stored capacity geometry hash;
- stored capacity bounds changed to 100 m;
- an intermediate single-execution edge changed from mass 1 to mass 2;
- a terminal no-origin execution changed from mass index 0 to 1.

All four passed after the trust-boundary changes.

## Fresh Verification

```text
python manage.py test \
  design.test_maas_single_execution \
  design.test_maas_outcome_render_memory \
  design.test_maas_flow_regressions

Found 63 test(s).
Ran 63 tests in 6.919s
OK
```
