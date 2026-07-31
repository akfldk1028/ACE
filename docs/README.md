# 25_ACE Documentation

## For the next AI agent

Start here. Read these docs in order:

1. **[SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md)** — Architecture, ports, services, how everything connects
2. **[LAND_ANALYSIS.md](LAND_ANALYSIS.md)** — Land regulation API: endpoints, request/response, 41 regulations, 21 zones, service pipeline
3. **[LAW_PIPELINE.md](LAW_PIPELINE.md)** — Law ingestion (10 laws → Neo4j), embedding pipeline (HANG + relationship), 7-stage search, vector indexes
4. **[FRONTEND_LAND_PAGE.md](FRONTEND_LAND_PAGE.md)** — AG-frontend /land page: components, hooks, i18n, E2E tests
5. **[AGENT_TEAMS.md](AGENT_TEAMS.md)** — Multi-agent team 039 (6-agent land analysis), SharedMemory, report structure
6. **[CHANGELOG_2026-02.md](CHANGELOG_2026-02.md)** — What was done, problems solved, current state

## Also read

- `CLAUDE.md` (project root) — Coding conventions, API contracts, environment setup
- `ARR/backend/CLAUDE.md` — Django backend specifics
- `ARR/backend/law/PIPELINE.md` — Detailed law pipeline steps

## Current State (2026-02-26)

| Component | Status | Tests |
|-----------|--------|-------|
| ARR backend (land) | Phase 3.5 DONE (41 regs) | 93 pass |
| AG-frontend (/land) | Phase 4 DONE | 16 E2E pass |
| Multi-Agent team 039 | Phase 5 DONE (JSON created) | Manual only |
| Neo4j (10 laws) | 9,514 nodes, all indexes ONLINE | - |
| HANG embeddings (step3) | 3,943 DONE | - |
| Relationship embeddings (step5) | 9,502 DONE | 3 search tests pass |
| `contains_embedding` index | ONLINE | - |

## Key Commands

```bash
# Django tests
cd ARR/backend && python manage.py test land -v 2

# Frontend
cd AG-frontend && npx tsc --noEmit && npm run build && npx playwright test e2e/land.spec.ts

# Start services
# 1. Neo4j Desktop (port 7687)
# 2. cd AG/agent/law-domain-agents && python -m uvicorn server:app --port 8011
# 3. cd ARR/backend && python manage.py runserver 8000
# 4. cd AG-frontend && npm run dev
```
