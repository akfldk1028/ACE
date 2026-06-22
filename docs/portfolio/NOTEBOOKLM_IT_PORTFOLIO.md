# 25_ACE Slide Decks — NotebookLM 4 Versions

**Notebook**: [The 25_ACE Project](https://notebooklm.google.com/notebook/291e0dfc-7add-4594-aa07-38c0e4c2bf63)
**Account**: hanvit4303@gmail.com (PRO)
**Date**: 2026-04-29

---

## ⭐ V3 (FINAL) — "25_ACE Architectural Intelligence" — 16 slides DEEP TECHNICAL

Latest. IT 포폴 + drawio 아키텍처 + 알고리즘 특징 전부 포함.

| # | Title | Content |
|---|---|---|
| 1 | Hero | "25_ACE / Automated Architectural Intelligence Pipeline" + soft purple blob, "DongHyeon Kim · 2026" |
| 2 | Problem → Solution | Manual (5-10min/clause, 60% acc, 0.1 designs/min) vs AI (<1s, 95%+, 300+ designs/min) |
| 3 | Tech Stack | 4×3 cards: React 19/TS/Vite 7/Tailwind/Django/Python/Neo4j/OpenAI emb/Cesium/Shapely/CF Workers/Railway+Oracle |
| 4 | **drawio System Architecture** | Layered diagram with HTTPS/A2A JSON-RPC arrows: Browser→AG-frontend (:5173)→CF Pages Functions/AG-light Worker (256KB)→ARR Django :8000 (Railway) ↔ law-domain-agents :8011 ↔ Jina v3 Vectorize (1024d) → Neo4j Bolt :7687 (31K, vector+fulltext) + Vworld API + Open-Meteo GLO-90 + Oracle VM Hermes Gateway |
| 5 | Data Flow 8 steps | (1) Address → (2) Vworld geocoding → (3) PNU → (4) Vworld land use → (5) Neo4j 7-stage → (6) §119 datum → (7) §86 envelope → (8) NSGA-II → Cesium 3D |
| 6 | Law Search Funnel | 7-stage hybrid pipeline: Exact → Fulltext (CJK bigram) → Vector 3072d → Rel boost (CONTAINS) → RRF → MMR → Domain re-rank |
| 7 | **§119 Datum 6-case Tree** | Root parcel_variance_m → FLAT (<2m) / SLOPE_LE3M (2-8m, indigo) / SLOPE_GT3M (>8m) / ROAD_FLAT / ROAD_SLOPED (>1m) / SITE_ABOVE_ROAD. "Thresholds calibrated via 90m DEM noise absorption" |
| 8 | §86 Envelope LOCKED | Cross-section showing 4-stage stair-step + slope 2:1 + 3-layer protection + "9 commits" stamp |
| 9 | NSGA-II Multi-Objective GA | pop 30, gen 30, crossover 0.9, mutation 0.1 + Pareto front (FAR vs sunlight vs landscaping) |
| 10 | **10 Mass Algorithm Types** | 5×2 cards with isometric outlines: Additive (K=5 boxes) / Subtractive / Grid 3×3 / L-shape / U-shape / Cross / Courtyard / Tower+Podium / H-shape / Radial |
| 11 | **4 Floor Plan Algorithms** | 2×2 cards: GA+Series Gene (Pareto multi-obj 30g/30p), Subdivision (recursive binary BFS), MCTS (UCB tree, RL-Floorplan port ~300 LOC), Circle Packing (physics→grid). "104 tests pass" chip |
| 12 | Setback Geometry 7+1 | 인접대지선/도로사선폐지/정북일조 §86 4단계/인동거리/채광사선/도로폭/BCR-FAR + 3D 클리핑 |
| 13 | Multi-Agent | Telegram bot @DK_arch_bot → Hermes Plugin (Oracle 158.180.66.165) → ARR Django → 6 specialized agents ↔ MCP 57 tools ↔ A2A :9020 |
| 14 | Live 4-Service Deploy | AG-frontend (CF Pages), ARR Backend (Railway $5), AG-light Worker (CF free 256KB), Hermes Gateway (Oracle $22.63) |
| 15 | Validation Stack | Unit (39 datum + 167 land = 178+) / Integration (Playwright 235 tests, 31s) / Live (8 PNU 11m urban + 3.7m coastal accuracy) |
| 16 | Roadmap + CTA | Q1 MVP / Q2 B2B Pilot / Q3 Public Beta / Q4 B2G Enterprise — "Building the next standard..." |

### Visual Confirmed
- White #FFFFFF background, indigo #4F46E5 single accent (sparingly)
- Inter / SF Pro typography, big bold headlines
- Cards: rounded 12-16px, thin 1px #E5E7EB borders
- drawio aesthetic: rounded service boxes + thin black 1px arrows + port labels + layer dividers
- Indigo highlights on SELECTED tree branch (e.g., SLOPE_LE3M)

### Screenshots
- `v3-deck-overview.png` — slide 1 hero + thumbnail strip
- `v3-slide4-drawio-arch.png` — drawio system architecture (HTTPS/A2A JSON-RPC labeled arrows)
- `v3-slide7-datum-6case.png` — §119 6-case dispatcher decision tree
- `v3-slide10-mass-types.png` — 10 mass types with isometric icons
- `v3-slide11-floorplan-algos.png` — 4 floor plan algorithms 2×2 + 104 tests

---

## V2 — "25_ACE Technical Datasheet" (12 slides)

Initial IT 포폴 — high-level overview only. Missing: floor plan algorithms, drawio detail, algorithm characteristics. Superseded by V3.

## V1 — "25_ACE Architectural AI" (12 slides)

Sharp-Edged Minimalism / 건축저널 스타일 — rejected by user. "건축포폴 몰라 존나 이상하게 나왔는데"

## V0 — "25_ACE Generative Blueprint" (12 slides)

NotebookLM default style.

## Process Narrative — "The Journey of a Building"

8-section text report (NOTEBOOKLM_REPORT.md). Supplementary, kept.

---

## 접근 방법

NotebookLM Studio panel → "25_ACE Architectural Intelligence" 클릭 → Expand 아이콘 → 16장 thumbnail navigation.

Slide Deck export: PPTX 다운로드 가능 (NotebookLM 우상단 ⋯ 메뉴).
