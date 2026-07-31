# Law Ingestion & Search Pipeline

> Last updated: 2026-02-26

## Overview

Korean legal texts (10 laws) are structured, stored in Neo4j as a hierarchical graph, embedded with OpenAI vectors, and searchable via a 7-stage hybrid pipeline.

## Data Sources

### law.go.kr Open API (Recommended)

```bash
cd ARR/backend
python law/scripts/law_downloader.py --oc hanvit4303 --force
# Downloads 10 laws to law/data/api/*.json
```

**10 target laws:**
- 국토의 계획 및 이용에 관한 법률 (법률, 시행령, 시행규칙)
- 건축법 (법률, 시행령, 시행규칙)
- 농지법
- 산지관리법
- 자연공원법
- 수도법

### PDF Pipeline (Legacy, 국토계획법 only)

```bash
python law/STEP/run_all.py
# PDF → JSON → Neo4j → Embeddings → Domains → RelEmbeddings
```

## Neo4j Graph Structure

```
LAW ──CONTAINS──→ JANG (장)
                   └──CONTAINS──→ JEOL (절)
                                   └──CONTAINS──→ JO (조)
                                                  └──CONTAINS──→ HANG (항)
                                                                 └──CONTAINS──→ HO (호)
                                                                                └──CONTAINS──→ MOK (목)
```

### Node Counts (2026-02-26)

| Label | Count | Description |
|-------|-------|-------------|
| LAW | 10 | Top-level law documents |
| JANG | 73 | 장 (Chapter) |
| JEOL | 27 | 절 (Section) |
| JO | 1,774 | 조 (Article) |
| HANG | 3,943 | 항 (Paragraph) — primary search target |
| HO | 3,135 | 호 (Item) |
| MOK | 550 | 목 (Sub-item) |
| Domain | 5 | Search domain groupings |
| **Total** | **9,517** | |

### Relationship Counts

| Type | Count | Embeddings |
|------|-------|------------|
| CONTAINS | 9,502 | 9,502 (100%) |

## Ingestion Pipeline Steps

### Step 1: Download (law_downloader.py)
- law.go.kr Open API → structured JSON (조/항/호/목)
- Env: `LAW_API_OC=hanvit4303`
- Output: `law/data/api/<법률명>.json`

### Step 2: JSON → Neo4j (step2)
- Parses JSON, creates graph nodes with `full_id` property
- Creates CONTAINS relationships with `order` property
- Idempotent: clears existing data for each law before insert

### Step 3: HANG Embeddings (step3)
- OpenAI `text-embedding-3-large` (3,072-dim)
- Embeds all 3,943 HANG node `content` fields
- Creates vector indexes: `hang_embedding_index`, `ho_embedding_index`, `mok_embedding_index`, `jo_embedding_index`
- Cost: ~$0.50 for all HANG nodes
- Standalone script: `NEO4J_PASSWORD=11111111 python law/scripts/run_step3_standalone.py`

### Step 4: Domain Assignment (step4/initialize_domains.py)
- Groups HANG nodes into 5 search domains
- Setup: `python AG/agent/law-domain-setup/initialize_domains.py`

### Step 5: Relationship Embeddings (step5)

**Purpose**: Embed CONTAINS relationship context for semantic relationship search.

Pipeline (all in `law/relationship_embedding/`):

```
step2_extract_contexts.py   → relationship_contexts.json (9,502 entries)
step3_generate_embeddings.py → relationship_contexts_with_embeddings.json (830 MB)
step4_update_neo4j.py        → Upload to Neo4j CONTAINS relations
step5_create_index_and_test.py → Create contains_embedding vector index
```

**How to run**:
```bash
cd ARR/backend
export NEO4J_PASSWORD=11111111
export PYTHONIOENCODING=utf-8

python law/relationship_embedding/step2_extract_contexts.py   # ~1s
python law/relationship_embedding/step3_generate_embeddings.py # ~90s, ~$0.07
python law/relationship_embedding/step4_update_neo4j.py        # ~80s (uses id(r))
python law/relationship_embedding/step5_create_index_and_test.py # ~10s
```

