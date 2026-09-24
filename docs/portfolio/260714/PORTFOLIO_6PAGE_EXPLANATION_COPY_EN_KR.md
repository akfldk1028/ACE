# SUPERSEDED — 25_ACE Portfolio Explanation Copy (EN/KR)

> 이 문서는 이전 `1_1.jpg`–`1_6.jpg` 해석을 기준으로 작성되어 더 이상 최종 원고가 아니다.  
> 정리된 최종 다이어그램 `260707_16.jpg`–`260707_21.jpg`용 원고는 `PORTFOLIO_260707_16_21_FULL_LOGIC_COPY_EN_KR.md`를 사용한다.

Updated: 2026-07-16  
Target layout: `1_1.jpg`–`1_6.jpg`

아래의 **EN**은 포트폴리오에 직접 넣는 영문 원고다. **KR**은 영문의 의미와 사실관계를 확인하기 위한 한국어 번역이다. JPG 안에 현재 들어 있는 반복 영문은 모두 이 원고로 교체한다.

---

## PAGE 1 — Cover

### Main title

**EN**  
`ARCHITECTURAL DESIGN AUTOMATION`

**KR**  
`건축 설계 자동화`

### Subtitle

**EN**  
`From Address to Evidence-Backed Massing`

**KR**  
`주소에서 근거 기반 매스까지`

### Project information

**EN**

```text
Personal Research & Development
Legal Knowledge Graph · Multi-Agent Design · Generative Massing
July 2026
```

**KR**

```text
개인 연구 및 개발 프로젝트
법규 지식그래프 · 멀티에이전트 설계 · 생성형 매스
2026년 7월
```

### Upper-right introduction

**EN**

> Architectural feasibility is usually assembled from disconnected sources: parcel data, zoning rules, legal clauses, parking standards, and geometric constraints. This project connects them into one traceable design pipeline. A typed address becomes a parcel key, the parcel key retrieves site and legal evidence, and specialized agents translate that evidence into executable massing alternatives. Instead of presenting one opaque AI image, the system preserves the origin, geometry, constraints, and review status of every candidate.

**KR**

> 건축 가능성은 대지정보, 용도지역, 법조항, 주차기준, 형상 제약처럼 서로 분리된 자료를 종합해야 판단할 수 있다. 이 프로젝트는 이를 하나의 추적 가능한 설계 파이프라인으로 연결한다. 사용자가 입력한 주소는 필지 식별자로 변환되고, 필지 정보는 대지와 법규 근거를 불러오며, 전문 에이전트는 이 근거를 실행 가능한 매스 대안으로 번역한다. 하나의 불투명한 AI 이미지 대신, 모든 후보의 출처와 형상, 제약조건, 검토 상태를 함께 보존한다.

### Image caption

**EN**  
`A design ambition: moving from legal volume to an architecturally legible building.`

**KR**  
`법적 가능 볼륨을 건축적으로 읽히는 건물로 발전시키는 설계 목표.`

---

## PAGE 2 — Legal Knowledge Graph

### Main title

**EN**  
`THE LAW IS A GRAPH`

**KR**  
`법은 그래프다`

### Subtitle

**EN**  
`A seven-level statute structure transformed into searchable design evidence.`

**KR**  
`7단계 법령 구조를 검색 가능한 설계 근거로 변환한다.`

### Left introduction

**EN**

> Korean building regulations are not a flat collection of documents. A clause belongs to a hierarchy, follows neighboring clauses, and often cites another statute. The system models this structure in Neo4j as LAW, chapter, section, article, paragraph, item, and sub-item nodes. A hybrid retrieval pipeline combines exact, full-text, vector, and relationship-context search, allowing an agent to return both a relevant rule and the path that explains why it applies.

**KR**

> 한국의 건축 관련 법규는 평면적인 문서 집합이 아니다. 하나의 조항은 계층구조에 속하고, 같은 단계의 전후 조항과 연결되며, 다른 법령을 인용하기도 한다. 시스템은 이를 Neo4j에서 법, 장, 절, 조, 항, 호, 목 노드로 모델링한다. 정확검색, 전문검색, 벡터검색, 관계 맥락 검색을 결합하여 관련 규정뿐 아니라 그 규정이 적용되는 이유와 경로까지 함께 반환한다.

