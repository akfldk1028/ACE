# LLM-Authored MASS and Elevation Research Bundle Design

## Status and precedence

Approved by the user on 2026-07-30. This decision supersedes the production
generation architecture in
`2026-07-30-strict-unitbox-diverse-mass-design.md` wherever that document
requires one handcrafted recipe per named family. Existing family recipes
remain optional deterministic fixtures and regression examples only.

## Goal

The LLM authors arbitrary typed `GeometryProgram` ASTs from the canonical
`1/1 UnitBox` and generic operators. The deterministic compiler and geometry
gates decide whether the program is executable. Morphology/family labels are
derived after compilation and must never select a handcrafted generation
recipe.

Every generated MASS is persisted as a self-contained folder containing the
source program, all Matrix4 transforms, the indexed 3D mesh, interoperable
OBJ/CSV files, deterministic technical views, and a hash-bound pre-legal
elevation research handoff.

## Alternatives considered

1. One recipe per family was rejected as a closed-world form vocabulary.
2. An unconstrained LLM emitting mesh coordinates was rejected because it
   creates a second geometry authority and cannot be replayed safely.
3. The selected architecture is LLM-authored typed AST, deterministic
   compile/gate/repair, then post-hoc morphology classification. Explicit
   recipe fixtures remain available only for offline regression and demos.

## Authoring contract

Production author sources are:

- `llm`: the existing structured OpenAI geometry author, called only after an
  explicit paid-provider opt-in;
- `payload`: a previously authored structured LLM payload, allowing replay
  without another provider call;
- `recipe_fixture`: an explicitly selected compatibility mode for tests and
  deterministic demonstrations.

The portfolio builder consumes `GeometryProgram` objects, not family IDs.
Each program must contain exactly one canonical `UnitBox` primitive and may
derive any number of solids through generic typed operations. Compilation,
clean-geometry, connectedness, hash uniqueness, and morphology-distance gates
remain deterministic. Invalid programs are rejected with structured
diagnostics; the live LLM author already owns a bounded compiler-feedback
repair loop.

The author evidence persisted with each candidate includes source kind,
provider/model/response identity when present, cache status, and prompt
contract. Missing provider credentials must fail closed and must never
silently switch to a handcrafted family recipe.

## Post-hoc classification

Family is an observation, not an input. After compilation, a deterministic
classifier derives a morphology signature from plan aspect, height-to-plan
ratio, curved/bridge/array/void/oblique operator evidence, and final topology.
The resulting label is used only for filtering, diversity accounting, and
memory retrieval. It cannot call a builder or mutate geometry.

Fixture mode may preserve its declared legacy label as fixture evidence while
also persisting the post-hoc label.

## MASS folder contract

Each candidate is written under:

```text
<run>/masses/<candidate-id>/
  manifest.json
  program/
    geometry-program.json
    author-evidence.json
  transforms/
    matrix4-trace.json
  mesh/
    indexed-mesh.json
    vertices.csv
    triangles.csv
    mass.obj
  views/
    front.png
    right.png
    back.png
    left.png
    top.png
    axon.png
  elevation-research/
    handoff.json
    floor-guides.json
    camera-poses.json
    surface-normals.json
    facade-planes.json
```

`manifest.json` binds every file to `run_id + candidate_id + program_hash +
geometry_hash + PNU` and records relative paths plus SHA-256 hashes.
`mass.obj` and the CSV files are research conveniences; indexed-mesh JSON
remains the exact geometry authority.

The six PNGs are deterministic projections of the same indexed mesh. Camera
direction/up, axes, view Matrix4, projected metric bounds, and depth range are
persisted. Floor guides come from the actual storey contract. Facade planes
come from exact compiled bounds. Stable face IDs and triangle normals allow
another session to attach facade, section, material, or elevation studies
without guessing mesh identity.

The research handoff is `prelegal_research_ready`, never `accepted`. It sets
`geometry_mutation_allowed=false` and lists missing legal, parking, and
certified-floor authorities. Final elevation evidence still requires the
certified single-execution handoff.

## Compatibility

The existing `<run>/candidates/*.json`, `<run>/renders/*.png`, portfolio JSON,
frontend graph, and board remain available during migration. Candidate records
gain `mass_directory`, `mass_manifest`, and `elevation_research_handoff`
relative paths. No existing legal status is upgraded.

## Testing and completion

Tests must prove:

- an injected authored program builds without consulting the recipe registry;
- family is assigned after compilation and author evidence survives;
- missing LLM credentials do not fall back to recipes;
- every MASS folder contains the full file contract;
- OBJ/CSV counts match indexed-mesh counts;
- all six camera/view artifacts exist and share exact identity hashes;
- floor guides, view Matrix4 values, normals, facade planes, and stable face
  IDs are present;
- all relative paths stay inside the run directory;
- focused creative portfolio, command, compiler, and elevation projection
  regressions pass.

