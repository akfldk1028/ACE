# SUPERSEDED — 25_ACE Portfolio Full Project Logic Copy (EN/KR)

> 이 초안에는 현재 16–21페이지보다 확장된 내부 에이전트 명칭과 이전 해석이 섞여 있다. 최종 편집에는 `PORTFOLIO_260707_16_21_EXACT_PAGE_COPY_KR_EN.md`를 사용한다.

Updated: 2026-07-16  
Final diagram set: `260707_16.jpg`–`260707_21.jpg`

## How to use this document

- **EN**: 포트폴리오에 직접 넣는 영문 원고.
- **KR**: 영문의 의미를 확인하기 위한 한국어 번역.
- 각 페이지를 독립된 기능 소개로 쓰지 않고, 앞 페이지의 결과가 다음 페이지의 입력이 되는 하나의 프로젝트 로직으로 연결한다.

## Whole-project logic

```text
USER ADDRESS
  → PNU / VWORLD PARCEL & GIS CONTEXT
  → NEO4J LEGAL KNOWLEDGE GRAPH
  → HOST AGENT / A2A ROUTING / MCP TOOLS
  → LAW · MASS · PLAN · ELEVATION · MASTER PLAN · VLM CAPABILITIES
  → EXECUTABLE COMPONENT GRAPH / GEOMETRY PROGRAM
  → GEOMETRY COMPILER
  → LEGAL · FAR · PARKING · GEOMETRY HARD GATES
  → QUALITY-DIVERSITY ARCHIVE / VLM CRITIC & TYPED REVISION
  → MASSING ALTERNATIVES
  → PLAN · ELEVATION · FACADE DEVELOPMENT
  → SHARED MEMORY / LINEAGE / USER INTERFACE
  → HUMAN REVIEW AND NEXT REVISION
```

### Core project statement

**EN**

> 25_ACE is an evidence-backed architectural design system that connects parcel intelligence, legal knowledge, multi-agent collaboration, executable geometry, deterministic validation, and human review. The system does not ask a language model to declare compliance or draw an untraceable final image. It preserves the path from address and law to geometry, alternatives, evaluation, and revision.

**KR**

> 25_ACE는 필지 인텔리전스, 법규 지식, 멀티에이전트 협업, 실행 가능한 형상, 결정론적 검증, 사람의 검토를 연결하는 근거 기반 건축 설계 시스템이다. 언어모델이 법규 적합을 임의로 선언하거나 출처를 추적할 수 없는 최종 이미지를 그리게 하지 않는다. 주소와 법규에서 형상, 대안, 평가, 수정으로 이어지는 전체 경로를 보존한다.

## Diagram labeling system

각 다이어그램에는 아래 세 단계가 모두 필요하다.

1. **Diagram subtitle**: 그림 전체가 어떤 시스템 단계를 보여주는지 설명.
2. **Element label**: 에이전트, 데이터베이스, 도구, 결과물의 정확한 이름.
3. **One-line caption**: 이 다이어그램이 전체 프로젝트에서 수행하는 역할.

### Visual hierarchy

```text
DIAGRAM SUBTITLE       12–16 pt / uppercase / semibold
Element Label           8–10 pt / role name
One-line Caption        8–10 pt / one or two lines
```

긴 본문을 다이어그램 바로 옆에 반복하지 않는다. 소제목은 명사형, 캡션은 작동 방식과 결과를 설명하는 한 문장으로 쓴다.

### Canonical portfolio agent names

아래 명칭을 18–21페이지에서 동일하게 사용한다.

| English display name | 한국어 | Role in the portfolio |
|---|---|---|
| `Design Orchestrator` | 설계 오케스트레이터 | 사용자 요청을 해석하고 전문 에이전트 작업을 조정한다. |
| `Law Graph Agent` | 법규 그래프 에이전트 | Neo4j에서 관련 법규 근거와 출처를 검색한다. |
| `Parking Agent` | 주차 검토 에이전트 | 필요 주차대수와 mass-stage 배치 가능성을 hard gate로 검토한다. |
| `Site / Masterplan Agent` | 대지·마스터플랜 에이전트 | 필지, 접근, 배치, 외부공간 맥락을 구조화한다. |
| `Massing Agent` | 매스 에이전트 | 건축언어를 실행 가능한 component graph와 geometry program으로 변환한다. |
| `VLM Critic Agent` | VLM 비평 에이전트 | 렌더링을 검토하고 제한된 typed graph edit을 제안한다. |
| `Plan Agent` | 평면 에이전트 | 매스 외피 안에서 프로그램, 패킹, 인접, 동선을 탐색한다. |
| `Elevation & Facade Agent` | 입면·파사드 에이전트 | 외부 면과 방향을 추출하고 입면·파사드 자산을 발전시킨다. |
| `Review Agent` | 최종 검토 에이전트 | 법규·주차·형상·시각 근거를 모아 최종 검토 상태를 기록한다. |

### Infrastructure names — do not label these as agents

