# MAAS 에이전트 협업 흐름 — 코드 감사 및 PPT 원고

• 이해했습니다. 목표는 둘 중 하나가 아니라 법규·주차·용적 hard constraint
  를 만족하면서도, 20개가 각기 명확한 건축언어와 현상설계급 공간 논리를
  갖는 것입니다. 지금 문제가 생긴 이유는 논문·VLM·레퍼런스가 없어서가 아
  니라, 그 지식이 실제 geometry로 내려가는 계약이 끊겨 있기 때문입니다.
  VLM이 courtyard/bridge/fold를 요구해도 materializer가 같은 2–3개 박스로
  만들면 논문을 더 넣어도 결과는 안 바뀝니다. 이 연결부부터 증거로 고치겠
  습니다.

Updated: 2026-07-14

## 한국어 PPT 원고: 에이전트별 설명

이 절은 각 에이전트를 PPT 한 장씩 설명할 수 있도록 정리한 발표 원고다.
각 장은 `필요성 -> 입력 -> 판단 -> 출력 -> 다음 단계 -> 실패 조건` 순서다.

현재 실험 상태를 먼저 밝힌다. 3방향 실루엣 중복을 hard gate로 적용한
`v68-pnu-1168011800104170004-three-view-silhouette` 결과는 **16/20,
technical_fail**이다. 아래 내용은 구현된 협업 구조를 설명하지만 현상설계급
20개가 완성되었다는 뜻은 아니다.

### PPT 01. 전체 MAAS 협업 구조

**핵심:** MAAS는 한 AI가 한 번에 건물을 그리는 구조가 아니다. 대지를 읽고,
건축언어를 쓰고, 실제 형상으로 컴파일하고, VLM이 비평하고, 법규·주차를
검증하고, 마지막으로 서로 다른 20안을 고르는 역할이 분리되어 있다.

```text
[PNU / 대지 / 용도 / 레퍼런스]
                 |
                 v
[대지 맥락] -> [레퍼런스 VLM] -> [LLM 건축가]
                                         |
                                         v
                                 [MassDSL / Graph]
                                         |
                                         v
                                 [Geometry Compiler]
                                         |
                    +--------------------+--------------------+
                    v                                         v
              [VLM 디자인 비평]                       [정량 Hard Gate]
                    |                              형상·프로그램·법규·주차
                    v                                         |
             [Graph Mutation] --------------------------------+
                    |
                    v
            [Archive + 최종 Selector]
                    |
                    v
          [20안 JSON / PNG / GRL / 세션 메모리]
```

VLM은 픽셀을 보고 비평하지만 직접 mesh를 생성하지 않는다. 실제 형상
생성기는 component graph를 실행하는 source compiler다. 법규와 주차의
최종 진실은 LLM/VLM 점수가 아니라 deterministic gate가 가진다.

### PPT 02. 대지 맥락 단계 — Site Context

**필요성:** 같은 건축언어도 대지 형상, 장축, 도로 접면, 진입 방향에 따라
배치와 열린 공간이 달라져야 한다.

```text
PNU -> VWorld 필지 경계 + 인접 도로 -> 미터 단위 대지 polygon
    -> 장축 / 비례 / 도로 접면 / 주 진입 edge -> site_context
```

- 입력: PNU, VWorld 경계·도로, 용도, FAR/BCR/높이 조건
- 판단: 면적, dominant axis, 종횡비, 도로 접면, 주 진입 edge
- 출력: `site_context`, metric parcel polygon, access geometry
- 다음 단계: Reference VLM과 LLM 건축가가 같은 대지 정보를 공유한다.
- 실패 조건: live 또는 PNU 일치 cache 경계가 없는 경우
- 코드: `run_neighborhood_vlm_a2a.py::_resolve_metric_site`,
  `llm_proposals.py::build_site_context`

이 단계는 직접 설계하지 않는다. 임의 좌표 대신 실제 대지 근거를 제공한다.

### PPT 03. 레퍼런스 해석 에이전트 — Reference VLM Distiller

**필요성:** ArchDaily나 사용자가 준 이미지를 그대로 복제하지 않고, 이미지의
건축적 원리를 편집 가능한 언어로 바꾸기 위해 필요하다.

```text
레퍼런스 이미지 + 용도 + 대지 맥락
              -> [Reference VLM]
              -> dominant gesture / spatial rule / operation recipe / avoid
```

- 입력: 로컬 레퍼런스, ArchDaily corpus, 건물 용도
- 판단: 연속체, 중정, 브리지, 절곡 단면, 계단형, 군집 등의 시각 원리
- 출력: 좌표를 복사하지 않는 `reference_language_brief`
- 다음 단계: LLM 건축가의 graph authoring prompt
- 실패 조건: 이미지/API/schema 오류, 현재 vocabulary로 표현 불가능한 원리
- 코드: `preference/reference_language_distiller.py`

하지 않는 일: 사진에서 3D mesh를 직접 만들거나 법규를 승인하지 않는다.
레퍼런스가 많아도 compiler가 표현하지 못하면 결과는 박스로 붕괴한다.

