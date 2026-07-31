# MAAS Evidence Bundle

Updated: 2026-06-09

## Purpose

The MAAS evidence bundle is the canonical JSON packet that one mass candidate must carry before agents can review it.

Do not make this only a massing geometry schema. A reviewable candidate must include legal, datum, program, parking/access, life-safety, environmental, artifact, provenance, and agent-review evidence.

Machine-readable draft schema:

- `schema/arr.maas.evidence.v0.schema.json`
- `schema/arr.maas.evidence.v0.example.json`

Treat that schema file as the current contract source of truth. This markdown explains the design rationale and examples.

Current local sanity check:

```bash
python - <<'PY'
import json
from pathlib import Path
schema = json.loads(Path('docs/ai-session-memory/schema/arr.maas.evidence.v0.schema.json').read_text())
data = json.loads(Path('docs/ai-session-memory/schema/arr.maas.evidence.v0.example.json').read_text())
assert not [k for k in schema['required'] if k not in data]
assert not [k for k in data if k not in schema['properties']]
print('manual contract sanity ok')
PY
```

Full Draft 2020-12 validation can use the existing AJV 8 install under AutoGen Studio:

```bash
node - <<'NODE'
const fs = require('fs');
const Ajv2020 = require('./AG/autogen_a2a_kit/autogen_source/python/packages/autogen-studio/frontend/node_modules/ajv/dist/2020').default;
const schema = JSON.parse(fs.readFileSync('docs/ai-session-memory/schema/arr.maas.evidence.v0.schema.json','utf8'));
const data = JSON.parse(fs.readFileSync('docs/ai-session-memory/schema/arr.maas.evidence.v0.example.json','utf8'));
const ajv = new Ajv2020({ allErrors: true, strict: false });
const validate = ajv.compile(schema);
if (!validate(data)) {
  console.error(JSON.stringify(validate.errors, null, 2));
  process.exit(1);
}
console.log('AJV Draft 2020-12 validation ok');
NODE
```

## Stability Principles

This schema is expensive to change because it will be consumed by ARR, AG-light MCP tools, agents, Graph DB provenance, CLI gates, and the frontend. Design it with a small stable core and extensible domain blocks.

Rules:

1. Keep top-level keys stable. Add new checks inside domain blocks instead of adding many new top-level keys.
2. Every check-like object must carry `status`, `source`, `basis`, and `evidence_refs` when possible.
3. Use explicit status values: `pass`, `fail`, `needs_evidence`, `not_applicable`, `text_only`, `unknown`.
4. Separate measured facts from legal judgments. Example: `provided_count` and `required_count` are facts; `status` is the judgment.
5. Do not remove fields. Deprecate with `deprecated: true` and add replacements.
6. Prefer arrays of typed objects for evolving items such as legal checks, validator runs, and evidence artifacts.
7. Store geometry as GeoJSON artifacts, not as graph nodes. Store graph IDs, hashes, and relationships separately.
8. Include hashes/IDs for large artifacts so the same evidence can be referenced by agents, CLI outputs, and Neo4j without copying everything.
9. Unknown is not pass. If a legal domain cannot be checked, record `needs_evidence` or `text_only`.
10. Keep both human-readable summaries and machine-readable fields. Agents need summaries; validators need structured values.

## 2026-06-09 Aesthetic Generation Update

MAAS image generation is downstream of the evidence bundle. It is not allowed to
replace the legal mass.

Local implementation started under:

- `ARR/backend/design/maas/aesthetic/`
- `ARR/backend/design/maas/reviews/2026-06-09_aesthetic_image_generation_plan.md`

Current contract:

```text
MAAS evidence bundle
-> locked reference render spec
-> facade/material prompt
-> image/texturing backend
-> silhouette/geometry validation
-> generated asset reference in evidence
```

The image backend may change facade material, window rhythm, surface detail,
lighting, and presentation style. It must not change mass geometry, footprint,
height, floor count, setbacks, roofline, or legal envelope.

Latest research triage:

- UniTEX, CVPR 2026 / arXiv 2025, is locally checked out for inspection at
  `ARR/backend/design/maas/aesthetic/external/UniTEX` revision `affa1e2`.
  License is Apache-2.0. It accepts a reference image and input mesh path, but
  requires a separate GPU/CUDA environment.
- MD-ProjTex has a repository, but code is currently marked as coming soon.
- WACV 2025 `3D Synthesis for Architectural Design` is the closest architectural
  paper fit, but no code link was visible in the latest check.

Do not install UniTEX dependencies into the ARR Django backend venv. If used, it
should become a separate GPU worker called by a small ARR adapter.

## 2026-06-09 Playwright Verification

Playwright verification was run against the live local stack:

- Frontend: `http://127.0.0.1:5174/`
- Design page: `http://127.0.0.1:5174/design`
- Land page: `http://127.0.0.1:5174/land`
- MAAS evidence API:
  `http://127.0.0.1:18000/design/jobs/6ee6ae55-7f06-45d7-ac7e-0a5013c22b00/results/900000/evidence/`
- AG-light health: `http://127.0.0.1:8200/health`

Result file:

- `docs/playwright/maas-aesthetic-verify/verify-results.json`

Observed results:

