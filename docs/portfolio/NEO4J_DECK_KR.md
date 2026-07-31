# Korean Architectural Law Knowledge Graph — NotebookLM Slide Deck

**제목**: "Korean Architectural Law Knowledge Graph"
**소스**: 8 (기존 7 + Pasted Text 추가)
**날짜**: 2026-04-29
**슬라이드 수**: 10장
**스타일**: IT 포폴 모던 화이트 + 인디고 액센트 + drawio 다이어그램

NotebookLM URL: https://notebooklm.google.com/notebook/291e0dfc-7add-4594-aa07-38c0e4c2bf63 → Studio → "Korean Architectural Law Knowledge Graph"

## 슬라이드 구성 (10장)

| # | 제목 | 내용 |
|---|---|---|
| **1** | Hero | "Korean Architectural Law as a Knowledge Graph" + "Neo4j Architecture · 31K nodes · 58 laws · 3072d embeddings" + 인디고 그라데이션 블롭 |
| **2** | Numbers Dashboard | 5 카드: 31,126 nodes / 58 laws / 12,069 HANG (100%) / 3072 dim / >95% accuracy |
| **3** ⭐ | Schema 7-Tier Hierarchy | drawio 수직 체인: LAW(58) → JANG(258) → JEOL(102) → **JO(4,928)** → **HANG(12,069)** → HO(11,550) → MOK(2,156). JO/HANG 인디고 하이라이트. [CONTAINS] 화살표 |
| **4** | 3 Edge Types | 3 카드 + mini-diagram: CONTAINS (parent-child tree, 31,063, 100% embedded with 3072d), NEXT (sequential sibling), CITES (cross-reference, RAG reinforcement) |
| **5** | Node Properties Table | 8개 properties: law_name / number / title / content / full_id (UNIQUE) / order / metadata (json) / embedding[3072] |
| **6** | 7 Indexes | 2-column: Vector (5종, 3072d cosine) + Fulltext (2종, CJK bigram). **contains_embedding** 인디고 하이라이트 (+20% accuracy via edge embedding) |
| **7** ⭐ | 7-Stage Hybrid Search Funnel | drawio 깔때기: Exact → Fulltext CJK → Vector 3072d → Relationship Boost → RRF → MMR → Domain Re-rank. "Top-20 in 0.1s · 95%+ accuracy" |
| **8** ⭐ | Cypher Query Showcase | 다크 코드 블록 (mac window) — 일조권 §86 쿼리 (vector + 3-level traversal). 푸터: "Vector match + 3-level hierarchy + sub-item aggregation in ONE query. RDB equivalent: 6 JOIN operations" |
| **9** ⭐ | Graph vs RDB | 3-column 비교표 5행: 7-tier traversal / Sibling order / Cross-law citation / Vector on relationships / Fulltext+Vector. 인디고 ✅ vs RDB ❌ |
| **10** | Pipeline & Stack | 5-step 타임라인 (law.go.kr → JSON → Neo4j → OpenAI emb $0.40 → Domain → Rel emb) + Stack chip + 178+ tests |

## 핵심 캡처

- `neo4j-deck-hero.png` — 슬라이드 1 (Hero)
- `neo4j-deck-slide3-hierarchy.png` — 7-tier 계층 (drawio)
- `neo4j-deck-slide4-edges.png` — 3 엣지 카드
- `neo4j-deck-slide7.png` — 7-stage 검색 깔때기
- `neo4j-deck-slide8-cypher.png` — Cypher 쇼케이스 (다크 코드)
- `neo4j-deck-slide9-graph-vs-rdb.png` — Graph vs RDB 비교표

## 발표 시나리오 (5분 그래프 DB 단독)

1. **0:00 인트로** (slide 1): "한국 건축법을 그래프로 모델링했습니다."
2. **0:30 숫자** (slide 2): "31K 노드, 58 법령, 12K 임베딩 100%."
3. **1:00 계층** (slide 3): "법은 7단계 계층입니다. JO(조)와 HANG(항)이 검색 핵심."
4. **1:45 엣지** (slide 4): "3종 관계: CONTAINS는 트리 뼈대인데, **관계 자체에도 임베딩**을 박았어요."
5. **2:30 검색** (slide 7): "7-stage hybrid funnel — 0.1초 안에 31K 중 top-20."
6. **3:30 Cypher** (slide 8): "이게 한 쿼리로 됩니다. RDB는 6 JOIN."
7. **4:30 비교표** (slide 9): "이래서 Neo4j입니다." → 끝.

## 면접 단골 질문 대비

**Q: 왜 그래프 DB?**
→ slide 9 보여주기. "법조항은 본질적으로 그래프 (계층 + 순서 + 인용)다. RDB는 6 JOIN 폭발."

**Q: relationship에 임베딩 왜?**
→ slide 6 인디고 하이라이트. "단순 노드 매칭은 60%대 정확도. 관계 컨텍스트 가산점으로 +20% 향상."

**Q: 한국어 검색 어떻게?**
→ slide 6 Fulltext CJK Bigram. "한국어는 띄어쓰기 일관성 낮아서 2-gram 분석기 필수."

**Q: 임베딩 모델은?**
→ OpenAI text-embedding-3-large 3072차원. HANG 12K 적재 비용 ~$0.40 (1회).

## NotebookLM에서 이 데크 위치

Studio 패널 가장 위에 "Korean Architectural Law Knowledge Graph". 클릭 → Expand → 10장 thumbnail 좌측 navigation. PPTX export 가능 (⋯ 메뉴).
