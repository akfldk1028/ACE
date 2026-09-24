# 25_ACE 포트폴리오 16–21페이지 최종 설명문 (KR/EN)

작성 기준: `260707_16.jpg`–`260707_21.jpg` 여섯 장만 페이지별로 직접 확인한 결과  
업데이트: 2026-07-16

이 문서는 현재 레이아웃에 실제로 배치된 도식과 빈 텍스트 영역을 기준으로 한다. 기존 에이전트 도식의 이름은 유지하며, 분홍색은 해당 페이지에서 활성화된 역할을 뜻한다.

## 전체 페이지 흐름

```text
16  Project Vision
    프로젝트 목표와 결과 이미지

17  Legal Knowledge Graph
    주소와 필지를 법규 근거에 연결

18  GIS + Legal Envelope + A2A
    대지·법규 정보를 설계 제약조건으로 만들고 에이전트에 전달

19  MASS Agent + VLM Agent
    실행 가능한 조형 연산으로 매스 대안을 생성하고 비평·수정

20  Plan Agent + Elevation Agent
    선택된 매스를 평면·입면·파사드 대안으로 발전

21  Shared Memory + Interface
    과정과 결과를 공유 메모리에 남기고 사용자 검토로 연결
```

## 에이전트 도식 표기 원칙

- 현재 그림의 이름인 `Host Agent`, `Plan Agent`, `Elevation Agent`, `MASS Agent`, `VLM Agent`, `Master Plan Agent`, `Law Agent`, `GRAPH DB`를 그대로 사용한다.
- 모든 페이지에 새 에이전트를 추가하지 않는다.
- 분홍색 에이전트는 해당 단계에서 활성화된 역할, 회색은 다른 단계에서 사용되는 역할이다.
- `GRAPH DB`는 에이전트가 아니라 법규 근거 저장소다.
- 주차 검증은 실제 시스템의 중요한 hard gate지만, 현재 도식에 별도 아이콘을 추가하지 않고 본문에서 법규·용적률·주차 검증으로 설명한다.

---

# 260707_16.jpg — Project Overview

## 페이지에서 실제로 보이는 것

- 좌측 상단: `Design Automation`
- 좌측 중앙: 임시 부제와 프로젝트 정보
- 우측 상단: 현재 프로젝트와 무관한 임시 영문 단락
- 하단: 도심 대지에 삽입된 건축 결과 이미지

## 메인 타이틀

`DESIGN AUTOMATION`

## 부제 — 기존 `Urban Rhythms to Rural Pauses` 교체

**EN**  
`EVIDENCE-DRIVEN MULTI-AGENT ARCHITECTURE`

**KR**  
`근거 기반 멀티에이전트 건축 설계`

## 우측 상단 설명문

**EN**

> 25_ACE is an evidence-driven architectural design system that connects a real parcel, legal knowledge, multi-agent collaboration, and executable geometry. A typed address is resolved into parcel and regulatory context, translated into a legal design envelope, and developed through massing, plan, and elevation alternatives. Every proposal retains its source conditions, generation history, and validation results so that the designer can review not only the image, but also the reasoning behind it.

**KR**

> 25_ACE는 실제 필지, 법규 지식, 멀티에이전트 협업, 실행 가능한 형상 생성을 연결한 근거 기반 건축 설계 시스템이다. 입력된 주소는 필지와 법규 맥락으로 변환되고, 법적 설계 가능 범위를 거쳐 매스·평면·입면 대안으로 발전한다. 각 대안은 입력 조건, 생성 과정, 검증 결과를 함께 보존하므로 설계자는 결과 이미지뿐 아니라 그 결과가 만들어진 근거까지 검토할 수 있다.

## 이미지 소제목

**EN**: `PROJECT VISION`  
**KR**: `프로젝트 비전`

**Caption EN**  
`From a measurable legal envelope to an architecturally legible alternative.`

**Caption KR**  
`측정 가능한 법적 범위에서 건축적으로 읽히는 설계 대안까지.`

---

# 260707_17.jpg — The Law Is a Graph

## 페이지 역할

주소와 PNU를 기준으로 관련 법규를 찾고, 조문 구조와 인용 관계를 추적 가능한 그래프로 만드는 단계다. 이 페이지는 형상을 생성하는 페이지가 아니라 다음 설계 단계에 전달할 법적 근거를 구성하는 페이지다.

