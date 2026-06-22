---
name: Page 3 — Core Modules
description: 핵심 4 모듈 상세. Law Pipeline / §119 Datum / 정북일조 Envelope / NSGA-II Mass.
type: project
originSessionId: 5fb8be34-8660-4347-81b7-6bf5ae10ee85
---
## Module A: Law Pipeline (Neo4j 31K nodes)

**20개 법률 × 시행령/시행규칙 = 58 법령 적재 완료**:

| # | 법률 | 시행령 | 시행규칙 |
|---|---|---|---|
| 1 | 국토계획법 | ✅ | ✅ |
| 2 | 건축법 | ✅ | ✅ |
| 3 | 농지법 | ✅ | ✅ |
| 4 | 산지관리법 | ✅ | ✅ |
| 5 | 자연공원법 | ✅ | ✅ |
| 6 | 수도법 | ✅ | ✅ |
| 7 | 주택법 | ✅ | ✅ |
| 8 | 주차장법 | ✅ | ✅ |
| 9 | 하수도법 | ✅ | ✅ |
| 10 | 경관법 ×2 | ✅ | ✅ |
| 11 | 문화유산법 | ✅ | ✅ |
| 12 | 군사시설법 | ✅ | ✅ |
| 13 | 학교보건법 | ✅ | ✅ |
| 14 | 소방시설법 | ✅ | ✅ |
| 15 | 장애인편의법 | ✅ | ✅ |
| 16 | 녹색건축물법 | ✅ | ✅ |
| 17 | 도시정비법 | ✅ | ✅ |
| 18 | 도시공원법 | ✅ | ✅ |
| 19 | 도로법 | ✅ | ✅ |
| 20 | 개발제한구역법 ×2 | ✅ | ✅ |

**임베딩**: HANG 12,069 / CONTAINS rel 31,063 = **100%**.

**7-stage Hybrid Search**:
```
Exact match → Fulltext (CJK bi-gram) → Vector (3072d cosine)
  → Relationship boost → RRF + PageRank → RNE → MMR → Hierarchy
```

## Module B: §119 Datum Plane (Phase 1~2D-3, 9 commits)

**5 서브폴더 메모리 박제**:
- `spec/` 법규 원문 (§119, §86, 6 케이스)
- `data/` 표고 API (Vworld 없음 / Open-Meteo / NGII 5m)
- `flow/` 5단계 (1-fetch / 2-weighted-avg / 3-case / 4-envelope / 5-frontend)
- `tuning/` 임계값 / 알려진 이슈 / LOCKED SPEC
- `progress/` Phase 1~2D-3 완료 기록

**6 케이스 dispatcher**:

| Case | 조건 | datum 공식 | 법근거 |
|---|---|---|---|
| FLAT | 변동 < 2m | site centroid | §119① 5호 |
| SLOPE_LE3M | 2~8m | 외벽 둘레 가중평균 | §119② |
| SLOPE_GT3M | > 8m | 가중평균 + 분할 stub | §119② 단서 |
| ROAD_FLAT | 도로접지 평지 | 도로 중심선 | §119① 5호 가목 |
| ROAD_SLOPED | 도로접지 경사 | 도로 노면 가중평균 | §119① 5호 가목 단서 |
| SITE_ABOVE_ROAD | 대지 > 도로 | (parcel + road) / 2 | §119① 5호 나목 |
| NEIGHBOR_AVG_86 | §86 정북인접지 | (my + neighbor) / 2 | §86 별도 |

**가중평균 공식 (§119②)**:
```
H_datum = Σ(L_i × h_i) / Σ(L_i)

L_i = 외벽 둘레 segment 수평거리 (m)
h_i = 해당 segment 위치 지표면 표고 (m, Open-Meteo)
```

**임계값 (90m DEM 노이즈 흡수)**:
```python
FLAT_VARIANCE_THRESHOLD_M = 2.0    # ← 0.5에서 상향
SLOPE_3M_THRESHOLD_M      = 8.0    # ← 3.0에서 상향
ROAD_SLOPE_THRESHOLD_M    = 1.0    # ← 0.5에서 상향
MAX_PARCEL_VERTICES       = 500    # DoS guard
```

## Module C: 정북일조 Envelope (LOCKED SPEC, Session 14)

**§86①제2호 삼각비**: `H = max(10, d × 2), cap 50m` (slope 2:1)

```
H (m)
  | 50 ──────────                    ← cap
  |             ╲                    ← slope 2:1
  | 10 ─────╮   ╲                   ← §86①제1호 plateau
  |          │      
  |          │ 1.5m (수직 직각벽)
  |  0 ─────┴──────────→ x
            1.5    25m
```

**LOCKED SPEC 보호 (3-layer)**:

| Layer | 위치 | 동작 |
|---|---|---|
| 1 | `config.ENABLE_DATUM_ELEVATION=false` | datum 계산 안 됨 (default) |
| 2 | `envelope.elevation_source=null` | frontend 트리거 안 됨 |
| 3 | frontend ternary | source!=='open_meteo' → terrainH |

**검증**:
- `verify_envelope_coords.py` 9 threshold 법규 대조
- `verify_envelope_profile.py` §86① 단면 자동
- Session 14 사용자 12회+ 시각 검증

## Module D: NSGA-II Mass Optimization

**10 알고리즘**:

| # | 이름 | 설명 |
|---|---|---|
| 1 | 자유형 (Additive) | K=5 box 합 |
| 2 | 감산형 (Subtractive) | block에서 void 빼기 |
| 3 | 격자형 (Grid) | 3×3 셀 활성/비활성 |
| 4 | ㄱ자형 (L-shape) | 코너형 매스 |
| 5 | ㄷ자형 (U-shape) | 중정 한면 열림 |
| 6 | 십자형 (Cross) | 4방향 익스텐션 |
| 7 | 중정형 (Courtyard) | ㅁ자 닫힌 중정 |
| 8 | 타워+기단 (Tower+Podium) | 2층 매스 |
| 9 | H자형 (H-shape) | H 형태 |
| 10 | 방사형 (Radial) | 중심 + 가지 |

**자동 제약 변환**:
```
land/analyze/ 결과
  ↓ constraint_bridge.py
GA constraints (BCR, FAR, 이격, 높이)
  ↓ NSGA-II runner
Pareto front (gen × population)
  ↓ Frontend
3D 매스 + Pareto chart
```

**용도별 Pareto 목적함수**:
- 주거: floor_area + daylight_score
- 상업: floor_area + landscaping_pct
- 문화: floor_area + setback

## 호출 체인 (E2E)

```
ENABLE_DATUM_ELEVATION=true
   ↓
land/views.py:354 _core_analysis()
   ↓
setback_geometry.compute_setback_lines(parcel, reg, compute_datum=True)
   ↓
_maybe_compute_datum(parcel)
   ↓
datum.compute_datum_elevation(DatumContext)         ← Step 3
   ├─ calculator.parcel_datum_119(parcel)            ← Step 2
   │      └─ elevation_api.fetch_elevations(points) ← Step 1
   └─ DatumResult
   ↓
envelopes/sunlight.compute_sunlight_envelope(..., datum=result)  ← Step 4
   ↓ output dict + 4 metadata 필드
frontend SunlightEnvelope
   ↓
lib/envelopes/sunlight.ts groundH ternary             ← Step 5
   ↓ Cesium entity 렌더
DatumInfoCard 카드 표시
```