- Frontend root returned HTTP 200 and rendered the law search surface.
- `/design` returned HTTP 200 and rendered `MAAS Legal Morphology Search`.
- `/land` returned HTTP 200 and rendered the parcel selection surface.
- Playwright console/page/request error count was 0.
- MAAS evidence API returned HTTP 200.
- Evidence summary:
  - `schema_version`: `arr.maas.evidence.v0`
  - `pnu`: `1168011800104170004`
  - `candidate_id`: `maas_01`
  - `final_status`: `needs_evidence`
  - `candidate.diversity.class`: `plan_diverse`
  - `legal.graph_projection.available`: `true`
  - `legal.law_articles.length`: `6`
  - `final_decision.missing_evidence.length`: `4`
- AG-light `/health` returned HTTP 200.

Known verification caveat:

- Playwright `page.screenshot()` timed out while waiting in Chromium's screenshot
  capture path, so PNG screenshots were not produced in this run. DOM rendering,
  HTTP status, console events, and API evidence were verified successfully.

## 2026-06-09 `/design` Focused Verification

Focused Playwright verification was then run only against `/design`.

Result files:

- `docs/playwright/design-route-verify/design-route-verify.json`
- `docs/playwright/design-route-verify/design-optimize-verify.json`

Flow checked:

1. Opened `http://127.0.0.1:5174/design`.
2. Filled PNU `1168011800104170004`.
3. Clicked `조회`.
4. Verified API calls:
   - `POST /design/site-boundary/` -> HTTP 200
   - `POST /design/auto-constraints/` -> HTTP 200
5. Verified rendered `/design` text:
   - `MAAS Legal Morphology Search`
   - site area `264.13 m²`
   - zoning `제2종일반주거지역`
   - legal basis/datum section
   - `MAAS Agent Workspace`
6. Ran `OPTIMIZE` from the UI with a small test budget.
7. Verified API calls:
   - `POST /design/jobs/` -> HTTP 202
   - `GET /design/jobs/4db643f9-c9d0-4d1f-9d7c-db5820b3b6a5/results/` -> HTTP 200
8. Verified backend job result:
   - job status `complete`
   - `total_designs`: 18
   - designs with `mass_geojson`: 18
   - unique `mass_shape`: 17

Mass generation confirmed through `/design` route. The frontend consumes
`designs[].mass_geojson`; the results endpoint does not need a top-level
`feature_collection` for this route.

## 2026-06-09 Aesthetic Pipeline Implementation

The MAAS aesthetic pipeline is now implemented as a modular backend package, not
only a plan.

Implemented modules:

- `ARR/backend/design/maas/aesthetic/PLANMODE.md`
- `ARR/backend/design/maas/aesthetic/contracts.py`
- `ARR/backend/design/maas/aesthetic/pipeline.py`
- `ARR/backend/design/maas/aesthetic/renderers/reference_png.py`
- `ARR/backend/design/maas/aesthetic/adapters/openai_image.py`
- `ARR/backend/design/maas/aesthetic/adapters/nano_banana.py`
- `ARR/backend/design/maas/aesthetic/storage/evidence_assets.py`

Implemented flow:

```text
evidence bundle
-> build_aesthetic_image_job()
-> locked_geometry snapshot
-> ReferencePngRenderer
-> provider adapter
-> provider result validation
-> optional evidence asset/provenance attachment
```

Provider status:

- `placeholder`: local dry-run, no external provider.
- `gpt-image`: OpenAI Image API edit adapter. Uses `OPENAI_API_KEY`; default
  model `gpt-image-2`.
- `nano-banana`: Gemini 2.5 Flash Image adapter. Uses `GEMINI_API_KEY` or
  `GOOGLE_API_KEY`; default model `gemini-2.5-flash-image-preview`. Also
  supports generic HTTP fallback with `NANO_BANANA_ENDPOINT` and
  `NANO_BANANA_API_KEY`.
- `unitex`: external code inspected; should be separate CUDA worker.

Live dry-run result:

- Source evidence:
  `job_id=6ee6ae55-7f06-45d7-ac7e-0a5013c22b00`, `design_id=900000`
- Pipeline status: `needs_provider`
- Job validation: `pass`
- Provider validation: `pass`
- Reference PNG:
  `docs/playwright/design-route-verify/aesthetic-reference/62e70d5c89fd8b59.png`
- Reference SHA256:
  `311e497423e22f7e941e0232c45794b158f34ebbeafea875dd015f0204cf794a`

Tests:

- `env -u NEO4J_URI .venv/bin/python manage.py test design.test_maas_export --verbosity 1`
- Result: 23 tests OK

Important testing note:

- Tests explicitly clear `OPENAI_API_KEY`, `NANO_BANANA_ENDPOINT`, and
  `NANO_BANANA_API_KEY` so provider tests never call external paid APIs.

## 2026-06-09 Provider Model Correction

Provider defaults were corrected after checking current public docs.

- OpenAI GPT Image:
  - Default model changed from `gpt-image-1.5` to `gpt-image-2`.
  - Official docs say GPT Image models include the latest `gpt-image-2`, and
    Image API supports generation and edit endpoints.
  - Source: https://developers.openai.com/api/docs/guides/image-generation
  - Source: https://developers.openai.com/api/docs/models/gpt-image-2
- Nano Banana:
  - Implemented as Google Gemini API first, not only generic HTTP fallback.
  - Default model: `gemini-2.5-flash-image-preview`.
  - Uses `GEMINI_API_KEY` or `GOOGLE_API_KEY`.
  - Generic HTTP fallback remains available with `NANO_BANANA_ENDPOINT` and
    `NANO_BANANA_API_KEY`.
  - Source: https://developers.googleblog.com/introducing-gemini-2-5-flash-image/

