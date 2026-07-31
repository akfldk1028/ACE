# MASS Thumbnail, Deduplication, and Elevation Agent Boundary

## Goal

Make the bottom archive read as one unique MASS per card, while preserving
every execution in the chronological timeline and keeping creative elevation
generation in the independent `elevationAgent`.

## Bottom archive contract

- One card contains one isometric MASS image.
- Four-view composites, elevation sheets, BOOK rasters and VLM references are
  forbidden in the bottom rail.
- Single-execution cards use an immutable `/thumbnail/` image derived from the
  isometric panel of the exact compiled four-view MASS render.
- Runs sharing a non-empty `geometry_hash` collapse to one card. The newest run
  represents that geometry; selecting a historical duplicate still marks the
  representative geometry card as selected.
- The top execution timeline remains lossless and continues to show every run.
- Portfolio MASS cards keep their existing single-card preview contract.

## Elevation agent boundary

`ARR/backend/agents/elevationAgent` is the independent specialist identity and
private-memory boundary. The MAAS-owned deterministic adapter only produces
mesh projections and a condition pack. Future creative generation follows:

`immutable MASS + condition pack -> elevationAgent -> replaceable image model
provider -> facade images -> cross-view/mesh consistency critic -> accepted
elevation evidence`.

No image model name is hardcoded into MASS geometry code. A future provider may
use an OpenAI image model or another generator without changing the UnitBox,
GeometryProgram, compiler, mesh hash or graph provenance.

## Verification

- Backend test proves `/thumbnail/` returns one cropped image and run rows
  expose `geometry_hash` and `thumbnail_url`.
- Frontend test proves duplicate geometry hashes produce one card and all
  single-execution cards use `/thumbnail/`.
- Browser verification proves every visible bottom image contains one MASS,
  clicking a card changes the graph/right evidence, and no image is broken.