### PPT 04. 설계 저작 에이전트 — LLMArchitectAgent

**필요성:** 대지와 프로그램을 읽고 어떤 건축언어와 연산을 어떤 순서로
사용할지 제안하는 설계 저작자가 필요하다.

```text
site_context + program + reference briefs + 이전 실패 피드백
                         -> [LLM Architect]
                         -> MassComponentGraph + VerbSequence
```

- 입력: 대지, 용도, 수용량 목표, 레퍼런스 언어, 이전 VLM 비평
- 판단: primary/void/support/connector node, verb, relation, parameter
- 출력: 최대 6개 node의 typed component graph와 MassDSL sequence
- 다음 단계: graph validator와 source compiler
- 실패 조건: schema 위반, 잘못된 parent/relation, 동일 언어의 방향 반복
- 코드: `agents/llm_architect_agent/agent.py`, `llm_proposals.py`

하지 않는 일: polygon/surface를 직접 만들거나 법규·주차를 승인하지 않는다.

### PPT 05. MassDSL·Component Graph 검증 단계

**필요성:** 자연어 제안을 그대로 geometry로 보내면 부모 관계, node 수,
지원하지 않는 연산 때문에 형상이 깨지므로 실행 가능한 계약이 필요하다.

```text
LLM graph -> root / parent / role / relation / verb / parameter 검증
          -> 실행 가능한 graph 또는 명시적 reject
```

- 입력: LLM이 작성한 `MassComponentGraph`
- 판단: root 유일성, parent 순서, role/relation, node 수, verb schema
- 출력: 검증된 graph와 `VerbSequence`
- 다음 단계: source geometry compiler
- 실패 조건: root 수정, 없는 parent, 6개 초과 node, 불법 verb
- 코드: `grammar/component_graph.py`, `grammar/verb_sequence.py`

문법이 맞다는 사실은 건축적으로 아름답다는 뜻이 아니다.

### PPT 06. 형상 생성기 — Source Geometry Compiler

**필요성:** `split`, `courtyard`, `bend`, `stack`, `connect` 같은 graph 연산을
실제 footprint, volume, profiled surface로 바꿔야 한다.

```text
validated graph
 -> [graph materializer + formal principle + surface compiler]
 -> SourceMass = footprint + volumes + surfaces + geometry evidence
```

- 입력: 실제 대지 polygon, 검증된 graph/MassDSL
- 판단: node 관계의 공간 연산, 높이 band, void, 연결부, 연속 surface
- 출력: `SourceMass`, volume/surface signature, compiler evidence
- 다음 단계: 정량 gate, preview renderer, VLM critic
- 실패 조건: 빈 polygon, 과도한 조각, 서로 다른 verb가 같은 박스로 붕괴,
  void/connector가 metadata로만 남는 경우
- 코드: `source_geometry/compiler.py`, `graph_materializer.py`,
  `formal_principles.py`, `design_fields.py`, `surfaces.py`

현재 핵심 병목이다. 서로 다른 author graph 29개가 3방향 실루엣 기준 약
16개의 고유 형상으로 붕괴한다. selector 이전에 representation을 고쳐야 한다.

### PPT 07. 정량 형상·프로그램 Gate

**필요성:** VLM이 좋아 보인다고 해도 조각이 너무 많거나 프로그램과 용적을
담지 못하는 안은 후보가 될 수 없다.

- 입력: SourceMass, 층수·높이, 용도 profile, FAR 목표
- 판단: volume/surface 수, 작은 조각, program fit, FAR utilization
- 출력: `ProgramElite` 또는 reject evidence
- 다음 단계: preview/VLM과 behavior archive
- 실패 조건: volume > 4, non-profiled surface > 48, program hard-pass false,
  architectural score 부족, 최소 FAR 미달
- 코드: `vlm_a2a.py::_compile_verified`, `program_massing/scoring.py`

이것은 오프라인 clean/capacity gate이며 법규·주차 전체 검증과 같지 않다.

### PPT 08. 디자인 비평 에이전트 — VLM Critic

**필요성:** 수치만으로 박스 적층, 약한 중심 제스처, 레퍼런스와의 언어
불일치를 판단하기 어렵다.

```text
candidate PNG + geometry evidence + matched references
                         -> [VLM Critic]
                         -> scores + actions + typed graph_edits
```

- 입력: 렌더 PNG, 대지·진입 표시, feature evidence, 매칭 레퍼런스
- 판단: dominant gesture, void, ground relation, continuity, box-likeness,
  fragmentation, reference alignment
- 출력: 점수, `too_box_like` 등의 action, typed graph edit
- 다음 단계: graph mutation/revision
- 실패 조건: API/schema 오류, 근거 없는 점수, 수정 가능한 edit 없음
- 코드: `preference/vlm_scorer.py`, `preference/loop.py`

권한 제한: 법규·주차를 판정하지 않고 픽셀을 직접 geometry로 바꾸지 않는다.