## 메인 타이틀

`THE LAW IS A GRAPH`

## 보조 제목

**EN**: `EVIDENCE-BACKED LEGAL RETRIEVAL`  
**KR**: `근거 기반 법규 검색`

## 좌측 설명문 — 현재 네 문단 교체

**EN**

> A typed address resolves to a PNU and its parcel context. Relevant statutes, ordinances, articles, and reference paths are retrieved from a Neo4j knowledge graph. The system combines exact, full-text, vector, and relationship-aware retrieval, then passes both constraints and source references to the design agents. The graph provides legal evidence; geometry is generated and validated in the following stages.

**KR**

> 입력한 주소는 PNU와 필지 맥락으로 변환된다. 관련 법령·조례·조문과 참조 경로는 Neo4j 지식 그래프에서 검색된다. 시스템은 정확 검색, 전문 검색, 벡터 검색, 관계 기반 검색을 결합하고, 설계 에이전트에 제약조건과 출처를 함께 전달한다. 그래프는 법적 근거를 제공하며, 실제 형상 생성과 검증은 이후 단계에서 수행된다.

## 다이어그램 소제목

### 01 — 좌측 하단 법령 위계

**EN**: `7-LEVEL STATUTE TREE`  
**KR**: `7단계 법령 위계`

**Caption EN**  
`LAW → JANG → JEOL → JO → HANG → HO → MOK preserves the original statutory hierarchy.`

**Caption KR**  
`법령 → 장 → 절 → 조 → 항 → 호 → 목의 원문 위계를 보존한다.`

현재 그림은 두 열로 갈라져 보여 위계가 오해될 수 있다. 최종본에서는 위 순서를 하나의 연속 트리로 연결하는 것이 맞다.

### 02 — 중앙 관계 도식

**EN**: `CONTAINS / NEXT / CITES`  
**KR**: `포함 / 순서 / 인용 관계`

**Caption EN**  
`CONTAINS preserves hierarchy, NEXT preserves sequence, and CITES connects cross-law references.`

**Caption KR**  
`CONTAINS는 위계, NEXT는 조문 순서, CITES는 법령 간 인용 경로를 보존한다.`

### 03 — 중앙 상단 노드 정보

**EN**: `LEGAL NODE SCHEMA`  
**KR**: `법규 노드 스키마`

**Caption EN**  
`Each node stores identity, content, hierarchy, revision metadata, provenance, and retrieval features.`

**Caption KR**  
`각 노드는 식별 정보, 본문, 위계, 개정 정보, 출처, 검색 특성을 함께 저장한다.`

### 04 — 우측 대형 그래프

**EN**: `LEGAL CLUSTER FIELD`  
**KR**: `법규 클러스터 필드`

**Caption EN**  
`Planning, building, housing, height, and daylight rules remain connected through their reference paths.`

**Caption KR**  
`도시계획·건축·주택·높이·일조 관련 규정이 참조 경로를 통해 연결된다.`

---

# 260707_18.jpg — A2A Protocol + GIS

## 페이지 역할

17페이지의 법규 근거와 실제 필지의 GIS 정보를 설계 입력으로 묶고, Host Agent가 필요한 역할과 도구에 작업을 전달하는 단계다.

## 메인 타이틀

현재 줄바꿈은 유지해도 된다.

```text
A2A
PROTOCOL
+ GIS
```

또는 현재 표현을 유지하려면 마지막 줄 `GIS` 앞에 작은 `+`만 추가한다.

## 보조 제목

**EN**: `FROM ADDRESS TO DESIGN CONSTRAINTS`  
**KR**: `주소에서 설계 제약조건까지`

## 좌측 설명문 — 현재 네 문단 교체

**EN**

> The address becomes a parcel key, and the parcel key gathers boundary, road, zoning, imagery, and terrain context where available. Legal evidence is converted into a measurable envelope including building coverage, floor-area ratio, height, setback, and parking conditions. The Host Agent then routes this shared context to the agents responsible for site planning and legal review.

**KR**

> 주소는 필지 키로 변환되고, 필지 키를 기준으로 경계, 도로, 용도지역, 영상, 지형 정보를 가용 범위에서 수집한다. 법규 근거는 건폐율, 용적률, 높이, 이격, 주차 조건을 포함한 측정 가능한 설계 가능 범위로 변환된다. Host Agent는 이 공통 맥락을 대지 계획과 법규 검토를 담당하는 에이전트에 전달한다.

