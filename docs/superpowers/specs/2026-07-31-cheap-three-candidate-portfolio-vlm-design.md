# Cheap Three-Candidate Portfolio VLM Design

Date: 2026-07-31
Repository: `D:\Data\25_ACE`

## Goal

Produce a same-parcel MASS portfolio in PNG form while keeping paid visual
review small and truthful. Normal lawful BaseVolume-derived candidates remain
valid. A bounded subset may use inhabitable plate, slab, wall, shell, void,
intersection, curved, or continuous-section relationships. Named precedents
are capability-range evidence, never recipes, copies, required families, or
portfolio quotas.

## Cost contract

Generation and deterministic review produce twenty candidates without paid
provider calls. Geometry, spatial capacity, exact parcel placement, PNU law,
floor, parking, and authored-identity gates run before VLM.

The deterministic selector sends exactly three surviving candidates to one
portfolio VLM request:

- one 3-card candidate PNG, not three candidate requests;
- at most two exact local ArchDaily reference images;
- `gpt-5.4-mini`;
- candidate board detail `high`;
- reference detail `low`;
- one paid HTTP request;
- zero automatic retries;
- process-wide and live VLM request ceilings both set to one.

If fewer than three deterministic survivors exist, the request is not made.
The PNG still shows the available passes and retained rejects with their exact
failure reasons.

## BaseVolume and Matrix4 authority

The normalized `1/1 UnitBox` is the sole mathematical root authority. It is
not the final building-shaped BaseVolume.

Every affine BaseVolume is an evaluated UnitBox plus an explicit homogeneous
4x4 matrix:

```text
UnitBox
-> Matrix4(scale, rotation, translation, optional shear)
-> evaluated BaseVolume
```

This permits block, slab, bar, tower, rotated, oblique, and skewed starting
proportions without treating a literal cube as the architectural result.
`scale`, `rotate`, `translate`, and `shear` shorthands may remain accepted at
the author boundary, but persisted normalized AST and execution evidence must
contain the composed `matrix4`.

Matrix4 cannot change topology. Circular, elliptical, faceted, plate, shell,
void, and intersecting systems therefore continue from the evaluated
BaseVolume through typed topology-changing operations:

```text
BaseVolume
-> circularize / section_surface / host_face_surface / loft_surface
-> shell_thicken / profile_sweep_3d
-> boolean / bridge / attach / carve
-> connected inhabitable MASS
```

The current independent `profiled_prism` primitive must not remain a second
base authority. It moves to a derived topology lane downstream of the UnitBox
and Matrix4 BaseVolume.

BOOK fractional BaseVolumes remain normalized scope/host derivations. Their
cell assemblies are topology derived from the evaluated host and do not
create competing primitive roots.

## Board-specific reference VLM

`score_portfolio_board_with_openai_vlm` receives:

- the exact 3-card PNG;
- compact candidate summaries with candidate, program, and final geometry
  identities;
- explicit `reference_matches`;
- optional run/PNU identity;
- image-detail and reference-limit controls.

The request content order is:

1. board-specific portfolio prompt;
2. exact candidate board image;
3. reference 1 label and exact image;
4. reference 2 label and exact image.

The prompt explicitly says that the first image contains three separate
candidate cards and requires one decision per candidate ID. It must not call
the board a four-view single candidate.

The result persists:

- response ID and model;
- API usage;
- request/retry counts;
- board path and SHA-256;
- every submitted reference path and SHA-256;
- `used_by_vlm=true` only for actually submitted images;
- candidate program and geometry identities;
- portfolio verdict, per-candidate keep/replace decisions, transferable
  spatial relations, and failure reasons;
- `legal_or_parking_score=false`.

The cache key includes board hash, prompt/schema version, model, compact
candidate identities, program/PNU context, and submitted reference image
identities. A reference change cannot reuse a stale board audit.

## PNG outputs

Every run produces human-viewable PNG evidence:

1. `maas-same-site-20.png` — all twenty slots, including rejected candidates
   and exact deterministic failure labels.
2. `maas-vlm-shortlist-3.png` — the three deterministic survivors submitted
   to VLM.
3. `maas-vlm-shortlist-3-audit.png` — the exact three-card board plus VLM
   decisions, concept/failure summary, request count, response ID, and the two
   reference thumbnails.

JSON remains the machine-readable authority, but it is never the only
user-facing result.

## Selection policy

The three candidates are selected without named-form quotas:

1. all hard gates pass;
2. distinct final geometry hashes;
3. plausible occupied floor/circulation/program capacity;
4. authored identity preserved after legal projection;
5. maximum portfolio separation in measured spatial relationships, including
   solid/void organization, section, ground threshold, component hierarchy,
   plate/shell participation, and plan organization.

The selector may choose three ordinary solids, three relational systems, or a
mix if that is what the lawful supply supports. It must not force OMA, SANAA,
Qatar, disc, ellipse, long-span, or stepped coverage.

## Failure behavior

- Missing API credentials: fail closed before reserving a paid request.
- Missing/unreadable reference image: omit it before request construction and
  record it as retrieved but not used; never claim it was submitted.
- Paid budget exhausted: write a failed audit and preserve both PNG boards.
- HTTP/provider failure: no retry; persist one attempted request and error.
- Invalid VLM JSON: fail the visual audit; deterministic candidates remain
  unaccepted visually.
- Fewer than three hard-pass candidates: spend zero and show truthful reject
  evidence in the twenty-slot PNG.

## Test contract

Implementation follows red-green TDD.

1. A failing transport test proves the portfolio request contains one board
   image plus two exact reference images and only one HTTP call.
2. A failing identity test proves output binds board/reference SHA-256 values
   and response ID.
3. A failing cache test proves changing a reference image identity changes the
   cache key.
4. A failing prompt test proves the board is described as three candidate
   cards, not one four-view candidate.
5. BaseVolume tests prove affine seeds have exactly one UnitBox root and an
   explicit Matrix4 node in normalized evidence.
6. A topology-authority test proves profiled/circular/plate variants descend
   from the evaluated BaseVolume rather than introduce a second primitive
   root.
7. Renderer tests open all three PNGs and verify expected card counts,
   dimensions, and nonblank mass pixels.

No paid provider is called by tests.
