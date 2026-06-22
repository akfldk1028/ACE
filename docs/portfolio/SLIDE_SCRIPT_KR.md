# 25_ACE Architectural Intelligence — 16장 슬라이드 한글 발표 스크립트

**데크**: NotebookLM "25_ACE Architectural Intelligence" (V3)
**소요**: 1장당 30~60초, 총 10~15분
**용도**: 면접 / 투자자 / 교수 / 포트폴리오 발표

---

## 1. Hero — 25_ACE 인트로 (30초)

> "안녕하세요. **25_ACE — Automated Architectural Intelligence Pipeline** 발표하겠습니다.
> 한 줄로 요약하면 **주소만 입력하면 한국 건축법규 42개를 자동 분석하고, 일조권 사선과 매스 최적화까지 3D로 시각화하는 AI 파이프라인**입니다."

**핵심 메시지**: 단일 입력 → 전 과정 자동화

---

## 2. Problem → Solution — 왜 만들었나 (45초)

> "기존엔 건축사가 수기로 했습니다.
> - **법조항 1개 검색 5~10분**
> - 정확도 약 60% (사람 실수)
> - 분당 0.1개 디자인
>
> 25_ACE는:
> - **<1초** 만에 7-stage 하이브리드 검색
> - **95%+** 정확도 (178개 자동 테스트)
> - 분당 **300개+** 매스 생성
>
> **결론: 90% 시간 단축**."

**핵심 메시지**: 정량 비교 → 압도적 효율 향상

---

## 3. Tech Stack — 기술 스택 (45초)

> "12개 핵심 기술을 결합했습니다:
> - **프론트엔드**: React 19, TypeScript, Vite 7, Tailwind v4
> - **백엔드**: Django, Python 3.13
> - **데이터**: Neo4j (31K 법조항 그래프), OpenAI text-embedding-3-large (3072차원)
> - **3D/지오메트리**: Cesium 3D, Shapely + pyproj
> - **배포**: Cloudflare Workers (엣지), Railway (백엔드)"

**핵심 메시지**: 모던 풀스택 + AI/3D 도메인 전문 라이브러리

---

## 4. ⭐ System Architecture (drawio) — 시스템 아키텍처 (90초)

> "전체 시스템을 **3 layer**로 나눴습니다:
>
> **상단 (클라이언트)**: 브라우저 → AG-frontend (Vite/React 19, 포트 5173)
>
> **중단 (백엔드)**: Cloudflare Pages Functions → ARR Django :8000 (Railway 호스팅) ↔ law-domain-agents :8011 (FastAPI)
> 두 백엔드 서비스는 **A2A JSON-RPC 2.0** 프로토콜로 통신합니다.
>
> **하단 (데이터)**:
> - Neo4j Bolt :7687 — 31K 법조항 노드, vector + fulltext 인덱스
> - Vworld API — 주소→PNU 지오코딩
> - Open-Meteo GLO-90 — 90m 해상도 표고 데이터
>
> **사이드 (엣지/게이트웨이)**:
> - AG-light Worker (Cloudflare, 256KB 번들) — 모바일/외부 access
> - Jina v3 Vectorize (1024차원) — 엣지 임베딩 캐시
> - Oracle VM Hermes Gateway — Telegram 봇 인터페이스"

**핵심 메시지**: 마이크로서비스 분리 + 명확한 통신 프로토콜

---

## 5. Data Flow 8 Steps — 데이터 흐름 (60초)

> "주소 입력부터 3D 매스까지 **8단계**:
>
> 1. **Address** (주소 문자열)
> 2. **Vworld geocoding** → 좌표
> 3. **PNU 19자리 코드** 추출 (필지 고유번호)
> 4. **Vworld land use** → 용도지역, 필지 면적
> 5. **Neo4j 7-stage hybrid 검색** → 42개 규제 법조항
> 6. **§119 datum dispatcher** + Open-Meteo elevation → 대지 기준높이
> 7. **§86 일조권 envelope** (slope 2:1 사선) → 3D 건축 가능 볼륨
> 8. **NSGA-II 유전 알고리즘** → 매스 후보 → Cesium 3D 렌더링"

