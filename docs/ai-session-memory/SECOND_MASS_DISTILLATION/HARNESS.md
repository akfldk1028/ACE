# Second Mass Distillation Harness

## Run

```bash
PYTHONPATH=ARR/backend ARR/backend/.venv/bin/python -m design.maas.preference.harness \
  --input-json docs/playwright/design-route-live-verify/maas-20-alt-latest.json \
  --output-json docs/playwright/design-route-live-verify/maas-20-alt-preference-latest.json \
  --image-path docs/playwright/design-route-live-verify/maas-20-alt-latest.png
```

With OpenAI VLM:

```bash
PYTHONPATH=ARR/backend ARR/backend/.venv/bin/python -m design.maas.preference.harness \
  --use-vlm \
  --vlm-model "${MAAS_PREFERENCE_VLM_MODEL:-gpt-5.4-mini}" \
  --input-json docs/playwright/design-route-live-verify/maas-20-alt-latest.json \
  --output-json docs/playwright/design-route-live-verify/maas-20-alt-vlm-latest.json \
  --image-path docs/playwright/design-route-live-verify/maas-20-alt-latest.png \
  --candidate-crop-dir docs/playwright/design-route-live-verify/preference-crops/latest
```

The VLM route crops the contact sheet first. The model sees one candidate card
per call, not the whole 20-card sheet. The crop manifest is written under
`response.preference_harness.candidate_crop_manifest`.

Collect ArchDaily metadata from seeded URLs:

```bash
PYTHONPATH=ARR/backend ARR/backend/.venv/bin/python -m design.maas.preference.harness \
  --collect-archdaily
```

Collect ArchDaily search API references and images:

```bash
PYTHONPATH=ARR/backend ARR/backend/.venv/bin/python -m design.maas.preference.harness \
  --crawl-only \
  --crawl-archdaily-api \
  --archdaily-collection houses \
  --archdaily-api-path /projects/categories/houses \
  --archdaily-pages 1 \
  --archdaily-limit 6 \
  --download-archdaily-images
```

Collect exact seeded precedents and images:

```bash
PYTHONPATH=ARR/backend ARR/backend/.venv/bin/python -m design.maas.preference.harness \
  --crawl-only \
  --collect-archdaily \
  --archdaily-collection iconic_precedents \
  --download-archdaily-images
```

Browser probe for crawlability:

```bash
node docs/playwright/check-archdaily-crawl.cjs \
  https://www.archdaily.com/search/projects \
  docs/ai-session-memory/reference-corpus/archdaily/playwright_probe.json \
  docs/ai-session-memory/reference-corpus/archdaily/playwright_probe.png
```

Current result: Playwright times out on the ArchDaily search page, while the
JSON API route succeeds.

Current DB summary:

- `docs/ai-session-memory/reference-corpus/archdaily/DB_MANIFEST.json`
- 119 unique references loaded by harness.
- 175 local image files.

## Inputs

- MAAS JSON with 20 legal candidates.
- MAAS PNG sheet or candidate image.
- Optional `reference-corpus/archdaily/seed_urls.txt`.
- Optional pairwise labels JSONL.

## Outputs

- Preference-merged MAAS JSON.
- `response.preference_harness` summary.
- Candidate-level `properties.preference_distillation`.
- Candidate-level `properties.preference_rerank`.
- Optional per-candidate PNG crops when `--candidate-crop-dir` is set.

## Verification

```bash
node docs/playwright/design-route-live-verify/verify-maas-20-alt-json.cjs \
  docs/playwright/design-route-live-verify/maas-20-alt-preference-latest.json

node docs/playwright/design-route-live-verify/verify-maas-parking-json.cjs \
  docs/playwright/design-route-live-verify/maas-20-alt-preference-latest.json

python3 docs/playwright/design-route-live-verify/render_maas_20_alt_png.py \
  docs/playwright/design-route-live-verify/maas-20-alt-preference-latest.json \
  docs/playwright/design-route-live-verify/maas-20-alt-preference-latest.png

python3 docs/playwright/design-route-live-verify/verify-maas-png.py \
  docs/playwright/design-route-live-verify/maas-20-alt-preference-latest.png \
  docs/playwright/design-route-live-verify/maas-20-alt-preference-latest.json
```

Latest real VLM verification:

```bash
node docs/playwright/design-route-live-verify/verify-maas-20-alt-json.cjs \
  docs/playwright/design-route-live-verify/maas-20-alt-vlm-latest.json

node docs/playwright/design-route-live-verify/verify-maas-parking-json.cjs \
  docs/playwright/design-route-live-verify/maas-20-alt-vlm-latest.json

python3 docs/playwright/design-route-live-verify/render_maas_20_alt_png.py \
  docs/playwright/design-route-live-verify/maas-20-alt-vlm-latest.json \
  docs/playwright/design-route-live-verify/maas-20-alt-vlm-latest.png

python3 docs/playwright/design-route-live-verify/verify-maas-png.py \
  docs/playwright/design-route-live-verify/maas-20-alt-vlm-latest.png \
  docs/playwright/design-route-live-verify/maas-20-alt-vlm-latest.json
```

2026-07-08 result:

- `vlm_status=scored`: 20/20.
- Preference quality audit: pass.
- JSON verifier: pass.
- PNG verifier: pass.
- Parking verifier: mass-stage pass 20/20, permit-final 0/20.

The harness writes `response.preference_quality_audit`. This is the next-stage
test after DB collection: the top candidates must be legal, reference-backed,
orderly, non-stepback-dominated, and preference-scored.
