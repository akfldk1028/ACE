# 25_ACE Project - Claude Code Context

## Project Overview

AutoGen Studio SaaS platform with custom frontend, multi-agent orchestration, A2A protocol support, and **land regulation analysis system** (건축법규 분석).

**Core Goal**: AI agent가 땅 정보를 받아 관련 건축법규를 자동 분석하고, 건폐율/용적률/건축제한 등 모든 규제를 도출하는 시스템. **Phase 1-5 ALL DONE** — 주소→PNU→Vworld API→41규제+법조항 자동분석 완료. E2E 검증: "강남구 역삼동 677" → BCR=80%, FAR=1300%, 170개 법조항, 41개 규제.

```
25_ACE/
├── AG-frontend/          # SaaS Frontend (Vite 7 + React 19 + TS 5.9 + Tailwind v4)
├── AG/Auto-Claude/       # Electron app + CLI 24/7 Hub (20 agents)
├── AG/autogen_a2a_kit/   # AutoGen + A2A agents + SDK + ACE MCP Server
├── AG/agent/law-domain-agents/  # Law search engine (FastAPI, port 8011)
├── AG/AG-Research/       # Multi-Agent Termination Study (paper)
├── ARR/backend/          # Django backend (port 8000)
│   ├── law/              #   Law search proxy (→ :8011) + ingestion pipeline
│   └── land/             #   Land regulation analysis (건폐율/용적률/건축제한)
├── ARR/frontend/         # Legacy React+Electron UI (law search UI at src/law/)
├── JSON_MODULES/         # 98 AutoGen component JSON files
├── tests/                # Cross-project integration tests
└── venv/                 # Python virtual environment
```

## Service Topology & Port Map

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLAUDE / AGENT LAYER                        │
│  Claude Code ←→ ACE MCP Server (stdio or :8200)                │
│                   57 tools (FastMCP)                            │
└───────┬──────────────┬──────────────┬──────────────┬────────────┘
        │              │              │              │
   AutoGen Studio  Message Bus  SharedMemory   Law Tools
        │              │              │         ┌────┴────┐
        ▼              ▼              ▼         ▼         ▼
   ┌─────────┐  ┌──────────┐  ┌──────────┐  Direct   ARR Proxy
   │ :8081   │  │ :8100    │  │ :8101    │  (fast)   (logged)
   │ AutoGen │  │ MsgBus   │  │ Memory   │    │         │
   │ Studio  │  │ +Viewer  │  │ Events   │    │    ┌────▼────┐
   └─────────┘  └──────────┘  └──────────┘    │    │ :8000   │
                                               │    │ ARR     │
                                               │    │ Django  │
                                               │    │ +SQLite │
                                               │    └────┬────┘
                                               │         │
                                               ▼         ▼
                                          ┌──────────────────┐
                                          │ :8011            │
                                          │ law-domain-agents│
                                          │ (FastAPI + A2A)  │
                                          └────────┬─────────┘
                                                   │
                                              ┌────▼────┐
                                              │ :7687   │
                                              │ Neo4j   │
                                              │ (bolt)  │
                                              └─────────┘
```

### Port Registry

| Port | Service | Project | Protocol |
|------|---------|---------|----------|
| 5173 | AG-frontend dev server | AG-frontend/ | HTTP (proxy→8081) |
| 7474 | Neo4j Browser | external | HTTP |
| 7687 | Neo4j Bolt | external | bolt:// |
| 8000 | ARR Django backend | ARR/backend/ | HTTP |
| 8011 | law-domain-agents | AG/agent/law-domain-agents/ | HTTP + A2A |
| 8081 | AutoGen Studio | AG/autogen_a2a_kit/ | HTTP + WS |
| 8100 | AG-CLI Message Bus | AG/autogen_a2a_kit/AG-cli/ | HTTP |
| 8101 | AG-CLI SharedMemory | AG/autogen_a2a_kit/AG-cli/ | HTTP |
| 8200 | ACE MCP Server (HTTP mode) | AG/autogen_a2a_kit/AG-cli/mcp/ | streamable-http |

### Law Search Data Flow

Two paths exist - choose based on whether logging is needed:

```
FAST (no logging):          MCP law_search → :8011/api/search → Neo4j
LOGGED (analytics):         MCP arr_law_search → :8000/law/search/ → :8011/api/search → Neo4j
                                                   └→ SearchLog (SQLite)
