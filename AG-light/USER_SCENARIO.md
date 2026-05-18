# AG-light 사용자 시나리오

## 시나리오: 강남구 역삼동 677번지 건축 가능 여부 확인

### 사용자 액션

```
POST /land/analyze
{ "input": "강남구 역삼동 677" }
```

이게 전부. 주소 한 줄이면 된다.

---

### Step 1. 주소 → PNU (pnu-resolver)

```
Vworld Geocode API
→ "강남구 역삼동 677"
← { x: 127.0365, y: 37.4993, level4LC: "1168010100106770003" }
```

```json
{
  "pnu": "1168010100106770003",
  "sido": "11",            // 서울
  "sigungu": "680",         // 강남구
  "eupmyeondong": "101",   // 역삼동
  "land_type_name": "대"
}
```

---

### Step 2. PNU → 토지 정보 (land-api, 4개 API 병렬)

```
┌─ getLandUseAttr ──→ 용도지역: ["제3종일반주거지역"]
│                     (cnflcAtNm="포함" 필터, "접함" 제외)
│
├─ ladfrlList ──────→ 면적: 330.5m², 지목: 대
│
├─ getIndvdLandPriceAttr → 공시지가: 5,120,000원/m²
│
└─ LP_PA_CBND_BUBUN(pnu) → 필지 폴리곤: GeoJSON Polygon
                            [[127.0361,37.4990], [127.0369,37.4990],
                             [127.0370,37.4996], [127.0362,37.4996], ...]
```

---

### Step 3. 규제 계산 — 3-tier Override

#### Tier 1: Static JSON (zoning-limits.json)
```
제3종일반주거지역:
  건폐율: 50%          ← 시행령 §84①
  용적률: 300%         ← 시행령 §85①
  높이제한: 없음 (가로구역별)
  정북일조: 적용        ← §86① (H≤10m→1.5m, H>10m→H×0.5)
  가각전제: 적용        ← 8m 미만 도로 모퉁이
  인접이격: 0.5m       ← §58
  조경: 200m² 이상 시 15%
```

#### Tier 2: 강남구 조례 Override (ordinance, sigungu=11680)
```diff
- 인접이격: 0.5m
+ 인접이격: 1.0m       ← 강남구 조례 override
```

#### Tier 3: LLM 보강 (llm-extractor, 3개 병렬)
```
Vectorize "정북 일조사선" → 시행령 §86 조문 텍스트
→ OpenAI gpt-4o-mini (temperature=0, json_object)
→ { sunlight_rules: [{condition:"H<=10m", setback_m:1.5}, ...], sunlight_article: "시행령 제86조제1항" }
→ regulations.sunlight_rules 갱신, source="law_text"
```

---

### Step 4. 도로 탐지 (road-detector)

```
필지 폴리곤 BBOX + 20m 버퍼
→ Vworld Data API LP_PA_CBND_BUBUN (geomFilter=BOX)
→ 인접 100개 필지 중 지목="도" 필터
→ 도로 필지 2개 발견

도로 A: 남쪽 변 공유, 도로폭 12m → 후퇴 불필요 (≥4m)
도로 B: 서쪽 변 공유, 도로폭 6m  → 후퇴 불필요 (≥4m)

가각전제: 도로 A+B 모두 ≥8m → 해당 없음
```

---

### Step 5. 규제선 계산 (setback, 8종)

