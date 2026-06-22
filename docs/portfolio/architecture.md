---
name: Page 2 — System Architecture
description: 4-service 라이브 배포 + 기술 스택 + 데이터 파이프라인 (datum 흐름 예시).
type: project
originSessionId: 5fb8be34-8660-4347-81b7-6bf5ae10ee85
---
## 4-Service Live Deployment

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
               │                                    │
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

## 배포 URL

| 서비스 | URL | 플랫폼 | 비용/월 |
|---|---|---|---|
| ARR Frontend | `arr-frontend.pages.dev` | CF Pages | $0 |
| AG-frontend | `ag-frontend-5s3.pages.dev` | CF Pages | $0 |
| AG-light Worker | `law-light-api.clickaround8.workers.dev` | CF Workers | $0 |
| ARR Backend | `arr-backend-production.up.railway.app` | Railway | ~$5 |
| Hermes Gateway | `158.180.66.165` (`arr-gateway`) | Oracle VM | ~$22 |

## Tech Stack

| Layer | Tech |
|---|---|
| **Frontend** | React 19, TypeScript 5.9, Vite 7, Tailwind v4, Cesium 3D, Vworld 3D Map |
| **Backend** | Django 6, Python 3.13, Shapely, pyproj, httpx |
| **Database** | Neo4j (법령 31K nodes, 임베딩 100%), SQLite (audit log) |
| **AI/ML** | OpenAI gpt-4o-mini (LLM 추출), text-embedding-3-large (3072d), Jina v3 (1024d) |
| **Geometry** | Vworld Data API, Open-Meteo Elevation API (Copernicus GLO-90) |
| **Optimization** | NSGA-II Genetic Algorithm, Pareto front |
| **Agents** | Hermes (Nous Research), MCP (57 tools), A2A protocol, Telegram bot |
| **DevOps** | Cloudflare Pages/Workers, Railway, Oracle VM, Playwright E2E |

## Data Pipeline (datum 예시)

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

## 모노레포 구조

```
25_ACE/
├── ARR/                    법규 + 토지 + 매스 (Railway 배포)
│   ├── backend/            Django :8000
│   │   ├── law/            법규 검색 (proxy → :8011)
│   │   ├── land/           토지 분석 (42 규제 + §119 datum)
│   │   ├── design/         매스 최적화 (NSGA-II)
│   │   ├── tools/          CLI 검증 도구 (verify_*.py)
│   │   └── core/           BaseModel, Organization
│   └── frontend/           React+Vite :5173 → CF Pages
│       └── src/
│           ├── law/        법규 채팅 UI
│           ├── land/       토지 분석 UI
│           └── design/     매스 최적화 + Cesium 3D
│
├── AG-light/worker/        CF Worker 256KB (도메인 폴더 4개)
│   ├── land/               토지 자동 분석
│   ├── regulation/         42규제 계산
│   ├── geometry/           8종 규제선
│   └── law/                법령 검색 (Vectorize)
│
├── AG/                     에이전트 시스템
│   ├── autogen_a2a_kit/    AutoGen Studio + ACE MCP (57 tools)
│   ├── agent/              law-domain-agents (FastAPI :8011)
│   └── Auto-Claude/        24/7 Hub (Electron + 20 agents)
│
└── memory/                 메모리 폴더 (이 디렉토리)
    └── arr/datum-elevation/    9 commits 박제 (5 서브폴더)
```

## 핵심 폴더 (datum)

```
ARR/backend/land/services/
├── datum/                          ⭐ 신규 (Phase 1)
│   ├── __init__.py
│   ├── elevation_api.py            Open-Meteo HTTP + 캐시
│   ├── calculator.py               §119 가중평균 수식
│   └── cases.py                    6 케이스 dispatcher
├── envelopes/                      LOCKED (Session 14)
│   └── sunlight.py                 정북일조 envelope
├── regulations/                    공유 컨텍스트
│   ├── building_context.py         §119 effective_height
│   └── registry.py                 RegulationSpec
├── setback_geometry.py             규제선 8종 통합
└── pnu_resolver.py                 Vworld geocode + PNU 추출
```
