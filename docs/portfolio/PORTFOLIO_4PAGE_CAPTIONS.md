# 포트폴리오 4-Page Captions

**Project**: 25_ACE — Architectural Design Automation
**Author**: DongHyeon KIM
**Date**: 2026-05-02
**Tone**: 격식체 + 설명형 (Problem → Decision → Impact 구조)

---

## PAGE 1 — Architectural Design Automation

### 메인 헤드라인
**ARCHITECTURAL DESIGN AUTOMATION**
*주소 한 줄에서 출발해, 건축 가능 영역까지 자동으로 도출하는 파이프라인.*

### 본문 단락
건축가가 부지를 받았을 때 가장 먼저 묻는 질문은 단순하다. "여기 무엇이 들어갈 수 있는가." 그러나 이 질문에 답하려면 20개 법령, 58개 시행령, 그리고 그 안에 흩어진 31,126개의 조항을 일일이 확인해야 한다. 본 프로젝트는 이 과정을 0.1초 안에 끝내는 시스템을 목표로 시작되었다.

사용자가 "강남구 역삼동 677"과 같이 주소를 입력하면, 프론트엔드는 Vworld API로 PNU를 조회하고, Django 백엔드가 토지이용계획·지가·면적을 수집한다. 수집된 데이터는 Neo4j에 적재된 법조항 그래프와 대조되어, 건폐율 80%·용적률 1,300%·관련 법조항 170개·규제 41개를 자동으로 도출한다. 이후 NSGA-II 최적화 엔진이 매스 형태까지 산출한다. 네 개 서비스(Cloudflare Pages 2개, Railway Django, Oracle VM Hermes)가 모두 라이브 상태로 연결되어 있다.

### 시스템 다이어그램 캡션 — `4-Service Live Stack`
초기에는 단일 서버 구조로 시작했다. Django 한 프로세스 안에 React 빌드, Neo4j, NSGA-II 엔진, 텔레그램 봇까지 모두 묶여 있었다. 그러나 프론트엔드 배포 한 번에 백엔드 응답이 멈추는 문제가 반복되었고, 클라우드 비용도 월 80달러를 넘어섰다.

책임을 네 개로 분리했다. 정적 자산은 Cloudflare Pages의 무료 CDN으로 글로벌 배포하고, 데이터 처리 워크로드만 Railway의 Django 인스턴스에 남겼다. 법규 검색은 응답 지연을 줄이기 위해 Cloudflare Worker(256KB) 위에 Jina v3 Vectorize 2,051개 벡터를 얹어 엣지에서 처리한다. 텔레그램 봇과 LLM persona routing은 메인 백엔드와 분리할 필요가 있어 Hermes Agent를 Oracle Cloud VM에 별도로 배치했다.

현재 네 서비스 모두 production 환경에서 운영 중이며, 월 운영비는 25달러 수준이다.

### 하단 KPI
- **20** Laws · **58** Decrees
- **31,126** Nodes · **31,063** Edges
- **3,072d** OpenAI Embedding · **100%** Vectorized
- **0.1s** Retrieval · **95%** Accuracy

---

## PAGE 2 — The Law Is a Graph

### 메인 헤드라인
**THE LAW IS A GRAPH**
*법조항을 RDB에 넣지 않고, 7계층 그래프로 풀어낸 이유.*

### 본문 단락
한국 법령은 본질적으로 트리 구조를 가진다. 법(LAW) 아래에 장(章)·절(節)·조(條)·항(項)·호(號)·목(目)이 최대 7단계로 중첩되며, 같은 레벨끼리는 NEXT 관계로 이어지고, 다른 법을 인용할 때는 CITES 관계로 건너뛴다. 이러한 구조를 RDB에서 표현하려면 한 조항을 조회하는 데에도 다수의 JOIN이 필요했다.

Neo4j 5.x 위에 31,126개의 노드와 31,063개의 관계를 적재했다. 모든 항(HANG)에 OpenAI text-embedding-3-large(3072차원) 임베딩을 100% 채웠고, 관계(CONTAINS)에도 임베딩을 부여하여 그래프 컨텍스트 자체가 검색 점수에 가산되도록 설계했다. 검색은 Exact → Fulltext(CJK Bigram) → Vector → Relationship Boost → RRF → MMR → Domain Re-ranking의 7단계 하이브리드 파이프라인을 거친다. 그 결과, 단순 BM25(약 70%) 대비 정확도 95%, 응답시간 0.1초로 Top-20 조항을 도출한다.

### 7-Level Hierarchy 다이어그램 캡션 — `From Law to Item`
한국 법령 체계는 LAW → JANG(章) → JEOL(節) → JO(條) → HANG(項) → HO(號) → MOK(目)의 7단계로 정의된다. 법령에 따라 중간 계층은 누락될 수 있으나, LAW와 JO는 모든 법령에 존재한다. 이 구조 자체를 그래프 노드 타입으로 매핑함으로써, 조항 간 부모-자식 관계와 인용 관계를 단일 쿼리로 탐색할 수 있게 했다.