Updated code:

- `ARR/backend/design/maas/aesthetic/adapters/openai_image.py`
- `ARR/backend/design/maas/aesthetic/adapters/nano_banana.py`
- `ARR/backend/design/maas/aesthetic/README.md`
- `ARR/backend/design/maas/aesthetic/PLANMODE.md`

Verification:

- `env -u NEO4J_URI .venv/bin/python manage.py test design.test_maas_export --verbosity 1`
- Result: 23 tests OK
- Live Nano Banana dry-run returns `needs_provider` with official Gemini key
  guidance and still generates the locked reference PNG.

## 2026-06-09 `/design` Screenshot Capture

Playwright `body` locator screenshots were captured successfully for `/design`.

Files:

- `docs/playwright/design-captures/design_lookup_1168011800104170004.png`
- `docs/playwright/design-captures/design_optimize_result_1168011800104170004.png`
- `docs/playwright/design-captures/capture-result.json`

Result:

- PNG size: 1440 x 1000.
- PNU: `1168011800104170004`.
- `/design` lookup rendered site area `264.13 m²` and zoning
  `제2종일반주거지역`.
- Optimization completed with 18 pareto candidates.
- BUILDING MASS panel rendered:
  - algorithm `maas_legal_envelope`
  - height `16.8m`
  - floors `6F`
  - BCR `39.0%`
  - FAR `175.5%`
  - floor area `463m²`
- Headless browser WebGL is disabled, so the central 3D map/canvas area displays
  the fallback message instead of the 3D mass view.

Correction after visual review:

- Treating a WebGL-disabled capture as visually verified was wrong.
- `/design` now has a 2D SVG fallback inside `SiteMapPanel` that renders
  `massFeatures[].mass_geojson` when VWorld/Cesium WebGL is unavailable.
- Updated file:
  `ARR/frontend/src/design/components/SiteMapPanel.tsx`
- Verification:
  - `npm run type-check` passed.
  - Fresh Vite server restarted on `127.0.0.1:5174`.
  - Playwright capture result:
    `docs/playwright/design-captures/design_optimize_result_with_2d_fallback_1168011800104170004.png`
  - Capture includes `2D MASS PREVIEW`, selected mass footprint, site boundary,
    and BUILDING MASS metrics.

## Schema Shape Decision

Use a hybrid layout:

- Stable top-level sections: `project`, `site`, `candidate`, `geometry`, `legal`, `program`, `mobility`, `life_safety`, `environment`, `validators`, `assets`, `provenance`, `agent_reviews`, `final_decision`.
- Inside each legal/design domain, use normalized check objects.
- Keep a flat `checks[]` index at top level so agents and Graph DB can query all compliance checks without knowing every domain's nested shape.

Canonical check object:

```json
{
  "key": "parking.required_count",
  "label": "주차대수",
  "status": "pass|fail|needs_evidence|not_applicable|text_only|unknown",
  "severity": "hard|soft|info",
  "source": "arr|ag-light|cli|law_text|manual|external",
  "basis": {
    "law_articles": [],
    "ordinance": null,
    "formula": null,
    "rule_text": ""
  },
  "inputs": {},
  "computed": {},
  "required": {},
  "provided": {},
  "evidence_refs": [],
  "warnings": [],
  "errors": []
}
```

This check object should be reused for parking, landscaping, fire, evacuation, accessibility, energy, public open space, site road requirement, and future domains. Do not make each domain invent a totally different result shape.

Top-level check index:

```json
{
  "checks": [
    {
      "key": "legal.bcr",
      "domain": "legal",
      "status": "pass",
      "severity": "hard",
      "object_refs": ["candidate:maas_01", "geometry:mass_geojson"],
      "evidence_refs": ["evidence:regulation_result", "evidence:mass_metrics"]
    }
  ]
}
```

Domain blocks may contain richer nested data, but every pass/fail/unknown judgment must also appear in `checks[]`.

## External Shape To Borrow

- GeoJSON / RFC 7946: keep mass/site/floor geometries as valid GeoJSON Features or FeatureCollections, with `bbox` where practical.
- STAC-style assets: use an `assets` object for PNG/SVG/SCAD/VWorld screenshots and generated evidence files.
- W3C PROV-style provenance: keep `entities`, `activities`, and `agents` concepts, plus derivation links such as generated-by, used, and derived-from.
- JSON Schema 2020-12: write an actual machine-checkable schema after the first implementation pass.

Building-code specific references:

- buildingSMART IDS: model requirements should be computer-interpretable and checkable against a model. ARR should borrow explicit requirements, applicability, and required/provided values, but not adopt IDS XML as the internal format yet.
- SHACL: validation should produce explicit constraint reports against a data graph. ARR should borrow the "shape/check report" concept for each rule.
- Automated Code Compliance Checking research: most ACC pipelines split into rule interpretation, model preparation, rule execution, and check reporting. The evidence bundle must keep those stages separate.
- BIM Collaboration Format (BCF): issue reports need textual comments plus contextual view/snapshot references. ARR should use `issues` and `assets` instead of hiding review failures in prose.
- LegalRuleML: useful as a future target for normative legal rules, but too heavy for the first internal MAAS schema.

## Required Top-Level Fields