### Node-schema caption

**EN**

> Each searchable node retains its legal identity, title, content, revision history, source metadata, and semantic embedding. The result is evidence that can be inspected and cited, rather than an uncited language-model answer.

**KR**

> 각 검색 노드는 법적 식별자, 제목, 본문, 개정 이력, 출처 메타데이터, 의미 임베딩을 보존한다. 따라서 결과는 출처 없는 언어모델 답변이 아니라 확인하고 인용할 수 있는 근거가 된다.

### Bottom block 01

**EN**

**01 / 7-LEVEL STATUTE TREE**  
`LAW → JANG → JEOL → JO → HANG → HO → MOK` preserves the maximum hierarchy of Korean statutes while allowing optional intermediate levels.

**KR**

**01 / 7단계 법령 트리**  
`법 → 장 → 절 → 조 → 항 → 호 → 목`의 최대 계층을 보존하며, 법령에 따라 생략되는 중간 단계도 수용한다.

### Bottom block 02

**EN**

**02 / CONTAINS · NEXT · CITES**  
`CONTAINS` stores hierarchy, `NEXT` preserves sequence, and `CITES` connects cross-law references.

**KR**

**02 / 포함 · 순서 · 인용 관계**  
`CONTAINS`는 계층, `NEXT`는 같은 단계의 순서, `CITES`는 법령 간 인용 관계를 저장한다.

### Bottom block 03

**EN**

**03 / HYBRID RETRIEVAL**  
Exact, CJK full-text, vector, relationship-context, RRF/RNE, and MMR stages balance relevance with legal diversity.

**KR**

**03 / 하이브리드 검색**  
정확검색, 한글 전문검색, 벡터, 관계 맥락, RRF/RNE, MMR 단계를 결합해 관련성과 법령 다양성을 함께 확보한다.

### Bottom block 04

**EN**

**04 / LEGAL CLUSTER FIELD**  
The expanded portfolio snapshot contains 31,126 nodes and 31,063 relationships, exposing legal neighborhoods instead of isolated text fragments.

**KR**

**04 / 법규 클러스터 필드**  
확장 포트폴리오 스냅숏은 31,126개 노드와 31,063개 관계를 포함하며, 고립된 문장 대신 서로 연결된 법규 영역을 보여준다.

---

## PAGE 3 — Parcel Intelligence & A2A Context

### Main title

**EN**  
`PARCEL INTELLIGENCE`

**KR**  
`필지 인텔리전스`

### Secondary label

**EN**  
`PNU · VWORLD · A2A CONTEXT`

**KR**  
`PNU · 브이월드 · 에이전트 협업 맥락`

### Left introduction

**EN**

> A typed address is first resolved into a nineteen-digit PNU. The PNU retrieves the live VWorld parcel boundary and establishes a local metric frame for design. Parcel area, dominant axis, zoning context, neighboring roads, and verified frontage are converted into structured site facts. These facts are shared with the design agents as descriptions and bounded parameters, while the geometry compiler works directly with the measured parcel polygon.

**KR**

> 사용자가 입력한 주소는 먼저 19자리 PNU로 변환된다. PNU를 통해 브이월드의 실제 필지 경계를 불러오고, 설계를 위한 로컬 미터 좌표계를 설정한다. 대지면적, 주축, 용도지역 맥락, 인접도로, 확인된 도로 접면은 구조화된 대지 정보로 변환된다. 에이전트는 이를 설명과 제한된 파라미터로 전달받고, 형상 컴파일러는 실제로 측정된 필지 폴리곤을 직접 사용한다.

### GIS-layer explanation

**EN**

> The active site path combines parcel boundaries, road-access geometry, zoning and land information, elevation or datum evidence where available, and map imagery for visual review. Additional geospatial layers remain an extensible context rather than mandatory inputs to every generation run.

