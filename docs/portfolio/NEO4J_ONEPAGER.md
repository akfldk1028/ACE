# 25_ACE · Neo4j Legal Graph

**Korean Architectural Law as a Knowledge Graph** — 31,126 nodes, 31,063 relationships, 7-stage hybrid search.

---

## Numbers

```
┌───────────┬───────────┬───────────┬───────────┬───────────┐
│  31,126   │   58      │  3,072    │ 12,069    │   95%+    │
│  nodes    │  laws     │  dim      │ HANG emb  │ accuracy  │
│           │ (20 acts) │  cosine   │  100%     │  vs ~70%  │
└───────────┴───────────┴───────────┴───────────┴───────────┘
```

---

## Schema — 7-tier Korean legal hierarchy

```
                LAW (58)  ─── 법령
                  │ CONTAINS
                JANG (258) ─── 장
                  │
                JEOL (102) ─── 절
                  │
                  JO (4,928) ─── 조  ⭐ statute unit
                  │
                HANG (12,069) ─── 항  ⭐ vector search core (100% emb)
                  │
                  HO (11,550) ─── 호
                  │
                MOK (2,156) ─── 목
```

**3 edge types**:
`CONTAINS` (31,063 · with embedding) · `NEXT` (same-level seq) · `CITES` (cross-law refs)

---

## Why a graph? Why Neo4j?

| Need                              | Graph Native | RDB        |
|-----------------------------------|--------------|------------|
| 7-tier hierarchy traversal        | 1-hop        | 6× JOIN    |
| Sibling order (NEXT)              | edge prop    | window fn  |
| Cross-law citation                | edge         | join table |
| Vector search **on relationships**| ✅ Neo4j 5.x | ❌         |
| Fulltext (CJK bigram) + vector    | ✅ same query| 2 systems  |

> **법조항은 본질적으로 그래프다.** 계층 + 순서 + 인용 + 의미 — 한 곳에서 풀어야 일관된다.

---

## 7-Stage Hybrid Search

```
  Query ──► [1] Exact ──► [2] Fulltext (CJK bigram) ──► [3] Vector (3072d cosine)
                                                            │
                                                            ▼
        ┌──── [4] Relationship Boost (contains_embedding) ◄─┘
        │
        ▼
  [5] RRF fusion ──► [6] MMR diversity ──► [7] Domain re-rank ──► Top-20  (≈ 0.1s)
```

**Differentiator**: Stage 4 uses embeddings on the *edges*, not just nodes — the CONTAINS relationship itself carries semantic meaning. **+20% accuracy** over node-only search.

---

## One Cypher query — full 일조권 §86 lookup

```cypher
CALL db.index.vector.queryNodes('hang_embedding_index', 5, $q) YIELD node AS hang, score
MATCH (jo:JO)-[:CONTAINS]->(hang)
OPTIONAL MATCH (hang)-[:CONTAINS]->(ho:HO)-[:CONTAINS]->(mok:MOK)
RETURN jo.title, hang.content,
       collect(DISTINCT ho.content)  AS items,
       collect(DISTINCT mok.content) AS subitems,
       score
ORDER BY score DESC
```

→ Vector match + 3-level hierarchy join + sub-item aggregation in **one round-trip**.

---

## Indexes (7)

```
Vector  (3072d cosine):  hang  ·  ho  ·  mok  ·  jo  ·  contains_embedding
Fulltext (CJK bigram):   hang_content  ·  jo_content
```

---

## Pipeline (one-time, automated)

```
law.go.kr API ──► JSON ──► Neo4j load ──► OpenAI embedding (12K HANG, ~$0.40)
   58 laws          step1     step2          step3 + step5 (rel emb)
```

5-step idempotent ingestion · incremental re-runs · zero downtime.

---

**Stack**: Neo4j 5.x · OpenAI text-embedding-3-large · Python 3.13 · law.go.kr Open API
**Validation**: 178+ Django tests · 8 PNU live runs · queries logged to SearchLog
