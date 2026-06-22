# 25_ACE — Architectural Regulation AI Pipeline + Multi-Agent System

**한 줄**: 주소 한 줄 입력 → 건축법규 42개 + §119 지반레벨 + 8종 규제선 + GA 매스 최적화 자동, 9 commits로 완성한 §119 datum 평면 시스템.

---

## Page 1 — Overview & Demo

### 무엇을 만들었나

**도시 필지 건축법 자동 분석 + 매스 최적화 통합 시스템.** 사용자는 "서울특별시 강남구 역삼동 677" 주소만 입력하면 AI 파이프라인이 다음을 자동 생성:

- **42개 건축 규제 수치** (건폐율 BCR, 용적률 FAR, 정북일조, 채광사선, 가각전제, 인접대지 이격 등)
- **§119 지반 레벨** (시행령 §119 가중평균 datum 평면, Open-Meteo 90m DEM 기반)
- **8종 규제선** (3D Cesium envelope: 정북일조 사선 + buildable_area + 도로 후퇴 + 가각전제 등)
- **GA 매스 최적화** (NSGA-II 10종 알고리즘, Pareto front)

### 핵심 데모 시나리오

```
[1] 주소 입력          서울특별시 강남구 역삼동 674-38
       ↓
[2] PNU 자동 추출      Vworld geocode → 1168010100106740038
       ↓
[3] 토지 데이터 수집   Vworld Data API ×4 (용도지역, 면적, 공시지가, 폴리곤)
       ↓
[4] 법규 분석          42 규제 (Neo4j 31K nodes, 7-stage hybrid search)
       ↓
[5] §119 지반 datum    Open-Meteo 90m DEM → 6 케이스 분류 → 가중평균면
       ↓
[6] 규제선 8종 + 3D    정북일조 envelope (slope 2:1, H = 2d)
       ↓
[7] GA 매스 최적화     NSGA-II 10 알고리즘 → Pareto front
       ↓
[8] Frontend 시각화    Cesium 3D + DatumInfoCard + ConstraintSummary
```

### 검증 결과 (라이브)

| 항목 | 수치 |
|---|---|
| 라이브 검증 PNU | 8개 (강남/성북/한남/여의도/우동/평창/대관령) |
| 정확도 측정 (18 landmark) | **도시 11m, 해안 3.7m** (도시 use case ✅) |
| 자동 테스트 | **178+ tests pass** (39 datum + 167 land 회귀) |
| LOCKED SPEC | Session 14 envelope 12회+ 검증 박제 |
| Git commits (datum 시리즈) | 9 commits |
| 배포 서비스 | 4서비스 라이브 (CF Worker + Pages + Railway) |

### 진짜 건축설계처럼 가능한가? ✅

1. PNU/주소 입력 → §119 datum 자동 (Vworld + Open-Meteo)
2. Cesium 3D envelope이 terrain 위 정확히 위치 (Z축 일치)
3. 6 케이스 자동 분류 (FLAT / SLOPE_LE3M / SLOPE_GT3M / ROAD / NEIGHBOR_AVG)
4. 사용자 시각 확인 (DatumInfoCard 카드 — H=48m 등)
5. 상업지/녹지 등 정북일조 미적용 zone에서도 datum 노출
6. Playwright 자동화 검증 통과

---

## Page 2 — System Architecture

### 4-Service Live Deployment

```
┌──────────────────────────────────────────────────────────────────┐
│                     사용자 (브라우저 / Telegram)                   │
└──────────────┬─────────────────────────────────────┬─────────────┘
               │                                     │
       ┌───────▼────────┐                  ┌────────▼─────────┐
       │ ARR Frontend   │                  │ Hermes Bot       │
       │ (CF Pages)     │                  │ (@DK_arch_bot,   │
       │ React+Vite     │                  │  Oracle VM)      │
       │ /law /land     │                  │                  │
       │ /design        │                  │                  │
       └───────┬────────┘                  └────────┬─────────┘
               │ /law/* /land/* /design/*           │
       ┌───────▼─────────────────────────────────────▼─────────┐
       │  ARR Backend (Django, Railway)                        │
       │  - 42 building regulations                            │
       │  - §119 datum 6-case dispatcher                       │
       │  - NSGA-II GA mass optimization                       │
       └─┬───────────────┬──────────────────────┬──────────────┘
         │               │                      │
   ┌─────▼─────┐  ┌─────▼─────┐         ┌──────▼────────┐
   │ Vworld    │  │ Open-Meteo│         │ AG-light      │
   │ (geo+필지)│  │ (90m DEM) │         │ Worker (CF)   │
   └───────────┘  └───────────┘         │ - 법령 검색    │
                                         │ - Vectorize   │
                                         └───────┬───────┘
                                                 │
                                         ┌───────▼────────┐
                                         │ Neo4j (local)  │
                                         │ 58법령 31K nodes│
                                         │ 7-stage search  │
                                         └────────────────┘
```