**KR**

> 현재 대지 분석 경로는 필지 경계, 도로 접근 형상, 용도지역과 토지정보, 이용 가능한 경우의 표고·기준면 근거, 시각 검토용 지도 영상을 결합한다. 그 밖의 공간정보 레이어는 모든 생성 과정의 필수 입력이 아니라 확장 가능한 맥락으로 다룬다.

### Agent-flow explanation

**EN**

> The orchestrator passes evidence through specialized roles for legal retrieval, parking review, architectural language, MassDSL authoring, geometry compilation, grammar criticism, and final review. Agent proposals can change design intent and graph parameters, but they cannot override deterministic legal, parking, capacity, or geometry gates.

**KR**

> 오케스트레이터는 법규 검색, 주차 검토, 건축언어 제안, MassDSL 작성, 형상 컴파일, 문법 비평, 최종 검토를 담당하는 전문 역할에 근거를 순차적으로 전달한다. 에이전트는 설계 의도와 그래프 파라미터를 수정할 수 있지만, 결정론적 법규·주차·용적·형상 검증을 무시할 수는 없다.

### Legal-envelope caption

**EN**  
`The parcel becomes a measured design field: site geometry, access, BCR, FAR, height, setback, sunlight, and parking remain explicit constraints.`

**KR**  
`필지는 측정 가능한 설계장으로 변환되며, 대지 형상과 접근, 건폐율, 용적률, 높이, 이격, 일조, 주차 조건이 명시적인 제약으로 유지된다.`

---

## PAGE 4 — Graph-to-Massing Generation

### Main title

**EN**  
`GRAPH TO MASSING`

**KR**  
`그래프에서 매스로`

### Subtitle

**EN**  
`Typed architectural operations compiled as measurable solids.`

**KR**  
`유형화된 건축 조작을 측정 가능한 솔리드로 컴파일한다.`

### Left introduction

**EN**

> Architectural intent is stored as an executable component graph rather than a style label. Each graph combines a base volume with typed operations such as carve, offset, split, bridge, fold, taper, sweep, loft, array, and stack. The compiler validates references, evaluates the operations recursively, and produces measurable geometry. Every accepted revision must change both the graph and the compiled solid before it can re-enter the candidate archive.

**KR**

> 건축적 의도는 스타일 이름이 아니라 실행 가능한 컴포넌트 그래프로 저장된다. 각 그래프는 기본 볼륨에 carve, offset, split, bridge, fold, taper, sweep, loft, array, stack과 같은 유형화된 조작을 결합한다. 컴파일러는 참조 관계를 검증하고 조작을 재귀적으로 계산하여 측정 가능한 형상을 생성한다. 수정된 후보는 그래프와 컴파일된 솔리드가 모두 실제로 달라져야 다시 후보 아카이브에 들어갈 수 있다.

### Upper-right operation-language explanation

**EN**

> The design vocabulary is derived from an architectural grammar: six relative base scopes, thirty operations, twenty combinations, nine aggregation recipes, and compound case-study languages. These are not fixed building templates. They are bounded transformation rules that can be recombined and evaluated on different sites and programs.

**KR**

> 설계 어휘는 건축 문법에서 도출된다. 여섯 개의 상대적 기본 스코프, 30개 조작, 20개 조합, 9개 집합 방식, 복합 사례 언어로 구성된다. 이는 고정된 건물 템플릿이 아니라 서로 다른 대지와 프로그램에서 재조합하고 평가할 수 있는 제한된 변환 규칙이다.

### Candidate-population explanation

**EN**

> Candidate selection combines geometry hard gates with a constrained quality-diversity archive. The system retains alternatives across curves, courts, split wings, steps, bridges, clusters, and oblique cuts while rejecting fragments, collisions, invalid solids, and near duplicates. A visual critic can propose bounded graph edits, but the compiler and hard gates decide whether the revised geometry survives.

**KR**