### PPT 09. Graph Mutation 에이전트 — Critic Revision

**필요성:** VLM 비평을 문장으로만 저장하지 않고 다음 세대 형상에 반영한다.

```text
CriticDirective
  set_parameter / replace / add / remove / reparent
                -> [bounded graph revision]
                -> validated child -> recompile -> recheck
```

- 입력: 부모 graph와 VLM typed edit
- 판단: 대상 node/parameter 존재, 값 범위, graph schema 보존
- 출력: 0개 또는 1개의 검증된 child graph
- 다음 단계: compiler와 VLM 재평가
- 실패 조건: root 편집, unknown verb, 필수 node 삭제, 6 node 초과
- 코드: `agents/llm_architect_agent/graph_revision.py`

child는 자동 채택되지 않는다. VLM 개선량 `+0.015` 이상, 프로그램 손실
`0.03` 이하, 모든 hard gate 재통과가 필요하다.

### PPT 10. 진화·Archive·다양성 에이전트

**필요성:** 단일 최고점만 남기면 동일한 박스형으로 수렴하므로 서로 다른
형태 영역에서 좋은 후보를 병렬 보존한다.

- 입력: ProgramElite population, graph behavior, VLM score
- 판단: behavior cell, 언어군, FAR tier, pose-invariant morphology,
  top/front/side silhouette distance
- 출력: 제한된 부모 frontier와 최종 archive 후보
- 다음 단계: final selector와 artifact writer
- 실패 조건: 회전·반사만 다른 가짜 다양성, 이름만 다른 동일 형상
- 코드: `graph_archive.py`, `morphology.py`, `search.py`

현재 v68은 이 기준에서 **16/20**을 반환했다. 중복으로 채우지 않은 것은
정직하지만 generator가 20개 고유 형상을 만들지 못했다는 뜻이다.

### PPT 11. 법규 검증 에이전트 — Legal Solver

**필요성:** BCR, FAR, 높이, 일조, setback은 디자인 점수가 아니라 계산 가능한
hard constraint로 다뤄야 한다.

- 입력: 대지, legal constraints, mass, 층수·높이
- 판단: BCR/FAR/높이/envelope/setback의 deterministic 계산
- 출력: 법규 metric, 위반 목록, repair된 후보
- 다음 단계: 주차 검증과 service final selector
- 실패 조건: envelope 밖 형상, 정수 투영 실패, constraint 위반
- 코드: `legal_envelope.py`, `legal_mesh_optimizer.py`

`law_graph_agent` review는 이미 계산된 근거를 요약한다. 실제 legal truth와
repair는 solver가 담당한다.

### PPT 12. 주차 검증 에이전트 — Parking Solver

**필요성:** 주차 대수뿐 아니라 진입, 배치 가능성, 소규모 부설주차 검토
근거까지 mass-stage에서 확인해야 한다.

- 입력: 용도, 연면적, local/Neo4j 규칙, 도로·대지 형상
- 판단: 필요 대수, 지상 배치, 진입, 8대 이하 연접·도로 aisle 검토 근거
- 출력: requirement/layout evidence와 mass-stage status
- 다음 단계: service final selector
- 실패 조건: 대수·진입·배치 부족, authority-review 근거 누락
- 코드: `parking_requirements.py`, `parking_layout.py`, `parking_strategy.py`

Neo4j는 선택적 규칙 보강이다. 꺼져 있다고 mass가 박스가 되는 것은 아니다.

### PPT 13. 최종 Selector 에이전트

**필요성:** gate를 통과한 안 중에서도 언어 다양성, 용량, cleanliness, VLM
품질을 함께 만족하는 정확한 20개를 골라야 한다.

- 입력: hard-pass 후보와 전체 evidence
- 판단: 언어군, 시각적 정갈함, 용량 tier, 출처, 형태 중복, 정확한 개수
- 출력: 최대 20개의 final feature
- 다음 단계: JSON/PNG/GRL 및 서비스 응답
- 실패 조건: pool 부족, quota 충돌, 3-view silhouette 중복
- 코드: offline `vlm_a2a.py`; service `selection/final_balanced.py`,
  `selection/integer_projection.py`

Selector는 없는 창의성을 만들 수 없다. 유효 후보가 16개면 16개를 반환해야
하며 중복으로 20칸을 채우면 안 된다.

### PPT 14. GRL·메모리·Artifact 단계

**필요성:** 후보가 어떤 대지, graph, VLM 비평, mutation, selector 판단을 거쳐
살아남았는지 다음 세션이 재현할 수 있어야 한다.

```text
selected archive
 +-> result JSON
 +-> review PNG / accepted-only PNG
 +-> GRL lineage JSON
 +-> VLM score cache
 +-> accepted graph seed + session memory
```