### Node Schema 박스 캡션 — `Embedding-First Node`
모든 노드는 `law_name · number · title · content · full_id · revision_dates · embedding[3072]`의 속성을 갖는다. 텍스트 본문과 의미 벡터를 함께 보관함으로써, 키워드 검색과 의미 검색을 동일한 인덱스 위에서 수행할 수 있다.

### 엣지 3종 캡션 — `Three Edges, Three Roles`
CONTAINS는 부모-자식 관계로, 31,063개 전체에 임베딩이 부여되어 그래프 컨텍스트 점수에 활용된다. NEXT는 같은 레벨의 순서를 표현하며, 페이지 단위 탐색에 사용된다. CITES는 타법 인용 관계로, RAG 응답 보강 시 교차 참조 경로로 활용된다.

### 우측 그래프 시각화 캡션 — `31K-Node Knowledge Graph`
31,126개 노드 전체를 Neo4j Bloom으로 펼친 결과다. 좌측의 거대한 클러스터는 국토계획법 계열, 우측은 건축법·주택법 계열에 해당한다. 단일 BM25 대비 정확도가 95%로 향상된 핵심 근거는, 관계 임베딩을 통해 그래프 컨텍스트를 검색 점수에 통합한 데에 있다.

---

## PAGE 3 — Generative Design

### 메인 헤드라인
**GENERATIVE DESIGN**
*Packing 알고리즘과 유전 알고리즘 — 평면과 매스를 각각 다른 생성 엔진으로 푼다.*

### 본문 단락
법조항을 모두 도출했다고 해서 건물이 자동으로 정의되지는 않는다. 평면(floor plan) 단계에서는 학교·병원·사무실 같은 용도별 실(室)을 충돌 없이 배치해야 하고, 매스(mass) 단계에서는 정북일조·도로사선·인접대지 이격이 동시에 작용하는 envelope 안에서 가장 합리적인 외형을 찾아야 한다. 두 문제는 본질이 다르다. Packing은 *공간 분할* 문제이며, 매스 최적화는 *다목적 trade-off* 문제다. 그래서 알고리즘도 두 갈래로 분리했고, 페이지 또한 좌측은 packing, 우측은 유전 알고리즘으로 구성했다.

좌측 페이지는 평면 packing에 할애했다. Grid Cell GA, Diffusion 모델, MCTS, Mesh Packing — 4종의 packing 알고리즘을 동일 부지에 적용해 결과를 비교한다. 각 알고리즘은 실 단위의 면적·인접·동선 제약을 다르게 다루며, 비정형 부지나 곡선 경계에서도 충돌 없이 영역을 채운다. AUA 프레임워크의 Grasshopper Python 2.7 코드 5개 프로젝트를 모두 Python 3.12 웹 환경으로 포팅했다.

우측 페이지는 유전 알고리즘 기반 매스 디자인이다. NSGA-II(Population 30, Generations 30, Crossover 0.9, Mutation 0.1)가 매스 형태 10종 — Additive, Subtractive, Grid, L-Shape, U-Shape, Cross, Courtyard, Tower+Podium, H-Shape, Radial — 을 후보로 두고 Pareto-optimal solution을 탐색한다. 용도지역에 따라 목적함수가 동적으로 매핑되며, 주거지역은 Max Area + Max Daylight를, 상업지역은 Max Area + Max Landscaping을 적용한다.

### 좌측 페이지 캡션 — `Packing Algorithms for Floor Plans`
좌측 페이지는 4종의 packing 알고리즘을 동일 부지에 적용한 비교 결과다. Grid Cell GA는 격자 셀 단위 유전 알고리즘으로 영역을 진화시키고, Diffusion 모델은 학습된 분포에서 평면을 샘플링하며, MCTS는 트리 탐색으로 분할 순서를 최적화한다. Mesh Packing은 비정형 부지에서 곡선 경계를 따라 실을 배치한다. 상단의 컬러 그리드는 알고리즘별 영역 분할 결과를 나란히 비교한 것이며, 컬러 영역은 용도별 실(교실·복도·관리실 등)에 대응한다. 하단의 시퀀스는 packing이 단계적으로 채워지는 과정을 입체로 시각화한 것으로, 빈 부지에서 출발해 실이 하나씩 배치되며 최종 평면이 완성되는 흐름을 보여준다.