### Tech Stack

| Layer | Tech |
|---|---|
| **Frontend** | React 19, TypeScript 5.9, Vite 7, Tailwind v4, Cesium 3D, Vworld 3D Map |
| **Backend** | Django 6, Python 3.13, Shapely, pyproj, httpx |
| **Database** | Neo4j (법령 31K nodes, 임베딩 100%), SQLite (audit log) |
| **AI/ML** | OpenAI gpt-4o-mini (LLM 추출), text-embedding-3-large (3072d), Jina v3 (Vectorize 1024d) |
| **Geometry** | Vworld Data API, Open-Meteo Elevation API (Copernicus GLO-90) |
| **Optimization** | NSGA-II Genetic Algorithm, Pareto front |
| **Agents** | Hermes (Nous Research), MCP (57 tools), A2A protocol, Telegram bot |
| **DevOps** | Cloudflare Pages/Workers, Railway, Oracle VM, Playwright E2E |

### Data Pipeline (datum 예시)

```
주소 → Vworld geocode → PNU
         ↓
PNU → Vworld LP_PA_CBND_BUBUN → 필지 polygon (WGS84)
         ↓
Polygon → UTM 변환 → 외벽 edge midpoints
         ↓
Midpoints → Open-Meteo Elevation API → 표고 list
         ↓
표고 list × edge 길이 → §119② 가중평균 → datum_m
         ↓
datum + parcel + road/neighbor flags → 6 케이스 분류
         ↓
DatumResult (case + elevation_m + basis + source)
         ↓
envelope output에 metadata 4 필드
         ↓
Frontend DatumInfoCard 카드 표시
```

---

## Page 3 — Core Modules

### Module A: Law Pipeline (Neo4j 31K nodes)

**20개 법률 × 시행령/시행규칙 = 58 법령 적재 완료**:
- 국토계획법, 건축법, 농지법, 산지관리법, 자연공원법, 수도법
- 주택법, 주차장법, 하수도법, 경관법, 문화유산법, 군사시설법
- 학교보건법, 소방시설법, 장애인편의법, 녹색건축물법
- 도시정비법, 도시공원법, 도로법, 개발제한구역법

**7-stage Hybrid Search**:
```
Exact match → Fulltext (CJK bi-gram) → Vector (3072d cosine)
  → Relationship boost → RRF + PageRank → RNE → MMR → Hierarchy
```

**임베딩**: HANG 12,069 / CONTAINS rel 31,063 — **100% 완료**.

### Module B: §119 Datum Plane (Phase 1~2D-3, 9 commits)

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

### Module C: 정북일조 Envelope (LOCKED SPEC, Session 14)

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

- 백엔드: `envelopes/sunlight.py` (LOCKED, 변경 0)
- 프런트: `lib/envelopes/sunlight.ts` (LOCKED, terrainH 통일)
- 검증: `verify_envelope_coords.py`, `verify_envelope_profile.py` CLI

### Module D: NSGA-II Mass Optimization

**10 알고리즘**:
1. 자유형 (Additive)
2. 감산형 (Subtractive)
3. 격자형 (Grid)
4. ㄱ자형 (L-shape)
5. ㄷ자형 (U-shape)
6. 십자형 (Cross)
7. 중정형 (Courtyard)
8. 타워+기단 (Tower+Podium)
9. H자형 (H-shape)
10. 방사형 (Radial)

**제약 자동 변환**: `land/analyze` → `constraint_bridge.py` → GA constraints (BCR/FAR/이격/높이) → NSGA-II → Pareto front.

---

## Page 4 — Agent System & Validation

### Agent Architecture (2026-04-26~28 결정 완료)

**Hermes (Nous Research) 채택** + 통일 skill 추상화 + Telegram bot persona별 분리:

```
사용자 (Telegram @DK_arch_bot)
       ↓
Hermes Gateway (Oracle VM Always-Free)
       ↓
LLM (Qwen-plus via DashScope)
       ↓ skill dispatch
┌─────────────────┬─────────────────┐
│ Light Skills    │ Heavy Skills     │
│ (즉시 응답)     │ (Celery enqueue) │
├─────────────────┼─────────────────┤
│ 법규 검색        │ 매스 최적화 GA   │
│ 토지 분석        │ 평면 생성        │
│ datum 계산       │ 시방서 생성      │
│ 규제선 조회      │ 견적 산출        │
└─────────────────┴─────────────────┘
       ↓ 일부 호출
ARR Backend (Django, Railway)
       ↓
ACE MCP Server (57 tools)
       ↓
AutoGen Studio + AG-CLI Multi-Agent
```