- 입력: 최종 archive와 전체 trace/evidence
- 판단: 생성 판단 없음; provenance와 lineage 직렬화
- 출력: JSON, PNG, GRL, cache, 다음 run seed
- 다음 단계: 사람 검토 및 명시적으로 경로를 전달한 다음 run
- 실패 조건: PNG/JSON 후보 수 불일치, 다른 geometry에 잘못된 cache 재사용
- 코드: `program_massing/grl_contract.py`, CLI writer,
  `docs/ai-session-memory/`

GRL은 generator·optimizer·trainer가 아니다. 메모리도 자동 학습이 아니며
다음 실행에 feedback/seed/cache 경로를 명시해야 사용된다.

### PPT 15. 오프라인 20안과 실제 서비스의 차이

| 구분 | 오프라인 VLM/A2A 연구 루프 | 동기 법규·주차 서비스 |
|---|---|---|
| 목적 | 창의적 언어, VLM feedback, 20안 archive | legal envelope와 parking mass-stage 검증 |
| VLM | 비평, rerank, typed graph edit | preference loop와 제한된 MassDSL 수정 |
| 법규·주차 | `legal_projection_status: not_run` | deterministic solver/gate 실행 |
| 결과 | JSON, PNG, GRL, cache | HTTP feature collection, browser card PNG |
| 현재 한계 | v68 16/20, graph-to-geometry collapse | 법규 pass가 디자인 품질을 보장하지 않음 |

발표에서 두 경로를 하나의 완성된 autonomous 협상으로 과장하면 안 된다.
최종 목표는 두 경로를 결합하되 graph/geometry/VLM과 법규·주차의 책임을
계속 분리하는 것이다.

---

아래는 코드 감사와 상세 실행 근거를 보존한 기술 부록이다.

This document records what the current code actually does when it creates and
reviews MAAS mass alternatives. It deliberately separates executable
generation from post-hoc agent narration. Do not infer a capability from an
agent name alone.

## Executive verdict

There are two different pipelines, and neither alone is the complete target
system.

1. The offline 20-alternative research loop in
   `program_massing/vlm_a2a.py` has a real image-critic feedback path:
   LLM-authored component graph -> deterministic compiler -> preview PNG ->
   VLM scores and typed graph edits -> bounded graph mutation -> recompile ->
   deterministic gates -> VLM recheck -> archive selection. This is the place
   where A2A changes candidate geometry, indirectly through MassDSL graph
   mutation.
2. The synchronous service path in `legal_mesh_optimizer.py` performs the
   actual legal-envelope and parking mass-stage checks. It also has a VLM
   critic geometry loop, but the `agent_reviews` returned at the end are
   deterministic, post-selection reviews of the top candidate; they are not
   the mechanism that generated the population.

The current VLM is **not a geometry generator**. It interprets reference
images, scores rendered candidates, and may emit bounded graph-edit directives.
`source_geometry/compiler.py` remains the executable geometry generator. A VLM
directive affects geometry only if the edit validates, recompiles, passes the
deterministic gates, and improves the acceptance objective.

The current offline 20-board is therefore a research/evaluation loop, not proof
of a legal design service. Its result explicitly writes
`legal_projection_status: not_run`. The service path is the legal/parking path,
but a legal or parking mass-stage pass is still not permit-final approval.

## System boundary

```text
                    EXECUTABLE GENERATIVE CORE

  site/PNU + program + references + prior accepted graphs
                             |
                             v
                  [LLM Architect / author]
                 typed component graph + MassDSL
                             |
                             v
           [Source compiler: deterministic geometry]
                 volumes + profiled surfaces
                             |
              +--------------+---------------+
              |                              |
              v                              v
       deterministic gates             preview renderer
       geometry/capacity or                  |
       law/parking, by path                  v
              |                         [VLM critic]
              |                    scores + actions +
              |                    typed graph edits
              |                              |
              |                              v
              |                    [bounded graph mutation]
              |                              |
              +<--------- recompile ----------+
              |
              v
       archive/selector -> JSON + PNG + audit evidence


                    EXPLAINABILITY / REVIEW LAYER

  already selected feature
           |
           v
  law -> parking -> LLM-language -> MassDSL -> geometry -> grammar
      -> preference -> final-review summaries

  This second chain reports evidence. It does not itself generate the 20.
```

## Offline 20-alternative VLM/A2A loop

Entry points:

- CLI: `scripts/run_neighborhood_vlm_a2a.py::main`
- Orchestrator: `ARR/backend/design/maas/program_massing/vlm_a2a.py::run_neighborhood_vlm_a2a_loop`

