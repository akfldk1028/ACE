# C24 west-ramp north-bar implementation plan

**Goal:** Persist one independently authored C24 AST from the exact v30
offset-100 offer, freeze it after production-context preflight, and perform one
canonical validator invocation.

**Architecture:** A canonical UnitBox/BaseVolume/Matrix4 living bar overlaps an
independently typed low wedge market ramp through allowed `attach_volume`; a
terminal WEST notch remains protected while the selected quarter-scope BOOK
fracture is inserted upstream.

**Tech stack:** Python 3, v30 geometry author parser, recursive geometry
compiler, BOOK projection adapter, static v4 packager, production-faithful
direct-fit validator.

---

### Task 1: Reconstruct exact context and preflight the authored topology

- Reconstruct the production author context with request batch `2/3`, offset
  `100`, count `8`, cumulative feedback A+B+C16+C17+C18+C19+C20+C21, and the
  unchanged v50 deficits.
- Assert the exact 32 offered path IDs and canonical offer hash.
- Parse the in-memory source under the exact `neighborhood_living` author gate.
- Compile source and exact BOOK-projected program; require one component,
  watertight manifold geometry, terminal WEST access, depth `2`, reserve `0`.
- Do not persist a fragment if any check fails.

### Task 2: Persist authorship evidence and freeze the response

- Write dedicated evidence under
  `v11-revisions-c/v30-round6-c24/` and a dedicated fragment directory under
  `tmp-v30-round6-c24/fragments/`.
- Persist request identity, normalized design context, exact cumulative
  feedback, v50 deficits, all 32 offers, selected lowering, allowed-operator
  preflight, and one-shot policy.
- Canonicalize the prompt, response, and morphology payloads and persist their
  SHA-256 hashes plus the exact direct response ID.
- Include v4 `offered_book_composition_path_ids` and
  `offered_path_ids_sha256` in the frozen fragment.

### Task 3: Package, audit membership, and invoke validator once

- Run the latest packager once into the dedicated C24 manifest/admission paths.
- Confirm v4 manifest schema, exact offer membership/hash, source hash,
  response binding, prompt binding, and unchanged morphology hash.
- Invoke `validate_static_codex_mass_v11.py` exactly once and capture stdout,
  stderr, exit code, manifest/admission copies, and result JSON in `.run-01`.
- Rename a rejected fragment to `.json.rejected` if required by the established
  evidence convention, without changing its bytes.
- Record the immutable result. Do not tune, rerun, or commit.
