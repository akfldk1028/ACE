# ArchDaily Reference Corpus

Updated: 2026-07-08

This folder stores the external ArchDaily precedent corpus for MAAS second-stage
mass preference distillation.

## Folder Contract

```text
archdaily/
  DB_MANIFEST.json
  seed_urls.txt
  api/
    <collection>/
      manifest.json
      metadata.jsonl
      images/
        archdaily_<document_id>.jpg
  seeded/
    <collection>/
      manifest.json
      metadata.jsonl
      images/
        archdaily_<document_id>.jpg
```

## Current DB

- Unique metadata items loaded by harness: 119
- Image files stored: 175
- Loader: `design.maas.preference.reference_corpus.load_reference_tree`
- Manifest: `docs/ai-session-memory/reference-corpus/archdaily/DB_MANIFEST.json`

Collections:

- `api/projects_latest`
- `api/houses`
- `api/apartments`
- `api/housing`
- `api/cultural_architecture`
- `seeded/iconic_precedents`
- `seeded/initial_smoke`

## Image Collection Methods

### ArchDaily Search API

Use this for broad DB slices. Browser Playwright crawling currently times out on
the search page, but the JSON API used by the ArchDaily search app works.

```bash
PYTHONPATH=ARR/backend ARR/backend/.venv/bin/python -m design.maas.preference.harness \
  --crawl-only \
  --crawl-archdaily-api \
  --archdaily-collection houses \
  --archdaily-api-path /projects/categories/houses \
  --archdaily-pages 2 \
  --archdaily-limit 36 \
  --download-archdaily-images
```

Output:

```text
docs/ai-session-memory/reference-corpus/archdaily/api/houses/metadata.jsonl
docs/ai-session-memory/reference-corpus/archdaily/api/houses/images/
docs/ai-session-memory/reference-corpus/archdaily/api/houses/manifest.json
```

### Manual Seed URLs

Use this for exact precedents such as BIG/OMA projects where search query
results are noisy.

1. Add URLs to `seed_urls.txt`.
2. Run:

```bash
PYTHONPATH=ARR/backend ARR/backend/.venv/bin/python -m design.maas.preference.harness \
  --crawl-only \
  --collect-archdaily \
  --archdaily-collection iconic_precedents \
  --download-archdaily-images
```

Output:

```text
docs/ai-session-memory/reference-corpus/archdaily/seeded/iconic_precedents/metadata.jsonl
docs/ai-session-memory/reference-corpus/archdaily/seeded/iconic_precedents/images/
docs/ai-session-memory/reference-corpus/archdaily/seeded/iconic_precedents/manifest.json
```

## Browser Probe

Playwright probe:

```bash
node docs/playwright/check-archdaily-crawl.cjs \
  https://www.archdaily.com/search/projects \
  docs/ai-session-memory/reference-corpus/archdaily/playwright_probe.json \
  docs/ai-session-memory/reference-corpus/archdaily/playwright_probe.png
```

Current result: the Playwright browser path times out; use the API/seed
collectors above for the DB.
