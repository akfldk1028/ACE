# Radial MASS and Roof-Semantic Elevation Correction

## Goal

Correct the two weaknesses found in r227 without weakening the one-UnitBox,
BOOK-language, compiler/GATE, immutable-MASS or single-graph contracts:

1. MASS 03 must read as several occupiable wings rotating from one common hub,
   not as bent or loosely merged bars.
2. MASS 05 ALT 01 must read its top panel as a roof/top projection, not as a
   vertical curtain-wall elevation.

The correction is first proved on two new executions. It then becomes the
default rule for later ten-MASS batches.

## Repeated Root-Cause Audit

### MASS 03

r223, r224 and r227 all admitted a synthesized `bend` before BOOK operations.
r225 removed the bend but still used `book_rotate + merge_related`. Visual
inspection shows that all four generations are one-sided branches or fans, not
a centered radial family.

The failure is semantic, not random:

- `book_rotate` partitions one body and rotates one partition around its shared
  hinge.
- `merge_related` attaches a measured related unit.
- Neither operation guarantees three wing directions or a shared central hub.
- The existing geometry-language system contract already defines the stable
  radial implementation as `radial_array + hub union`.

Therefore the family label `radial_cross` was stronger than its executable
operator contract.

### MASS 05

r223-r227 taper programs remain single-component, watertight and visually
coherent. The r227 generated ALT preserves the outer silhouette but applies the
vertical-fin facade rhythm to the top panel.

The failure is in image conditioning:

- The four-view sheet marks the top panel in text, but its colored MASS pixels
  are part of the same editable mask as facade pixels.
- The selected `vertical-fins-glass` strategy is valid on vertical faces but
  invalid on a roof.
- Prompt text already requested a roof/top view and still failed.

Therefore a prompt-only correction is insufficient. Panel semantics must affect
the editable regions and deterministic post-processing.

## Selected Architecture

### 1. Family Phenotype Contract

Add a focused family-contract module rather than adding special cases to the
compiler or growing `fresh_batch.py`.

The radial contract accepts only programs that:

- descend from one normalized UnitBox;
- contain `radial_array` or an equivalent `cross_mass`/hub composition;
- do not use `bend` before the radial relation;
- compile to one component;
- contain at least three distinct plan-direction wings;
- retain a non-empty shared central hub;
- keep every wing thickness above the existing occupiable-geometry tolerance.

Candidate generation remains parameterized and archive-novel. The contract
rejects the wrong phenotype; it does not prescribe parcel coordinates or copy
a completed form.

### 2. Roof-Semantic Image Contract

Add explicit `panel_roles` to the locked four-view image job:

- `isometric`: facade and roof materials allowed;
- `opposite`: facade and roof materials allowed;
- `top`: roof material only, no windows, mullions, balcony rails or vertical
  facade bays;
- `front`: facade materials and openings allowed.

The top region is derived from the stable four-view sheet layout and its MASS
mask. It is not derived from world coordinates.

After the single provider response:

- pixels outside the MASS remain restored by the existing silhouette lock;
- the top panel receives a roof-semantic guard;
- high-frequency facade-grid pixels in the editable top MASS are replaced by a
  low-frequency roof surface whose palette is measured from the provider
  output;
- the source top silhouette and boundary remain unchanged;
- the manifest records the panel-role schema, roof-guard status and changed
  pixel count.

No second provider call or retry is allowed.

### 3. Execution Flow

The proof flow is:

`UnitBox -> radial family author -> phenotype contract -> compiler/GATE ->
MASS 03 PNG`

and

`UnitBox -> taper -> compiler/GATE -> MASS 05 PNG -> elevation condition pack
-> facade strategy -> panel-role mask -> one image call -> silhouette lock ->
roof semantic guard -> ALT 01`.

Both results enrich their existing execution passports and the same frontend
graph. No second graph or alternate archive is introduced.

## Error Handling

- If no radial candidate satisfies the phenotype contract within the existing
  bounded search, the two-MASS proof is `incomplete`; no weaker branch is
  relabelled radial.
- If the provider rejects the image request, the proposal is `fail` with no
  retry.
- If the top panel still exceeds the roof-grid detector threshold after the
  guard, the proposal is `needs_review`, not active evidence.
- Existing r227 artifacts are immutable and remain available for comparison.

## Tests

Backend tests must prove:

- the radial spec no longer accepts `bend + book_rotate + merge_related`;
- the accepted radial program uses one UnitBox and a common-hub radial
  phenotype;
- the compiled geometry is one watertight/manifold component;
- the roof-role mask selects only top-panel MASS pixels;
- the roof guard does not change pixels outside the top MASS;
- a facade-grid synthetic top input is reduced below the detector threshold;
- image request count remains one and retry count remains zero.

Runtime verification must prove:

- two new program and geometry hashes are archive-unique;
- direct before/after PNG inspection;
- at most two paid image attempts total;
- MASS click changes MASS, technical elevation and ALT identity together;
- one graph, zero broken images, zero console errors and no Vite overlay.

## Honest Acceptance Boundary

Passing this correction means the two targeted form/image defects are fixed.
It does not mean the MASS is site-bound, FAR-compliant, parking-approved or
competition-ready. Those claims still require resolved PNU, parcel placement,
capacity, law and parking evidence.