| Correct label | 한국어 | Type |
|---|---|---|
| `Neo4j Legal Knowledge Graph` | Neo4j 법규 지식그래프 | Database |
| `MCP Tool Layer` | MCP 도구 계층 | Tool interface |
| `Geometry Compiler` | 형상 컴파일러 | Deterministic engine |
| `Legal / Parking Hard Gates` | 법규·주차 hard gate | Deterministic validators |
| `Quality-Diversity Archive` | 품질다양성 아카이브 | Candidate archive / selector |
| `Shared Memory Bus` | 공유 메모리 버스 | Collaboration infrastructure |
| `Live Design Interface` | 실제 설계 인터페이스 | User-facing application |

### Internal MAAS mapping note

포트폴리오의 `Massing Agent`는 이해를 돕기 위한 상위 기능명이다. 실제 내부 구현은 다음 역할로 더 세분화된다.

```text
LLM Architect Agent
  → MassDSL Agent
  → MAAS Geometry Agent
  → Grammar Critic Agent
  → Review Agent
```

따라서 포트폴리오에서 이 다섯 역할을 각각 아이콘으로 모두 추가할 필요는 없다. 대신 `Massing Agent` 아래에 작은 보조 라벨로 `Architectural Language · MassDSL · Geometry Compiler`를 붙이면 실제 구조를 지나치게 복잡하게 만들지 않으면서 정확성을 유지할 수 있다.

## Diagram subtitles and element labels by page

### 260707_16.jpg

#### Hero image

**Diagram subtitle — EN**  
`PROJECT VISION`

**Diagram subtitle — KR**  
`프로젝트 비전`

**One-line caption — EN**  
`From a measurable legal envelope to an architecturally legible alternative.`

**One-line caption — KR**  
`측정 가능한 법적 외피를 건축적으로 읽히는 대안으로 발전시킨다.`

### 260707_17.jpg

#### Legal node diagram

**Subtitle — EN**: `LEGAL NODE SCHEMA`  
**Subtitle — KR**: `법규 노드 스키마`

Element label:

```text
Legal Node
identity · content · provenance · embedding
```

#### CONTAINS / NEXT / CITES diagrams

**Subtitle — EN**: `LEGAL RELATIONSHIP LOGIC`  
**Subtitle — KR**: `법규 관계 로직`

Element labels:

```text
CONTAINS  / hierarchy & relationship context
NEXT      / same-level sequence
CITES     / cross-law reference
```

#### Seven-level hierarchy diagram

**Subtitle — EN**: `STATUTE HIERARCHY`  
**Subtitle — KR**: `법령 계층구조`

Correct node labels:

```text
LAW
JANG / Chapter
JEOL / Section
JO / Article
HANG / Paragraph
HO / Item
MOK / Sub-item
```

#### Large graph visualization

**Subtitle — EN**: `LEGAL KNOWLEDGE FIELD`  
**Subtitle — KR**: `법규 지식 필드`

Cluster labels:

```text
National Land Planning
Building / Housing Law
Height / Daylight Limits
Cross-Law Citation Paths
```

**Caption — EN**  
`The graph exposes connected legal neighborhoods and cited evidence instead of returning isolated clauses.`

**Caption — KR**  
`고립된 조항 대신 서로 연결된 법규 영역과 인용 근거를 보여준다.`

### 260707_18.jpg

#### GIS layer diagram

**Subtitle — EN**: `PARCEL & GIS CONTEXT`  
**Subtitle — KR**: `필지 및 GIS 맥락`

Active-data labels to emphasize:

```text
VWorld Parcel Boundary
Zoning & Land Information
Road / Frontage Geometry
Elevation / Legal Datum
Map / Orthoimagery Context
```

Extension-data labels may remain lighter:

```text
Land Cover
Hydrography
Geo Names
Structures
```

**Caption — EN**  
`A PNU becomes a measured parcel frame with site, access, legal, and visual context.`

**Caption — KR**  
`PNU를 대지, 접근, 법규, 시각 맥락을 가진 측정 가능한 필지 좌표계로 변환한다.`

#### Legal-envelope axonometric

**Subtitle — EN**: `REGULATORY DESIGN FIELD`  
**Subtitle — KR**: `법규 기반 설계장`

Element labels:

```text
BCR Limit
FAR Limit
Height / Daylight Envelope
Setback
Road Access
Parking Requirement
```

#### Agent team diagram

**Subtitle — EN**: `MULTI-AGENT DESIGN TEAM`  
**Subtitle — KR**: `멀티에이전트 설계 팀`

Replace current labels with:

```text
User
Design Orchestrator
Plan Agent
Elevation & Facade Agent
Massing Agent
VLM Critic Agent
Site / Masterplan Agent
Law Graph Agent
Parking Agent                  ← add as a hard-gate role
Neo4j Legal Knowledge Graph    ← database, not an agent
```

If there is no room for a separate parking icon, combine only the display label as:

`Law & Parking Review`

Do not merge the backend ownership in the explanatory text; the actual implementation still has separate `law_graph_agent` and `parking_agent` roles.

Active-color rule for page 18:

- Pink: `Design Orchestrator`, `Site / Masterplan Agent`, `Law Graph Agent`, `Parking Agent`.
- Gray: later-stage agents waiting for verified context.

#### A2A/MCP sequence diagram

**Subtitle — EN**: `A2A COORDINATION / MCP EXECUTION`  
**Subtitle — KR**: `A2A 작업 조정 / MCP 도구 실행`