### 우측 페이지 캡션 — `Mass Design via NSGA-II`
우측 페이지는 매스 단계의 유전 알고리즘 결과다. 상단의 산점도는 30세대 동안 수렴한 비지배 해 집합으로, 가로축은 면적, 세로축은 일조·조경 점수를 의미한다. 단일 최적해가 아닌 trade-off 공간을 제시함으로써, 사용자가 부지 조건과 사업 목표에 따라 직접 후보 매스를 선택하도록 설계했다. 하단의 매스 형태 10종은 NSGA-II가 탐색하는 design space의 전체 후보군이다. 각 typology는 별도의 generative rule을 가지며, 동일 부지에서도 용도지역과 목적함수에 따라 서로 다른 후보가 Pareto front에 진입한다.

---

## PAGE 4 — Multi-Agent Collaboration

### 메인 헤드라인
**MULTI-AGENT COLLABORATION**
*MCP, A2A, Hermes — 세 프로토콜로 에이전트를 묶었다.*

### 본문 단락
단일 LLM 호출로는 본 시스템의 작업을 모두 수행할 수 없었다. 법조항 검색은 Neo4j 쿼리, 매스 최적화는 NSGA-II 실행, 텔레그램 응답은 자연어 생성으로, 각 작업이 요구하는 도구와 응답 시간이 상이했다. 단일 에이전트에 모든 책임을 부여할 경우 hallucination 빈도가 급증했고, 응답 일관성을 보장하기 어려웠다.

이에 책임을 분리하는 방향으로 재설계했다. 중심에는 Hermes Agent(Oracle Cloud VM, DashScope Qwen-plus LLM)가 위치하며, 사용자 요청을 받아 persona routing을 수행하고, MCP Server(57개 tool)를 통해 ARR Backend Django를 호출한다. 에이전트 간 통신은 A2A JSON-RPC 2.0 프로토콜로 표준화했고, Shared Memory Bus가 중간 결과를 공유 메모리에 적재해 다른 에이전트가 다시 접근할 수 있도록 했다.

토폴로지 자체도 별도의 연구 주제였다. 에이전트가 *언제 종료해야 하는가*는 협력 패턴에 따라 달라진다. 14가지 coordination topology를 비교하여 termination dynamics를 정량적으로 측정했고, 그 결과를 COLM 2026에 *"When Should Multi-Agent Teams Stop? A Systematic Study of Termination Dynamics Across 14 Coordination Topologies"* 라는 논문으로 정리해 제출했다. 실 서비스의 6-Agent SelectorGroupChat 구성은 본 연구 결과를 반영하여, 41개 규제 도출을 0.1초 안에 완료한다.

### Agent Architecture 캡션 — `Three-Layer Separation`
시스템은 세 개의 layer로 분리되어 있다. MCP Server는 도구 호출 layer로, ARR Backend Django의 모든 기능을 57개의 표준 tool로 래핑한다. Hermes Agent는 persona routing layer로, 사용자 요청의 도메인을 판별해 적절한 도메인 에이전트를 호출한다. Shared Memory Bus는 state layer로, 모든 에이전트가 동일한 상태에 접근할 수 있도록 한다. 모든 통신은 A2A JSON-RPC 2.0으로 통일했다.

### A2A Mesh 캡션 — `Full-Mesh Coordination`
User · AI Agents · Tools · Memory가 풀 메시(full-mesh) 형태로 연결되며, 14개 토폴로지 중 한 형태에 해당한다. 메시 구조는 단일 실패점(SPOF)을 제거하지만, 종료 시점 판단이 어렵다는 trade-off를 동반한다. 본 연구는 이 trade-off를 정량적으로 비교한 결과다.

### Live Result 캡션 — `End-to-End Demo`
"강남구 역삼동 677"을 입력했을 때 BCR 80% / FAR 1,300% / 위성지도 오버레이가 1초 안에 렌더링되는 실제 화면이다. 6-Agent SelectorGroupChat 구성으로 41개 규제와 170여 개 법조항을 동시 도출한다.

---

## Footer (4페이지 공통)
**25_ACE Project · DongHyeon KIM · 2026**
- arr-frontend.pages.dev
- ag-frontend-5s3.pages.dev
- COLM 2026 Paper: *When Should Multi-Agent Teams Stop?*

---

## 참고: 톤 가이드라인

| 원칙 | 적용 방식 |
|------|-----------|
| Problem → Decision → Impact | 각 캡션을 "초기 한계 → 설계 결정 → 정량 결과"의 3단 구조로 통일 |
| 격식체 + 설명형 | "~다.", "~했다." 종결. 구어체("죽었다", "박았다") 배제 |
| 다이어그램 비중복 | 다이어그램이 보여주는 노드/화살표는 캡션에서 반복하지 않음. 의사결정 이유와 정량 결과 중심 |
| 정량 표현 | 비용(80→25달러), 속도(1.2초→0.1초), 정확도(70%→95%), 노드 수(31,126개) 등 구체 수치 명시 |
| 단락 길이 | 본문 단락 2~3문단 / 캡션 1~2문단 / 헤드라인 1줄 |