## 다이어그램 소제목

### 상단 중앙 GIS 레이어

**EN**: `PARCEL & GIS CONTEXT`  
**KR**: `필지 및 GIS 맥락`

**Caption EN**  
`Parcel boundary, road and frontage, zoning, imagery, and elevation data establish the physical site context.`

**Caption KR**  
`필지 경계, 도로와 접도, 용도지역, 영상, 표고 정보가 대지의 물리적 맥락을 구성한다.`

현재 그림의 `Land cover / Hydrography / Geo Names / Structure`는 일반 GIS 레이어 예시다. 실제 핵심 입력처럼 본문에서 모두 구현됐다고 단정하지 않는다.

### 상단 우측 회색 큐브

**EN**: `LEGAL DESIGN ENVELOPE`  
**KR**: `법적 설계 가능 범위`

**Caption EN**  
`Retrieved rules become numeric limits and spatial constraints before geometry generation begins.`

**Caption KR**  
`검색된 법규는 형상 생성 전에 수치 한계와 공간 제약조건으로 변환된다.`

### 하단 좌측 에이전트 도식

**EN**: `CONTEXT ORCHESTRATION`  
**KR**: `맥락 오케스트레이션`

**Caption EN**  
`Active on this page: Host Agent, Master Plan Agent, Law Agent, and GRAPH DB.`

**Caption KR**  
`이 페이지의 활성 역할: Host Agent, Master Plan Agent, Law Agent, GRAPH DB.`

### 하단 중앙 시퀀스 도식

**EN**: `A2A TASK ROUTING / MCP TOOL ACCESS`  
**KR**: `A2A 작업 전달 / MCP 도구 접근`

**Caption EN**  
`A2A coordinates tasks between agents, while MCP connects an agent to APIs and deterministic tools.`

**Caption KR**  
`A2A는 에이전트 간 작업을 조정하고, MCP는 에이전트를 API와 결정론적 도구에 연결한다.`

---

# 260707_19.jpg — Massing Generation + VLM Critique

## 페이지에서 실제로 보이는 것

- 좌측 상단의 큰 제목 영역이 현재 비어 있다.
- 우측 상단에는 16개의 조형 연산 아이콘이 있다.
- 좌측 하단 도식에서는 `Host Agent`, `MASS Agent`, `VLM Agent`가 분홍색이다.
- 우측 하단에는 10개의 주황색 매스 대안이 있다.

## 메인 타이틀 — 빈 좌측 상단에 추가

```text
MASSING
GENERATION
```

## 보조 제목

**EN**: `EXECUTABLE OPERATIONS + VISUAL CRITIQUE`  
**KR**: `실행 가능한 조형 연산과 시각 비평`

## 메인 설명문

**EN**

> The MASS Agent converts site and legal constraints into executable geometry programs rather than a single opaque image. A vocabulary of operations produces structurally different candidates, while deterministic gates check geometry, legal limits, floor-area ratio, parking, and retention. The VLM Agent acts as a critic: it reviews selected views and proposes typed revisions that can be executed, compared, and traced.

**KR**

> MASS Agent는 대지와 법규 제약을 하나의 불투명한 이미지가 아니라 실행 가능한 형상 프로그램으로 변환한다. 조형 연산 어휘가 구조적으로 다른 후보를 만들고, 결정론적 검증 단계가 형상, 법규, 용적률, 주차, 형상 보존율을 검사한다. VLM Agent는 선택된 뷰를 비평하고, 실행·비교·추적할 수 있는 형식화된 수정안을 제안한다.

## 다이어그램 소제목

### 우측 상단 연산 아이콘

**EN**: `MASSING OPERATION VOCABULARY`  
**KR**: `매스 조형 연산 어휘`

**Caption EN**  
`Operations such as split, shift, carve, notch, taper, bend, lift, and stack form an executable design language.`

**Caption KR**  
`분할, 이동, 파내기, 노치, 테이퍼, 굽힘, 들어 올리기, 적층 연산이 실행 가능한 설계 언어를 이룬다.`

### 좌측 하단 에이전트 도식

**EN**: `MASS–VLM REVISION LOOP`  
**KR**: `MASS–VLM 수정 루프`

**Caption EN**  
`Active on this page: Host Agent, MASS Agent, and VLM Agent.`