```text
 [PNU]
   |
   +--> VWorld parcel boundary --> metric/local site polygon
   |
   +--> nearby roads -----------> access edge/context
   |
   v
 [site_context + program profile + capacity policy]
   |
   +--> [reference corpus]
   |       |
   |       +--> VLM reference-language distillation
   |              -> coordinate-free operation briefs
   |
   v
 [LLMArchitectAgent.propose_population]
   -> MassComponentGraph V2 carried inside VerbSequence
   |
   +--> persisted accepted graphs
   +--> program seeds
   +--> creative seeds
   |
   v
 [search_program_elites]
   -> parameter mutation / compile / program score
   -> clean pool
   |
   v
 [capacity floor]
   -> capacity pool
   |
   v
 [GraphBehaviorArchive + bounded behavior frontier]
   -> language-balanced VLM parents
   |
   v
 [render candidate preview] --> [OpenAI VLM critic + references]
                                  |
                                  +--> concept scores
                                  +--> critic actions
                                  +--> typed graph_edits
                                          |
                                          v
                           [apply_critic_graph_edits]
                           set / replace / add / remove /
                           reparent within graph schema
                                          |
                                          v
                           [_compile_verified]
                           compile + clean/program/capacity gates
                                          |
                                          v
                              [VLM child recheck]
                                          |
                           improve VLM >= +0.015 and
                           program loss <= 0.03 ?
                              | yes              | no
                              v                  v
                         archive child       reject child
                              |
                              +---- next generation (<= 3)
                                          |
                                          v
 [visual floor -> language/novelty/capacity selector -> rebalance]
                                          |
                       +------------------+------------------+
                       v                  v                  v
                    result JSON       review PNG      accepted-only PNG
                       |
                       +--> GRL audit JSON
                       +--> reusable VLM score cache
                       +--> accepted graph records for an explicit next run
```

### Offline stages and failure conditions

| Stage | Actual implementation | Input | Output | Reject/failure condition |
|---|---|---|---|---|
| Site acquisition | `scripts/run_neighborhood_vlm_a2a.py::_resolve_metric_site` | PNU or cached matching boundary | metric parcel, boundary source, road/access context | neither live nor matching cached boundary exists |
| Reference interpretation | `preference/reference_language_distiller.py::distill_reference_languages_with_openai` | local reference corpus and building type | coordinate-free language briefs and supported verb recipes | provider/cache/schema failure; a brief alone creates no geometry |
| Graph authoring | `LLMArchitectAgent.propose_population` -> `llm_proposals.generate_llm_massdsl_batch` | site context, program, reference briefs, previous feedback | graph-native `VerbSequence` population | invalid schema/verbs/parameters; in required-live mode deterministic coverage repair causes run rejection |
| Genotype validation | `grammar/component_graph.py::MassComponentGraph.validate` | root and up to six typed nodes | valid component graph V2 | missing/duplicate root, invalid parent ordering/relation, more than six nodes |
| Source compilation | `source_geometry/compiler.py::compile_sequence_to_source_mass` | parcel and graph/sequence | `SourceMass` volumes and surfaces | graph operation cannot materialize, invalid/empty geometry, compiler coherence failure |
| Search | `program_massing/search.py::search_program_elites` | authored/persisted/program/creative seeds | mutated clean population | compile failure, program hard gate, low architectural score, novelty selection |
| Offline clean gate | `vlm_a2a.py::_compile_verified` | compiled source | `ProgramElite` | volume count > 4; non-profiled surface count > 48; profiled raw surfaces > 160; effective surfaces > 28; program hard-pass false; architectural score < 0.76; below minimum FAR utilization |
| Capacity filter | `run_neighborhood_vlm_a2a_loop` lines 201-222 | clean pool and capacity policy | capacity pool | normalized FAR utilization below program capacity minimum |
| Behavior archive | `program_massing/graph_archive.py` | capacity candidates | bounded MAP-Elites-like frontier | coarse cell limits and downstream novelty/coverage selection remove candidate |
| VLM scoring | `preference/vlm_scorer.py::score_candidate_with_openai_vlm` | candidate PNG, feature evidence, matched references | concept scores, actions and typed graph edits | API/schema failure; VLM is explicitly not allowed to decide law or parking |
| Graph revision | `agents/llm_architect_agent/graph_revision.py` | graph plus `CriticDirective` | zero or one revised graph | unknown parameter/verb, root edit, invalid parent, non-optional removal, graph > 6 nodes, graph validation error |
| Child acceptance | `run_neighborhood_vlm_a2a_loop` lines 304-366 | recompiled and rescored child | replacement parent/archive member | compile/hard-gate failure, VLM improvement < 0.015, or program fit loss > 0.03 |
| Final selector | `_select_language_balanced_archive`, `_rebalance_capacity_archive` | visual-floor finalists and durable archive | at most requested 20 | visual floor, language quota, capacity quota, persisted/fresh quota, rotation/reflection-invariant morphology repeat, three-view silhouette repeat |
| Artifact write | `_render_archive_sheet`, `build_archive_grl_contract` | review and accepted archives | JSON, two PNGs, GRL JSON | the loop can honestly return fewer than 20 and `technical_fail`; a board being rendered does not mean 20 accepted |

### What “A2A” means here

The actual generative A2A exchange is typed in-process data, not networked A2A
transport:

```text
LLM author output
  MassComponentGraph / VerbSequence
          |
          v
deterministic compiler output
  Feature + SourceMass + preview PNG
          |
          v
VLM critic output
  CriticDirective(actions, graph_edits, scores, references)
          |
          v
graph revision output
  validated MassComponentGraph
```

