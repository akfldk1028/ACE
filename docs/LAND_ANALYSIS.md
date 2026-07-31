# Land Regulation Analysis System

> Last updated: 2026-02-26

## Purpose

Given a Korean land parcel (by address or PNU code), automatically determine all applicable building regulations including BCR (건폐율), FAR (용적률), height limits, setbacks, and 31 extended regulations, with supporting legal article citations.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/land/analyze/` | Main analysis: input → regulations + law articles |
| POST | `/land/resolve/` | Address→PNU geocoding or PNU validation |
| GET | `/land/zones/` | List all 21 zoning types with default limits |
| GET | `/land/stats/` | Query statistics dashboard |

## Analyze Request

```json
{
  "input": "서울시 강남구 역삼동 677",
  "input_type": "address",
  "zones": [],
  "include_law": true
}
```

- `input`: Address string or 19-digit PNU code
- `input_type`: `"address"` or `"pnu"` (auto-detected if omitted)
- `zones`: Optional array of zone names to override Vworld lookup (e.g., `["일반상업지역"]`)
- `include_law`: Whether to search for related law articles (default: true)

## Analyze Response

```json
{
  "pnu": {
    "pnu": "1168010100100770000",
    "sido": "서울특별시",
    "sigungu": "강남구",
    "eupmyeondong": "역삼동",
    "ri": "",
    "land_type": "1",
    "main_number": "0077",
    "sub_number": "0000",
    "address": "서울시 강남구 역삼동 677"
  },
  "zone_info": {
    "matched": 1,
    "zones": [{"name": "일반상업지역", "bcr": 80, "far": 1300, "category": "상업"}],
    "unmatched": []
  },
  "land_info": {
    "success": true,
    "pnu": "1168010100100770000",
    "land_area_m2": 497.2,
    "official_land_price": 28620000,
    "land_use_situation": "대",
    "zones": ["일반상업지역"],
    "source": "vworld"
  },
  "regulations": {
    "bcr": {"limit_pct": 80, "article": "건축법 시행령 제84조"},
    "far": {"limit_pct": 1300, "article": "국토계획법 시행령 제85조"},
    "height": {"limit_m": null, "article": "건축법 제60조"},
    "sunlight_setback": {"applies": false, "direction": null, "article": "건축법 제61조"},
    "corner_cutoff": {"required": true, "article": "건축법 제46조"},
    "road_diagonal": {"multiplier": 1.5, "article": "건축법 제60조"},
    "building_line": {"setback_m": 0, "article": "건축법 제47조"},
    "adjacent_setback": {"min_m": 0.5, "article": "건축법 시행령 제80조의2"},
    "parking": {"rule": "시설면적 150m2당 1대", "article": "주차장법 시행령 별표1"},
    "landscaping": {"min_pct": 5, "article": "건축법 제42조"},
    "extended": {
      "use_restriction": {"value": "상업용도 (업무/판매/숙박)", "article": "국토계획법 제76조", "group": "A"},
      "road_access": {"value": "4m 이상 접도 필요", "article": "건축법 제44조", "group": "A"},
      "...": "31 items total in 3 groups (A/B/C)"
    }
  },
  "law_articles": {
    "articles": [
      {
        "query": "건폐율",
        "results": [
          {
            "hang_id": "HANG_001",
            "content": "건폐율은 80퍼센트 이하",
            "law_name": "건축법 시행령",
            "law_type": "시행령",
            "article": "제84조",
            "similarity": 0.92
          }
        ]
      }
    ],
    "total_count": 15,
    "errors": []
  },
  "restrictions": ["상업지역 내 주거용도 제한"],
  "errors": [],
  "warning": null
}
```

## 41 Regulation Items

### 10 Core Regulations (flat fields in `regulations`)

| Key | Description | Type |
|-----|-------------|------|
| `bcr` | 건폐율 (Building Coverage Ratio) | `limit_pct` (%) |
| `far` | 용적률 (Floor Area Ratio) | `limit_pct` (%) |
| `height` | 높이제한 | `limit_m` (meters or null) |
| `sunlight_setback` | 일조사선 | `applies`, `direction` |
| `corner_cutoff` | 가각전제 (도로 모퉁이) | `required` (bool) |
| `road_diagonal` | 도로사선 | `multiplier` |
| `building_line` | 건축선 후퇴 | `setback_m` |
| `adjacent_setback` | 인접대지 이격 | `min_m` |
| `parking` | 주차장 | `rule` (text) |
| `landscaping` | 조경 | `min_pct` (%) |

### 31 Extended Regulations (in `regulations.extended`)

**Group A — Zone-dependent (5 items)**
Lookup from `zoning_limits_extended.json` per zone type.
- `use_restriction`, `road_access`, `lot_subdivision`, `daylighting`, `zone_overlap`

**Group B — Scale-dependent (10 items)**
Computed by `regulation_calculator_ext.py` based on land area, FAR, etc.
- `structural_safety`, `open_space`, `fire_resistance`, `elevator`, `evacuation_route`, `earthquake_design`, `rainwater`, `energy_efficiency`, `barrier_free`, `noise_vibration`

**Group C — General regulations (16 items)**
Text-only, same for all zones.
- `fire_protection`, `disabled_access`, `energy_rating`, `cpted`, `mechanical`, `electrical`, `plumbing`, `waste`, `signage`, `demolition`, `temporary`, `maintenance`, `insurance`, `inspection`, `penalty`, `reporting`

## 21 Zoning Types

| Category | Zones |
|----------|-------|
| 주거 (6) | 제1종전용, 제2종전용, 제1종일반, 제2종일반, 제3종일반, 준주거 |
| 상업 (4) | 중심상업, 일반상업, 근린상업, 유통상업 |
| 공업 (3) | 전용공업, 일반공업, 준공업 |
| 녹지 (3) | 보전녹지, 생산녹지, 자연녹지 |
| 관리 (3) | 보전관리, 생산관리, 계획관리 |
| 농림 (1) | 농림지역 |
| 자연환경보전 (1) | 자연환경보전지역 |

## Service Pipeline

```
Input (address or PNU)
  │
  ├─ pnu_resolver.py
  │   └─ Vworld Geocoding API → coordinates + PNU (level4LC)
  │
  ├─ land_api.py (Vworld Data API × 3)
  │   ├─ getLandUseAttr → zone names from land use plan
  │   ├─ ladfrlList → land area (m²) + land use type
  │   └─ getIndvdLandPriceAttr → official land price (원/m²)
  │
  ├─ zoning_mapper.py
  │   └─ zone name → BCR/FAR limits (zoning_limits.json)
  │   └─ Multiple zones → strictest values applied
  │
  ├─ regulation_calculator_ext.py
  │   └─ area + FAR + zone → 31 extended regulations
  │
  └─ law_enricher.py → law-domain-agents :8011
      └─ 14 search queries (5 base + 9 extended)
      └─ fail-fast: 3 consecutive failures → abort
