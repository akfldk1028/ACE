# 25_ACE System Overview

> Last updated: 2026-02-26

## What is 25_ACE?

A **Multi-Agent Land Regulation Analysis Platform** that:
1. Takes a land address or PNU code as input
2. Retrieves zoning and land data from government APIs (Vworld)
3. Searches relevant legal articles from a Neo4j knowledge graph (10 Korean laws)
4. Computes 41 building regulations (BCR, FAR, height limits, setbacks, etc.)
5. Returns a comprehensive regulation report with legal citations

## Architecture Diagram

```
                     ┌──────────────────────────────────┐
                     │         AG-frontend :5173         │
                     │  React 19 + Vite 7 + Tailwind v4 │
                     │  /land page → LandPage.tsx        │
                     └──────────┬───────────────────────┘
                                │ /arr/* proxy
                                ▼
┌────────────────────────────────────────────────────────┐
│                   ARR Django :8000                       │
│                                                          │
│  POST /land/analyze/   ← Main analysis endpoint          │
│  POST /land/resolve/   ← Address→PNU geocoding            │
│  GET  /land/zones/     ← 21 zoning regulation list        │
│  GET  /land/stats/     ← Query statistics                 │
│                                                          │
│  Services:                                               │
│  ├─ pnu_resolver    → Vworld Geocoding API               │
│  ├─ land_api        → Vworld Data API (3 endpoints)      │
│  ├─ zoning_mapper   → Static JSON (21 zones)             │
│  ├─ regulation_calculator_ext → Scale-dependent rules    │
│  └─ law_enricher    → law-domain-agents :8011            │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│            law-domain-agents :8011                       │
│            FastAPI + A2A Protocol                        │
│                                                          │
│  7-Stage Search Pipeline:                                │
│  Exact → Fulltext CJK → Vector → Relationship →         │
│  RRF Fusion → RNE Rerank → MMR Diversity →              │
│  Hierarchy Expansion → Enrichment                       │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│                  Neo4j :7687                             │
│                                                          │
│  10 Laws → 9,514 nodes (HANG/HO/MOK/JO/JANG/JEOL/LAW) │
│  9,502 CONTAINS relationships                           │
│                                                          │
│  Vector Indexes:                                         │
│  ├─ hang_embedding_index    (3,943 HANG nodes)          │
│  ├─ ho_embedding_index      (3,135 HO nodes)            │
│  ├─ mok_embedding_index     (550 MOK nodes)             │
│  ├─ jo_embedding_index      (1,774 JO nodes)            │
│  └─ contains_embedding      (9,502 relationships)       │
│                                                          │
│  Fulltext Index:                                         │
│  └─ hang_content_fulltext   (CJK bi-gram)              │
│                                                          │
│  5 Domains:                                              │
│  national_land_planning(1526), building_standards(1018), │
│  land_use_regulation(959), zoning_regulation(312),       │
│  urban_planning(128)                                     │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│              ACE MCP Server (stdio / :8200)              │
│              57 tools via FastMCP                        │
│                                                          │
│  Land tools: arr_land_analyze, arr_land_resolve,        │
│              arr_land_zones, arr_land_stats              │
│  Law tools:  law_search, law_search_domain,             │
│              law_domains, law_health                     │
│  + AutoGen Studio, Message Bus, SharedMemory, A2A       │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│           AutoGen Studio :8081                           │
│           Team 039: Land Swarm Analysis (6 agents)      │
│                                                          │
│  land_analyst → legal_interpreter → regulatory_monitor  │
│  → spatial_analyzer → market_analyst → report_writer    │
└────────────────────────────────────────────────────────┘
```

## Port Registry

| Port | Service | Purpose |
|------|---------|---------|
| 5173 | AG-frontend | React SaaS UI (dev server) |
| 7474 | Neo4j Browser | Web interface for Neo4j |
| 7687 | Neo4j Bolt | Graph database protocol |
| 8000 | ARR Django | Backend API (land + law proxy) |
| 8011 | law-domain-agents | Law search engine (FastAPI) |
| 8081 | AutoGen Studio | Multi-agent orchestration |
| 8100 | Message Bus | Inter-agent messaging |
| 8101 | SharedMemory | Cross-agent state store |
| 8200 | ACE MCP Server | Claude Code tool interface |

## 10 Laws in Neo4j

| Law | Type | Nodes |
|-----|------|-------|
| 국토의 계획 및 이용에 관한 법률 | 법률 | ~1,800 |
| 국토의 계획 및 이용에 관한 법률 | 시행령 | ~2,150 |
| 국토의 계획 및 이용에 관한 법률 | 시행규칙 | ~340 |
| 건축법 | 법률 | ~1,060 |
| 건축법 | 시행령 | ~1,415 |
| 건축법 | 시행규칙 | ~420 |
| 농지법 | 법률 | ~520 |
| 산지관리법 | 법률 | ~610 |
| 자연공원법 | 법률 | ~470 |
| 수도법 | 법률 | ~730 |

## Quick Start

```bash
# 1. Start Neo4j Desktop (port 7687, pw=11111111)

# 2. Start law-domain-agents
cd AG/agent/law-domain-agents && python -m uvicorn server:app --port 8011

# 3. Start ARR Django backend
cd ARR/backend && python manage.py runserver 8000

# 4. Start AG-frontend
cd AG-frontend && npm run dev

# 5. Open http://localhost:5173/land
```

## Key Environment Variables

| Variable | Location | Purpose |
|----------|----------|---------|
| VWORLD_API_KEY | ARR/backend/.env | Vworld geocoding + data APIs |
| OPENAI_API_KEY | .env (multiple) | Embeddings + LLM calls |
| NEO4J_PASSWORD | System env / .env | Neo4j authentication (default: 11111111) |
| LAW_BACKEND_URL | System env | law-domain-agents URL (default: http://localhost:8011) |
| LAW_API_OC | System env | law.go.kr Open API ID (hanvit4303) |
