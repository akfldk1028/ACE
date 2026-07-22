# UnitBox 4x4 MASS Implementation Plan

**Goal:** Make one `1/1 UnitBox` the public MASS root, evaluate affine
transforms through explicit homogeneous 4x4 matrices, show derived BOOK volume
states below that root, and expose the exact data in the single language graph.

**Architecture:** Add a small matrix module owned by the core geometry
language. Preserve readable transform verbs at the DSL boundary, convert them
to matrices at compilation, and add an explicit `matrix4` operator. Change the
BOOK exploration graph from six base roots to one root plus derived volume
nodes. Adapt the selected-path frontend and render a compact matrix glyph.
Elevation remains a hash-bound downstream status, not a fabricated output.

**Stack:** Python 3, NumPy, manifold3d, Django tests, React/TypeScript/Vite.

---

### Task 1: Lock the matrix contract with failing tests

**Files:**
- Create: `backend/design/test_maas_unitbox_matrix.py`

Tests must prove identity/translation/scale/shear matrices, ordered
composition, pivot behavior, explicit matrix validation, and one public graph
root with derived BOOK volume children.

### Task 2: Add the homogeneous matrix module

**Files:**
- Create: `backend/design/maas/geometry_language/affine_matrix.py`
- Modify: `backend/design/maas/geometry_language/ast.py`
- Modify: `backend/design/maas/geometry_language/compiler.py`

Implement immutable 4x4 validation/build/composition helpers. Route transform
operators through one matrix evaluator and pass the top 3x4 block to the
geometry kernel. Accept explicit `matrix4` nodes and fail closed on invalid or
non-affine last rows.

### Task 3: Make UnitBox the public graph authority

**Files:**
- Modify: `backend/design/maas/book_exploration_graph.py`
- Modify: `backend/design/maas/language_system.py`
- Modify: `backend/design/maas/geometry_language/base_seeds.py`
- Modify relevant backend tests.

Emit one root `book:base-model:1-1`. Emit the other BOOK selections as
`derived_volume` nodes connected by `derives_volume`. Keep old seed IDs only as
hidden implementation details and attach an evaluated `matrix4` to every
box-derived preset.

### Task 4: Render the matrix and corrected path in the frontend

**Files:**
- Modify: `frontend/src/design/lib/language-system-types.ts`
- Modify: `frontend/src/design/components/book-language-flow/BookLanguageFlow.tsx`
- Modify: `frontend/src/design/components/book-language-flow/LanguageNetworkCanvas.tsx`
- Modify: `frontend/src/design/components/book-language-flow/book-language-flow.css`
- Modify relevant frontend unit tests.

Add `derived_volume` to graph ordering, build the selected path from UnitBox
through the selected derived state, and render a restrained monochrome/cyan
4x4 matrix glyph. Do not add another graph.

### Task 5: Record honest elevation continuation

**Files:**
- Modify: `backend/design/maas/geometry_language/elevation_handoff.py`
- Modify: `docs/ai-session-memory/maas-mass-flow/06_ELEVATION_HANDOFF.md`
- Add or modify elevation handoff tests.

Expose explicit next-stage nodes/status values for face extraction and
condition-pack generation. Do not claim an elevation result exists. Bind every
status to execution/program/geometry/PNU identity.

### Task 6: Full verification loop

Run focused backend tests, existing geometry/book graph regressions, frontend
unit tests, TypeScript build, one real single-MASS execution without an
unrequested paid VLM call, service-cache refresh, and browser verification at
`/design/language`. Inspect the produced MASS PNG. Record failures truthfully
and iterate until the new contract passes or a concrete external blocker is
identified.