**핵심 메시지**: 결정론적 파이프라인. 각 단계 검증 가능.

---

## 6. Law Search Funnel — 7단계 법조항 검색 (60초)

> "법조항 검색은 단순 키워드가 아닙니다. **7-stage hybrid funnel**입니다:
>
> 1. **Exact match** — 법조항 번호 직접 매칭
> 2. **Fulltext** (CJK 바이그램) — 한국어 형태소 처리
> 3. **Vector embedding** (3072d cosine) — 의미 유사도
> 4. **Relationship boosting** (CONTAINS edge) — 그래프 관계 가산점
> 5. **RRF (Reciprocal Rank Fusion)** — 여러 ranking 결합
> 6. **MMR (Maximal Marginal Relevance)** — 중복 제거 다양성 확보
> 7. **Domain re-ranking** — 5개 도메인 재정렬
>
> **결과**: 95%+ 정확도, 31K 노드 중 0.1초 안에 top-20 추출"

**핵심 메시지**: 의미 검색 + 그래프 + 다양성 — 단순 BM25 능가

---

## 7. ⭐ §119 Datum 6-case Dispatcher — 대지 기준높이 (75초)

> "건축법 §119 시행령은 **대지의 기준 평면 높이**를 결정합니다. 6가지 경우로 분류:
>
> **루트**: parcel_variance_m (필지 표고 분산)
>
> 1. **FLAT** (variance < 2m) → 필지 중심점 표고
> 2. **SLOPE_LE3M** (2~8m) → 둘레 가중평균
> 3. **SLOPE_GT3M** (>8m) → 분할 세그먼트 가중평균
> 4. **ROAD_FLAT** (도로 인접, slope <1m) → 도로 중심선
> 5. **ROAD_SLOPED** (도로 인접, slope >1m) → 도로 가중평균
> 6. **SITE_ABOVE_ROAD** (필지 ≫ 도로) → (필지+도로)/2 평균
>
> 임계값(2m/8m/1m)은 **90m DEM 노이즈 흡수 테스트**로 캘리브레이션했습니다.
>
> **검증**: 18개 랜드마크 측정 → 도시 평균 11m, 해안 3.7m 정확도"

**핵심 메시지**: 법령을 코드로 정확히 옮긴 **법-코드 1:1 매핑**

---

## 8. §86 Sunlight Envelope LOCKED SPEC — 일조권 사선 (60초)

> "건축법 §86 ① 2호 — **북측 인접 대지 일조권**.
>
> - 사선 비율 **2:1** (높이=거리×2)
> - 4단계 계단형 envelope (높이 9m마다)
> - **3-Layer 보호 (LOCKED SPEC)**:
>   1. config 플래그 (env)
>   2. 백엔드 source enum (open_meteo/failed/null)
>   3. 프론트엔드 ternary (datum vs terrain fallback)
>
> 9 commit으로 잠궜습니다. **시각 결과는 박제되어 변경 금지**."

**핵심 메시지**: Critical 스펙은 3중 방어. 회귀 방지 메커니즘.

---

## 9. NSGA-II Multi-Objective GA — 매스 최적화 (60초)

> "매스 생성은 **다목적 유전 알고리즘 NSGA-II**로 합니다:
>
> - **Population**: 30
> - **Generations**: 30
> - **Crossover**: 0.9
> - **Mutation**: 0.1
>
> 3개 목적함수를 **동시에 최적화** (서로 trade-off):
> - FAR (용적률 최대화)
> - Sunlight (일조권 점수)
> - Landscaping (조경 비율)
>
> 결과는 **Pareto front** — 단일 정답이 아니라 **최적 후보 집합**.
> 사용자는 산점도에서 원하는 균형점을 선택합니다."

