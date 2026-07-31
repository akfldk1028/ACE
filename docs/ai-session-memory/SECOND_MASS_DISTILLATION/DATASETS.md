# Second Mass Distillation Dataset Policy

External images are allowed for research use in this project.

## Primary Hugging Face Sources

- `terminusresearch/photo-architecture`
  - architecture/building photo corpus with captions.
- `Morris0401/Year-Guessr-Dataset`
  - architecture image and building age/region metadata.
- `gatecitypreservation/architectural_styles`
  - architectural style prior.
- Pick-a-Pic / open image preference datasets
  - general pairwise preference prior only; not architecture-specific truth.

## ArchDaily

ArchDaily can be used as an external precedent corpus:

- store URL,
- title,
- architect/project metadata,
- image URL/local path,
- tags,
- caption/description.

Use ArchDaily to improve precedent resonance and tag matching, not as legal or
parking evidence.

Current crawl route:

- Browser/Playwright search-page crawl: not reliable in this environment;
  current probe times out.
- Static search page: HTTP 200, but project cards are client-side.
- Search JSON API: works with
  `https://www.archdaily.com/search/api/v1/us/projects?page=1`.
- Stored smoke corpus:
  - `docs/ai-session-memory/reference-corpus/archdaily/DB_MANIFEST.json`
  - `docs/ai-session-memory/reference-corpus/archdaily/api/<collection>/metadata.jsonl`
  - `docs/ai-session-memory/reference-corpus/archdaily/api/<collection>/images/`
  - `docs/ai-session-memory/reference-corpus/archdaily/seeded/<collection>/metadata.jsonl`
  - `docs/ai-session-memory/reference-corpus/archdaily/seeded/<collection>/images/`

Image download methods are documented in:

- `docs/ai-session-memory/reference-corpus/archdaily/README.md`

Current test DB:

- 119 unique references loaded by the harness.
- 175 image files stored.
- Broad collections: projects, houses, apartments, housing, cultural
  architecture.
- Exact seed collection: BIG/OMA iconic precedents.