```json
{
  "schema_version": "arr.maas.evidence.v0",
  "bundle_id": "maas-evidence:<job_id>:<candidate_id>",
  "created_at": "ISO-8601",
  "source": {
    "system": "ARR",
    "algorithm": "maas_legal_envelope",
    "generator_version": "git-sha-or-build-id"
  },
  "project": {},
  "site": {},
  "candidate": {},
  "legal": {},
  "geometry": {},
  "program": {},
  "mobility": {},
  "life_safety": {},
  "environment": {},
  "checks": [],
  "issues": [],
  "validators": {},
  "assets": {},
  "provenance": {},
  "agent_reviews": [],
  "final_decision": {}
}
```

## Project / Application Context

This is mandatory. Building-code applicability changes by application type and review stage. Do not infer it only from the mass.

```json
{
  "project_id": null,
  "review_stage": "concept|precheck|building_permit|change_of_use|major_repair|construction_start|use_approval",
  "application_type": "new_construction|extension|renovation|relocation|change_of_use|major_repair|unknown",
  "jurisdiction": {
    "country": "KR",
    "sido": null,
    "sigungu": null,
    "authority": null
  },
  "applicant": {
    "owner_type": null,
    "designer_required": null,
    "architect_license_required": null
  },
  "review_scope": {
    "mass_only": true,
    "includes_floor_plan": false,
    "includes_parking_layout": false,
    "includes_fire_strategy": false,
    "includes_energy": false,
    "includes_structural": false
  },
  "assumptions": [],
  "exclusions": []
}
```

If `application_type` is unknown, all application-dependent checks must be `needs_evidence`.

## Site

```json
{
  "pnu": "1168011800104170004",
  "address": "",
  "site_area_m2": 0,
  "site_polygon": { "type": "Feature" },
  "administrative_codes": {
    "sido": null,
    "sigungu": null,
    "bjdong": null,
    "sigungu_code": null
  },
  "zones": [],
  "matched_zones": [],
  "unmatched_zones": [],
  "overlay_zones": [],
  "district_unit_plan": {
    "applies": null,
    "plan_id": null,
    "evidence_refs": []
  },
  "land_info": {
    "land_area_m2": null,
    "land_use": null,
    "official_land_price": null,
    "land_category": null,
    "land_use_situation": null
  },
  "road_frontages": [],
  "neighbor_parcels": []
}
```

## Candidate

```json
{
  "job_id": "",
  "design_id": 0,
  "candidate_id": "maas_01",
  "variant_id": "maas_01",
  "mass_shape": "legal_layered_max",
  "maas_concept": "",
  "intended_use": {
    "building_type": "공동주택",
    "primary_use": null,
    "secondary_uses": [],
    "use_classification": null,
    "units": null,
    "households": null,
    "occupancy_assumption": null
  },
  "score": 0,
  "rank": 0,
  "is_pareto_optimal": true,
  "is_feasible": true,
  "objectives": {},
  "repair_actions": [],
  "rejected_siblings": []
}
```

## Geometry

```json
{
  "crs": "EPSG:4326 for GeoJSON, local UTM only inside metrics",
  "mass_geojson": { "type": "Feature" },
  "bbox": [],
  "floor_plates": [],
  "floor_groups": [],
  "mass_volumes": [],
  "maas_model": {},
  "verb_sequence": [],
  "geometry_metrics": {
    "height_m": 0,
    "num_floors": 0,
    "floor_height_m": 0,
    "footprint_area_m2": 0,
    "total_floor_area_m2": 0,
    "min_floor_plate_area_m2": 0,
    "min_setback_m": 0,
    "open_space_pct": 0,
    "shape_signature": ""
  }
}
```

## Legal

Split legal review by domain. Do not hide everything under `legal_metrics`.

```json
{
  "summary": {
    "status": "pass|fail|unknown",
    "hard_failures": [],
    "warnings": []
  },
  "limits": {
    "bcr_pct": null,
    "far_pct": null,
    "height_limit_m": null
  },
  "metrics": {
    "bcr_pct": null,
    "far_pct": null,
    "height_m": null
  },
  "datum": {},
  "setbacks": {},
  "sunlight": {},
  "daylight_spacing": {},
  "road_building_line": {},
  "corner_cutoff": {},
  "landscaping": {},
  "building_use": {},
  "site_road_requirement": {},
  "split_zoning": {},
  "use_classification": {
    "requested_use": null,
    "normalized_use": null,
    "allowed": null,
    "prohibited": null,
    "conditional": null,
    "requires_discretionary_review": null,
    "basis": {
      "zone_tables": [],
      "ordinance_refs": [],
      "law_articles": []
    },
    "evidence_refs": []
  },
  "ordinance_overrides": [],
  "law_articles": [],
  "extended_regulations": {}
}
```

Local sources that should feed this:

- ARR `land.services.regulation_calculator`: 11 core regulations including BCR, FAR, height, sunlight, road diagonal, corner cutoff, building line, adjacent setback, parking, landscaping, and designation line.
- ARR `land.services.regulation_calculator_ext`: 31 extended regulations including use restriction, 접도의무, 대지분할, 채광 인동간격, 공개공지, 구조, 내화, 방화구획, 승강기, 개발행위허가, 소방, 장애인, 에너지, 피난, 채광/환기, 오수, 학교/문화재/군사, 설비.
- AG-light `worker/src/regulation/calculator.ts` and `calculator-ext.ts`: lightweight mirror for agent/MCP calls.