**핵심 메시지**: 단일 답 X, **선택 가능한 최적 집합**

---

## 10. ⭐ 10 Mass Algorithm Types — 10종 매스 알고리즘 (90초)

> "매스 형태는 **10가지 타입**으로 다양화합니다 (5×2 그리드):
>
> 1. **Additive** — 자유 블록 결합 (K=5 boxes)
> 2. **Subtractive** — Boolean cut으로 envelope에서 빼기
> 3. **Grid** — 모듈러 3×3 셀 조합
> 4. **L-shape** — 비대칭 코너 매스
> 5. **U-shape** — 한쪽 열린 중정
> 6. **Cross** — 십자 평면
> 7. **Courtyard** — 닫힌 중정
> 8. **Tower+Podium** — 수직 복합용도
> 9. **H-shape** — 쌍둥이 윙
> 10. **Radial** — 회전 대칭
>
> 각 타입마다 **고유 파라미터 공간**이 있어 GA가 안에서 탐색합니다."

**핵심 메시지**: 알고리즘 다양성 → 다양한 해 + 사용자 의도 반영

---

## 11. ⭐ 4 Floor Plan Algorithms — 4종 평면 알고리즘 (90초)

> "매스 안 **평면도 자동 생성**도 4가지 알고리즘으로:
>
> 1. **GA + Series Gene** — Pareto 다목적 (30g/30p), 인접성+면적+컴팩트성. 가장 느리지만 최고 품질.
> 2. **Subdivision** — 재귀 이진 분할, BFS 인접성 정렬. **가장 빠른 결정론적**.
> 3. **MCTS** — UCB 트리 탐색 (RL-Floorplan 포팅), 그리드 순차 배치. ~300 LOC.
> 4. **Circle Packing** — 인력/척력 물리 시뮬레이션 → 그리드 셀 할당. **유기적 레이아웃**.
>
> **104개 unit + E2E 테스트 통과**.
>
> 알고리즘별 특징이 달라서 사용자가 용도(주거/업무/근생)에 따라 선택합니다."

**핵심 메시지**: 매스 → 평면까지 **End-to-End 자동화**. 알고리즘 비교 분석.

---

## 12. Setback Geometry 7+1 — 규제선 7종 + 3D 클리핑 (60초)

> "법규는 **건폐율/용적률**만이 아닙니다. 7개 규제선을 모두 그립니다:
>
> 1. **인접대지선** — neighbor boundary
> 2. **도로사선 폐지** (2026년 폐지된 규정 제외)
> 3. **정북일조 §86** — 4단계 계단형
> 4. **인동거리** — 동 간 거리
> 5. **채광사선** — daylight oblique
> 6. **도로폭** offset
> 7. **BCR/FAR** boundary
>
> 거기에 +1: **3D 클리핑** — 매스가 envelope 침범시 자동 절단."

**핵심 메시지**: 단순 BCR/FAR 넘어 **법령 전수 적용**

---

## 13. Multi-Agent System — 다중 에이전트 (75초)

> "사용자 인터페이스는 **3가지 채널**:
>
> 1. **AG-frontend** (웹 UI)
> 2. **Telegram bot** `@DK_arch_bot`
> 3. **MCP** — Claude Code, Cursor 등 IDE에서 직접 호출 가능 (57 tools)
>
> 백엔드는:
> - **Hermes Plugin** (Oracle VM `158.180.66.165`) — Telegram 처리
> - ARR Django → **6 specialized agents**: Land / Law / Datum / Envelope / Mass / FloorPlan
> - **A2A JSON-RPC 2.0** 프로토콜 (포트 9020)
>
> 각 에이전트가 자기 도메인만 처리. 결합도 낮음."

**핵심 메시지**: **Agent-as-Service**. 다양한 클라이언트 + 모듈러 백엔드.