**Caption KR**  
`이 페이지의 활성 역할: Host Agent, MASS Agent, VLM Agent.`

### 우측 하단 매스 10개

**EN**: `LEGAL MASSING ALTERNATIVES`  
**KR**: `법규를 통과한 매스 대안`

**Caption EN**  
`Multiple candidates are preserved for comparison instead of collapsing the process into one answer.`

**Caption KR**  
`과정을 하나의 정답으로 축소하지 않고 여러 후보를 비교 가능한 상태로 보존한다.`

---

# 260707_20.jpg — Massing to Architecture

## 중요한 제목 수정

현재 `GRAPH TO MASSING`은 19페이지와 역할이 겹친다. 이 페이지의 실제 그림은 선택된 매스에서 평면·입면·파사드를 발전시키는 내용이므로 제목을 바꾸는 것이 맞다.

## 메인 타이틀 — 기존 제목 교체

```text
MASSING
TO
ARCHITECTURE
```

## 보조 제목

**EN**: `PLAN + ELEVATION DEVELOPMENT`  
**KR**: `평면과 입면의 설계 전개`

## 좌측 설명문 — 현재 네 문단 교체

**EN**

> A selected massing candidate becomes the boundary condition for downstream architectural development. The Plan Agent explores program distribution, adjacency, circulation, and core position inside the available volume. The Elevation Agent reads orientation and exposed faces to generate facade alternatives. These outputs remain coordinated with the same massing source instead of becoming unrelated images.

**KR**

> 선택된 매스 대안은 후속 건축 설계의 경계조건이 된다. Plan Agent는 가용 볼륨 안에서 프로그램 배치, 인접 관계, 동선, 코어 위치를 탐색한다. Elevation Agent는 방향과 노출된 면을 읽어 입면 대안을 만든다. 이 결과들은 서로 무관한 이미지가 아니라 동일한 매스 원본에 연결된 설계 대안으로 유지된다.

## 다이어그램 소제목

### 중앙 상단 회색 매스

**EN**: `SELECTED MASSING`  
**KR**: `선정 매스`

**Caption EN**  
`The selected envelope defines the shared boundary for plan and elevation development.`

**Caption KR**  
`선정된 볼륨이 평면과 입면 전개의 공통 경계를 정의한다.`

### 우측 상단 입면 이미지 열

**EN**: `FACADE ALTERNATIVES`  
**KR**: `파사드 대안`

**Caption EN**  
`Elevation studies test solid–void ratio, opening rhythm, material contrast, and the central gap.`

**Caption KR**  
`입면 연구는 솔리드와 보이드의 비율, 개구부 리듬, 재료 대비, 중앙 틈의 표현을 비교한다.`

### 중앙 하단 분홍색 평면 그리드

**EN**: `PLAN CONFIGURATION STUDIES`  
**KR**: `평면 구성 연구`

**Caption EN**  
`Program blocks are rearranged within the same massing boundary to compare adjacency and circulation.`

**Caption KR**  
`동일한 매스 경계 안에서 프로그램 블록을 재배치해 인접 관계와 동선을 비교한다.`

### 좌측 하단 에이전트 도식

**EN**: `DOWNSTREAM DESIGN AGENTS`  
**KR**: `후속 설계 에이전트`

**Caption EN**  
`Active on this page: Host Agent, Plan Agent, and Elevation Agent.`

**Caption KR**  
`이 페이지의 활성 역할: Host Agent, Plan Agent, Elevation Agent.`

### 하단 중앙 짙은 매스 도식

**EN**: `COORDINATED DESIGN OUTPUT`  
**KR**: `통합 설계 결과`

**Caption EN**  
`Plan and facade decisions are recombined into one coordinated architectural state.`

**Caption KR**  
`평면과 파사드의 선택을 하나의 통합된 건축 상태로 다시 결합한다.`

---

# 260707_21.jpg — Shared Memory + Interface

## 페이지 역할

각 에이전트가 만든 근거, 도구 결과, 후보, 평가, 수정 이력을 공유 메모리에 남기고 사용자 화면에서 검토하는 마지막 단계다.

## 메인 타이틀

`SHARED MEMORY`

## 보조 제목

**EN**: `PERSISTENT DESIGN LINEAGE`  
**KR**: `지속되는 설계 계보`

## 좌측 하단 설명문

**EN**