Use/zoning is not optional. At minimum, the bundle needs checks for:

- `legal.use.allowed_by_zone`
- `legal.use.prohibited_by_zone`
- `legal.use.conditional_or_discretionary`
- `legal.use.district_unit_plan_override`
- `legal.use.split_zoning_intersection`
- `legal.use.overlay_zone_restriction`

If the requested building use is unknown, these checks must be `needs_evidence`, not `pass`.

## Review Domain Taxonomy

Every evidence bundle should classify checks under these domains. A domain can be `not_applicable`, `text_only`, or `needs_evidence`, but it should not silently disappear.

```text
project_admin
  - application type, review stage, designer/license/document requirements

site_rights_and_cadastre
  - PNU, ownership/parcel identity, cadastral area, land category, official land price

zoning_and_land_use
  - 용도지역/지구/구역, 지구단위계획, overlay zones, allowed/prohibited/conditional use

bulk_and_density
  - BCR, FAR, height, floor count, gross floor area, exempt/excluded floor area assumptions

building_line_and_setbacks
  - 건축선, 인접대지 이격, 도로 후퇴, 대지 안의 공지, corner cutoff

datum_and_terrain
  - §119 datum, road datum, neighbor datum, §86 average plane, DEM source, split bands

sunlight_daylight_view
  - 정북일조, 채광 인동간격, 도로/인접 사선 or replacement height controls, room daylight/ventilation

roads_access_and_fire_access
  - 접도의무, frontage, road width, access geometry, emergency vehicle precheck

parking_loading_and_mobility
  - 주차대수, accessible/EV/mechanical parking assumptions, loading/drop-off, ramp/aisle feasibility

landscape_open_space_public
  - 조경, 공개공지, public open space, open-space incentives/relaxations

program_and_occupancy
  - building type, primary/secondary uses, households/units, occupancy assumptions, mixed-use treatment

core_circulation_and_egress
  - core area, corridor, stairs, exits, travel distance precheck, refuge/special stairs placeholders

fire_and_life_safety
  - fire compartment, fire-resistant construction, fire protection systems, finishing materials

structure_and_geotechnical
  - structural safety, seismic, retaining wall/slope/site safety, geotechnical assumptions

accessibility_and_welfare
  - disabled access, elevators, barrier-free, required welfare/community facilities where applicable

energy_green_and_environment
  - energy-saving plan, green building, insulation/system placeholders, environmental/disaster review

mechanical_electrical_plumbing
  - water, sewage, ventilation, electrical/communication, building systems, capacity placeholders

external_restricted_zones
  - school, cultural heritage, military, park, development restriction, other overlay constraints

housing_or_special_use_law
  - housing-law specific approvals, dormitory/hotel/medical/education/sales/cultural special rules

model_documents_and_artifacts
  - drawings, section/plan PNG, VWorld screenshot, GeoJSON, SCAD/mesh, hashes, model completeness

provenance_and_review
  - validator runs, agent reviews, issues, final decision, evidence lineage
```

This taxonomy is intentionally wider than current MAAS. Current unsupported domains should become `needs_evidence` or `text_only`, not `pass`.

## Program

```json
{
  "building_type": "공동주택",
  "program_packing": [],
  "core": {
    "status": "pass|fail|unknown",
    "min_core_area_m2": null,
    "provided_core_area_m2": null,
    "vertical_shafts": []
  },
  "usable_depth": {},
  "egress_precheck": {},
  "floor_plate_viability": []
}
```

Current `program_packing.status = ok` is not enough. It is a first-pass packing result, not a full architectural feasibility certificate.

## Mobility / Parking

Parking cannot stay as a text-only rule.

```json
{
  "parking": {
    "status": "pass|fail|unknown|text_only",
    "rule": "",
    "article": "",
    "required_count": null,
    "provided_count": null,
    "calculation_basis": {
      "building_type": "",
      "floor_area_m2": null,
      "units": null,
      "local_ordinance": null
    },
    "layout_feasibility": {
      "ramp_possible": null,
      "drive_aisle_possible": null,
      "mechanical_parking_possible": null
    }
  },
  "access": {
    "site_road_frontage_m": null,
    "min_required_frontage_m": null,
    "fire_truck_access_precheck": null
  }
}
```

Until a real parking calculator exists, parking must be:

```json
{
  "status": "needs_evidence",
  "reason": "parking rule text exists but required/provided count and layout feasibility are not computed"
}
```

Never mark parking `pass` from the current `parking_rule` string alone.

## Life Safety

```json
{
  "fire": {},
  "evacuation": {},
  "structural_safety": {},
  "elevator": {},
  "accessibility": {},
  "finishing_materials": {}
}
```

These are initially threshold/text checks, but the bundle must reserve slots so agents do not pretend BCR/FAR is the whole law.

## Environment / Systems

```json
{
  "energy_saving": {},
  "room_daylighting_ventilation": {},
  "sewage_treatment": {},
  "building_systems": {},
  "cpted": {},
  "public_open_space": {},
  "infrastructure_fee": {}
}
```

## Validators

```json
{
  "overall_status": "pass|fail|unknown",
  "runs": [
    {
      "validator": "maas_floor_plate_validator",
      "status": "pass",
      "checked_at": "ISO-8601",
      "inputs_hash": "",
      "result": {},
      "hard_failures": [],
      "warnings": []
    }
  ]
}
```

