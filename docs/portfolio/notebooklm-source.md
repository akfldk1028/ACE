---
name: NotebookLM Source — 통합 업로드용
description: NotebookLM에 단일 파일로 업로드 후 4페이지 포트폴리오 생성 프롬프트 사용. 모든 핵심 정보 압축.
type: project
originSessionId: 5fb8be34-8660-4347-81b7-6bf5ae10ee85
---
# 25_ACE — Architectural Regulation AI Pipeline + Multi-Agent System

## TL;DR

주소 한 줄 입력 → 건축법규 42개 + §119 지반레벨 + 8종 규제선 + GA 매스 최적화 자동.
9 commits, 178+ tests, 18 landmark 정확도 검증, Playwright 라이브 검증.

## 1. Project Overview

### What

도시 필지 건축법 자동 분석 + 매스 최적화 통합 시스템.
사용자는 "서울특별시 강남구 역삼동 677" 주소만 입력하면 AI 파이프라인이 다음을 자동 생성:
- 42개 건축 규제 수치 (BCR, FAR, 정북일조, 채광사선, 가각전제, 인접대지 이격)
- §119 지반 레벨 (시행령 §119 가중평균 datum 평면, Open-Meteo 90m DEM)
- 8종 규제선 (3D Cesium envelope: 정북일조 사선 + buildable_area + 도로 후퇴)
- GA 매스 최적화 (NSGA-II 10종 알고리즘, Pareto front)

### How (8 Step Pipeline)

1. 주소 입력
2. PNU 자동 추출 (Vworld geocode)
3. 토지 데이터 수집 (Vworld Data API ×4)
4. 법규 분석 (Neo4j 31K nodes, 7-stage hybrid search)
5. §119 지반 datum (Open-Meteo 90m DEM, 6 케이스 분류)
6. 규제선 8종 + 3D envelope (slope 2:1)
7. GA 매스 최적화 (NSGA-II 10 algorithms)
8. Frontend 시각화 (Cesium 3D + DatumInfoCard)

### Validation

- 라이브 검증 PNU 8개 (강남/성북/한남/여의도/우동/평창/대관령)
- 정확도: 도시 11m, 해안 3.7m, 산 63m (18 landmark)
- 자동 테스트: 178+ pass (39 datum + 167 land 회귀)
- LOCKED SPEC: Session 14 envelope 12회+ 사용자 검증
- 9 commits (datum elevation 시리즈)
- 4서비스 라이브 배포

## 2. System Architecture

### 4 Live Services

| Service | URL | Platform | Cost/mo |
|---|---|---|---|
| ARR Frontend | arr-frontend.pages.dev | CF Pages | $0 |
| AG-frontend | ag-frontend-5s3.pages.dev | CF Pages | $0 |
| AG-light Worker | law-light-api.clickaround8.workers.dev | CF Workers | $0 |
| ARR Backend | arr-backend-production.up.railway.app | Railway | ~$5 |
| Hermes Gateway | 158.180.66.165 | Oracle VM | ~$22 |

### Tech Stack

- Frontend: React 19, TypeScript 5.9, Vite 7, Tailwind v4, Cesium 3D, Vworld 3D Map
- Backend: Django 6, Python 3.13, Shapely, pyproj, httpx
- Database: Neo4j (법령 31K nodes, 임베딩 100%), SQLite (audit log)
- AI/ML: OpenAI gpt-4o-mini, text-embedding-3-large (3072d), Jina v3 (1024d)
- Geometry: Vworld Data API, Open-Meteo Elevation API (Copernicus GLO-90)
- Optimization: NSGA-II Genetic Algorithm
- Agents: Hermes (Nous Research), MCP (57 tools), A2A protocol
- DevOps: Cloudflare Pages/Workers, Railway, Oracle VM, Playwright E2E

### Data Pipeline (datum 흐름)

```
주소 → Vworld geocode → PNU
PNU → Vworld LP_PA_CBND_BUBUN → 필지 polygon (WGS84)
Polygon → UTM 변환 → 외벽 edge midpoints
Midpoints → Open-Meteo Elevation API → 표고 list
표고 list × edge 길이 → §119② 가중평균 → datum_m
datum + parcel/road/neighbor flags → 6 케이스 분류
DatumResult → envelope output metadata 4 필드
Frontend DatumInfoCard 카드 표시
```

## 3. Core Modules

### Module A: Law Pipeline

20개 법률 × 시행령/시행규칙 = 58 법령 적재 완료.
- 국토계획법, 건축법, 농지법, 산지관리법, 자연공원법, 수도법
- 주택법, 주차장법, 하수도법, 경관법, 문화유산법, 군사시설법
- 학교보건법, 소방시설법, 장애인편의법, 녹색건축물법
- 도시정비법, 도시공원법, 도로법, 개발제한구역법