```

Field mapping at each hop:
- MCP `arr_law_search(query, limit)` → ARR `{"q": query, "limit": limit}`
- ARR views.py → law-domain-agents `{"query": query, "limit": limit}`
- MCP `law_search(query, limit)` → law-domain-agents `{"query": query, "limit": limit}` (direct)

### Law Ingestion Pipeline

**Two data sources** (choose one per law):

```
A) PDF Pipeline (legacy, 국토계획법 only):
   ARR/backend/law/STEP/run_all.py → step1(PDF→JSON) → step2(JSON→Neo4j) → step3(embeddings) → step4(domains) → step5(rel-emb)

B) Open API Pipeline (recommended, 18 laws):
   ARR/backend/law/scripts/law_downloader.py → data/api/*.json → step2(JSON→Neo4j) → step3 → step4 → step5
   Requires: LAW_API_OC env var (open.law.go.kr 회원가입 후 로그인ID)
   Usage: python law_downloader.py --oc EMAIL [--list | --force]
```

**Current state (2026-02-27)**:
- step2: LAW 18, HANG 6171, HO 6026, MOK 1284, JO 2431, JANG 96, JEOL 50 = 16,081 nodes
- step3: ALL 6171 HANG embeddings (OpenAI text-embedding-3-large, 3072-dim) — 100%
- step4: 5 domains (land_use_regulation:2286, national_land_planning:2004, building_standards:1018, zoning_regulation:614, urban_planning:249)
- step5: ALL 16,058 CONTAINS rel embeddings — 100%

**law_downloader.py** targets 18 laws: 6개 법률(국토계획법, 건축법, 농지법, 산지관리법, 자연공원법, 수도법) × 3 types(법률, 시행령, 시행규칙)

**Neo4j**: `bolt://localhost:7687`, pw=`11111111` (Neo4j Community 5.26.0).

**Vector indexes**: `hang_embedding_index`, `ho_embedding_index`, `mok_embedding_index`, `jo_embedding_index`, `contains_embedding` (all ONLINE, 3072-dim cosine).
**Fulltext indexes**: `hang_content_fulltext` (CJK bi-gram), `jo_content_fulltext`.

### Land Regulation Analysis (`ARR/backend/land/`)

**Purpose**: 땅 정보(PNU/주소) → 용도지역 → 건폐율/용적률/건축제한 + 관련 법조항 분석

```
POST /land/analyze/   ← PNU/주소 + zones → 건폐율+용적률+법조항
POST /land/resolve/   ← 주소→PNU (Vworld) 또는 PNU 검증
GET  /land/zones/     ← 21개 용도지역 규제 목록
GET  /land/stats/     ← 쿼리 통계
```

Data flow:
```
Input (PNU/주소/zones)
  ├─ pnu_resolver: Vworld API 지오코딩 + **주소→PNU 자동 추출** (level4LC)
  ├─ land_api: Vworld Data API (3개: 토지이용계획+토지임야+공시지가) — Phase 3 DONE
  ├─ zoning_mapper: 21개 용도지역 → 건폐율/용적률 (static JSON, 복수시 최엄격)
  ├─ law_enricher: :8011 법조항 검색
  └─ LandQuery → SQLite (audit log)
```

**Vworld API** (2026-02-24 연동 완료):
- Key: `VWORLD_API_KEY` in `ARR/backend/.env` (만료: 2026-08-24)
- 주소→좌표+PNU: `api.vworld.kr/req/address` (PARCEL/ROAD)
- PNU 추출: `response.refined.structure.level4LC`에서 19자리 PNU 직접 추출
- 6/6 지번 주소 테스트 성공 (용인 죽전, 서초, 춘천, 나주, 분당, 강남)

**Phase status**:
- Phase 1-2: DONE (skeleton + static data + services + views, 27 tests)
- Phase 2.5: DONE (2026-02-24) — Vworld API 연동, 주소→PNU 자동 추출
- Phase 3: DONE (2026-02-24) — Vworld Data API 3개 (getLandUseAttr, ladfrlList, getIndvdLandPriceAttr) → 용도지역+면적+공시지가 자동조회, 66 tests
- Phase 4: DONE — MCP tools (arr_land_analyze/resolve/zones/stats) + Frontend Land page (/land)
- Phase 5: DONE — 6-agent SelectorGroupChat (039_Land_Swarm_Analysis_Team.json), 41규제(10core+31extended), 93 tests

**Env vars**: `VWORLD_API_KEY` (geocoding+PNU+DataAPI), `LAW_BACKEND_URL` (:8011), `LAW_API_OC` (law.go.kr Open API)

### ACE MCP Server

- **File**: `AG/autogen_a2a_kit/AG-cli/mcp/autogen_studio_server.py`
- **57 tools** in 17 categories
- **Config env vars**: AUTOGEN_STUDIO_URL(:8081), MESSAGE_BUS_URL(:8100), SHARED_MEMORY_URL(:8101), LAW_BACKEND_URL(:8011), ARR_BACKEND_URL(:8000)
- **Run**: `python autogen_studio_server.py` (stdio) or `--transport streamable-http --port 8200`

## AG-frontend (Primary Active Development)

### Stack
- **Vite 7.3** + **React 19** + **TypeScript 5.9** + **Tailwind v4.1**
- **Zustand** (state) + **TanStack Query v5** (server state) + **React Router v7**
- **@xyflow/react** + **dagre** (agent flow visualization)

### Commands
```bash
cd AG-frontend
npm run dev          # localhost:5173 (proxy -> :8081)
npm run build        # tsc -b && vite build (~3s)
npx tsc --noEmit     # Type check only
npx vitest run       # Unit tests (26 tests)
npx playwright test  # E2E tests (235 tests, 31s)
```

### Proxy & WebSocket
- `/api/*` proxied to `http://localhost:8081` (AutoGen Studio)
- `ws: true` REQUIRED in vite proxy for Playground WebSocket execution
- NEVER call `http://localhost:8081` directly from browser (CORS blocked)

### 9 Pages (lazy-loaded)
Team Builder(`/build`), Playground(`/`), MCP, A2A Agents(`/agents`), Gallery, History(`/history`), Deploy, **Land(`/land`)**, Settings

## Coding Conventions (MUST FOLLOW)

### React Patterns
- `React.memo()` on ALL list item / card components
- State updater pattern: `setState(prev => ...)` to avoid stale closures
- `pushToHistory` inside `setDraft` updater (not outside)
- DnD keys: name-based stable identity, NOT index-based
- Keyboard shortcuts: guard with `e.target instanceof HTMLTextAreaElement || HTMLInputElement`

### TypeScript
- `erasableSyntaxOnly`: class fields not in constructor params
- Union type casting: `as unknown as Record<string, unknown>` (no direct cast)
- Pure functions: `getTeamName()` / `getTeamPattern()` - NOT hooks, no `use` prefix

### CSS / Theme
- Use semantic tokens: `text-(--color-semantic-warning)` NOT `text-amber-500`
- Badge has no `className` prop - wrap in `<span className>` instead
- 7 themes x 2 modes (light/dark)

### Imports
- Path alias: `@/` -> `src/`
- Use `dagre` not `@dagrejs/dagre` (CJS compat issue with Vite)
- ARIA: Never `aria-hidden="true"` on backdrop (hides ALL children). Use `role="dialog" aria-modal="true"`

## API Contract Rules

These are AutoGen Studio backend specifics - do NOT assume standard REST:

| Operation | Correct | Wrong |
|-----------|---------|-------|
| Team update | `POST /api/teams/` (id in body, upsert) | `PUT /api/teams/:id` |
| Session messages | Use `GET /api/sessions/:id/runs` | No `/messages` endpoint |
| A2A register | `{ url }` field | `{ agent_url }` |
| A2A health single | `{ status: bool }` | Not `{ healthy }` |
| A2A health all | `{ agents: [{ is_online }] }` | Not `{ agents: [{ healthy }] }` |
| Health check | `{ status: true }` (boolean) | Not string |
| Validate | Tries instantiation, fails without API key | `is_valid: false` expected |

## AutoGen Studio

- Runs on port **8081**
- SQLite DB: `~/.autogenstudio/autogen04203.db`
- API: `GET /api/teams/`, `GET /api/sessions/`, `GET /api/sessions/{id}/runs`
- AssistantAgent v2: needs `reflect_on_tool_use: false` + `tool_call_summary_format: "{result}"`

## Windows Environment

- Always use `encoding='utf-8'` (default cp949 breaks everything)
- Chrome profile lock: kill chrome.exe and remove SingletonLock files

## Testing

- **E2E**: 235 Playwright tests (25 files) - run with backend on port 8081
- **Unit**: 26 vitest tests (3 files) - pure logic tests
- Before committing: `npx tsc --noEmit && npm run build && npx playwright test`