Validator runs should include CLI-derived gates:

- `check-design.mjs`
- `render_section.py`
- `render_plan.py`
- `verify_images.py`
- `verify_plan_images.py`
- `capture-vworld.mjs` when available

## Issues

Borrow BCF's idea: a failure is not only a boolean. It needs a topic, viewpoint/artifact references, responsible checker, and resolution state.

```json
{
  "issues": [
    {
      "id": "issue:parking:missing-count",
      "topic_type": "missing_evidence",
      "severity": "hard",
      "title": "주차대수 산정 미완료",
      "description": "parking_rule text exists, but required_count/provided_count/layout feasibility are missing.",
      "status": "open",
      "check_refs": ["check:mobility.parking.required_count"],
      "asset_refs": [],
      "assignee": "mobility_reviewer"
    }
  ]
}
```

## Assets

Use stable asset keys, STAC-style:

```json
{
  "section_png": {
    "href": "cli/design-regulation-check/out/pysections/...",
    "type": "image/png",
    "roles": ["evidence", "section"]
  },
  "plan_png": {
    "href": "",
    "type": "image/png",
    "roles": ["evidence", "plan"]
  },
  "vworld_screenshot": {
    "href": "",
    "type": "image/png",
    "roles": ["evidence", "visual-qa"]
  },
  "scad_export": {
    "href": "",
    "type": "text/plain",
    "roles": ["derived", "mesh-export"]
  }
}
```

## Provenance

```json
{
  "entities": [],
  "activities": [],
  "agents": [],
  "relations": [
    {"type": "used", "activity": "generate_maas_variants", "entity": "site_polygon"},
    {"type": "wasGeneratedBy", "entity": "candidate:maas_01", "activity": "generate_maas_variants"},
    {"type": "wasDerivedFrom", "entity": "candidate:maas_01", "source": "seed:legacy_best"}
  ]
}
```

This maps directly to Neo4j later. Do not store full geometry in Neo4j as the source of truth; store IDs, hashes, relationships, and small summaries.

## Agent Reviews

```json
[
  {
    "agent": "law_reviewer",
    "status": "pass|fail|needs_evidence",
    "scope": ["bcr", "far", "height", "setback", "parking"],
    "claims": [],
    "evidence_refs": [],
    "hard_failures": [],
    "warnings": [],
    "summary": ""
  }
]
```

## Final Decision

```json
{
  "status": "pass|fail|needs_evidence",
  "decided_by": "final_judge",
  "blocking_failures": [],
  "missing_evidence": [],
  "accepted_risks": [],
  "summary": ""
}
```

## Non-Negotiable

If parking, legal article basis, datum, floor plates, section/plan artifacts, and visual placement are missing, the bundle status must be `needs_evidence`, not `pass`.

## Implementation Order

1. Add ARR evidence exporter: done in `ARR/backend/design/maas/evidence.py`.
   - `ARR/backend/design/maas/evidence.py`
   - Input: `OptimizationJob`, `DesignResult`, `auto_constraints` result, optional CLI artifact paths.
   - Output must validate against `arr.maas.evidence.v0.schema.json`.
2. Add endpoint: done.
   - `GET /design/jobs/<job_id>/results/<design_id>/evidence/`
   - This endpoint should never invent missing checks as pass.
3. Add AG-light MCP tools: first pass done.
   - `arr_maas_evidence(job_id, design_id)`
   - `arr_maas_review(job_id, design_id)`
4. Add Graph DB projection:
   - Store `bundle_id`, `candidate_id`, check nodes, issue nodes, asset refs, and provenance refs.
   - Do not store full GeoJSON as graph truth.
5. Add frontend/A2UI rendering:
   - Summary decision.
   - Hard failures.
   - Missing evidence.
   - Domain check matrix.
6. Only after the above, let multi-agent reviewers operate over the bundle.

## Current Implementation Status

Implemented on 2026-06-08:

- Machine-readable schema: `docs/ai-session-memory/schema/arr.maas.evidence.v0.schema.json`.
- Example bundle: `docs/ai-session-memory/schema/arr.maas.evidence.v0.example.json`.
- ARR exporter: `ARR/backend/design/maas/evidence.py`.
- ARR endpoint: `GET /design/jobs/<job_id>/results/<design_id>/evidence/`.
- Test coverage: `MaasEvidenceBundleEndpointTest` in `ARR/backend/design/test_maas_export.py`.
- AG-light MCP tools: `arr_maas_evidence(job_id, design_id)` and `arr_maas_review(job_id, design_id)` in `AG-light/server/mcp_tools/tools.py`.

Verified:

- `ARR/backend/.venv/bin/python manage.py test design.test_maas_export` -> 16 tests passed.
- AJV Draft 2020-12 schema validation of the example bundle -> passed. AJV warns that date-time format is ignored because `ajv-formats` is not installed in that node_modules tree; structural schema validation still passed.
- `python -m py_compile AG-light/server/mcp_tools/tools.py` -> passed.
- Live ARR endpoint check on `http://127.0.0.1:18000/design/jobs/6ee6ae55-7f06-45d7-ac7e-0a5013c22b00/results/900000/evidence/` -> JSON returned with `schema_version = arr.maas.evidence.v0` and `final_decision.status = needs_evidence`.
- AG-light local Python environment created at `AG-light/server/.venv` and installed from `AG-light/server/requirements.txt`.
- AG-light server check passed on `http://127.0.0.1:8200/health` with MCP mounted at `/mcp/mcp`.
- MCP streamable HTTP client check passed against `http://127.0.0.1:8200/mcp/mcp`:
  - `list_tools` returned 22 tools.
  - `arr_maas_evidence` and `arr_maas_review` were present.
  - `arr_maas_review(job_id=6ee6ae55-7f06-45d7-ac7e-0a5013c22b00, design_id=900000)` returned `final_status = needs_evidence`.