```
필지 폴리곤 (local meters 변환)
├── 변 분류 (도로 데이터로 실측 매칭)
│   ├── 남쪽 변: 도로 A (12m) → road
│   ├── 서쪽 변: 도로 B (6m) → road
│   ├── 북쪽 변: 바깥 법선 정북 → north + adjacent
│   └── 동쪽 변: → adjacent
│
├── 1. 건축가능영역: 필지 inward buffer 1.0m (조례 적용)
│      → Polygon (필지보다 1m 안쪽)
│
├── 2. 정북일조 4단계 (북쪽 변 기준):
│      H=10m → 1.5m 이격선  ───── 🟢
│      H=20m → 10m 이격선   ───── 🟡
│      H=30m → 15m 이격선   ───── 🟠
│      H=40m → 20m 이격선   ───── 🔴
│      (필지 내부로 클리핑)
│
├── 3. 인접대지 이격: 동쪽+북쪽 변에서 1.0m 내측
│      → LineString (강남구 조례 1.0m)
│
├── 4. 건축선 후퇴: 남쪽+서쪽 도로변
│      → 12m, 6m 둘 다 ≥4m → 후퇴 0m (선 없음)
│
├── 5. 가각전제: 도로 ≥8m → 해당 없음 (null)
│
├── 6. 건축지정선: 지구단위계획 아님 → 해당 없음 (null)
│
├── 7. 정북일조 3D 경사면:
│      수직벽 (0→1.5m, 높이 0→10m) + 경사면 (slope 2:1)
│      → Cesium Wall 데이터
│
└── 8. 채광사선 3D: 비공동주택 → 해당 없음 (null)
```

---

### Step 6. 응답 JSON

```json
{
  "pnu": {
    "pnu": "1168010100106770003",
    "sido": "11", "sigungu": "680",
    "land_type_name": "대"
  },

  "regulations": {
    "bcr_pct": 50,
    "bcr_article": "국토계획법 시행령 제84조제1항제2호",
    "far_pct": 300,
    "far_article": "국토계획법 시행령 제85조제1항제5호",
    "height_limit_m": null,
    "sunlight_applies": true,
    "sunlight_rules": [
      {"condition": "H <= 10m", "setback_m": 1.5},
      {"condition": "H > 10m", "formula": "H * 0.5"}
    ],
    "sunlight_source": "law_text",
    "corner_cutoff_required": true,
    "corner_cutoff_m": null,
    "adjacent_setback_m": 1.0,
    "adjacent_setback_source": "law_text",
    "zone_category": "주거지역",
    "matched_zones": ["제3종일반주거지역"]
  },

  "extended_regulations": {
    "building_use_restriction": {
      "name": "건축물 용도 제한",
      "allowed_summary": "단독·공동주택, 제1·2종 근린생활시설, 업무시설 등",
      "prohibited_summary": "공장, 위락시설, 일부 숙박시설 등"
    },
    "structural_safety": {
      "name": "구조안전 확인/내진설계",
      "applies_when": "3층 이상 또는 연면적 500m² 이상"
    }
    // ... 31개
  },

  "land_info": {
    "pnu": "1168010100106770003",
    "zones": ["제3종일반주거지역"],
    "land_area_m2": 330.5,
    "official_land_price": 5120000,
    "land_use_situation": "대",
    "source": "vworld"
  },

  "parcel_geojson": {
    "type": "Polygon",
    "coordinates": [[[127.0361,37.4990], [127.0369,37.4990],
                     [127.0370,37.4996], [127.0362,37.4996],
                     [127.0361,37.4990]]]
  },

  "setback_lines": {
    "buildable_area": {
      "type": "Polygon",
      "coordinates": [[[127.0362,37.4991], ...]]
    },
    "north_setback": {
      "type": "FeatureCollection",
      "features": [
        {"properties": {"height_m":10, "offset_m":1.5, "label":"H=10m → 1.5m"},
         "geometry": {"type":"LineString", "coordinates": [...]}},
        {"properties": {"height_m":20, "offset_m":10, "label":"H=20m → 10m"},
         "geometry": {"type":"LineString", "coordinates": [...]}},
        {"properties": {"height_m":30, "offset_m":15, "label":"H=30m → 15m"},
         "geometry": {"type":"LineString", "coordinates": [...]}},
        {"properties": {"height_m":40, "offset_m":20, "label":"H=40m → 20m"},
         "geometry": {"type":"LineString", "coordinates": [...]}}
      ]
    },
    "adjacent_setback": {
      "type": "MultiLineString",
      "coordinates": [[[127.0369,37.4991], ...], ...]
    },
    "road_setback": null,
    "corner_cutoff": null,
    "sunlight_envelope": {
      "walls": [
        {"positions": [[127.0362,37.4996], ...], "min_heights": [0,0,...], "max_heights": [0,10,...]}
      ],
      "slope": 2, "base_setback_m": 1.5, "base_height_m": 10
    },
    "building_designation_line": null,
    "daylight_diagonal_envelope": null
  },

  "restrictions": [
    "건폐율 상한: 50%",
    "용적률 상한: 300%",
    "정북일조 사선제한 적용"
  ],

  "law_articles": {
    "articles": [...],
    "total_count": 45
  }
}
```