Replace generic labels:

```text
Agent 1  → Requesting Agent
Agent 2  → Specialist Agent
Tools    → MCP Tool Layer
```

Arrow labels:

```text
Discover Capability
Send Structured Task
Invoke Tool
Return Evidence
Return Agent Result
```

### 260707_19.jpg

#### Operation icons

**Subtitle — EN**: `EXECUTABLE FORMAL OPERATIONS`  
**Subtitle — KR**: `실행 가능한 형태 조작`

Optional category labels below the icon rows:

```text
ADD / DISPLACE / SUBTRACT / COMBINE / AGGREGATE
```

Representative operation labels:

```text
Carve · Offset · Split · Bridge · Fold · Taper
Sweep · Loft · Array · Stack · Rotate · Twist
```

**Caption — EN**  
`Typed operations form a recursive geometry language rather than a fixed catalogue of buildings.`

**Caption — KR**  
`유형화된 조작을 고정 건물 목록이 아닌 재귀적 형상 언어로 사용한다.`

#### Agent loop

**Subtitle — EN**: `MASSING AUTHOR–CRITIC LOOP`  
**Subtitle — KR**: `매스 작성–비평 루프`

Active labels for page 19:

```text
Design Orchestrator
Massing Agent
  Architectural Language · MassDSL · Geometry Compiler
VLM Critic Agent
Law Graph Agent
Parking Agent
Legal / Parking Hard Gates
```

Active-color rule for page 19:

- Pink: `Design Orchestrator`, `Massing Agent`, `VLM Critic Agent`.
- Navy or dark outline: hard-gate path.
- Gray: downstream Plan and Elevation agents.

#### Candidate board

**Subtitle — EN**: `QUALITY-DIVERSITY MASSING ARCHIVE`  
**Subtitle — KR**: `품질다양성 매스 아카이브`

Suggested group labels:

```text
Continuous
Courtyard / Carved
Stepped / Folded
Bridge / Split
Cluster
Oblique / Cut
```

**Caption — EN**  
`Clean, capacity-aware, non-duplicate alternatives survive deterministic gates and visual review.`

**Caption — KR**  
`형상·용적·중복 검증과 시각 검토를 통과한 대안만 보존한다.`

### 260707_20.jpg

#### Agent team diagram

**Subtitle — EN**: `DESIGN DEVELOPMENT TEAM`  
**Subtitle — KR**: `설계 발전 팀`

Active labels for page 20:

```text
Design Orchestrator
Plan Agent
Elevation & Facade Agent
Massing Agent / Source Geometry
Review Agent
```

Active-color rule for page 20:

- Pink: `Design Orchestrator`, `Plan Agent`, `Elevation & Facade Agent`.
- Gray: `Massing Agent`, because the selected source mass is now an input.

#### Upper facade strip

**Subtitle — EN**: `FACADE & ELEVATION VARIATIONS`  
**Subtitle — KR**: `파사드 및 입면 대안`

**Caption — EN**  
`Directional facade studies are derived from the selected source geometry and its exterior planes.`

**Caption — KR**  
`선택된 소스 형상과 외부 면을 기준으로 방향별 파사드 대안을 발전시킨다.`

#### Upper mass axonometric

**Subtitle — EN**: `SELECTED SOURCE MASS`  
**Subtitle — KR**: `선택된 소스 매스`

Suggested element labels:

```text
Primary Volume
Carved Void / Connection
Site Boundary
Road-Facing Edge
```

#### Plan grid

**Subtitle — EN**: `PROGRAM & PLAN ALTERNATIVES`  
**Subtitle — KR**: `프로그램 및 평면 대안`

Optional evaluation labels:

```text
Area Fit
Adjacency
Circulation
Access
Program Distribution
```

**Caption — EN**  
`Alternative spatial organizations are compared inside the same selected envelope.`

**Caption — KR**  
`동일한 선택 외피 안에서 서로 다른 공간 구성 대안을 비교한다.`

#### Lower dark mass diagram

**Subtitle — EN**: `COORDINATED DESIGN BASE`  
**Subtitle — KR**: `통합 설계 기준 형상`

**Caption — EN**  
`One traceable geometry becomes the shared reference for plan, facade, and further architectural coordination.`

**Caption — KR**  
`하나의 추적 가능한 형상이 평면·파사드·후속 건축 조정의 공통 기준이 된다.`

### 260707_21.jpg

#### Agent-memory diagram

**Subtitle — EN**: `EVIDENCE WRITE / READ FLOW`  
**Subtitle — KR**: `근거 기록 및 조회 흐름`

Replace generic nodes with:

```text
User
Law Graph Agent
Design Agent
Review Agent
MCP Tool Layer
Shared Memory Bus
Decision Store
Event / Evidence Store
```

Replace `Agent A / Neo4j Search` with:

`Law Graph Agent / Neo4j Retrieval`

Arrow labels:

```text
Write Evidence
Read Context
Invoke Tool
Publish Event
Store Decision
Return Reviewed Result
```

**Caption — EN**  
`Agents exchange structured evidence through shared state instead of repeating unverified prompt text.`

**Caption — KR**  
`에이전트는 검증되지 않은 프롬프트 문장을 반복하는 대신 공유 상태를 통해 구조화된 근거를 교환한다.`

