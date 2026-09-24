# 260806 Proposal Page-Copy Memory

Updated: 2026-08-06 KST

## Active files

- Slide images: `docs/proposal/260806/`
- Editable page copy: `docs/proposal/260806/260806_페이지별_원고.md`

## Non-negotiable editing rule

Do not redesign the user's slides or replace the page structure with a new
proposal outline. Open and read each PNG first, then write copy for the actual
diagram, photograph, placeholder paragraph, or lower blue bar visible on that
page.

Each page entry uses:

1. short wording that can be placed directly on the PPT;
2. speaker notes for verbal explanation;
3. a project connection only when the page needs it.

Avoid repeating the same slogan across neighboring pages. The lower-bar copy
must summarize the specific visual argument of that slide.

## Actual project authority

Agent descriptions must come from the real contracts under
`ARR/backend/design/maas/agents/` and from the canonical MAAS memory. The
current specialist set used in the proposal is:

- `design_orchestrator`
- `law_graph_agent`
- `parking_agent`
- `llm_architect_agent`
- `massdsl_agent`
- `maas_geometry_agent`
- `grammar_critic_agent`
- `preference_distiller_agent`
- `review_agent`
- `elevation_agent`

Agents support the architect's early-design and pre-permit review workflow.
They do not replace the architect, permit authority, specialist engineer,
construction supervisor, use approval, official building register, or
facility maintenance process.

## Confirmed page decisions

### Page 01 — 건축사 업무

Lower bar:

> 건축사는 설계만 하는 사람이 아니라, 건축 전 과정의 전문가와 의사결정을 연결한다.

The page introduces the architect's broad coordination role. The research
scope is only the early-design through pre-permit review portion.

### Page 02 — 건축설계 업무

Lower bar:

> 건축설계는 다양한 전문영역을 기획설계·계획설계·기본설계·실시설계의 단계로 통합하고 구체화하는 과정이다.

This wording must reflect both halves of the diagram: evacuation, space,
landscape, parking, structure, barrier-free and master-plan design on the
left; schematic/planning/basic/detail design stages on the right.

### Page 03 — 건축법 체계

The two right-side placeholder paragraphs are used for:

- `01 국가 법령 체계`: law -> enforcement decree -> enforcement rule;
- `02 지역·대지별 적용`: ordinance, zoning, district-unit plan, road and
  parcel conditions.

Lower bar:

> 설계 가능한 형태는 법률의 위계와 대지별 적용조건이 함께 결정한다.

### Page 04 — 필로티 주차와 가각전제

This page needs two explanatory text blocks, not only a slogan.

- Piloti parking: required parking and vehicle access affect columns, core,
  ground-floor void and the upper MASS.
- Corner cut (`가각전제`): road width and intersection angle change the
  usable building area, corner geometry and pedestrian/vehicle entry.

Agent chain used in the project connection:

`law_graph_agent -> parking_agent -> maas_geometry_agent -> repair_delta`

Lower bar:

> 하나의 법규 조건이 대지경계에서 배치로, 1층 공간에서 전체 MASS로 연쇄적으로 이어진다.

### Page 05 — MASS STUDY problem framing

The page is not merely about diversity. It establishes the human-design
bottleneck: every alternative must coordinate law, structure, function and
beauty, so producing several sufficiently reviewed options takes substantial
time.

Lower bar:

> 법규를 지키고 구조·기능·미를 갖춘 설계 대안—오랜 설계와 검토 끝에도 한두 개에 그친다.

The research bridge is `design exploration + deterministic legal review`, not
shape-count maximization.

## Current continuation point

Pages 01-05 have received user-directed copy corrections. Continue from the
next slide by inspecting its actual PNG first. When an earlier page is revised,
update both the page-copy MD and this memory if the decision affects the deck's
ongoing narrative or editing rules.
