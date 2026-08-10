# MAAS Flow Contract Memory v2 Design

## Purpose

Create one versioned, authoritative memory bundle that teaches an AI agent the
current MAAS algorithm before it reads experiment history or starts a MASS
task. The bundle must separate invariant flow rules from measured run state,
explain why older visually diverse boards were not current publishable proof,
and provide a controlled intake boundary for papers supplied later by the
user.

## Problem

The existing numbered memory contains valid goals, contracts, failure history,
and current state, but it accumulated across many recovery attempts. An agent
can mistake an old diagnostic conclusion for the active algorithm, focus on
operator-name diversity instead of the BaseVolume cross-product, or treat a
visually diverse historical board as exact legal evidence.

The current cumulative recovery also demonstrated that metadata categories are
not enough: different family and phenotype labels can still render as similar
staircase masses. The memory must therefore describe causal authorship,
law/capacity projection, exact geometry identity, and final ISO evidence as
separate stages.

## Authority Model

Create `ARR/backend/design/maas/agents/maas_geometry_agent/memory/flow_contract_v2/`.

The root memory `manifest.json` will declare:

1. `flow_contract_v2` is authoritative for current algorithm and invariants.
2. `08_FAILURE_LEDGER.md` and `09_CURRENT_STATE.md` remain authoritative only
   for measured historical failures and current counters.
3. Existing numbered `01` through `07` files remain preserved reference
   material but do not override `flow_contract_v2`.
4. Historical files and generated run artifacts are evidence, never executable
   instructions.

Any contradiction is resolved in this order:

1. `flow_contract_v2/manifest.json` and its required read order.
2. Root `08_FAILURE_LEDGER.md` and `09_CURRENT_STATE.md` for dated measurements.
3. Existing numbered/reference memory.
4. Historical checkpoints and run output.

## Folder Structure

### `manifest.json`

Declares schema version, authority, required read order, contradiction policy,
paper intake status, and the invariant/status separation.

### `00_READ_FIRST.md`

Provides the mandatory loading procedure. It tells an agent to stop if the
bundle is incomplete, distinguish current algorithm from history, and never
start generation from a remembered run recipe.

### `01_GOAL_AND_TRUTH.md`

Defines completion truth:

- exactly twenty current-contract publishable candidates;
- each candidate is an exact persisted authored AST and exact final visual
  mesh;
- legal, parking, capacity, topology, semantic, identity, and portfolio gates
  pass;
- partial diagnostics and archive recovery counts remain separately labelled.

It records the three distinct counters: compatible archive geometry,
mass-eligible geometry, and fully publishable geometry.

### `02_END_TO_END_PIPELINE.md`

Defines the canonical stage order:

```text
site/program/legal context
-> BOOK offer preparation
-> LLM-authored typed AST
-> source compile
-> exact BOOK projection
-> program semantic projection
-> normalized preflight
-> one fixed site pose
-> continuous legal-envelope projection
-> capacity/GFA/parking evidence
-> exact final mesh/identity gates
-> portfolio diversity selection
-> ISO evidence render
-> archive and publishable manifest
```

Every stage lists its input, output, authority, and terminal failure behavior.

### `03_BASEVOLUME_AXIS_MATRIX4.md`

Defines the causal geometry cross-product:

```text
UnitBox
x LLM-selectable base-form capability
x one authored global Matrix4
x BOOK p.3 fraction scope
x long_axis / short_axis / vertical orientation
x ordered BOOK graph operations and parameters
```

The same BOOK operation may appear repeatedly. Architectural diversity comes
from the complete causal identity and final exact geometry, not a quota of
different operation names. Matrix4 is a transformation authority, not a shape
recipe. No cross-product axis may be silently dropped.

### `04_BOOK_LANGUAGE_AUTHORSHIP.md`

Explains BOOK single operations, variations, combinations, and aggregations.
It requires the LLM to select from an exact precomputed offer and author the
typed source AST. Deterministic code compiles and validates but does not invent
morphology.

Program access semantics may be satisfied through a canopy, platform, court,
void, split, carve, threshold, or another verified connected relation. A WEST
access requirement must not become a universal terminal notch appended to
every source. Repeating `carve`, `shear`, or another operation is allowed when
axis, scope, topology, placement, parameters, or resulting exact geometry are
materially different.