---

### Step 7. 프론트엔드 렌더링

```
┌──────────────────────────────────────────────┐
│  🗺️ 2D 지도 (OpenLayers + Vworld 배경)        │
│                                              │
│   ┌──────────────────────┐                   │
│   │ ░░░░░░░░░░░░░░░░░░░░ │ ← 필지 폴리곤     │
│   │ ░┌────────────────┐░ │                   │
│   │ ░│ 🟦 건축가능영역   │░ │ ← 1.0m buffer   │
│   │ ░│                │░ │                   │
│   │ ░│  🟢─────────── │░ │ ← H=10m 일조선    │
│   │ ░│  🟡─────────── │░ │ ← H=20m 일조선    │
│   │ ░│  🟠─────────── │░ │ ← H=30m 일조선    │
│   │ ░│  🔴─────────── │░ │ ← H=40m 일조선    │
│   │ ░└────────────────┘░ │                   │
│   │ ░░░░░░░░░░░░░░░░░░░░ │                   │
│   └──────────────────────┘                   │
│     ↑ 북쪽                                    │
│                                              │
│  📊 규제 패널                                  │
│  ┌────────────────────────────────┐          │
│  │ 건폐율: 50%  용적률: 300%       │          │
│  │ 면적: 330.5m²  공시지가: 512만/m² │          │
│  │ 정북일조 사선제한 적용            │          │
│  │ 인접대지 이격 1.0m (강남구 조례)   │          │
│  │ 관련 법조항 45개                 │          │
│  └────────────────────────────────┘          │
│                                              │
│  🏗️ 3D 뷰 (Cesium) →                         │
│  정북일조 경사면 (slope 2:1)                    │
│  수직벽 10m + 경사면 최대 30m depth              │
└──────────────────────────────────────────────┘
```

---

### 시나리오 변형

| 입력 | 차이점 |
|------|--------|
| `"서초구 서초동 1321"` | sigungu=11650, 조례 없음(강남만), 정북일조 동일 |
| `"용인시 수지구 죽전동 1234"` | 경기도(41), 다른 용도지역 가능, 조례 없음 |
| `{"input":"...", "zones":["일반상업지역"]}` | 수동 zone, 일조 비적용, BCR=80/FAR=1300 |
| PNU 직접: `"4146510200101230005"` | 지오코딩 생략, PNU 파싱만 |
| `+ parcel_geojson` 직접 제공 | 자동 조회 생략, 사용자 폴리곤 사용 |

### 실패 시 graceful degradation

| 조건 | 결과 |
|------|------|
| 주소 인식 실패 | 400 에러 + 메시지 |
| Vworld API 키 없음 | zones 비어있음 → 수동 입력 안내 |
| 필지 폴리곤 조회 실패 | setback_lines: null, 나머지 정상 |
| 도로 탐지 실패 | 최장변 휴리스틱 fallback |
| OpenAI 키 없음 | LLM 보강 건너뜀, static JSON 유지 |
| Vectorize 비어있음 | 법제처 메타데이터 fallback |