#### Memory bus

**Subtitle — EN**: `SHARED MEMORY BUS`  
**Subtitle — KR**: `공유 메모리 버스`

Suggested memory-cell labels:

```text
Parcel
Legal Evidence
Parking
Program
Component Graph
Geometry
Gate Results
VLM Review
User Decision
Lineage
```

#### Device screenshot

**Subtitle — EN**: `LIVE DESIGN INTERFACE`  
**Subtitle — KR**: `실제 설계 인터페이스`

Suggested interface callouts:

```text
Address / PNU Input
Regulatory Summary
VWorld Site Context
Generated Alternatives
Review Status
Next Design Action
```

**Caption — EN**  
`The complete evidence chain returns to the user as an inspectable design workspace.`

**Caption — KR**  
`전체 근거 사슬을 사용자가 확인할 수 있는 설계 작업공간으로 되돌려준다.`

## Agent-name consistency checklist

- Use `Design Orchestrator`, not both `Host Agent` and `Orchestrator Agent` on different pages.
- Use `Massing Agent`, not alternating `MASS Agent`, `Mass Agent`, and `Geometry Agent`.
- Use `VLM Critic Agent`, not only `VLM Agent`, because its role is critique and typed revision.
- Use `Elevation & Facade Agent`, since page 20 shows both elevation and facade output.
- Use `Law Graph Agent`, not generic `Law Agent`, because it retrieves graph-backed evidence.
- Add `Parking Agent` or the compact display label `Law & Parking Review`; parking is a real hard gate and should not disappear from the portfolio logic.
- Label `Neo4j Legal Knowledge Graph` as a database, never as an agent.
- Label `Geometry Compiler` and `Legal / Parking Hard Gates` as deterministic engines, never as LLM agents.
- Keep the active agent color consistent by page: context on 18, massing on 19, design development on 20, memory/review on 21.

---

# 260707_16.jpg — Project Overview

## Page function in the whole story

프로젝트가 해결하려는 전체 문제를 먼저 제시한다. 하단 건물 이미지는 특정 알고리즘의 최종 결과 증명이라기보다, 법적 가능 볼륨을 실제 건축적 대안으로 발전시키려는 프로젝트의 목표를 보여주는 대표 이미지다.

## Main title

**EN**  
`DESIGN AUTOMATION`

**KR**  
`설계 자동화`

## Subtitle

**EN**  
`From Address to Evidence-Backed Architecture`

**KR**  
`주소에서 근거 기반 건축까지`

## Project information

**EN**

```text
Personal Research & Development
Legal Knowledge Graph · Multi-Agent Design · Generative Geometry
July 2026
```

**KR**

```text
개인 연구 및 개발 프로젝트
법규 지식그래프 · 멀티에이전트 설계 · 생성형 형상
2026년 7월
```

## Upper-right main description

**EN**

> Architectural design begins long before a building takes shape. A single site requires parcel identification, spatial context, legal interpretation, parking review, program decisions, geometric exploration, and visual judgment. This project connects those fragmented tasks into one traceable workflow. A typed address becomes verified site and legal evidence; specialized agents transform that evidence into executable design graphs; deterministic engines compile and test the geometry; and the resulting alternatives return to the user for comparison and revision.

**KR**

> 건축 설계는 건물의 형태가 만들어지기 훨씬 전부터 시작된다. 하나의 대지를 다루기 위해서는 필지 식별, 공간정보 분석, 법규 해석, 주차 검토, 프로그램 결정, 형상 탐색, 시각적 판단이 함께 필요하다. 이 프로젝트는 분리된 작업들을 하나의 추적 가능한 흐름으로 연결한다. 사용자가 입력한 주소는 검증된 대지·법규 근거가 되고, 전문 에이전트는 이를 실행 가능한 설계 그래프로 변환하며, 결정론적 엔진은 형상을 컴파일하고 검증한다. 생성된 대안은 다시 사용자에게 돌아가 비교와 수정의 대상이 된다.

## Hero-image caption

**EN**  
`The project goal is not a legal envelope alone, but a legible architectural alternative whose evidence and transformations can be traced.`

**KR**  
`프로젝트의 목표는 단순한 법적 외피가 아니라, 근거와 변환 과정을 추적할 수 있는 건축적 대안을 만드는 것이다.`

---

# 260707_17.jpg — The Law Is a Graph

## Page function in the whole story

전체 시스템의 첫 번째 지식 기반이다. 주소가 PNU와 대지 맥락으로 변환된 뒤, 설계에 필요한 규정을 문장 검색만으로 찾는 것이 아니라 계층과 관계를 가진 법규 그래프에서 검색한다. 이 페이지의 결과는 다음 페이지의 Law Agent와 다른 설계 에이전트가 함께 사용하는 구조화된 근거가 된다.

## Main title

**EN**  
`THE LAW IS A GRAPH`

**KR**  
`법은 그래프다`

## Left introduction — replace the four temporary paragraphs

**EN**

> A typed address resolves to a PNU and a measurable parcel.

> The parcel activates a legal search across a Neo4j knowledge graph.

> Relevant clauses return with hierarchy, sequence, citations, and source metadata.