```

## Testing

```bash
# All 93 tests (no Neo4j or API key needed)
cd ARR/backend && python manage.py test land -v 2

# Test classes:
# AnalyzeViewTest (15), AnalyzeWithLandApiTest (3), ExtendedCalculatorTest (17),
# ExtendedLawEnricherTest (4), ExtendedViewTest (5), LandApiNormalizationTest (3),
# LandApiParseTest (7), LandApiStubTest (2), PnuResolverTest (4),
# RegulationCalculatorTest (14), ResolveViewTest (4), StatsViewTest (1),
# ZonesViewTest (2), ZoningMapperTest (8)
```

## Phase History

| Phase | Date | Content |
|-------|------|---------|
| 1-2 | 2026-02-22 | Skeleton + static data + services + views (27 tests) |
| 2.5 | 2026-02-24 | Vworld geocoding + address→PNU auto-extraction |
| 3 | 2026-02-24 | Vworld Data API × 3 (zone + area + price), 66 tests |
| 3.5 | 2026-02-25 | Extended 31 regulations (Group A/B/C), 93 tests |
| 4 | 2026-02-25 | Frontend (AG-frontend /land page), 16 E2E tests |
| 5 | 2026-02-25 | Multi-Agent team (039, 6-agent SelectorGroupChat) |
