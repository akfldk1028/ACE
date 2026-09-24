# Pre-Legal Diversity r1 - 2026-08-05 KST

## Command and runtime

Executed exactly once for PNU `1168011800104170004`, program context
`neighborhood`, target `20`, and capacity ceiling `332.322 m2`:

```powershell
python manage.py generate_maas_creative_100 --count 20 --pnu 1168011800104170004 --capacity-ceiling-m2 332.322 --output-root D:\Data\25_ACE\docs\playwright\design-route-live-verify --run-id prelegal-diversity-r1 --author-mode hybrid --author-cache-root D:\Data\25_ACE\docs\ai-session-memory\reference-corpus\geometry-author-cache --max-fresh-author-requests 3
```

- Process exit: `0`
- Measured command runtime: `11.4 s`
- Result: `complete`, `20/20`, deficit `0`

## Test PASS count

- Task 2 focused author/cache/supply verification: `7 passed`.
- Task 3 report plus adjacent non-baseline verification: `15 passed`.
- Task 4 hybrid command verification with Django runner: `2 passed`.
- Final combined Django verification: `45/45 passed` in `27.856 s`.
- The prior count-100 recipe baseline was recovered without changing either
  morphology threshold. Root-cause analysis found clustered modular source
  selection in the stepped and inflated legacy pools. Their deterministic,
  coprime source strides are now `16/31` and `20/33`; the same 100-card
  schedule retains 100 unique program, geometry, and normalized-mesh hashes.

## Author cache/fresh/429 funnel

| Measure | Count |
|---|---:|
| Valid cached programs admitted to supply | 60 |
| Duplicate program hashes in supply | 0 |
| Fresh transport attempted | 0 |
| Fresh programs returned | 0 |
| Fresh programs accepted | 0 |
| Deferred after HTTP 429 | 0 |
| HTTP 429 | 0 |
| Fresh transport error | 0 |

The cache alone reached the retained target, so no provider transport was
executed. Paid author and paid VLM request counts are both `0`.

## Compile and structural PASS funnel

| Stage | PASS |
|---|---:|
| Author input available | 60 |
| Normalized program | 20 |
| Unique program hash | 20 |
| Canonical compile | 20 |
| Connected, watertight and manifold structural gate | 20 |
| Physical candidate | 20 |
| Unique geometry hash | 20 |
| Unique normalized authored-mesh hash | 20 |
| Morphology retained | 20 |

Processing stopped after the target was retained; the remaining 40 cached
programs were supply reserve, not rejected candidates.

## Duplicate and morphology rejection funnel

- Rejection count: `0`.
- Program-hash duplicate: `0`.
- Geometry-hash duplicate: `0`.
- Normalized authored-mesh duplicate: `0`.
- Morphology-distance rejection: `0`.
- Retained nearest-distance distribution: count `20`, minimum
  `0.067480418906`, median `0.149525632216`, maximum `1.0`.

## Retained phenotype/body/section/plan evidence

Post-hoc phenotype counts:

| Phenotype | Count |
|---|---:|
| morph-bridge-low | 1 |
| morph-bridge-mid | 1 |
| morph-compact-low | 7 |
| morph-compact-mid | 4 |
| morph-curved-low | 1 |
| morph-curved-tall | 1 |
| morph-linear-low | 5 |

Capacity bands are balanced at `5` each for `spatial_reserve`,
`balanced_yield`, `brief_target`, and `maximum_target`. Direct board review
shows curved bars, courtyard/U forms, stacked bodies, split/bridge bodies, and
linear bars; it is not a stepped-only board. Compact and linear low-rise forms
still account for `16/20`, so the board is distinct but not claimed to have a
uniform phenotype distribution. The current descriptor does not expose a
typed `visible_stepped` value, recorded truthfully as `unknown: 20`.

## Board path and SHA-256

- Board: `D:\Data\25_ACE\docs\playwright\design-route-live-verify\prelegal-diversity-r1\maas-creative-board.png`
- Board SHA-256: `0A2E9A340B2A83993CB855EA69A09E65B0E9E8A05CC2C9D9C349E5969F41E1B3`
- Artifact inventory: `443` files, `4,441,583` bytes total.
- Stage ledger: `D:\Data\25_ACE\docs\playwright\design-route-live-verify\prelegal-diversity-r1\maas-prelegal-stage-ledger.json`

## Comparison with r87

r87 was a full BOOK legal/downstream benchmark and selected `1/5` after law,
parking, program, final-VLM, and selector gates. Its preselection supply was
constrained by one replenishment HTTP 429 followed by four deferred cycles.
This r1 run is deliberately earlier and cheaper: it demonstrates `20/20`
distinct canonical pre-legal candidates from accepted cache with no transport
or VLM request. It does not demonstrate that any of these twenty would improve
r87's legal, parking, program, final-VLM, or selected counts.

## Acceptance decision

`PASS 20/20` for the bounded pre-legal diversity diagnostic. Every retained
candidate has a unique program hash, geometry hash, and normalized authored
mesh hash and passed canonical compilation plus connected, watertight and
manifold checks. The result is accepted only under the scope
`pre_legal_not_evaluated`.

Safe-commit decision:

```text
BLOCKED: required creative source/test dependencies are absent from HEAD or
overlap unrelated work; implementation is verified in the shared worktree but
no unsafe inner commit was made.
```

## Explicit non-claims

- This is not a law pass.
- This is not a parking pass.
- This is not a capacity certification.
- This is not a program-fit pass.
- This is not a VLM acceptance or competition-grade selection.
- This does not repair or supersede r87's `1/5` full BOOK result.
- No morphology threshold, geometry gate, legal gate, parking gate, final-VLM
  gate, selector rule, or recipe fixture was weakened.