> The graph supplies evidence and constraints to the design agents; geometry is created only by the downstream compiler.

**KR**

> 사용자가 입력한 주소는 PNU와 측정 가능한 필지로 변환된다.

> 필지 정보는 Neo4j 법규 지식그래프 검색을 활성화한다.

> 관련 조항은 계층, 순서, 인용관계, 출처 메타데이터와 함께 반환된다.

> 그래프는 설계 에이전트에 근거와 제약조건을 제공하며, 실제 형상은 이후 단계의 컴파일러가 생성한다.

## Node description

**EN**

> Each legal node retains its identifier, title, content, revision history, source metadata, and semantic embedding. Search results therefore remain inspectable and citable instead of becoming uncited model prose.

**KR**

> 각 법규 노드는 식별자, 제목, 본문, 개정 이력, 출처 메타데이터, 의미 임베딩을 보존한다. 따라서 검색 결과는 출처 없는 모델 문장이 아니라 직접 확인하고 인용할 수 있는 근거가 된다.

## Relation labels

### NODE

**EN**  
`A legal unit with identity, content, provenance, and embedding.`

**KR**  
`식별자, 본문, 출처, 임베딩을 가진 법규 단위.`

### CONTAINS

**EN**  
`Parent-child hierarchy with relationship-context embedding.`

**KR**  
`관계 맥락 임베딩을 포함하는 부모-자식 계층.`

### NEXT

**EN**  
`Same-level sequence for adjacent legal traversal.`

**KR**  
`같은 단계의 전후 법규를 탐색하기 위한 순서 관계.`

### CITES

**EN**  
`Cross-law reference paths used to expand legal evidence.`

**KR**  
`법규 근거를 확장하는 타법 인용 경로.`

## Bottom block 01

**EN**

**01 / 7-LEVEL STATUTE TREE**  
`LAW → JANG → JEOL → JO → HANG → HO → MOK` models the maximum hierarchy of Korean statutes.

**KR**

**01 / 7단계 법령 트리**  
`법 → 장 → 절 → 조 → 항 → 호 → 목`으로 한국 법령의 최대 계층구조를 모델링한다.

## Bottom block 02

**EN**

**02 / CONTAINS · NEXT · CITES**  
Hierarchy, adjacency, and cross-law references remain explicit graph relations.

**KR**

**02 / 포함 · 순서 · 인용**  
계층, 인접 관계, 타법 인용을 명시적인 그래프 관계로 보존한다.

## Bottom block 03

**EN**

**03 / HYBRID RETRIEVAL**  
Exact, CJK full-text, vector, relationship-context, RRF/RNE, and MMR stages combine relevance with legal diversity.

**KR**

**03 / 하이브리드 검색**  
정확검색, 한글 전문검색, 벡터, 관계 맥락, RRF/RNE, MMR을 결합해 관련성과 법령 다양성을 확보한다.

## Bottom block 04

**EN**

**04 / CLUSTER FIELD**  
The expanded portfolio snapshot contains 31,126 nodes and 31,063 relationships, revealing connected legal fields rather than isolated text.

**KR**

**04 / 클러스터 필드**  
확장 포트폴리오 스냅숏은 31,126개 노드와 31,063개 관계를 포함하며, 고립된 문장이 아닌 연결된 법규 영역을 보여준다.

## Small lower-left closing line

**EN**  
`The graph determines what evidence enters the design process—not the final shape of the building.`

**KR**  
`그래프는 설계에 어떤 근거가 들어가는지를 결정하지만, 건물의 최종 형태를 직접 만들지는 않는다.`

---

# 260707_18.jpg — A2A Protocol + GIS

## Page function in the whole story

법규 그래프와 대지정보를 실제 설계 작업에 연결하는 통신·도구 계층이다. Host Agent가 사용자의 요청을 해석하고, A2A로 적절한 전문 에이전트에 작업을 전달하며, 각 에이전트는 MCP를 통해 GIS, 법규, 형상, 분석 도구를 호출한다.

## Main title

**EN**

```text
A2A PROTOCOL
GIS + TOOLS
```

**KR**

```text
A2A 프로토콜
GIS와 설계 도구
```

## Left introduction — replace the four temporary paragraphs

**EN**

> The Host Agent interprets the user request and assembles the required design team.

> A2A carries tasks, evidence, and results between specialized agents.

> MCP gives each agent controlled access to GIS, legal search, geometry, and evaluation tools.

> The shared context keeps parcel facts, legal sources, program intent, and design decisions aligned.

**KR**

> Host Agent는 사용자의 요청을 해석하고 필요한 설계 팀을 구성한다.

> A2A는 전문 에이전트 사이에서 작업, 근거, 결과를 전달한다.

> MCP는 각 에이전트가 GIS, 법규 검색, 형상 생성, 평가 도구를 통제된 방식으로 호출하게 한다.

> 공유 맥락은 필지 정보, 법규 출처, 프로그램 의도, 설계 결정을 서로 일치시킨다.

## GIS diagram paragraph — upper-right text block

**EN**

> The parcel is reconstructed as a design context rather than a coordinate alone. Active inputs include the VWorld boundary, parcel area and axis, zoning and land information, neighboring roads, verified frontage, map imagery, and elevation or datum evidence where available. Additional GIS layers remain extensible context and are activated only when the task requires them.