> 후보 선택은 형상 hard gate와 제약 기반 품질다양성 아카이브를 결합한다. 곡선, 중정, 분리된 동, 계단형 매스, 브리지, 클러스터, 사선 절삭 대안을 보존하면서 파편, 충돌, 잘못된 솔리드, 근접 중복을 제거한다. 시각 비평 에이전트는 제한된 그래프 수정을 제안할 수 있지만, 수정된 형상의 생존 여부는 컴파일러와 hard gate가 결정한다.

### Current benchmark caption

**EN**

> In the latest bounded three-program benchmark, 60 of 60 selected recursive portfolios passed the combined legal, FAR, parking, and geometry-retention gates. This demonstrates procedural coverage and constraint retention—not competition-level architectural resolution.

**KR**

> 최신 제한형 3개 프로그램 벤치마크에서는 선택된 재귀형 포트폴리오 60개 모두가 법규, 용적, 주차, 형상 유지 통합 검증을 통과했다. 이는 절차적 설계언어의 범위와 제약 유지 능력을 보여주지만, 공모전 수준의 건축적 완성도를 의미하지는 않는다.

---

## PAGE 5 — Massing to Design Development

### Main title

**EN**  
`MASSING TO DESIGN DEVELOPMENT`

**KR**  
`매스에서 설계 발전으로`

### Subtitle

**EN**  
`A shared geometric base for plan, facade, and projection studies.`

**KR**  
`평면·입면·프로젝션 연구를 위한 공통 형상 기반.`

### Left introduction

**EN**

> A selected mass is not treated as a finished building. Its source volumes, surfaces, roles, and directional relationships become a shared geometric base for the next design studies. Floor-plan packing explores spatial organization inside the available envelope, while facade modules extract exterior planes and generate direction-aware visual assets. Each layer remains editable and traceable to the mass that produced it.

**KR**

> 선택된 매스는 완성된 건물로 취급되지 않는다. 매스의 소스 볼륨, 표면, 역할, 방향 관계는 다음 설계 연구를 위한 공통 형상 기반이 된다. 평면 패킹은 사용 가능한 외피 안에서 공간 구성을 탐색하고, 파사드 모듈은 외부 면을 추출해 방향별 시각 자산을 생성한다. 각 단계는 수정 가능하며 자신이 출발한 매스까지 추적할 수 있다.

### Upper-right facade explanation

**EN**

> The facade path identifies exterior planes, road-facing edges, floor ranges, and view directions. Generated front, right, back, left, axonometric, and top panels are stored with a projection manifest and can be mapped back to Cesium wall entities or exported with the textured mesh. The images support architectural review; they are not permit-ready construction elevations.

**KR**

> 파사드 경로는 외부 면, 도로를 향한 변, 층 범위, 시점 방향을 식별한다. 생성된 정면·우측면·배면·좌측면·축측면·상부 패널은 프로젝션 매니페스트와 함께 저장되며, Cesium 벽체 엔티티에 다시 적용하거나 텍스처 메시와 함께 내보낼 수 있다. 이 이미지는 건축적 검토를 위한 것이며 인허가용 실시 입면도는 아니다.

### Plan-alternative explanation

**EN**

> Plan alternatives compare different packing and adjacency strategies within the selected envelope. Their purpose is to expose spatial trade-offs and provide a structured starting point for further design—not to claim that an early mass has already become a complete BIM model.

**KR**

> 평면 대안은 선택된 외피 안에서 서로 다른 패킹과 인접 관계 전략을 비교한다. 목적은 공간적 상충관계를 드러내고 후속 설계를 위한 구조화된 출발점을 제공하는 것이다. 초기 매스가 이미 완성된 BIM 모델이 되었다고 주장하는 단계는 아니다.

### Lower-right development caption

**EN**

> Geometry, program, and facade studies remain parallel design layers until they are reconciled through circulation, structure, public space, and detailed code review.

**KR**

> 형상, 프로그램, 파사드 연구는 동선, 구조, 공공공간, 상세 법규 검토를 통해 통합되기 전까지 서로 병렬적인 설계 단계로 유지된다.

---

## PAGE 6 — Shared Memory & Live Interface

### Main title

