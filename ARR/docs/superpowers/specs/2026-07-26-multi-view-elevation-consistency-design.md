# Multi-View Elevation Synthesis and Consistency Design

**Date:** 2026-07-26

## Goal

Extend the existing `elevationAgent` from one architectural render sheet into
four real facade proposals for one immutable MASS: front, right, back and left.
No proposal becomes accepted elevation evidence until deterministic
mesh-registration checks and one bounded multimodal critic both pass.

The first proof target is
`r230-radial-roof-render-03-radial-cross`. MASS 04 is eligible only after MASS
03 completes the full generation and consistency path.

## Immutable authority

The MASS compiler remains the only geometry authority. Every generated facade
is bound to:

`execution_id + program_hash + geometry_hash + view`.

The elevation agent consumes the existing indexed mesh, stable face IDs,
facade planes, floor guides and deterministic front/right/back/left
projections. It may add facade materials, openings and architectural detail
inside the registered MASS mask. It may not change the silhouette, add mass,
remove mass, move floor guides or invent legal/parking approval.

The technical six-view bundle remains separate evidence. The creative output
contains four facade views; top and axon stay deterministic verification views.

## Considered approaches

### Independent facade calls with a shared contract

Generate each facade from its own deterministic orthographic projection. All
four calls use one shared facade strategy, material palette, floor datum and
opening-module contract. Evaluate the four outputs together.

This is the selected approach. Each view has full resolution and independent
provenance, while a joint critic can reject contradictions without allowing one
view's image artifacts to become the next view's geometry authority.

### One four-panel sheet followed by cropping

This costs fewer calls but gives each facade less resolution and makes panel
boundaries, labels and perspective leakage harder to control. It also prevents
clean per-view retries and provenance.

### Autoregressive adjacent-view generation

This can improve superficial style continuity, but an error in one facade
propagates into later views. The approach is rejected as the primary path.
Adjacent accepted views may be supplied as non-authoritative style context in a
repair request, but never as geometry input.

## Components

### Multi-view contract

A new typed contract records:

- immutable execution/program/geometry identity;
- one shared facade strategy and its hash;
- required view order: front, right, back, left;
- deterministic source projection and mask hash for every view;
- provider, model, request ID, prompt hash, input/output hashes and usage;
- per-view status and issue list;
- deterministic consistency measurements;
- joint critic response and submitted montage hash;
- repair round and bounded request counts;
- final status: `complete`, `needs_review` or `failed`.

Materialized files live under:

`elevation/proposals/multi-view-alt-01/`.

The bundle contains one JSON manifest, four PNG files, one critic montage and
one critic-evidence JSON document. Writes are atomic and an existing complete
identity-matching manifest is reused without another paid call.

### Provider-neutral facade generator

The elevation agent calls the existing replaceable image-provider boundary.
The selected runtime configuration may use `gpt-image-2`; provider and model
names do not enter MASS geometry code.

Each request receives:

- the exact deterministic projection for its view;
- an editable mask derived from that projection;
- the shared facade strategy;
- the view's facade plane and floor guides;
- explicit instructions that pixels outside the MASS and roof-only regions are
  immutable;
- shared material, bay and opening rules.

The post-composite silhouette lock remains mandatory. A provider response with
missing bytes, mismatched identity or an altered immutable region fails closed.

### Deterministic consistency gate

Before a paid critic is called, all four outputs must pass:

- exact identity and artifact hash checks;
- zero changed pixels outside the editable MASS mask after post-composite;
- silhouette registration against the deterministic projection;
- floor-guide alignment within the configured pixel tolerance;
- facade-plane extent and image-dimension agreement;
- corresponding corner datum agreement for front-right, right-back,
  back-left and left-front pairs;
- presence of all four distinct required views.

Tolerance values are explicit in the manifest and tests. A failed deterministic
gate skips the critic and marks only the affected view for repair.

### Joint multimodal critic

One montage contains the four generated facades, labeled with their view and
the shared identity. A bounded multimodal critic evaluates:

- the same material and facade system across views;
- matching floor count and horizontal datums;
- compatible opening rhythm at adjacent corners;
- absence of facade treatment on roof-only surfaces;
- no visible contradiction with the locked MASS projections.

The critic returns structured per-view issues and a final
`pass`/`needs_review` result. Its response ID, model, prompt hash, montage hash,
input hashes, token usage and raw structured response are persisted.
`not_evaluated` is never a pass.

## Paid-call budget and repair loop

For one MASS:

1. Initial generation: exactly four image calls, one per facade.
2. Initial critic: at most one multimodal call after deterministic preflight.
3. Repair: at most one additional image call per failed facade.
4. Final critic: at most one additional multimodal call after repair.

The maximum is ten paid calls per MASS: eight image calls and two critic calls.
There are zero transport retries. Provider/network failure is recorded as a
failed attempt and does not silently consume another request slot.

The first run is MASS 03 only. MASS 04 is not generated until MASS 03 passes or
exhausts its bounded repair loop with an honest failed status.

## Causal graph and frontend

The existing single MASS graph is extended; no second graph is introduced:

`elevation:condition_pack -> elevation:multi_view_agent ->
elevation:multi_view_consistency -> elevation:accepted`.

The accepted edge activates only when both the deterministic gate and joint
critic pass. Failed and review states retain visible audit nodes with inactive
acceptance edges.

The selected MASS sidebar presents:

1. immutable compiler MASS;
2. existing architectural render ALT;
3. deterministic six-view geometry verification;
4. creative front/right/back/left facade proposals;
5. deterministic and critic consistency status with issue details.

The bottom archive remains MASS-only.

## Error handling

- Identity mismatch: fail before provider invocation.
- Missing deterministic view/mask: fail before provider invocation.
- Provider failure: persist the failed attempt and affected view.
- Deterministic gate failure: skip critic and repair only affected views.
- Critic failure or invalid structured response: remain `needs_review`.
- Exhausted repair budget: remain failed or `needs_review`; never promote.
- Existing matching complete bundle: return it idempotently with zero new paid
  calls.

## Verification

Tests must cover:

- four exact view requests with shared identity and strategy;
- no duplicate or missing views;
- post-composite silhouette preservation;
- floor and adjacent-corner datum failures;
- critic skipped when deterministic preflight fails;
- critic provenance and structured issue persistence;
- only failed views regenerated in the single repair round;
- ten-call hard ceiling and zero automatic retries;
- idempotent reuse of an accepted manifest;
- passport graph activation only after both gates pass;
- frontend separation of technical six views and creative four facades.

The proof run must additionally verify:

- MASS 03 program and geometry hashes are unchanged;
- four creative facade PNGs exist and their hashes match the manifest;
- the critic montage and evidence exist;
- browser selection shows the same execution identity, no broken images, no
  hidden 4xx/5xx requests, no console errors and no second graph;
- exact paid request counts and final status are written to the canonical MASS
  memory.
