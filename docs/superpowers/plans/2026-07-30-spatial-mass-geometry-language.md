# Spatial MASS Geometry Language Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make direct LLM-authored GeometryPrograms reliably express thickened plates, arbitrary connected interlocking discs, profile sweeps, and generic surface-to-solid shells from the one canonical UnitBox authority.

**Architecture:** Preserve the certified manifold solid compiler and extend it in two layers. First, expose existing generic solid operators consistently across author, mutation, compiler-trace, and VLM contracts. Second, add typed `surface` intermediates and one `shell_thicken` conversion boundary while keeping every final root a connected closed solid.

**Tech Stack:** Python 3, Django `SimpleTestCase`, dataclasses, NumPy, manifold3d, existing MAAS GeometryProgram AST/compiler, existing OpenAI LLM/VLM adapters.

## Global Constraints

- Production geometry has exactly one canonical `1/1 UnitBox` BaseVolume authority.
- Do not create `Qatar`, `OMA`, `SANAA`, museum, library, or other named operators, recipes, selectors, or quotas.
- A plane used as MASS must become a positive-thickness closed solid before it can be a final root.
- Final geometry must remain connected, watertight, manifold, and positive-volume.
- `circularize`, `matrix_array`, `profile_sweep_3d`, `attach`, and `bridge` remain generic typed operations.
- Every executable compiler parameter must be exposed in the author and VLM parameter contract; unknown JSON-only parameters fail closed.
- Surface values cannot enter solid-only Boolean, pattern, composition, law, floor, render, or final-root operations.
- No paid LLM, image, or VLM provider call is allowed in this plan.
- The local ArchDaily Qatar National Library asset is later VLM evidence, not a geometry recipe.
- Work in the isolated `D:\Data\25_ACE-spatial-mass` worktree without staging
  unrelated user files. The source checkout remains untouched.

## File Structure

- Modify `ARR/backend/design/maas/geometry_language/mutation.py`: one authoritative executable parameter vocabulary.
- Modify `ARR/backend/design/maas/geometry_language/llm_adapter.py`: direct-author prompt/schema and body-language classification.
- Modify `ARR/backend/design/maas/geometry_language/vlm_adapter.py`: VLM-readable operator effects.
- Modify `ARR/backend/design/maas/geometry_language/ast.py`: value kinds, surface/conversion operators, type validation.
- Create `ARR/backend/design/maas/geometry_language/surface_geometry.py`: immutable bounded-surface data and normalized validation.
- Modify `ARR/backend/design/maas/geometry_language/compiler.py`: evaluate surface values and convert them to manifold solids.
- Modify `ARR/backend/design/maas/geometry_language/__init__.py`: export only the new public surface value type needed by callers.
- Create `ARR/backend/design/test_maas_spatial_mass_language.py`: focused direct-authorship, type, compile, and regression tests.
- Modify `ARR/backend/design/test_maas_geometry_language.py`: author/VLM contract integration assertions.
- Create, then modify `ARR/backend/design/test_maas_strict_unitbox_operators.py`:
  preserve exact UnitBox and kernel invariants.

---

### Task 0: Restore the already-authored generic solid operators

**Why this prerequisite exists:** The original dirty checkout contains the
tested `circularize`, `matrix_array`, and `profile_sweep_3d` implementation,
but those bounded hunks and their standalone strict test were not present in
commit `317bcd6`. Task 1 must not advertise operators that the isolated
compiler cannot execute.

**Files:**
- Modify selectively: `ARR/backend/design/maas/geometry_language/ast.py`
- Modify selectively: `ARR/backend/design/maas/geometry_language/compiler.py`
- Create: `ARR/backend/design/test_maas_strict_unitbox_operators.py`
- Source only: the corresponding files in `D:\Data\25_ACE`

- [ ] **Step 1: Add the strict test unchanged and verify RED**

Copy the complete standalone test from the source checkout. Run:

```powershell
python manage.py test design.test_maas_strict_unitbox_operators --verbosity 2
```

Expected: import or validation failures because the three operators are absent.

- [ ] **Step 2: Transplant only the bounded AST hunks**

Add `isfinite`; register `circularize` and `profile_sweep_3d` as modifiers and
`matrix_array` as a pattern; add only their parameter validation plus
`_finite_vector` and `_affine_matrix4`.

