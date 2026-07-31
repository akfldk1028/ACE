# Changelog: February 2026

## 2026-02-26: Step 5 Relationship Embeddings Complete

### What was done
- Re-ran full relationship embedding pipeline (step2→step3→step4→step5) for all 10 laws
- 9,502 CONTAINS relationships now have 3,072-dim OpenAI embeddings
- `contains_embedding` vector index created and ONLINE in Neo4j
- This enables Stage 4 `_relationship_search()` in law_search_engine.py

### Problems solved
1. **Neo4j DB offline after restart**: `neo4j` database was locked by stale lock file
   - Fix: Delete `~/.Neo4jDesktop2/.../data/databases/neo4j/database_lock`, then `START DATABASE neo4j`
2. **Stale embeddings data**: Previous embeddings file only covered 3 laws (국토계획법) from old PDF pipeline, but Neo4j now has 10 laws from API pipeline
   - Fix: Re-ran from step2 to regenerate contexts for all 9,502 current relationships
3. **step4 ID matching unstable**: Original script uses `id(r)` (Neo4j internal IDs) which change on restart
   - Fix: Created `step4_fix_upload.py` using `full_id` property matching (stable across restarts)
   - Note: Original step4 still works if run immediately after step2 (IDs match within same session)

### Test results
- 93 Django land tests: ALL PASS
- AG-frontend TypeScript: CLEAN (0 errors)
- AG-frontend build: SUCCESS (3.25s)
- Step 5 search tests: 3/3 queries return correct semantic types (EXCEPTION, REFERENCE, DETAIL)

## 2026-02-25: Phase 4 Frontend + Phase 5 Multi-Agent

### Phase 4: Land Page Frontend
- Created `AG-frontend/src/features/land/` with 9 new files
- LandPage + 7 components + useLand TanStack Query hooks
- Route `/land` added with lazy loading
- Sidebar navigation with MapPin icon
- i18n: 38 keys each for ko-KR and en-US
- 16 Playwright E2E tests (all API-mocked)
- Fixed `arrClient.ts` types to match actual backend response:
  - `regulation` (singular, flat) → `regulations` (plural, nested with article citations)
  - Added `zone_info`, `land_info`, `law_articles` proper types
  - Added `extended` regulations type

### Phase 5: Multi-Agent Team
- Created `039_Land_Swarm_Analysis_Team.json`
- 6-agent SelectorGroupChat: land_analyst, legal_interpreter, regulatory_monitor, spatial_analyzer, market_analyst, report_writer
- Phased selector routing, max 25 messages

## 2026-02-25: Phase 3.5 Extended Regulations

- Added 31 extended regulation items (Group A/B/C)
- New: `regulation_calculator_ext.py` for scale-dependent calculations
- New: `zoning_limits_extended.json` for zone-dependent lookups
- New: `LandAnalysisResult.regulations_extended` JSONField
- 27 new tests (total: 93)

## 2026-02-24: Phase 3 Vworld Data API + 10 Laws Loaded

- Vworld Data API integration (3 endpoints): zone + area + price
- Zone name normalization ("일반상업" → "일반상업지역")
- Partial failure tolerance (any 1 of 3 APIs succeeding = overall success)
- 10 laws downloaded from law.go.kr API and loaded into Neo4j
- All HANG nodes embedded (step3), 5 domains created (step4)
- Search pipeline v2: Fulltext CJK, MMR diversity, per-law caps

## 2026-02-24: Phase 2.5 Vworld Geocoding

- Vworld geocoding API: address → coordinates + PNU
- PNU extraction from `level4LC` field (19-digit code)
- 6/6 address test cases pass