---

## 14. Live 4-Service Deployment — 실서비스 배포 (60초)

> "**4개 서비스 라이브 운영 중**:
>
> | 서비스 | URL | 플랫폼 | 비용/월 |
> |--------|-----|--------|---------|
> | AG-frontend | ag-frontend-5s3.pages.dev | Cloudflare Pages | $0 |
> | ARR Backend | arr-backend-production.up.railway.app | Railway | $5 |
> | AG-light Worker | law-light-api.clickaround8.workers.dev | Cloudflare Workers | $0 |
> | Hermes Gateway | 158.180.66.165 | Oracle VM | $22.63 |
>
> **합계 약 $28/월**. 학생 프로젝트 수준 비용으로 **프로덕션급 멀티 서비스** 운영."

**핵심 메시지**: 실제 배포 + 비용 효율 + 검증된 운영

---

## 15. Validation Stack — 검증 (60초)

> "**3-Tier 검증** 체계:
>
> 1. **Unit Tests** (178+개 Django 테스트)
>    - 39 datum 테스트 (§119 6-case 전수)
>    - 167 land regression 테스트
>
> 2. **Integration Tests** (Playwright E2E 235개, 31초 실행)
>    - 프론트엔드 ↔ 백엔드 ↔ DB 풀스택 검증
>
> 3. **Live Tests** (8개 PNU 실측)
>    - 강남, 성북, 한남, 여의도, 우동, 평창, 대관령 등
>    - 도시 평균 **11m** 정확도, 해안 **3.7m**
>
> **9 commit**으로 §119 datum 안정화 (린한 엔지니어링)."

**핵심 메시지**: 자동 + 수동 + 실측 → **다층 신뢰성**

---

## 16. Roadmap 2026 + Closing — 로드맵 + 마무리 (45초)

> "2026 로드맵:
>
> - **Q1 — MVP** (현재): 매스 + 평면 + 법규 자동 분석
> - **Q2 — B2B Pilot**: 건축사무소 5곳 베타
> - **Q3 — Public Beta**: 일반 공개
> - **Q4 — B2G Enterprise**: 지자체 / 인허가 자동화
>
> 마무리:
>
> > **'Building the next standard of architectural feasibility.'**
> > **'건축 타당성 검토의 다음 표준을 만들어갑니다.'**
>
> 감사합니다. 질문 받겠습니다."

**핵심 메시지**: 명확한 단계별 확장 + 비전

---

## 발표 팁

### 시간 배분
- **5분 버전**: 1, 2, 4(짧게), 6 또는 11(택1), 14, 16
- **10분 버전**: 1, 2, 4, 5, 7, 10, 11, 14, 15, 16
- **15분 버전**: 16장 전체

### 청중별 강조 포인트
- **건축사/교수**: 7(§119), 8(§86), 10(매스), 12(규제선) → 도메인 정확도
- **개발자**: 4(아키텍처), 6(검색), 11(알고리즘), 15(테스트) → 엔지니어링
- **투자자**: 2(시장), 9(GA), 14(배포 비용), 16(로드맵) → 비즈니스
- **종합 면접**: 16장 전체 + Q&A

### 자주 받는 질문 대비
- "왜 NSGA-II?" → 다목적 trade-off 본질, Pareto가 사용자 선택권
- "왜 Neo4j?" → 법조항 간 CONTAINS 관계가 중요. 그래프 boost +20% 정확도
- "Hermes는 왜?" → 오픈소스 + plugin 시스템 + Telegram 기본 지원
- "비용 어떻게 $28?" → CF Pages/Workers Free Tier + Oracle Always Free 활용

---

## 데크 위치

NotebookLM → Studio 패널 → **"25_ACE Architectural Intelligence"** (가장 위) → Expand 클릭 → 16장 thumbnail 좌측 navigation.

PPTX export: 우상단 ⋯ 메뉴 → "Download as PowerPoint".