임베딩: HANG 12,069 / CONTAINS rel 31,063 = 100%.

7-stage Hybrid Search:
Exact → Fulltext (CJK bi-gram) → Vector (3072d cosine) → Relationship boost → RRF + PageRank → RNE → MMR → Hierarchy.

### Module B: §119 Datum Plane (Phase 1~2D-3, 9 commits)

6 케이스 dispatcher:

| Case | 조건 | datum 공식 | 법근거 |
|---|---|---|---|
| FLAT | 변동 < 2m | site centroid | §119① 5호 |
| SLOPE_LE3M | 2~8m | 외벽 둘레 가중평균 | §119② |
| SLOPE_GT3M | > 8m | 가중평균 + 분할 stub | §119② 단서 |
| ROAD_FLAT | 도로접지 평지 | 도로 중심선 | §119① 5호 가목 |
| ROAD_SLOPED | 도로접지 경사 | 도로 노면 가중평균 | §119① 5호 가목 단서 |
| SITE_ABOVE_ROAD | 대지 > 도로 | (parcel + road) / 2 | §119① 5호 나목 |
| NEIGHBOR_AVG_86 | §86 정북인접지 | (my + neighbor) / 2 | §86 별도 |

가중평균 공식 (§119②):
H_datum = Σ(L_i × h_i) / Σ(L_i)

### Module C: 정북일조 Envelope (LOCKED SPEC, Session 14)

§86①제2호 삼각비: H = max(10, d × 2), cap 50m (slope 2:1)

3-Layer LOCKED SPEC 보호:
- Layer 1: config.ENABLE_DATUM_ELEVATION=false (default)
- Layer 2: envelope.elevation_source=null
- Layer 3: frontend ternary → terrainH

### Module D: NSGA-II Mass Optimization

10 알고리즘:
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

자동 제약 변환: land/analyze 결과 → constraint_bridge.py → GA constraints → NSGA-II → Pareto front.

## 4. Agent System & Validation

### Agent Architecture

Hermes (Nous Research) 채택 + 통일 skill 추상화 + Telegram bot persona별 분리.

ACE MCP Server: 57 tools, 17 categories
- 법조항 검색, 토지 분석, AutoGen 팀, 세션 관리, A2A 에이전트, Message Bus, SharedMemory.

A2A Protocol:
- JSON-RPC 2.0
- Agent card discovery: /.well-known/agent-card/{slug}.json
- Bidirectional messaging
- Multi-agent collaboration

### 9 Commits

```
8443395 fix(design): Phase 2D-3 — Z축 일치 + 시각 helper 개선
1b408ce feat(frontend): Phase 2D-2 — datum 독립 노출
98f9c6d feat(frontend): Phase 2D — datum 시각 카드 (land + design)
c49e09f feat(verify): Open-Meteo 90m DEM 정확도 검증 CLI
44a5e5f feat(datum): Phase 2C — 라이브 8 PNU 검증 + 임계값 조정
8894423 feat(verify): verify_datum_119 CLI envelope 통합
d67d1a4 feat(datum): Phase 2B — 호출 체인 + frontend 3-state
09023de feat(envelope): Phase 2A — datum metadata LOCKED SPEC 호환
5fcc39d feat(datum): Phase 1 — Open-Meteo + 6 케이스 dispatcher
```

### Roadmap

- Phase 1~2D-3: DONE
- 임계값 조정: DONE (FLAT 2.0, SLOPE 8.0)
- Phase 3 NGII 5m: TODO (산악지 정밀화)
- §86 정북인접: TODO
- §119 도로 활성: TODO
- Phase 4 3m 분할: TODO
- Hermes 통합: TODO

### Differentiation

| 기존 | 25_ACE |
|---|---|
| 수동 법규 검색 | 자동 Neo4j 7-stage hybrid search |
| 단순 평탄지 envelope | §119 6 케이스 datum (산악/도로/인접지) |
| 정적 법규 데이터 | LLM 동적 추출 + 18 landmark 정확도 |
| Cesium 1차원 시각 | Z축 일치 + DatumInfoCard + 3D envelope |
| 로컬 단일 | MCP 57 tools + A2A + Telegram bot 멀티에이전트 |

## NotebookLM 사용 프롬프트 (이 파일 업로드 후)

```
이 소스를 기반으로 25_ACE 프로젝트의 4페이지 포트폴리오를 만들어줘:

Page 1: Overview & Demo (한 줄 요약 + 8 step 데모 + 검증 결과)
Page 2: System Architecture (4 service + tech stack + data pipeline)
Page 3: Core Modules (Law / Datum / Envelope / Mass)
Page 4: Agent System & Validation (Hermes / MCP / A2A / 9 commits / Roadmap)

각 페이지는 다이어그램 + 표 + 핵심 수치 포함. 한국어로 작성.
```