### MCP & A2A Protocol

**ACE MCP** (57 tools, 17 categories):
- 법조항 검색 (`law_search`, `arr_law_search`)
- 토지 분석 (`arr_land_analyze/resolve/zones/stats`)
- 매스 최적화 (`arr_land_design`)
- AutoGen 팀 실행 + RunSummary
- A2A 에이전트 등록 + health
- Message Bus + SharedMemory

**A2A**: JSON-RPC 2.0, agent card discovery (`/.well-known/agent-card.json`), 양방향 통신.

### Validation Framework

| 검증 | 방법 | 결과 |
|---|---|---|
| **단위 테스트** | Django TestCase | 39 datum + 27 zoning + 100+ regulation = **178+ pass** |
| **회귀 테스트** | `python manage.py test land` | **167 pass** |
| **CLI 검증** | `verify_datum_multi.py` (8 PNU) | 8/8 ✅ |
| **정확도 측정** | `verify_elevation_accuracy.py` (18 landmark) | 도시 11m, 해안 3.7m |
| **LOCKED SPEC** | `test_envelope_walls_slanted_unchanged_by_datum` | byte-identical ✅ |
| **시각 검증** | Playwright (자동) | 카드 + envelope 표시 ✅ |
| **E2E 라이브** | 강남 역삼동 677 | BCR=80%, FAR=1300%, 42규제 ✅ |

### 9 Commits (Phase 1~2D-3, datum elevation 시리즈)

```
8443395 fix(design): Phase 2D-3 — Z축 일치 + 시각 helper 개선
1b408ce feat(frontend): Phase 2D-2 — datum 독립 노출 (envelope 미적용 zone)
98f9c6d feat(frontend): Phase 2D — datum 시각 카드 (land + design)
c49e09f feat(verify): Open-Meteo 90m DEM 정확도 검증 CLI
44a5e5f feat(datum): Phase 2C — 라이브 8 PNU 검증 + 임계값 조정
8894423 feat(verify): verify_datum_119 CLI envelope 통합
d67d1a4 feat(datum): Phase 2B — 호출 체인 + frontend 3-state
09023de feat(envelope): Phase 2A — datum metadata LOCKED SPEC 호환
5fcc39d feat(datum): Phase 1 — Open-Meteo + 6 케이스 dispatcher
```

### Roadmap

| Phase | 상태 | 내용 |
|---|---|---|
| 1~2D-3 | ✅ DONE | datum 평면 + envelope + UI 카드 + Z축 fix |
| 임계값 조정 | ✅ DONE | 90m DEM 노이즈 흡수 (FLAT 2.0, SLOPE 8.0) |
| **3 (NGII 5m)** | TODO | 산악지 정밀화 (90m → 5m, 18배) |
| **§86 정북인접** | TODO | views.py에서 인접 polygon 추출 |
| **§119 도로 활성** | TODO | views.py에서 centerline 추출 |
| **4 (3m 분할)** | TODO | §119② 단서 polygon segmentation |
| **Hermes 통합** | TODO | Telegram bot → ARR backend 직접 호출 |

### Differentiation

| 기존 시스템 | 25_ACE |
|---|---|
| 사용자 수동 법규 검색 | **자동** Neo4j 7-stage hybrid search |
| 단순 평탄지 envelope | **§119 6 케이스** datum (산악/도로/인접지 자동) |
| 정적 법규 데이터 | **LLM 동적 추출** + 18 landmark 정확도 검증 |
| Cesium 1차원 시각 | **Z축 일치** + DatumInfoCard 카드 + 3D envelope |
| 로컬 단일 사용자 | **MCP 57 tools + A2A + Telegram bot** 멀티에이전트 |

---

**핵심 메시지**: 한국 건축법 시행령 §119/§86을 **AI로 자동 분석 + 시각화**한 첫 시스템. 9 commits로 datum 평면 완성, 178+ tests 통과, Playwright 라이브 검증, LOCKED SPEC 12회+ 사용자 검증 박제.

**Tech**: React + Django + Neo4j + Cesium + NSGA-II GA + Hermes Agents.

**검증 가능**: `tools/verify_datum_multi.py` 또는 `localhost:5173/design` 직접 라이브.