> Shared memory preserves the project state across agents: parcel evidence, legal sources, tool results, geometry programs, candidate lineage, validation outcomes, and review notes. Each agent reads the same evolving context instead of rebuilding it from an isolated prompt. The result is a design process that can be resumed, compared, and audited.

**KR**

> 공유 메모리는 필지 근거, 법규 출처, 도구 결과, 형상 프로그램, 후보 계보, 검증 결과, 검토 기록을 에이전트 사이에 보존한다. 각 에이전트는 고립된 프롬프트에서 정보를 다시 만드는 대신 같은 프로젝트 맥락을 이어받는다. 따라서 설계 과정은 중단 후 재개하고, 대안을 비교하고, 근거를 감사할 수 있는 상태로 유지된다.

## 우측 상단 설명문

**EN**

> The memory layer records what was requested, which evidence was used, which tool produced each result, and how a candidate changed. This continuity keeps legal retrieval, massing generation, design development, and review connected as one project rather than separate demonstrations.

**KR**

> 메모리 계층은 무엇을 요청했는지, 어떤 근거를 사용했는지, 어떤 도구가 결과를 만들었는지, 후보가 어떻게 바뀌었는지를 기록한다. 이를 통해 법규 검색, 매스 생성, 설계 전개, 검토가 서로 분리된 시연이 아니라 하나의 프로젝트로 이어진다.

## 우측 중단 설명문

**EN**

> The interface returns this traceable state to the designer. The user can inspect parcel and legal context, compare alternatives, review validation values, and decide the next revision. Automation supports the decision; it does not remove authorship from the architect.

**KR**

> 인터페이스는 추적 가능한 프로젝트 상태를 다시 설계자에게 제공한다. 사용자는 필지와 법규 맥락을 확인하고, 대안을 비교하고, 검증값을 검토한 뒤 다음 수정 방향을 결정한다. 자동화는 판단을 지원하지만 건축가의 설계 주체성을 대체하지 않는다.

## 다이어그램 소제목

### 좌측 상단 네트워크 도식

**EN**: `AGENT COLLABORATION GRAPH`  
**KR**: `에이전트 협업 그래프`

**Caption EN**  
`Agents exchange evidence, tool outputs, and revision state through a shared project context.`

**Caption KR**  
`에이전트는 공유 프로젝트 맥락을 통해 근거, 도구 결과, 수정 상태를 교환한다.`

### 상단 버스 도식

**EN**: `SHARED MEMORY BUS`  
**KR**: `공유 메모리 버스`

**Caption EN**  
`Typed records preserve continuity between retrieval, generation, validation, and review.`

**Caption KR**  
`형식화된 기록이 검색, 생성, 검증, 검토 사이의 연속성을 보존한다.`

### 우측 하단 기기 화면

**EN**: `LIVE DESIGN INTERFACE`  
**KR**: `실시간 설계 인터페이스`

**Caption EN**  
`The user reviews parcel context, regulatory values, and design outcomes in one interface.`

**Caption KR**  
`사용자는 하나의 화면에서 필지 맥락, 법규 수치, 설계 결과를 검토한다.`

---

# 최종 편집 우선순위

1. 16페이지의 농업 연구시설 관련 임시 문구와 부제를 전부 교체한다.
2. 19페이지 좌측 상단에 `MASSING GENERATION` 제목을 추가한다.
3. 20페이지 제목을 `GRAPH TO MASSING`에서 `MASSING TO ARCHITECTURE`로 교체한다.
4. 17페이지 법령 위계를 `법령 → 장 → 절 → 조 → 항 → 호 → 목`의 연속 구조로 정리한다.
5. 18–20페이지의 에이전트 이름은 그대로 두고, 분홍색 활성 역할의 변화가 페이지 흐름으로 읽히게 한다.
6. 각 그림 바로 아래에는 이 문서의 다이어그램 소제목과 한 줄 캡션만 넣고, 긴 본문은 현재 회색 임시 문단 위치에 배치한다.

# 포트폴리오 전체 한 문장

**EN**

> 25_ACE turns parcel and legal evidence into traceable architectural alternatives through coordinated agents, executable geometry, deterministic validation, shared memory, and human review.

**KR**

> 25_ACE는 필지와 법규 근거를 에이전트 협업, 실행 가능한 형상, 결정론적 검증, 공유 메모리, 사람의 검토를 통해 추적 가능한 건축 대안으로 전환한다.