- Evidence correctness fixes applied after review:
  - Numeric values now preserve `0` and `0.0`; fallbacks only happen for `None`.
  - Missing PNU now remains `null`; ARR does not synthesize `"0000000000000000000"`.
  - Missing PNU adds `site_rights_and_cadastre.pnu_identity` as a hard `needs_evidence` check and `issue:site:missing-pnu`.
  - AG-light `health_check()` now marks overall status false when bus or memory checks fail.
  - AG-light MCP mount now creates a fresh FastMCP/session manager during app lifespan startup, so repeated TestClient startup/shutdown does not reuse a spent session manager.
- Additional verification after these fixes:
  - `ARR/backend/.venv/bin/python manage.py test design.test_maas_export` -> 18 tests passed.
  - AG-light `TestClient(main.app)` startup/shutdown twice -> passed with MCP mounted both times.
  - AJV Draft 2020-12 schema validation -> example bundle valid; `site.pnu = null` variant valid.
- Live MCP `health_check` correctly returned overall `status = false` while Worker `8787` was down and ARR/bus/memory were reachable.
- Graph DB / Neo4j review on 2026-06-08:
  - WSL Docker CLI is not available (`docker: command not found`), so Neo4j cannot be started from this WSL session until Docker Desktop WSL integration is enabled or Neo4j Desktop is started on Windows.
  - Neo4j ports `7474` and `7687` were not listening.
  - ARR backend venv was missing the `neo4j` Python driver; `neo4j>=5.14,<6.0` was added to `ARR/backend/requirements.txt` and installed into `ARR/backend/.venv`.
  - After reinstall/restart, `law.views.HAS_NEO4J = True`, but runtime connection to `bolt://localhost:7687` still fails because the server is down.
  - `/law/article/?full_id=건축법_제60조` attempted Neo4j, logged connection failure, and fell back to Worker; Worker returned 502 at the time of verification.
  - `law/STEP/verify_system.py` was fixed so Neo4j-down cases report structured failures instead of crashing.
  - Current graph verification command:
    ```bash
    cd /mnt/d/Data/25_ACE/ARR/backend
    NEO4J_URI=bolt://localhost:7687 NEO4J_USER=neo4j NEO4J_PASSWORD=11111111 .venv/bin/python law/STEP/verify_system.py
    ```
  - Current result with Neo4j down: `0/6` checks passed, all failures are connection-refused on `localhost:7687`.
  - Important: Graph DB/law assets exist, but MAAS evidence export still does not query Neo4j. The next implementation step is an adapter that projects law article refs, graph status, and provenance into the MAAS evidence bundle.
- Neo4j Desktop WSL connectivity after Windows restart on 2026-06-08:
  - Windows Neo4j is now listening on `7474` and `7687`; WSL still cannot use `localhost` because that points to WSL itself.
  - Use `NEO4J_URI=bolt://172.27.80.1:7687` from this WSL session. `host.docker.internal:7687` also accepted TCP.
  - Verified graph contents through Bolt: `HANG=12069`, `HO=11550`, `JO=4928`, `MOK=2156`, `JANG=258`, `JEOL=102`, `LAW=58`, `Domain=5`.
  - `law/STEP/verify_system.py` passed `6/6` with `NEO4J_URI=bolt://172.27.80.1:7687 NEO4J_USER=neo4j NEO4J_PASSWORD=11111111`.
  - ARR backend was restarted on `127.0.0.1:18000` with the same WSL Neo4j URI.
  - `/law/article/?full_id=건축법_제60조` now returns the Neo4j article payload directly: title `건축물의 높이 제한`, `hang_count=4`, `ho_count=0`.
  - Current MAAS evidence sample `job_id=6ee6ae55-7f06-45d7-ac7e-0a5013c22b00`, `design_id=900000` still returns `schema=arr.maas.evidence.v0`, `pnu=1168011800104170004`, `checks=7`, `issues=3`, `agent_reviews=0`; Graph DB law provenance is not projected into the evidence bundle yet.
- Playwright DOM smoke check for `http://127.0.0.1:5174/design` passed:
  - HTTP status 200.
  - MAAS UI text rendered.
  - No console errors.
  - No failed network requests.
  - Headless browser still reports WebGL unavailable, so this is not a final VWorld pixel/3D validation.
- Repeat Playwright check after Neo4j/ARR restart on 2026-06-08 also passed:
  - `http://127.0.0.1:5174/design` returned HTTP 200.
  - Body rendered `건물 매스 최적화`, `MAAS Legal Morphology Search`, `MAAS 법규 탐색`, and `MAAS Agent Workspace`.
  - No Vite/error overlay, no console errors, no failed requests.
  - Browser still reports `WebGL을 사용할 수 없어 3D 지도를 비활성화했습니다.` in headless mode, so VWorld/Cesium pixel validation remains unproven.