**IMPORTANT**: step4 uses `id(r)` (Neo4j internal IDs) which are NOT stable across restarts. If step4 shows low match rates after a DB restart, re-run from step2 to regenerate contexts with current IDs. Alternative: use `full_id` matching (see `step4_fix_upload.py` pattern in git history).

**Semantic type distribution** (9,502 relationships):
| Type | Count | % | Description |
|------|-------|---|-------------|
| REFERENCE | 4,618 | 48.6% | Cross-article references (제N조) |
| DETAIL | 2,493 | 26.2% | Detail listings (다음 각 호) |
| EXCEPTION | 1,869 | 19.7% | Exception clauses (다만, 제외) |
| GENERAL | 404 | 4.3% | General hierarchy |
| ADDITION | 117 | 1.2% | Additive clauses (또한, 및) |
| CONDITION | 1 | 0.0% | Conditional clauses |

**Result**: `contains_embedding` vector index enables Stage 4 relationship search in law_search_engine.py.

## Vector Indexes

| Index Name | Target | Dimensions | Status |
|------------|--------|------------|--------|
| `hang_embedding_index` | HANG.embedding | 3,072 | ONLINE |
| `ho_embedding_index` | HO.embedding | 3,072 | ONLINE |
| `mok_embedding_index` | MOK.embedding | 3,072 | ONLINE |
| `jo_embedding_index` | JO.embedding | 3,072 | ONLINE |
| `contains_embedding` | CONTAINS.embedding | 3,072 | ONLINE |
| `hang_content_fulltext` | HANG.content | N/A (fulltext) | ONLINE |

## 7-Stage Search Pipeline (law-domain-agents)

```
Query: "건폐율 80퍼센트"

Stage 1: Exact Match     → HANG where content contains exact query
Stage 2: Fulltext CJK    → hang_content_fulltext bi-gram search (per-law cap: 3)
Stage 3: Vector Search   → hang_embedding_index cosine similarity (per-law cap: 4)
Stage 4: Relationship    → contains_embedding relationship vector search
Stage 5: RRF Fusion      → Reciprocal Rank Fusion across stages
Stage 6: RNE Rerank      → Relevance-Novelty-Enrichment (threshold: 0.35)
Stage 7: MMR Diversity   → Maximal Marginal Relevance (λ=0.7)
  └─ Hierarchy Expansion → Cross-law type references (법률↔시행령↔시행규칙)
  └─ Enrichment          → Parent/child context addition
```

**Cross-law diversity examples:**
- "용도지역" → 6 laws (ALL)
- "건폐율" → 국토계획법 + 건축법 + 농지법
- "농지전용" → 농지법 + 산지관리법 + 국토계획법

## Neo4j Connection

```
URI: bolt://localhost:7687
Password: 11111111
Database: neo4j (default)
```

**Known issue**: After Neo4j Desktop restart, `neo4j` database may be offline due to lock file. Fix:
1. Delete lock file at `~/.Neo4jDesktop2/Data/dbmss/<id>/data/databases/neo4j/database_lock`
2. Connect to system DB and run `START DATABASE neo4j`

## File Locations

| File | Purpose |
|------|---------|
| `ARR/backend/law/scripts/law_downloader.py` | Download laws from API |
| `ARR/backend/law/STEP/run_all.py` | Run full ingestion pipeline |
| `ARR/backend/law/scripts/run_step3_standalone.py` | Run embeddings only |
| `ARR/backend/law/relationship_embedding/` | Relationship embedding pipeline |
| `ARR/backend/law/data/api/` | Downloaded law JSON files |
| `ARR/backend/law/data/zoning_limits.json` | 21 zone BCR/FAR limits |
| `ARR/backend/law/data/zoning_limits_extended.json` | Extended zone regulations |
| `AG/agent/law-domain-agents/` | Search engine (FastAPI) |
| `AG/agent/law-domain-setup/` | Domain initialization scripts |