`agents/orchestrator/generative_loop.py::run_generative_a2a_loop` expresses the
same injected author/compiler/gate/critic/reviser/archive contract, but current
repository callers are tests only. The production offline benchmark implements
its own equivalent closed loop directly in `program_massing/vlm_a2a.py`.

## Synchronous legal/parking service path

Entry points:

- HTTP: `POST /design/maas/legal-variants/` in
  `ARR/backend/design/views.py::maas_legal_variants`
- Generator: `ARR/backend/design/maas/legal_mesh_optimizer.py::generate_legal_mass_variants`
- Browser evidence: `docs/playwright/design-route-live-verify/render-maas-20-alt.cjs`

```text
 [mass seed + site + legal constraints + PNU/options]
                         |
                         v
              [build legal envelope]
        BCR / FAR / height / sunlight / setbacks
                         |
                         v
            [repair initial seed to envelope]
                         |
       +-----------------+------------------+
       |                                    |
       v                                    v
 legal floor-stack anchor       LLM graph proposals + seed grammar
                                            |
                                  island parameter/crossover mutation
       |                                    |
       +-----------------+------------------+
                         v
        [repair each candidate + compute legal metrics]
                         |
               failed_constraint_metrics?
                 | yes              | no
                 v                  v
              reject       bounded legal candidate pool
                                      |
                                      v
                         [parking requirement + layout]
                       graph/local rules + deterministic placer
                                      |
                         mass-stage gate / optional repair
                                      |
                                      v
                         [VLM preference loop]
                                      |
                       actionable critic directives?
                         | no               | yes
                         |                   v
                         |       MassDSL mutation -> legal repair
                         |       -> parking/clean gate -> VLM rescore
                         +-------------------+
                                      |
                                      v
                balanced selector + exact integer projection
              law / parking / coherence / VLM / diversity quotas
                                      |
                                      v
                            final selected features
                                      |
                         +------------+-------------+
                         v                          v
                  agent evidence/reviews      service JSON
                  (post-selection report)          |
                                                   v
                                          browser/card PNG renderer
```

### Service hard-gate boundary

- `build_legal_envelope`, `repair_design`, and `failed_constraint_metrics` own
  deterministic BCR/FAR/height/envelope truth. The LLM and VLM do not approve
  legality.
- `_attach_parking_requirements` resolves the required count and calls the
  deterministic parking strategy/layout path. `parking_layout.py` describes
  itself as a conservative mass-stage capacity/layout precheck, not a final
  solver.
- `selection/constraints.py::final_mass_stage_parking_pass` accepts `pass`,
  `needs_mechanical_parking_review`, and `needs_drive_connectivity_review` for
  mass-stage selection. This is intentionally broader than permit approval.
- Small attached parking relief is evaluated by
  `parking_layout.py::evaluate_small_attached_parking_relief`; it records
  road-as-aisle/tandem authority-review evidence and does not grant approval.
- Neo4j is optional for parking-rule enrichment. By default,
  `parking_requirements.py::load_parking_requirement_rules` can load reviewed
  local structured seed rules. Turning Neo4j off does not explain bad mass
  geometry and does not necessarily disable parking count evaluation.
- The offline `program_massing/vlm_a2a.py` path does **not** call these legal
  and parking stages. Its clean/capacity gates must not be reported as legal or
  parking passes.

## Agent-by-agent truth table

| Named agent/module | Executable role | What it does not do |
|---|---|---|
| `design_orchestrator` | agent card and route summary | does not schedule the population generator or stop the flow on failure |
| `law_graph_agent` | rechecks already attached FAR/BCR/height metrics against constraints | does not build the legal envelope; does not query every law needed for a permit |
| `parking_agent` | summarizes already attached requirement/layout evidence | does not generate parking; `parking_layout.py` and parking strategy code do |
| `llm_architect_agent` | owns live structured architectural-language population call and audits parameter provenance | does not materialize geometry or approve law/parking |
| `massdsl_agent` | packages/validates a selected candidate's MassDSL evidence contract | in the review chain it is post-hoc; the actual compiler consumes authored graphs earlier |
| `source_geometry/compiler.py` | executable component-graph/MassDSL geometry materializer | does not judge architectural beauty or permit compliance |
| `maas_geometry_agent` | reports geometry/repair context for an already selected feature | its `run` method is not the source compiler |
| `grammar_critic_agent` | deterministic evidence and orderliness review | does not use pixels and does not mutate geometry |
| `preference_distiller_agent` / VLM scorer | image/reference preference critic and reranker | cannot rescue a law/parking hard-gate failure and is not a geometry generator |
| `graph_revision.py` | converts supported VLM graph edits into bounded genotype mutations | cannot invent unsupported operations or bypass graph validation |
| `review_agent` | final audit summary | does not select or generate the final archive |
| `GraphBehaviorArchive` and selectors | retain behavior cells; enforce novelty, language, capacity and source quotas | quotas do not prove architectural quality; they can return fewer than 20 |
| `GRL` adapter | serializes site -> principle -> candidate lineage and morphology relations | is explicitly an evidence/lineage viewer, not a generator, optimizer, DB, or trainer |
| memory/cache artifacts | allow explicit feedback, cached VLM scores, and accepted graph reuse in later CLI runs | are not autonomous online learning; the next run must be given the relevant paths |