**EN**  
`SHARED MEMORY, LIVE INTERFACE`

**KR**  
`공유 메모리와 실제 인터페이스`

### Subtitle

**EN**  
`Evidence persists across agents, tools, and design-review stages.`

**KR**  
`근거는 에이전트와 도구, 설계 검토 단계 사이에서 지속된다.`

### Upper-right block 1 — collaboration infrastructure

**EN**

> AG-light provides the collaboration layer around the design system. Its message bus records direct and broadcast communication, while Shared Memory stores decisions, events, and reusable evidence. MCP tools expose legal search, parcel analysis, and design services through a common interface, allowing specialist agents to exchange structured results instead of copying unverified prose between prompts.

**KR**

> AG-light는 설계 시스템을 둘러싼 협업 계층을 제공한다. Message Bus는 에이전트 간 직접 통신과 브로드캐스트를 기록하고, Shared Memory는 결정사항, 이벤트, 재사용 가능한 근거를 저장한다. MCP 도구는 법규 검색, 필지 분석, 설계 서비스를 공통 인터페이스로 제공하여 전문 에이전트가 검증되지 않은 자연어를 복사하는 대신 구조화된 결과를 교환하도록 한다.

### Upper-right block 2 — durable design memory

**EN**

> The research loop also keeps durable candidate archives, geometry-keyed visual scores, typed graph edits, and parent-child lineage. Previous accepted graphs can be supplied to a later run and revalidated against a new context. This is explicit, auditable reuse—not autonomous model training or unrestricted lifelong learning.

**KR**

> 연구 루프는 지속 가능한 후보 아카이브, 형상 기반 시각 점수, 유형화된 그래프 수정, 부모-자식 계보도 함께 보존한다. 이전에 채택된 그래프는 다음 실행에 다시 제공되어 새로운 맥락에서 재검증될 수 있다. 이는 명시적이고 감사 가능한 재사용이며, 자율적인 모델 학습이나 제한 없는 평생학습을 의미하지 않는다.

### Lower-left short copy

**EN**

> Every candidate remains connected to its parcel, legal evidence, authored graph, compiled geometry, gate results, and review history.

**KR**

> 모든 후보는 자신의 필지, 법규 근거, 작성된 그래프, 컴파일 형상, 검증 결과, 검토 이력과 연결된 상태로 유지된다.

### Interface caption

**EN**

> The live interface brings the pipeline back to the user: address and PNU input, regulatory evidence, map context, mass alternatives, and review results are presented in one workspace.

**KR**

> 실제 인터페이스는 전체 파이프라인을 다시 사용자에게 연결한다. 주소와 PNU 입력, 법규 근거, 지도 맥락, 매스 대안, 검토 결과를 하나의 작업공간에서 제시한다.

---

## Final short project statement

### English

> 25_ACE is an evidence-backed architectural design system that connects parcel intelligence, legal knowledge, executable geometry, multi-agent review, and human selection. Its goal is not to replace architectural judgment, but to make the path from constraint to alternative visible, testable, and editable.

### 한국어

> 25_ACE는 필지 인텔리전스, 법규 지식, 실행 가능한 형상, 멀티에이전트 검토, 사람의 선택을 연결하는 근거 기반 건축 설계 시스템이다. 목표는 건축적 판단을 대체하는 것이 아니라 제약조건에서 설계 대안에 이르는 과정을 가시적이고 검증 가능하며 수정 가능한 형태로 만드는 것이다.

## Claims that must remain qualified

- `60/60 hard pass` is the latest bounded procedural benchmark, not permit approval or architectural completion.
- `architecture_grade_claim_allowed=false` remains the honest project status.
- The generic GIS stack contains extension layers that are not mandatory inputs to every run.
- The three-agent icon is a simplified collaboration symbol; the canonical MAAS flow contains seven specialist stages plus the orchestrator.
- Plan, facade, and mass modules exist, but the current images do not prove one uninterrupted automatic BIM/IFC pipeline.
- Shared Memory is implemented infrastructure; not every internal v90/recursive-program operation is routed through it.
