# r337 preflight: Task8 materialization repair

Date: 2026-08-03 KST

## Product invariant

MASS is the current product boundary. The intended flow remains:

`UnitBox/Matrix4 BaseVolume -> LLM GeometryProgram/AST -> typed BOOK -> authored legal projection -> legal/GFA/parking -> render/VLM -> typed revision -> diverse selection`

Floor legal volumes are analysis authority only. They must never replace the authored visual mass. The post-BOOK AST is final program authority, and the certified projected surface is final visual authority. Elevation work remains deferred.

## r336 diagnosis

r336 produced 0/3 after 16 graph observations. Terminal failures were 8 authored visual authority, 4 BOOK projection, 2 semantic carrier, and 2 authored identity collapse. No floor-affine terminal remained, proving the maximal-lower legal projection repair worked. BOOK pre/post hashes changed, proving BOOK execution worked. No candidate reached VLM.

## Task8A: profiled legal materialization

- Polygon, MultiPolygon, disjoint components, and holes are supported generically.
- The serialized triangle mesh is reconstructed and checked as a finite closed manifold.
- Per-floor midplane topology, components, holes, area, symmetric difference, Hausdorff distance, and strict legal containment are recomputed from the actual mesh.
- The legal section binding is derived independently from live authoritative occupied/legal floor sections and origin.
- The binding is stored outside the certificate and explicitly propagated through portfolio, archive replay, certified measurement, preference, and outcome paths.
- Artifact semantic context is never accepted as the legal anchor. Missing legacy profiled anchors fail closed.
- Coordinated triangle/WKB/hash resealing attacks fail against the external anchor.
- Preflight bounds all authority-hash strings, collections, WKB, triangles, floors, components, contours, and points before serialization or manifold work.

## Task8B: BOOK and semantic carrier

- The immutable semantic-carrier return AST is adopted into the real post-BOOK AST.
- The carrier is a geometry-identity matrix4 wrapper; geometry remains unchanged and post-BOOK remains program authority.
- Carrier binding applies to actual BOOK-call paths and remains fail-closed there.
- BOOK failures preserve typed code, scope, verbs, chassis, effect, and pre/post identities through broad exception paths.
- Protected split_wing plus overlap rejection remains intentional.
- Benchmark summaries use the standard JSON serializer; literal newline corruption is removed.

## Task8C: identity evidence

- Identity evidence is frozen from the exact authored-source/materialized pair.
- Frozen evidence includes before/after phenotype, step visibility, step intent, raw silhouette metric, threshold 0.40, and predicate version.
- Terminal evidence and certificates copy this record without later recomputation.
- `surfaces_missing`, empty, and no-valid-surface variants map to the typed empty/no-valid category while retaining original cause and mode.

## Verification gate

Independent integration review: PASS.

Focused regression result: 44/44 passed.

Next action: run exactly one r337 target3 full MASS portfolio including provider authoring, materialization, legal/GFA/parking, render, VLM, selection, and PNG. If it fails, do not loop; inspect the new typed terminal evidence.