## Post-hoc review chain: do not confuse with generation

`agents/shared/registry.py::run_review_flow` executes the fixed
`REVIEW_AGENT_SEQUENCE` using a list comprehension. Every review receives the
same `AgentContext`; `next_agent` is descriptive metadata. A failure does not
branch, halt, or regenerate a candidate.

In `generate_legal_mass_variants`, this review flow is called after final
selection and only with `top_feature`. Consequently:

- `agent_reviews` proves that the named review contracts ran;
- it does not prove that eight autonomous agents negotiated all 20 candidates;
- the actual multi-step population work is performed by the generator,
  compiler, legal/parking services, VLM loop, and selectors described above.

## Selector and archive semantics

The offline and service selectors are also different.

### Offline archive

- `GraphBehaviorArchive` uses graph behavior descriptors and keeps high-score
  elites per cell.
- `bounded_behavior_frontier` reduces the thousands-candidate pool before
  expensive image review.
- `_select_language_balanced_archive` applies language, novelty, authored,
  fresh/persisted, and capacity constraints.
- `morphology.py` removes translation/rotation/reflection pose as a false
  source of novelty; `_silhouette_repeat_pairs` audits three-view silhouette.
- If only 19 genuinely qualifying candidates exist, returning 19 is correct.
  Filling the twentieth slot with a duplicate would be a false pass.

### Legal service selector

- `selection/final_balanced.py` balances legal/parking-pass candidates across
  visible language and evidence categories.
- `selection/integer_projection.py::solve_final_integer_projection` performs
  the exact final binary selection under available quotas.
- `legal_mesh_optimizer.py` requires legal/parking/order/coherence evidence
  before an item enters the integer pool and completes VLM scoring for the
  final set when VLM is required.
- A selector can only choose from geometry the compiler produced. Better
  quotas cannot turn a weak box-dominated source population into
  competition-grade architecture.

## Output and memory flow

```text
 offline result
   |
   +-- <stem>.json                 complete trace and accepted sequences
   +-- <stem>.png                  up-to-20 review sheet, may include rejects
   +-- <stem>-accepted-only.png    accepted candidates only
   +-- <stem>-grl.json             lineage/morphology audit view
   +-- <stem>-vlm-score-cache.json geometry/site/reference/model keyed cache
   |
   +-- next run --accepted-seed-from / --feedback-from / cache arguments
                     (explicit reuse, not automatic learning)

 service result
   |
   +-- HTTP JSON feature collection + rejected/evidence/traces
   +-- optional verified service cache
   +-- Playwright/browser renderer creates the 20-card PNG separately
```

VLM cache keys include model, canonical component graph, volume signatures,
surface signatures, site boundary/access and matched reference IDs. Reusing a
cache therefore does not intentionally transplant a score onto different
geometry or a different site.

GRL output is produced only after the offline archive has been selected. It
cannot change a graph in the current pipeline. Historical memory and
Mass-Brain shadow proposals are also separate adapters; neither should be
described as the active geometry optimizer unless a trace shows a promoted
proposal affecting selection.

## Known limits that affect the current 20-board

1. The offline loop combines a real PNU and road context with program/capacity
   gates, but its legal and parking projection is not run.
2. The graph genotype is intentionally limited to six nodes and the clean
   source mass to at most four visible volumes in `_compile_verified`. This
   controls LEGO fragmentation but also bounds representational richness.
3. VLM edits are constrained to the supported verb and parameter schemas. An
   attractive reference that cannot be expressed by those operations cannot
   be recovered by more reranking.
4. The service review-agent chain is mostly explainability, not an autonomous
   network protocol.
5. Reference-language distillation creates operation briefs, not a copied 3D
   model. Reference quantity alone cannot fix a weak compiler representation.
6. Archive counts and zero measured repeats are necessary but not sufficient.
   The PNG still requires direct architectural review.
7. The offline review PNG can contain rejected cards to make shortages visible;
   only the accepted-only PNG represents the accepted archive.

## Where to modify each responsibility

The current separation allows direction changes without rewriting the entire
pipeline:

```text
 change author/model/prompt
   -> llm_proposals.py, llm_architect_agent/

 change graph vocabulary or mutation
   -> grammar/, graph_revision.py, evolution/

 change geometric expressivity
   -> source_geometry/ (compiler, formal principles, design fields, surfaces)

 change law/parking truth
   -> legal_envelope.py, legal_mesh_optimizer.py, parking_requirements.py,
      parking_layout.py, parking_strategy.py

 change VLM/ref interpretation
   -> preference/ (reference distiller, matcher, scorer, loop)

 change diversity/archive policy
   -> program_massing/morphology.py, graph_archive.py, search.py,
      selection/

 change audit transport/viewer
   -> program_massing/grl_contract.py

 change service vs offline orchestration
   -> legal_mesh_optimizer.py vs program_massing/vlm_a2a.py
```