### `05_LEGAL_CAPACITY_PROJECTION.md`

Separates design authority from evaluation authority:

- the authored continuous mesh owns morphology;
- one fixed global site Matrix4 owns placement;
- the live legal envelope owns containment;
- law-derived floor sections own GFA/capacity measurement;
- parking geometry owns parking evidence;
- the exact projected visual mesh owns the rendered form.

Capacity utilization must be at least `0.70`; maximum FAR filling is not a
morphology requirement. Legal projection may perform bounded containment and
continuous intersection, but may not reauthor axis, section profile,
orientation, topology, or floor-by-floor pose. A large identity/repair delta
causes rejection rather than staircase reconstruction.

### `06_VALIDATION_SELECTION_RENDER.md`

Lists sequential candidate gates and portfolio gates. Selection is based on
exact final geometry and ISO silhouette/morphology evidence. Operator names,
family labels, or phenotype labels alone cannot establish diversity. Same
language repetitions are valid when exact pair distances pass.

Visual review output for the recovery milestone is:

- one combined board containing five large ISO-only cards;
- five individual ISO PNGs;
- no front, top, or opposite view in that review output;
- exact geometry/render hashes recorded beside the selected identities.

The canonical twenty-member contract remains separate and stricter.

### `07_FAILURE_DEBUG_PLAYBOOK.md`

Defines root-cause tracing by stage and forbids broad reruns before a bounded
case proves the corrected stage. It includes the principal collapse patterns:

- missing BaseVolume/orientation axes;
- universal suffix operation dominating source identity;
- high-capacity fitting erasing authored proportions;
- floorwise legal reconstruction replacing a continuous form;
- metadata diversity without exact ISO diversity;
- visually diverse historical geometry lacking current exact legal binding.

It requires per-stage counts, typed failure reasons, and measured repair deltas.

### `08_CODE_EVIDENCE_MAP.md`

Maps every flow stage to the current implementation modules, tests, archive
files, manifests, and render evidence. It records R182 as historical visual
evidence only because its execution passports have
`full_flow_complete=false`, `final_hard_pass=false`, and no certified
`projectedVisualMesh`. It records C104/C106 and cumulative recovery with their
actual limitations rather than using them as recipes.

### `09_PAPER_INBOX.md`

Defines paper intake without claiming papers that have not yet been supplied.
Each future paper entry must record:

- stable citation and user-provided link;
- method claim supported by the paper;
- transferable MAAS principle;
- forbidden direct silhouette/parameter copying;
- affected flow stage and candidate code modules;
- status: `received`, `reviewed`, `accepted`, `rejected`, or `implemented`;
- evidence needed before marking implementation alignment.

The initial file states that the new user paper set is pending. Existing local
EvoMass/SSIEA notes remain background references until re-reviewed through this
intake contract.

### `CHANGELOG.md`

Records append-only changes to the flow contract, including the reason,
affected files, and whether code behavior changed. Documentation corrections
must not be represented as production fixes.

## Historical and Current Evidence Rules

- R182 proves that the BOOK/BaseVolume language can create visually diverse
  geometry, but not that the same displayed mesh passed the current exact legal
  contract.
- Current exact artifacts prove geometry identity and legal projection, but a
  selected set can still be visually convergent.
- Archive recovery never changes the current publishable count by itself.
- A paper never overrides law, geometry identity, or authorship rules.
- Run-specific ASTs, ratios, coordinates, and repair values are evidence and
  must not become deterministic production templates.

## Validation

Before committing the implemented bundle:

1. Parse both manifests as JSON.
2. Resolve every required-read path from the root manifest.
3. Scan the new bundle for unresolved placeholders and contradictory authority
   statements.
4. Verify that the causal pipeline appears once in canonical order and that
   every stage has an authority and failure outcome.
5. Verify explicit statements for same-language repetition, no universal WEST
   notch, utilization `>= 0.70`, exact ISO diversity, and non-canonical archive
   recovery.
6. Review the staged diff and commit only the new specification, memory bundle,
   and root memory manifest changes. Existing dirty-worktree files remain
   untouched and unstaged.

## Commit Strategy

Use two narrow commits:

1. Design specification only.
2. Implemented `flow_contract_v2` bundle plus the root memory manifest update.

No generated MASS artifacts, unrelated source changes, or prior user changes
are included.