**KR**

> 필지는 단순한 좌표가 아니라 설계 맥락으로 재구성된다. 현재 활성 입력에는 브이월드 필지 경계, 대지면적과 주축, 용도지역과 토지정보, 인접도로, 확인된 도로 접면, 지도 영상, 이용 가능한 경우의 표고·기준면 근거가 포함된다. 다른 GIS 레이어는 확장 가능한 맥락으로 남으며 작업에 필요할 때만 활성화된다.

## Agent-team caption — lower-left text block

**EN**

> The portfolio diagram groups capabilities as Law, Mass, Plan, Elevation, Master Plan, and VLM agents. Internally, the MAAS path further separates legal review, parking, architectural language, MassDSL, geometry compilation, grammar criticism, and final review.

**KR**

> 포트폴리오 다이어그램은 기능을 Law, Mass, Plan, Elevation, Master Plan, VLM 에이전트로 묶어 보여준다. 실제 MAAS 내부에서는 법규 검토, 주차, 건축언어, MassDSL, 형상 컴파일, 문법 비평, 최종 검토 역할이 더 세분화된다.

## A2A/MCP sequence caption — lower-right text block

**EN**

> A2A coordinates who performs the task; MCP controls which tools are invoked. The protocol layer carries structured evidence and artifacts, while the compiler and deterministic solvers retain authority over geometry and compliance.

**KR**

> A2A는 누가 작업을 수행할지 조정하고, MCP는 어떤 도구를 호출할지 통제한다. 프로토콜 계층은 구조화된 근거와 산출물을 전달하며, 형상과 적합성에 대한 최종 권한은 컴파일러와 결정론적 솔버가 유지한다.

## Legal-envelope caption

**EN**  
`The shared parcel context becomes an explicit design field of access, BCR, FAR, height, setback, sunlight, and parking constraints.`

**KR**  
`공유된 필지 맥락은 접근, 건폐율, 용적률, 높이, 이격, 일조, 주차 제약을 가진 명시적인 설계장으로 변환된다.`

---

# 260707_19.jpg — Massing Generation & Visual Critique

## Page function in the whole story

앞 페이지에서 구성된 대지·법규·프로그램 맥락이 실제 형상 대안으로 변환되는 핵심 생성 단계다. Mass Agent는 실행 가능한 component graph와 geometry program을 작성하고, 컴파일러가 이를 솔리드로 변환한다. VLM Agent는 이미지를 보고 비평하거나 제한된 typed edit을 제안하며, 수정 결과는 다시 컴파일·검증되어야 한다.

## Main title — place in the empty upper-left area

**EN**

```text
MASSING
GENERATION
```

**KR**

```text
매스 생성
```

## Main description — upper-left area

**EN**

> Site evidence and architectural intent are translated into an executable design graph. Base volumes are transformed through typed operations—carve, offset, split, bridge, fold, taper, sweep, loft, array, and stack—then compiled as measurable solids. The graph defines what should happen; only the geometry compiler can create the resulting form.

**KR**

> 대지 근거와 건축적 의도는 실행 가능한 설계 그래프로 번역된다. 기본 볼륨에 carve, offset, split, bridge, fold, taper, sweep, loft, array, stack과 같은 유형화된 조작을 적용하고, 이를 측정 가능한 솔리드로 컴파일한다. 그래프는 어떤 변환이 일어나야 하는지를 정의하며, 실제 형상을 만드는 권한은 형상 컴파일러에 있다.

## Operation-icon paragraph — upper-right text block

**EN**

> The design vocabulary is not a catalogue of finished buildings. It is a recursive architectural grammar built from relative base scopes, operations, combinations, and aggregation rules. The same language can therefore be tested across different parcels and programs without copying fixed coordinates or precedent forms.

**KR**

> 설계 어휘는 완성된 건물 형태의 카탈로그가 아니다. 상대적인 기본 스코프, 조작, 조합, 집합 규칙으로 구성된 재귀적 건축 문법이다. 따라서 고정 좌표나 선례 건물의 형태를 복사하지 않고도 같은 언어를 서로 다른 대지와 프로그램에서 검증할 수 있다.

## Agent-loop caption — lower-left text block

**EN**

> The Mass Agent authors executable geometry; the VLM Agent inspects rendered evidence and may request bounded graph edits. Law and program evidence remain connected throughout the loop.

**KR**

> Mass Agent는 실행 가능한 형상을 작성하고, VLM Agent는 렌더링된 근거를 검토해 제한된 그래프 수정을 요청할 수 있다. 법규와 프로그램 근거는 전체 루프에서 계속 연결된 상태로 유지된다.

## Candidate-board paragraph — lower-right text block

**EN**

> Candidates enter a constrained quality-diversity archive only after geometry, capacity, and coherence checks. Visual review then preserves meaningful differences across curves, courts, split wings, steps, bridges, clusters, and oblique cuts while rejecting collisions, fragments, invalid solids, and near duplicates. A revised graph survives only when both its graph hash and compiled geometry actually change and all hard gates pass again.

**KR**