The next architecture correction should keep these boundaries: improve the
graph and source representation first, use VLM critique to request validated
graph changes, retain deterministic legal/parking gates, and let the selector
reject an undersized archive rather than inventing duplicate filler.

## Code references audited

- `scripts/run_neighborhood_vlm_a2a.py`
- `ARR/backend/design/views.py::maas_legal_variants`
- `ARR/backend/design/maas/program_massing/vlm_a2a.py`
- `ARR/backend/design/maas/program_massing/search.py`
- `ARR/backend/design/maas/program_massing/graph_archive.py`
- `ARR/backend/design/maas/program_massing/grl_contract.py`
- `ARR/backend/design/maas/agents/orchestrator/generative_loop.py`
- `ARR/backend/design/maas/agents/shared/registry.py`
- `ARR/backend/design/maas/agents/llm_architect_agent/agent.py`
- `ARR/backend/design/maas/agents/llm_architect_agent/graph_revision.py`
- `ARR/backend/design/maas/grammar/component_graph.py`
- `ARR/backend/design/maas/source_geometry/compiler.py`
- `ARR/backend/design/maas/preference/reference_language_distiller.py`
- `ARR/backend/design/maas/preference/vlm_scorer.py`
- `ARR/backend/design/maas/preference/loop.py`
- `ARR/backend/design/maas/evolution/critic_loop.py`
- `ARR/backend/design/maas/legal_mesh_optimizer.py`
- `ARR/backend/design/maas/parking_requirements.py`
- `ARR/backend/design/maas/parking_layout.py`
- `ARR/backend/design/maas/selection/constraints.py`
- `ARR/backend/design/maas/selection/final_balanced.py`

## 2026-07-14 executable graph-primary and branched-field correction

The current agent contract has one additional non-negotiable rule:

```text
LLM author graph
  -> exactly one node.role == primary
  -> compiler chooses executable family from that primary operation
  -> support/void/connector nodes modify or annotate the primary
  -> filename, typology and mass_language never replace primary geometry
```

For a branched continuous field, the geometry boundary is:

```text
typed bend graph (field_topology=branched)
  -> parcel-frame trunk + arm paths
  -> editable profiled quad-strip surfaces (VLM/render evidence)
  -> unioned single SourceVolume (clean legal/FAR proxy)
  -> program/capacity gate
  -> VLM critic and typed graph edit
  -> recompile and rescore
```

The one-volume proxy is not a fallback. It prevents intentional trunk/arm
continuity from being misread as three colliding LEGO solids. The surface patch
contract preserves the editable architectural section and is part of VLM cache
identity. v74 proves the full loop retains one branched candidate, but the
offline board remains 17/20 and box-dominant. Legal and parking still run only
in the separate deterministic service path.

## 2026-07-14 adaptive archive ownership correction

The current offline collaboration loop is now:

```text
LLM Architect Agent
  -> typed MassDSL component graph
  -> shared parameter bounds
  -> source-geometry compiler
  -> clean/program/capacity gates
  -> VLM critic + reference matches
  -> typed graph edits
  -> recompile (no image-only rerank mutation)
  -> intrinsic diversity + language-balanced selector
  -> honest accepted archive
  -> deficit feedback
  -> focused author replenishment round
  -> compare with best-so-far archive
```

Ownership rules:

- `llm_proposals.py` authors and validates executable graph language. It does
  not decide law or parking.
- `parameter_schema.py` is the shared editable numeric contract. A graph JSON
  must contain the same bounded values the compiler uses.
- `source_geometry/compiler.py` materializes the graph. Array/cluster hierarchy
  is controlled by `hierarchy_ratio` and `stagger_ratio`, not a fixed precedent
  footprint.
- `language_quality.py` validates that the rendered geometry proves its claimed
  language. Labels cannot substitute for sectional progression, spatial field
  hierarchy or a legible void.
- `vlm_a2a.py` owns critic scoring and final archive gates. VLM remains a critic
  and typed graph-edit director, not a freeform 3D generator.
- `adaptive_loop.py` owns bounded replenishment and best-so-far retention. A
  later round may add candidates but cannot replace a better earlier archive
  with a regression.
- deterministic legal/FAR/parking services remain a separate downstream
  projection. The current offline v79 evidence has not run that projection.

Production timing boundary:

```text
synchronous request
  -> PNU/site load
  -> retrieve verified graph archive
  -> bounded site adaptation + deterministic law/parking projection
  -> return review candidates

asynchronous quality job
  -> fresh LLM author
  -> search + VLM critique/revision
  -> strict PNG/archive audit
  -> promote only if best-so-far improves
```

Do not place the 7-15 minute fresh author/VLM replenishment loop directly in a
normal service request. Neo4j/GRL may persist lineage and evidence, but neither
is required to generate the current geometry and neither fixes a weak mass.