- Code review fixes on 2026-06-09:
  - AG-light `create_app()` now copies registered routes from the module app when called after import, so repeated TestClient/factory calls expose `/health`, `/bus/*`, and `/memory/*` instead of returning 404.
  - AG-light MAAS tool default `ARR_BACKEND_URL` is now `http://127.0.0.1:18000`, matching the current ARR Django dev server.
  - `law/STEP/verify_system.py` now checks the boolean result of `Neo4jService.connect()` and exits with one clear connection failure message instead of cascading the same connection error through every verification step.
  - Verification: AG-light TestClient `main.app` and `create_app()` both returned `200` for `/health`, `/bus/status`, `/memory/status`.
  - Verification: bad Neo4j URI returns a concise failure with WSL host-IP guidance; good WSL URI `bolt://172.27.80.1:7687` still passes `6/6`.
  - Verification: `ARR/backend/.venv/bin/python manage.py test design.test_maas_export --verbosity 1` passed 18 tests.
- MAAS review folder and law graph projection on 2026-06-09:
  - Added `ARR/backend/design/maas/reviews/` for MAAS-local review logs/gates.
  - Added `ARR/backend/design/maas/reviews/2026-06-09_maas_evidence_review.md`.
  - Added `ARR/backend/design/maas/law_provenance.py` to project Neo4j law article refs into evidence without changing pass/fail status.
  - Evidence now merges graph law refs into `checks[].basis.law_articles`, `checks[].evidence_refs`, `legal.law_articles`, and `provenance`.
  - Live sample evidence resolves 6 graph refs: BCR `국계법 제77조`, FAR `국계법 제78조`, height `건축법 제60조`, adjacent setback `건축법 제58조`, zoning/use `국계법 제76조`, parking `주차장법 제19조`.
  - Live sample still correctly reports `final_decision.status = needs_evidence`; law refs are provenance, not proof that zoning/parking/VWorld checks passed.
  - `design.test_maas_export` now has 19 tests and passes with graph projection disabled during tests unless explicitly opted in.
- MAAS massing diversity review on 2026-06-09:
  - Added `ARR/backend/design/maas/reviews/2026-06-09_massing_diversity_review.md`.
  - Existing generator already uses legal-envelope-first generation, morphology/grammar seed variants, legal repair/check, and concept-family selection.
  - Sample diversity scenario returned 8 candidates, 8 unique `mass_shape` values, and 8 unique concept labels.
  - Selected concepts included legal envelope, podium/tower, multi-step sunlight, podium tower offset, cave/inset/void, open court, courtyard, and slender bar.
  - All sample selected candidates stayed within BCR/FAR/height constraints.
  - Weak spot: footprint IoU can be 1.0 for sectional variants that share the same ground footprint but differ in volume bands; current `diversity_score` is footprint-based and should become a 3D signature.
  - Next gate: add `shape_signature_3d` / `candidate.diversity` / `maas_diversity_validator` so plan diversity and section diversity are distinguished explicitly.
- MAAS 3D diversity signature implementation on 2026-06-09:
  - `legal_mesh_optimizer.py` now attaches `shape_signature_3d` and `candidate_diversity` to generated candidates.
  - Diversity classes are `plan_diverse`, `section_diverse`, and `near_duplicate`.
  - `evidence.py` now exposes this as `candidate.diversity` and `geometry.geometry_metrics.shape_signature_3d`.
  - Existing saved candidates without the new fields get a fallback signature from saved `floor_plates` and `mass_volumes`.
  - Live sample `design_id=900000` now reports `candidate.diversity.class = plan_diverse`, `volume_count = 2`, `floor_plate_count = 5`.
  - `design.test_maas_export` still passes 19 tests.

Important limitation:

- The first exporter only assembles evidence from saved `OptimizationJob`, `DesignResult`, `mass_geojson`, and `job.constraints`.
- It deliberately marks zoning use allowance, parking count/layout, and real-browser VWorld placement as `needs_evidence`.
- It does not yet attach CLI artifacts, auto-constraints `datum_result`, law article enrichment, or Graph DB projection.
- AG-light tools currently fetch/summarize ARR evidence only. They do not run independent multi-agent review yet.
- Direct AG-light module import in the base Python environment still fails because `mcp` is not installed there (`ModuleNotFoundError: No module named 'mcp'`). This is expected. Use `AG-light/server/.venv`.

Run commands:

```bash
cd /mnt/d/Data/25_ACE/AG-light/server
ARR_BACKEND_URL=http://127.0.0.1:18000 .venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8200
```

Minimal MCP verification:

```bash
cd /mnt/d/Data/25_ACE
AG-light/server/.venv/bin/python - <<'PY'
import asyncio, json
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

URL = "http://127.0.0.1:8200/mcp/mcp"
JOB = "6ee6ae55-7f06-45d7-ac7e-0a5013c22b00"
DESIGN = 900000

async def main():
    async with streamablehttp_client(URL) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [tool.name for tool in tools.tools]
            print("tool_count", len(names))
            print("has_arr_maas_review", "arr_maas_review" in names)
            result = await session.call_tool(
                "arr_maas_review",
                {"job_id": JOB, "design_id": DESIGN},
            )
            payload = json.loads(result.content[0].text)
            print("final_status", payload["final_status"])
            print("missing_evidence", payload["missing_evidence"])

asyncio.run(main())
PY
```