> 후보는 형상, 용적, 일관성 검증을 통과한 뒤에만 제약 기반 품질다양성 아카이브에 들어간다. 시각 검토는 곡선, 중정, 분리된 동, 계단형 매스, 브리지, 클러스터, 사선 절삭의 의미 있는 차이를 보존하면서 충돌, 파편, 잘못된 솔리드, 근접 중복을 제거한다. 수정된 그래프는 그래프 해시와 컴파일 형상이 실제로 달라지고 모든 hard gate를 다시 통과해야 살아남는다.

## Optional current-result line

**EN**  
`The latest bounded three-program integration selected 60 procedural alternatives and passed the combined legal, FAR, parking, and geometry-retention gates for all 60; architectural completion remains a separate review.`

**KR**  
`최신 제한형 3개 프로그램 통합은 60개의 절차적 대안을 선택했고, 60개 모두 법규·용적·주차·형상 유지 통합 검증을 통과했다. 건축적 완성도는 별도의 검토 과제로 남아 있다.`

---

# 260707_20.jpg — From Massing to Architectural Development

## Page function in the whole story

19페이지에서 생성·검토된 매스가 평면, 입면, 파사드 연구로 이어지는 단계다. 현재 페이지 제목 `GRAPH TO MASSING`은 앞 페이지 역할과 중복되므로, 이 페이지의 실제 다이어그램 내용에 맞춰 아래 제목으로 변경하는 것이 논리적으로 정확하다.

## Main title — replace `GRAPH TO MASSING`

**EN**

```text
MASSING TO
ARCHITECTURE
```

**KR**

```text
매스에서
건축으로
```

Alternative English title: `DESIGN DEVELOPMENT`

## Left introduction — replace the four temporary paragraphs

**EN**

> A selected mass is treated as a shared geometric base, not a finished building.

> Plan agents explore packing, adjacency, circulation, and program distribution inside the envelope.

> Elevation agents extract facade planes, orientation, floor ranges, and road-facing edges.

> The resulting studies remain linked to the source mass and return to the review loop for coordination.

**KR**

> 선택된 매스는 완성된 건물이 아니라 공통 형상 기반으로 다뤄진다.

> Plan Agent는 외피 안에서 패킹, 인접 관계, 동선, 프로그램 배치를 탐색한다.

> Elevation Agent는 파사드 면, 방향, 층 범위, 도로를 향한 변을 추출한다.

> 생성된 연구 결과는 소스 매스와 연결된 상태로 다시 검토 루프에 돌아가 조정된다.

## Facade-strip paragraph — upper-right text block

**EN**

> Facade studies translate the geometric envelope into directional architectural views. Exterior planes are paired with front, right, back, left, axonometric, and top assets, then stored with projection metadata so that they can be reviewed in the interface or mapped back to the 3D mass. These are design-development images, not permit-ready construction elevations.

**KR**

> 파사드 연구는 형상 외피를 방향별 건축 이미지로 번역한다. 외부 면은 정면, 우측면, 배면, 좌측면, 축측면, 상부 자산과 연결되고, 프로젝션 메타데이터와 함께 저장되어 인터페이스에서 검토하거나 3D 매스에 다시 적용할 수 있다. 이는 설계 발전을 위한 이미지이며 인허가용 실시 입면도는 아니다.

## Plan-grid paragraph — lower-right text block

**EN**

> Plan alternatives compare different spatial organizations within the same geometric and legal envelope. They expose trade-offs between area, adjacency, circulation, and program rather than claiming that the selected mass has already become a complete BIM model. Plan, elevation, structure, public realm, and detailed code review must still be coordinated by the designer.

**KR**

> 평면 대안은 동일한 형상·법규 외피 안에서 서로 다른 공간 구성을 비교한다. 선택된 매스가 이미 완성된 BIM 모델이 되었다고 주장하는 대신, 면적, 인접 관계, 동선, 프로그램 사이의 상충관계를 드러낸다. 평면, 입면, 구조, 공공공간, 상세 법규는 이후에도 설계자가 통합적으로 조정해야 한다.

## Agent-diagram caption — lower-left text block

**EN**

> As the project advances, emphasis shifts from Mass and VLM agents to Plan and Elevation agents. The same evidence chain is retained, so downstream design decisions remain connected to the parcel, law, program, and selected geometry.

**KR**

> 프로젝트가 발전하면서 중심 역할은 Mass·VLM Agent에서 Plan·Elevation Agent로 이동한다. 동일한 근거 사슬을 유지하므로 후속 설계 결정도 필지, 법규, 프로그램, 선택된 형상과 계속 연결된다.

## Lower mass-diagram caption

**EN**  
`One selected geometry becomes the common reference for spatial and facade development.`

**KR**  
`하나의 선택된 형상이 공간과 파사드 설계 발전의 공통 기준이 된다.`

---

# 260707_21.jpg — Shared Memory & Live Interface

## Page function in the whole story

전체 프로젝트를 닫는 페이지다. 앞선 단계의 필지정보, 법규 근거, 에이전트 결정, 형상 그래프, 검증 결과, 사용자 피드백을 Shared Memory와 durable archive에 남기고, 실제 인터페이스에서 사용자가 결과를 확인하고 다음 수정을 요청하도록 한다. 따라서 이 페이지는 단순 저장소가 아니라 전체 루프를 다시 시작하게 하는 연결점이다.