Exclude `legal_section_clip`, execution contracts, capacity replay, schema
transport, and every other unrelated dirty-checkout change.

- [ ] **Step 3: Transplant only the bounded compiler hunks**

Add:

- trace rows for explicit `matrix_array` matrices and `profile_sweep_3d` path
  metrics;
- special dispatch for `circularize` and `profile_sweep_3d`;
- `_circularize`;
- the leading `matrix_array` pattern branch;
- `_profile_sweep_3d`.

Reuse the clean compiler's existing imports and helpers. Exclude mesh
canonicalization/repair, gate changes, law clipping, capacity replay,
host-subset Boolean optimization, and `_evaluate_node(..., node_map=...)`.

- [ ] **Step 4: Verify the restored executable baseline**

```powershell
python -m py_compile design/maas/geometry_language/ast.py design/maas/geometry_language/compiler.py design/test_maas_strict_unitbox_operators.py
python manage.py test design.test_maas_strict_unitbox_operators --verbosity 2
python manage.py test design.test_maas_geometry_language --verbosity 1
git diff --check -- ARR/backend/design/maas/geometry_language/ast.py ARR/backend/design/maas/geometry_language/compiler.py ARR/backend/design/test_maas_strict_unitbox_operators.py
```

- [ ] **Step 5: Commit Task 0**

```powershell
git add -- ARR/backend/design/maas/geometry_language/ast.py ARR/backend/design/maas/geometry_language/compiler.py ARR/backend/design/test_maas_strict_unitbox_operators.py docs/superpowers/plans/2026-07-30-spatial-mass-geometry-language.md
git commit -m "feat(maas): restore generic spatial operators"
```

---

### Task 1: Expose the existing generic plate/disc language

**Files:**
- Modify: `ARR/backend/design/maas/geometry_language/mutation.py:145-285`
- Modify: `ARR/backend/design/maas/geometry_language/llm_adapter.py:692-782`
- Modify: `ARR/backend/design/maas/geometry_language/llm_adapter.py:1206-1255`
- Modify: `ARR/backend/design/maas/geometry_language/vlm_adapter.py:41-85`
- Test: `ARR/backend/design/test_maas_geometry_language.py`

**Interfaces:**
- Consumes: existing `OPERATOR_PARAMETER_CONTRACTS`, `BOOLEAN_PARAMETERS`, `_author_prompt`, and `OPERATOR_EFFECTS`.
- Produces: executable contracts for `circularize`, `matrix_array`, `profile_sweep_3d`, `attach`, and `bridge`.

- [ ] **Step 1: Write the failing cross-contract test**

Add a test that names the production change that would make it fail:

```python
def test_direct_author_contract_exposes_existing_plate_disc_operators(self):
    expected = {
        "matrix4": {"matrix4"},
        "circularize": {"segments"},
        "matrix_array": {"matrices", "require_connected"},
        "profile_sweep_3d": {"path", "require_connected"},
        "attach": {
            "host_face", "anchor", "guest_extent",
            "engagement", "rotation_degrees",
        },
        "bridge": {"height", "height_ratio", "width", "width_ratio"},
    }
    prompt = geometry_llm_adapter._author_prompt({
        "program": "neighborhood_living",
        "instruction": "author one executable spatial mass",
    }, 1)
    for operator, parameters in expected.items():
        self.assertIn(operator, prompt)
        self.assertTrue(
            parameters.issubset(OPERATOR_PARAMETER_CONTRACTS[operator])
        )
        self.assertIn(operator, geometry_vlm_adapter.OPERATOR_EFFECTS)
```

Also assert `require_connected` is a Boolean parameter and `matrix4` and
`matrices` use the adapter's `structured_literal` value contract, which is
serialized as `structured_json` in the strict author schema.

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
python manage.py test design.test_maas_geometry_language.MaasGeometryLanguageTest.test_direct_author_contract_exposes_existing_plate_disc_operators --verbosity 2
```

Expected: FAIL because the parameter contracts and prompt/effect vocabulary
omit the operators or parameters.

- [ ] **Step 3: Add the exact executable parameter contracts**

Implement these entries in `mutation.py`:

```python
BOOLEAN_PARAMETERS = frozenset({
    "center", "bridge", "ground_spine", "require_connected",
})