## Main title

**EN**

```text
SHARED
MEMORY
```

**KR**

```text
공유 메모리
```

## Lower-left main description

**EN**

> Every stage writes structured evidence instead of leaving design reasoning inside a temporary conversation. Shared Memory stores decisions and events; the Message Bus records agent communication; and durable archives retain accepted graphs, geometry fingerprints, visual scores, hard-gate results, and parent-child lineage. The next task can therefore reuse verified evidence without treating cached results as autonomous model training.

**KR**

> 각 단계는 설계 판단을 일시적인 대화 안에 남겨두는 대신 구조화된 근거로 기록한다. Shared Memory는 결정과 이벤트를 저장하고, Message Bus는 에이전트 통신을 기록하며, 지속 가능한 아카이브는 채택된 그래프, 형상 지문, 시각 점수, hard-gate 결과, 부모-자식 계보를 보존한다. 따라서 다음 작업은 캐시를 자율학습으로 과장하지 않으면서 검증된 근거를 재사용할 수 있다.

## Upper-right block — continuity across agents

**EN**

> Shared state allows one agent to continue from another agent's verified result. A legal clause can become a structured constraint; the constraint can become a geometry parameter; the geometry can become a reviewed candidate; and every transformation keeps its source and status. This prevents the workflow from collapsing into unrelated prompts and images.

**KR**

> 공유 상태를 통해 한 에이전트는 다른 에이전트가 검증한 결과에서 작업을 이어갈 수 있다. 법조항은 구조화된 제약조건이 되고, 제약조건은 형상 파라미터가 되며, 형상은 검토된 후보가 된다. 모든 변환은 출처와 상태를 유지하므로 전체 과정이 서로 무관한 프롬프트와 이미지로 분절되지 않는다.

## Middle-right block — human feedback loop

**EN**

> The archive is not the final design authority. Previous candidates are retrieved explicitly, recompiled, and checked again against the current site and program. User selection and rejection are recorded as evidence for the next bounded search, while deterministic legal, parking, and geometry checks remain binding.

**KR**

> 아카이브가 최종 설계 권한을 갖는 것은 아니다. 이전 후보는 명시적으로 불러온 뒤 현재 대지와 프로그램에 맞춰 다시 컴파일하고 검증한다. 사용자의 선택과 거절은 다음 제한형 탐색의 근거로 기록되며, 결정론적 법규·주차·형상 검증은 계속 강제된다.

## Interface caption

**EN**

> The live interface returns the full chain to the user: address and PNU input, legal and parcel evidence, map context, generated alternatives, evaluation status, and the next design action are presented in one workspace.

**KR**

> 실제 인터페이스는 전체 사슬을 사용자에게 다시 보여준다. 주소와 PNU 입력, 법규·필지 근거, 지도 맥락, 생성된 대안, 평가 상태, 다음 설계 작업을 하나의 작업공간에서 제시한다.

## Final closing line

**EN**

> The project automates evidence, generation, and comparison so that architectural judgment can operate on a transparent field of alternatives.

**KR**

> 이 프로젝트는 근거 수집, 생성, 비교를 자동화하여 건축적 판단이 투명한 대안의 장 위에서 작동하도록 한다.

---

# Accuracy boundaries for the full portfolio

These points should remain outside the main visual copy or appear in a small project note.

## English

- The expanded legal-graph snapshot and smaller runtime graph instances are different snapshots; do not combine their counts.
- The GIS stack includes extensible layers that are not mandatory inputs to every run.
- Portfolio agent names are capability groups; the internal MAAS review chain is more specialized.
- A VLM may propose typed edits, but only the compiler and deterministic gates admit geometry.
- The latest 60/60 result is a bounded procedural integration benchmark, not permit approval or competition-level architecture.
- `architecture_grade_claim_allowed=false` remains the honest status.
- Plan, elevation, facade, and mass modules are connected design layers, not proof of automatic BIM/IFC completion.
- Shared Memory and durable archives support explicit reuse; they are not autonomous lifelong model training.

## 한국어

- 확장 법규 그래프 스냅숏과 더 작은 런타임 그래프는 서로 다른 시점의 데이터이므로 수치를 섞지 않는다.
- GIS 다이어그램에는 확장 가능한 레이어도 포함되어 있으며 모든 실행의 필수 입력은 아니다.
- 포트폴리오의 에이전트 이름은 기능 그룹이고, 실제 MAAS 내부 검토 체계는 더 세분화되어 있다.
- VLM은 유형화된 수정을 제안할 수 있지만 형상 채택 권한은 컴파일러와 결정론적 gate에 있다.
- 최신 60/60 결과는 제한된 절차적 통합 벤치마크이며 인허가 승인이나 공모전 수준의 건축을 의미하지 않는다.
- 정직한 현재 상태는 여전히 `architecture_grade_claim_allowed=false`다.
- 매스, 평면, 입면, 파사드 모듈은 연결된 설계 단계지만 자동 BIM/IFC 완성을 증명하지는 않는다.
- Shared Memory와 지속 가능한 아카이브는 명시적 재사용을 지원하며 자율적인 평생 모델학습이 아니다.