OPERATOR_PARAMETER_CONTRACTS.update({
    "matrix4": frozenset({"matrix4"}),
    "circularize": frozenset({"segments"}),
    "matrix_array": frozenset({"matrices", "require_connected"}),
    "profile_sweep_3d": frozenset({"path", "require_connected"}),
    "attach": frozenset({
        "host_face", "anchor", "guest_extent",
        "engagement", "rotation_degrees",
    }),
    "bridge": frozenset({
        "z", "height", "height_ratio", "width", "width_ratio",
    }),
})
```

Add `matrices` to the structured-JSON parameter set used by the strict author
schema. Do not add a parameter that the compiler does not read.

- [ ] **Step 4: Make the author and VLM vocabularies agree**

Add the operators to the explicit author prompt and body-language
classification. Add effects such as:

```python
"circularize": (
    "derive a bounded positive-thickness elliptical plate from live bounds"
),
"matrix_array": (
    "place explicit affine instances and require a connected volumetric union"
),
"profile_sweep_3d": (
    "sweep the live positive section along a three-dimensional path"
),
"attach": (
    "engage a guest with a normalized live host face through real overlap"
),
"bridge": (
    "join two distinct solids with an embedded volumetric connector"
),
```

The prompt must call these generic capabilities and must not mention a named
building as an output target.

- [ ] **Step 5: Run focused and neighboring tests**

Run:

```powershell
python manage.py test design.test_maas_geometry_language design.test_maas_strict_unitbox_operators --verbosity 1
```

Expected: PASS with zero provider calls.

- [ ] **Step 6: Commit Task 1**

```powershell
git add -- ARR/backend/design/maas/geometry_language/mutation.py ARR/backend/design/maas/geometry_language/llm_adapter.py ARR/backend/design/maas/geometry_language/vlm_adapter.py ARR/backend/design/test_maas_geometry_language.py
git commit -m "feat(maas): expose generic plate disc operators"
```

---

### Task 2: Prove non-recipe interlocking plates through direct authorship

**Files:**
- Create: `ARR/backend/design/test_maas_spatial_mass_language.py`
- Modify only if the test exposes a real boundary defect:
  `ARR/backend/design/maas/creative_program_author.py`

**Interfaces:**
- Consumes: `authored_programs_from_payload`, canonical UnitBox normalization,
  `compile_geometry_program`.
- Produces: `direct_interlocking_plate_program() -> GeometryProgram` as a test
  fixture proving the production payload path.

- [ ] **Step 1: Write the direct-authorship test fixture**

Build one program without importing any creative recipe:

```python
def direct_interlocking_plate_program() -> GeometryProgram:
    thin_plate_matrix4 = [
        [4.0, 0.0, 0.0, -2.0],
        [0.0, 1.6, 0.0, -0.8],
        [0.0, 0.0, 0.25, -0.125],
        [0.0, 0.0, 0.0, 1.0],
    ]
    overlapping_arbitrary_xyz_matrices = [
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 0.573576, -0.819152, 0.0],
            [0.0, 0.819152, 0.573576, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        [
            [0.707107, 0.0, -0.707107, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.707107, 0.0, 0.707107, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
    ]
    unitbox = GeometryNode(
        "unitbox", "primitive", "box",
        parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
        semantic_role="base_seed",
    )
    plate = GeometryNode(
        "plate", "transform", "matrix4", inputs=("unitbox",),
        parameters={"matrix4": thin_plate_matrix4},
        semantic_role="occupied_slab",
    )
    disc = GeometryNode(
        "disc", "modifier", "circularize", inputs=("plate",),
        parameters={"segments": 32},
        semantic_role="envelope",
    )
    assembly = GeometryNode(
        "assembly", "pattern", "matrix_array", inputs=("disc",),
        parameters={
            "matrices": overlapping_arbitrary_xyz_matrices,
            "require_connected": True,
        },
        semantic_role="envelope",
    )
    return GeometryProgram(
        nodes=(unitbox, plate, disc, assembly),
        root_id="assembly",
        name="direct_interlocking_plate",
    )
```

Use explicit overlapping x/y/z rotation matrices. Keep every scale positive.

- [ ] **Step 2: Write the failing production-payload assertion**

```python
def test_payload_authorship_accepts_unnamed_interlocking_plate_program(self):
    source = direct_interlocking_plate_program()
    payload = {
        "schema_version": "arr.maas.geometry_llm_author_cache.v3",
        "compiled_programs": [source.to_dict()],
        "response_id": "fixture-no-provider",
    }
    authored = authored_programs_from_payload(
        payload,
        expected_count=1,
        program_context={"pnu": "fixture"},
    )
    result = compile_geometry_program(authored[0].program)

    self.assertEqual(result.status, "compiled", result.issues)
    self.assertTrue(exactly_one_canonical_unitbox(result.program))
    self.assertEqual(result.metrics["component_count"], 1)
    self.assertTrue(result.metrics["watertight"])
    self.assertTrue(result.metrics["manifold"])
    self.assertEqual(
        [node.operator for node in result.program.topological_nodes()],
        ["box", "matrix4", "circularize", "matrix_array"],
    )
```

- [ ] **Step 3: Run the test and verify RED or existing GREEN**

Run:

```powershell
python manage.py test design.test_maas_spatial_mass_language.DirectPlateAuthorshipTest --verbosity 2
```

If it passes immediately, retain it as a characterization test because the
production direct-authorship boundary already supports the exact behavior.
If it fails, the accepted fix scope is limited to payload parsing or UnitBox
normalization; do not add a recipe fallback.

- [ ] **Step 4: Add disconnected negative evidence**

Move one matrix beyond overlap and assert:

```python
self.assertEqual(result.status, "compile_failed")
self.assertEqual(result.issues[0].code, "disconnected_matrix_array")
```

- [ ] **Step 5: Run the focused test module**

```powershell
python manage.py test design.test_maas_spatial_mass_language --verbosity 1
```

Expected: connected direct payload passes; disconnected placement fails
closed; paid request count remains zero.

- [ ] **Step 6: Commit Task 2**

```powershell
git add -- ARR/backend/design/test_maas_spatial_mass_language.py ARR/backend/design/maas/creative_program_author.py
git commit -m "test(maas): prove direct interlocking plate authorship"
```

Do not stage `creative_program_author.py` if no production change was needed.

---

### Task 3: Add typed surface values to the AST

**Files:**
- Modify: `ARR/backend/design/maas/geometry_language/ast.py:19-84`
- Modify: `ARR/backend/design/maas/geometry_language/ast.py:350-530`
- Modify: `ARR/backend/design/test_maas_spatial_mass_language.py`

**Interfaces:**
- Consumes: `GeometryNode`, `GeometryProgram.validate()`, topological node
  order.
- Produces:
  - `GeometryValueKind = Literal["solid", "surface"]`
  - `geometry_node_output_kind(node) -> str`
  - `geometry_node_input_kinds(node) -> tuple[str, ...]`
  - surface operators `section_surface`, `loft_surface`,
    `host_face_surface`
  - conversion operator `shell_thicken`

- [ ] **Step 1: Write failing AST type tests**

Add tests for:

```python
def test_surface_node_cannot_be_program_root(self):
    program = program_with_root("section_surface")
    self.assertIn(
        "surface_root_not_allowed",
        {issue.code for issue in program.validate()},
    )

def test_surface_cannot_enter_solid_boolean(self):
    program = program_with_surface_input_to_union()
    self.assertIn(
        "geometry_value_kind_mismatch",
        {issue.code for issue in program.validate()},
    )

def test_shell_thicken_converts_surface_to_solid(self):
    program = program_with_section_surface_and_shell()
    self.assertEqual(program.validate(), ())
```

Also test that an unknown surface operator and a `shell_thicken` node with a
solid input reject.

- [ ] **Step 2: Run the AST tests and verify RED**

```powershell
python manage.py test design.test_maas_spatial_mass_language.SurfaceAstTypeTest --verbosity 2
```

Expected: FAIL because `surface` and `conversion` kinds do not exist.

- [ ] **Step 3: Add value-kind contracts**

Extend the AST constants:

```python
NODE_KINDS = frozenset({
    "primitive", "transform", "modifier", "boolean", "pattern",
    "composition", "macro", "surface", "conversion",
})

OPERATORS_BY_KIND["surface"] = frozenset({
    "section_surface", "loft_surface", "host_face_surface",
})
OPERATORS_BY_KIND["conversion"] = frozenset({"shell_thicken"})
```

Define output kinds:

```python
def geometry_node_output_kind(node: GeometryNode) -> str:
    return "surface" if node.kind == "surface" else "solid"
```

Define input contracts:

```python
def geometry_node_input_kinds(node: GeometryNode) -> tuple[str, ...]:
    if node.kind == "surface":
        return ("solid",)
    if node.operator == "shell_thicken":
        return ("surface",)
    return tuple("solid" for _ in node.inputs)
```

After unknown-input and topological checks, walk nodes in topological order,
compare each input node's output kind, and emit
`geometry_value_kind_mismatch`. Emit `surface_root_not_allowed` when the
root output kind is not `solid`.

- [ ] **Step 4: Add arity and parameter validation**

Require exactly one input for `surface` and `conversion`. Validate:

- `section_surface.section_controls`: 2..12 finite `[u, height_ratio]` pairs,
  strictly increasing `u`, first `u=0`, last `u=1`;
- `loft_surface.profiles`: 2..12 ordered profiles with finite normalized
  points;
- `host_face_surface.host_face`: east/west/north/south/top/bottom;
- `shell_thicken.thickness_ratio`: finite and in `[0.005, 0.25]`;
- `shell_thicken.side`: center/inward/outward;
- `shell_thicken.close_edges`: true.

Use explicit issue codes:

```text
invalid_surface_controls
invalid_surface_profile
unsupported_host_face
shell_thickness_out_of_bounds
unsupported_shell_side
open_shell_edges
```

- [ ] **Step 5: Run AST and existing geometry tests**

```powershell
python manage.py test design.test_maas_spatial_mass_language.SurfaceAstTypeTest design.test_maas_geometry_language --verbosity 1
```

Expected: PASS without changing existing solid program hashes.

- [ ] **Step 6: Commit Task 3**

```powershell
git add -- ARR/backend/design/maas/geometry_language/ast.py ARR/backend/design/test_maas_spatial_mass_language.py
git commit -m "feat(maas): type surface geometry values"
```

---

### Task 4: Model bounded surfaces independently of the kernel

**Files:**
- Create: `ARR/backend/design/maas/geometry_language/surface_geometry.py`
- Modify: `ARR/backend/design/maas/geometry_language/__init__.py`
- Modify: `ARR/backend/design/test_maas_spatial_mass_language.py`

**Interfaces:**
- Consumes: a live solid's six-value bounds and normalized surface parameters.
- Produces:

```python
Vec3 = tuple[float, float, float]

@dataclass(frozen=True)
class BoundedSurface:
    operator: str
    sections: tuple[tuple[Vec3, ...], ...]
    source_bounds: tuple[float, float, float, float, float, float]

    def validate(self) -> tuple[str, ...]: ...
```

Functions:

```python
section_surface_from_bounds(bounds, parameters) -> BoundedSurface
loft_surface_from_bounds(bounds, parameters) -> BoundedSurface
host_face_surface_from_bounds(bounds, parameters) -> BoundedSurface
```

- [ ] **Step 1: Write pure surface-construction tests**

Test deterministic section creation:

```python
surface = section_surface_from_bounds(
    (0.0, 0.0, 0.0, 20.0, 12.0, 8.0),
    {
        "span_axis": "x",
        "section_controls": [[0.0, 0.15], [0.5, 0.85], [1.0, 0.2]],
    },
)
self.assertEqual(len(surface.sections), 3)
self.assertEqual(surface.sections[0][0], (0.0, 0.0, 1.2))
self.assertEqual(surface.sections[0][1], (0.0, 12.0, 1.2))
self.assertEqual(surface.sections[-1][0], (20.0, 0.0, 1.6))
```

Test `loft_surface` preserves ordered normalized profiles and
`host_face_surface` returns exactly four bounded corner points on the selected
live face.

- [ ] **Step 2: Run pure tests and verify RED**

```powershell
python manage.py test design.test_maas_spatial_mass_language.BoundedSurfaceTest --verbosity 2
```

Expected: ERROR because `surface_geometry.py` does not exist.

- [ ] **Step 3: Implement the immutable surface module**

Use normalized parameters only. Convert them through live bounds inside the
three constructor functions. Reject:

- nonfinite points;
- fewer than two sections;
- inconsistent vertex count between adjacent sections;
- zero-length section edges;
- repeated consecutive sections; and
- points outside the live bounds beyond `1e-7`.

`BoundedSurface` contains no manifold3d object and is JSON-serializable through
`to_dict()`. This keeps AST/type testing separate from kernel execution.

- [ ] **Step 4: Export the public type**

Add only these exports:

```python
from .surface_geometry import BoundedSurface
```

Do not export fixture constructors as production architecture selectors.

- [ ] **Step 5: Run pure and import tests**

```powershell
python manage.py test design.test_maas_spatial_mass_language.BoundedSurfaceTest --verbosity 1
python -m py_compile design/maas/geometry_language/surface_geometry.py
```

Expected: PASS.

- [ ] **Step 6: Commit Task 4**

```powershell
git add -- ARR/backend/design/maas/geometry_language/surface_geometry.py ARR/backend/design/maas/geometry_language/__init__.py ARR/backend/design/test_maas_spatial_mass_language.py
git commit -m "feat(maas): model bounded architectural surfaces"
```

---

### Task 5: Compile surfaces through one shell-thickening boundary

**Files:**
- Modify: `ARR/backend/design/maas/geometry_language/compiler.py:180-280`
- Modify: `ARR/backend/design/maas/geometry_language/compiler.py:560-600`
- Modify: `ARR/backend/design/maas/geometry_language/compiler.py:2975-3165`
- Modify: `ARR/backend/design/test_maas_spatial_mass_language.py`
- Modify: `ARR/backend/design/test_maas_strict_unitbox_operators.py`

**Interfaces:**
- Consumes: `BoundedSurface`, typed AST validation, live input solid bounds.
- Produces:

```python
_surface_node(node, source_solid) -> BoundedSurface
_shell_thicken(surface, parameters, node_id) -> manifold3d.Manifold
```

- [ ] **Step 1: Write the shell compilation RED test**

Construct:

```text
UnitBox
  -> matrix4(site-like 20 x 12 x 8 positive solid)
  -> section_surface(three controls)
  -> shell_thicken(thickness_ratio=0.04, side=center, close_edges=true)
```

Assert:

```python
self.assertEqual(result.status, "compiled", result.issues)
self.assertTrue(exactly_one_canonical_unitbox(result.program))
self.assertEqual(result.metrics["component_count"], 1)
self.assertTrue(result.metrics["closed_solid"])
self.assertTrue(result.metrics["watertight"])
self.assertTrue(result.metrics["manifold"])
self.assertGreater(result.metrics["volume"], 0.0)
```

Assert the compiler trace contains a `surface` row with no fake volume and a
`shell_thicken` row with thickness in live meters.

- [ ] **Step 2: Run the compilation test and verify RED**

```powershell
python manage.py test design.test_maas_spatial_mass_language.SurfaceShellCompileTest.test_section_surface_thickens_to_closed_mass --verbosity 2
```

Expected: FAIL because the compiler assumes every cached value is a manifold
solid and calls `.is_empty()` on it.

- [ ] **Step 3: Teach the evaluator about typed values**

Change the evaluation cache to:

```python
cache: dict[str, Any] = {}
```

For a surface result:

- call `BoundedSurface.validate()`;
- do not call manifold `.is_empty()`, `.status()`, `.num_tri()`, or
  `.volume()`;
- write `output_value_kind="surface"` and section/point counts to the trace.

For a solid result, retain the existing kernel checks unchanged.

At the final root, assert the value is a manifold solid even though AST
validation already rejects surface roots.

- [ ] **Step 4: Implement surface construction dispatch**

In `_evaluate_node`:

```python
if node.kind == "surface":
    return _surface_node(node, inputs[0]), ["live_bounds", node.operator]
if node.kind == "conversion" and node.operator == "shell_thicken":
    return _shell_thicken(
        inputs[0], node.parameters, node.id
    ), ["surface_offset", "edge_closure", "segment_hulls", "union"]
```

`_surface_node` must dispatch only to the three constructors from
`surface_geometry.py`.

- [ ] **Step 5: Implement a closed positive-thickness shell**

For each adjacent pair of equal-vertex-count sections:

1. compute deterministic section tangents;
2. compute a stable normal, falling back to the least-parallel global axis;
3. offset both sections by half/full thickness according to
   `center|inward|outward`;
4. create one convex segment with
   `m3d.Manifold.hull_points([*lower_start, *upper_start, *lower_end, *upper_end])`;
5. Boolean-union adjacent segments.

Thickness in meters is:

```python
live_scale = min(
    maxx - minx,
    maxy - miny,
    maxz - minz,
)
thickness_m = live_scale * thickness_ratio
```

Reject an empty segment, kernel error, self-intersection, disconnected union,
or non-positive thickness with explicit `GeometryCompileError` codes.

- [ ] **Step 6: Write and pass negative kernel tests**

Cover:

- `thickness_ratio=0`;
- `close_edges=false`;
- repeated/collapsed surface section;
- a sharp control arrangement that self-intersects after thickening; and
- a legal surface node followed by solid-only `union`.

Expected failures are `invalid_program` when caught by AST validation and
`compile_failed` when only the kernel can detect the invalid shell.

- [ ] **Step 7: Run geometry regression suites**

```powershell
python manage.py test design.test_maas_spatial_mass_language design.test_maas_strict_unitbox_operators design.test_maas_geometry_language --verbosity 1
```

Expected: PASS. Existing solid program and geometry hash fixtures remain
unchanged.

- [ ] **Step 8: Commit Task 5**

```powershell
git add -- ARR/backend/design/maas/geometry_language/compiler.py ARR/backend/design/test_maas_spatial_mass_language.py ARR/backend/design/test_maas_strict_unitbox_operators.py
git commit -m "feat(maas): thicken bounded surfaces into mass"
```

---

### Task 6: Expose surface authorship without named form recipes

**Files:**
- Modify: `ARR/backend/design/maas/geometry_language/mutation.py`
- Modify: `ARR/backend/design/maas/geometry_language/llm_adapter.py`
- Modify: `ARR/backend/design/maas/geometry_language/vlm_adapter.py`
- Modify: `ARR/backend/design/test_maas_geometry_language.py`
- Modify: `ARR/backend/design/test_maas_spatial_mass_language.py`

**Interfaces:**
- Consumes: typed surface AST and compiler from Tasks 3-5.
- Produces: strict author schema and VLM graph notes for surface construction
  and shell conversion.

- [ ] **Step 1: Write failing author-schema tests**

Assert that `_strict_author_node_schema()` includes:

- kind `surface` with exactly one input and operators
  `section_surface|loft_surface|host_face_surface`;
- kind `conversion` with exactly one input and operator `shell_thicken`;
- structured JSON for `section_controls` and `profiles`;
- enum values for `span_axis`, `host_face`, and `side`;
- Boolean `close_edges`; and
- numeric `thickness_ratio`.

Also parse one serialized direct surface program through the same strict
response parser used by `author_geometry_programs_with_openai`, without making
a provider call.

- [ ] **Step 2: Run and verify RED**

```powershell
python manage.py test design.test_maas_geometry_language.MaasGeometryLanguageTest.test_author_schema_exposes_typed_surface_to_shell_path --verbosity 2
```

Expected: FAIL because the schema variants do not include the new kinds.

- [ ] **Step 3: Add exact surface parameter contracts**

```python
OPERATOR_PARAMETER_CONTRACTS.update({
    "section_surface": frozenset({"span_axis", "section_controls"}),
    "loft_surface": frozenset({"profiles"}),
    "host_face_surface": frozenset({"host_face", "inset_ratio"}),
    "shell_thicken": frozenset({
        "thickness_ratio", "side", "close_edges",
    }),
})
```

Add exact enum and Boolean contracts. Do not accept arbitrary prose roles as
parameters.

- [ ] **Step 4: Add strict schema variants and prompt rules**

The prompt must explain:

- surface nodes are intermediate, never roots;
- every surface path ends in `shell_thicken`;
- zero-thickness planes are forbidden;
- all controls are normalized to the live BaseVolume;
- a shell must still pass the unchanged connected/watertight/manifold gate;
  and
- named buildings are precedent capability evidence, not requested output.

- [ ] **Step 5: Add VLM-readable effects**

Add:

```python
"section_surface": "derive a bounded normalized sectional surface",
"loft_surface": "derive a bounded surface through ordered section profiles",
"host_face_surface": "derive a bounded sub-surface from a live solid face",
"shell_thicken": (
    "convert a bounded surface into a positive-thickness closed solid"
),
```

Graph notes must report `output_value_kind`, thickness, side, and edge closure
without claiming the shell is occupiable; spatial evidence belongs to the next
same-parcel plan.

- [ ] **Step 6: Run author/VLM and compiler tests**

```powershell
python manage.py test design.test_maas_spatial_mass_language design.test_maas_geometry_language --verbosity 1
```

Expected: PASS with provider calls patched to fail if invoked.

- [ ] **Step 7: Commit Task 6**

```powershell
git add -- ARR/backend/design/maas/geometry_language/mutation.py ARR/backend/design/maas/geometry_language/llm_adapter.py ARR/backend/design/maas/geometry_language/vlm_adapter.py ARR/backend/design/test_maas_geometry_language.py ARR/backend/design/test_maas_spatial_mass_language.py
git commit -m "feat(maas): expose typed surface shell authorship"
```

---

### Task 7: Verify the complete MASS language checkpoint

**Files:**
- Modify: `docs/ai-session-memory/MAAS_LAWFUL_DIVERSE_LLM_PILOT_20260730.md`
- Modify: `docs/ai-session-memory/maas-mass-flow/00_READ_FIRST.md`
- Modify: `docs/ai-session-memory/maas-mass-flow/current-checkpoint.json`

**Interfaces:**
- Consumes: all implementation and test evidence from Tasks 1-6.
- Produces: a restart-safe checkpoint and exact next-plan boundary.

- [ ] **Step 1: Run the full relevant backend verification**

```powershell
python manage.py test design.test_maas_spatial_mass_language design.test_maas_strict_unitbox_operators design.test_maas_geometry_language design.test_maas_creative_program_author design.test_maas_creative_floor_portfolio_command --verbosity 1
python -m py_compile design/maas/geometry_language/ast.py design/maas/geometry_language/surface_geometry.py design/maas/geometry_language/compiler.py design/maas/geometry_language/mutation.py design/maas/geometry_language/llm_adapter.py design/maas/geometry_language/vlm_adapter.py
```

Expected: every selected test passes; compile exits zero.

- [ ] **Step 2: Run static contract checks**

```powershell
rg -n "qatar_|sanaa_|oma_" ARR/backend/design/maas/geometry_language
git diff --check -- ARR/backend/design/maas/geometry_language ARR/backend/design/test_maas_spatial_mass_language.py ARR/backend/design/test_maas_geometry_language.py ARR/backend/design/test_maas_strict_unitbox_operators.py
```

Expected: no named operator identifiers and no whitespace errors. Ordinary
prose saying named precedents are forbidden is allowed only in documentation
or author instructions.

- [ ] **Step 3: Materialize two zero-paid diagnostic artifacts**

Write one direct interlocking-disc payload and one
`section_surface -> shell_thicken` payload to a new diagnostic run. Compile,
render, and persist their program/geometry hashes, individual PNGs, and exact
manifests. Label both `PRE-LEGAL / NOT EVALUATED`.

Do not route to law, parking, or VLM in this plan.

- [ ] **Step 4: Inspect both PNGs directly**

Confirm:

- the disc candidate visibly contains multiple oblique intersecting plates;
- the shell candidate visibly reads as a continuous thickened sectional
  field rather than a stepped box;
- neither render has disconnected fragments; and
- the identity shown in the sidecar matches the compiled hashes.

If either visual is wrong, return to the task whose operator produced it. Do
not tune the renderer to hide incorrect geometry.

- [ ] **Step 5: Update restart memory**

Record:

- operator contracts added;
- surface AST schema and compile boundary;
- focused test command and exact pass count;
- diagnostic artifact paths and hashes;
- paid request count `0`; and
- next plan:
  `same real parcel -> occupied-space evidence -> exact BCR/FAR/GFA`.

- [ ] **Step 6: Commit and push the checkpoint**

Stage only the MASS language implementation, focused tests, diagnostic
manifests/renders, and the three memory files:

```powershell
git commit -m "feat(maas): complete spatial mass language"
git push origin DK-BB
```

Do not stage unrelated dirty-worktree files.

## Plan Self-Review

- Spec coverage: existing generic operator wiring, direct non-recipe
  interlocking plates, typed surfaces, constant positive thickness, UnitBox
  authority, VLM vocabulary, negative gates, diagnostics, and restart memory
  are covered.
- Deferred by explicit subsystem boundary: same real parcel placement,
  occupiable floor/circulation evidence, exact BCR/FAR/GFA, parking, 20-card
  selection, retained legal rejects, and the one paid VLM smoke request belong
  to the next two implementation plans.
- Completion scan: every step names concrete files, commands, expected
  evidence, error codes, and cross-task interfaces.
- Type consistency: `surface` nodes output `BoundedSurface`; only
  `shell_thicken` accepts a surface and returns a manifold solid; all final
  roots remain solid.
