1. 법규부터 디자인까지 멀티에이전트로 에이전트끼리 협업해서 법규 및 디자인 최적화

2. 사용자가 그래프에서 움직여도 그걸 mass 가 자연스럽게 변형이되게 유도 

3. 주차장법 빨리 추가할것

4. three.js 로 하면 바로 bim ifc 파일로 보낼수있지않나라고 말함



• 결론부터 말하면: AG-light는 멀티에이전트 “기반 세팅”은 되어 있는데, 우리가 말하는 법규→디자인 최적화용 실전 멀티에이전트 팀은 아직 안 됐어.

  현재 되어 있는 것:

  - AG-light/server/main.py
      - FastAPI 서버 있음.
      - /health
      - /bus/* Message Bus
      - /memory/* SharedMemory
      - /mcp/mcp FastMCP mount 구조 있음.

  - AG-light/server/mcp_tools/tools.py
      - MCP 22개 tool 있음.
      - 법 검색 tool
      - 토지 분석 tool
      - arr_maas_evidence
      - arr_maas_review
      - send_message, broadcast_message, get_conversation_log
      - store_decision, publish_event 등 있음.

  - AG-light/server/agents/
      - message_bus.py
      - shared_memory.py
      - collaborative.py
      - 즉 agent끼리 메시지 보내고, 결정 공유하고, 이벤트 남기는 기반은 있음.

  - AG-light/data/teams/, AG-light/data/patterns/
      - AutoGen/A2A 스타일 팀 JSON, 패턴 JSON 있음.
      - sequential, debate, reflection, magentic, mixture 등 패턴 있음.

  - .claude/agents/
      - land-analyst
      - legal-interpreter
      - design-advisor
      - qa-reviewer
      - 이런 역할 정의는 있음.

  안 되어 있는 것:

  - 법규→datum→주차→MAAS→디자인 최적화→VWorld QA를 도는 실제 workflow 코드는 없음.
  - law_graph_agent, parking_agent, maas_geometry_agent, design_optimizer_agent 같은 실전 role agent 파일은 아직 없음.
  - agent들이 서로 대화하면서 evidence를 보고 반박/수정요청하는 orchestration도 아직 없음.
  - arr_maas_review는 지금 “evidence 요약 tool”이지, 여러 agent가 독립 검토하는 진짜 multi-agent review가 아님.
  - AG-light 서버도 지금은 안 떠 있음. 방금 확인했을 때 127.0.0.1:8200 connection refused.

  정확히 말하면 현재 상태는:

  멀티에이전트 인프라: 있음
  MCP tool layer: 있음
  MessageBus/SharedMemory: 있음
  팀/패턴 JSON 자산: 있음
  ARR MAAS evidence 연결: 1차 있음

  하지만
  법규-디자인 최적화 agent team runtime: 미구현
  주차 agent: 미구현
  실제 AutoGen식 협업 loop: 미구현

  그래서 다음에 해야 할 건 폴더 구조상 이거야:

  AG-light/server/agents/roles/
    law_graph_agent.py
    datum_agent.py
    parking_agent.py
    maas_geometry_agent.py
    design_optimizer_agent.py
    visual_qa_agent.py
    review_agent.py

  AG-light/server/agents/workflows/
    legal_design_optimization.py
    parking_review.py
    graph_edit_to_mass.py

  AG-light/server/mcp_tools/
    maas_tools.py
    parking_tools.py
    design_tools.py


## MAAS 다양성/Agent 목표 원칙 업데이트

## MAAS Architecture-Grade Geometry Goal

사용자 최신 목표:

- 결과 메스는 단순히 법규 통과/다양성 카운터 통과가 아니라, 기하학적으로 멋있는 건축 매스여야 한다.
- 사용자가 준 책/건축 레퍼런스도 논문과 같은 수준의 설계 언어 근거로 사용한다.
- 참조 감각:
  - 트리마제: 강한 수직성, 슬렌더 타워, 정리된 podium/ground 관계.
  - Vancouver House / BIG: 비틀림, 언더컷, 조각적 하부-상부 전이, 구조적 제약 안의 강한 실루엣.
  - OMA / Seattle Central Library: 프로그램/층판이 읽히는 stacked platform, shifted volume, 다이어그램적 단면 질서.
  - 사용자가 제공한 건축 책/레퍼런스: mass composition, figure-ground, datum, void, tower-base, slab-stack, carved solid, connector, sectional diagram 같은 formal principle로 번역한다.

새 성공 기준:

1. 법규/주차 hard gate는 그대로 유지한다.
   - FAR/BCR/height/setback/sunlight/parking count/mass-stage parking은 deterministic solver가 판정한다.
   - LLM은 통과 판정을 하지 않는다.

2. 메스 목표는 “건축적 아이콘성 + 질서”다.
   - twisted/torqued tower
   - undercut podium
   - tapered tower over base
   - stacked shifted platforms
   - folded/sloped roof volume
   - carved atrium/courtyard
   - bridge/split mass with clear connector
   - monolithic slab cut by void

3. 금지:
   - 작은 조각을 많이 붙여 다양해 보이게 하기.
   - family label만 다양하고 실루엣이 비슷한 후보.
   - parking overlay나 color만 화려하고 mass geometry는 평범한 후보.
   - 법규 envelope stack을 그대로 건축 디자인이라고 부르는 것.

4. Agent 협업 목표:
   - `llm_architect_agent`: 책/논문/precedent principle을 primary/secondary language와 MassDSL proposal로 변환.
   - `parking_agent`: ground/podium/piloti/drive connectivity 요구를 실패 이유로 제시.
   - `massdsl_agent`: 제안 언어를 executable sequence로 고정.
   - `maas_geometry_agent`: source geometry가 실제 큰 제스처로 읽히는지 기록.
   - `grammar_critic_agent`: orderliness만 보지 말고 architectural ambition도 점검.
   - `review_agent`: legal pass와 design ambition pass를 분리해 보고.

5. 다음 구현은 단순 threshold 추가가 아니라 architectural ambition evidence를 추가해야 한다.
   - `architectural_ambition_evidence`
   - `reference_basis`
   - `precedent_principle`
   - `dominant_gesture`
   - `silhouette_strength`
   - `podium_tower_relationship`
   - `sectional_diagram_clarity`
   - `ground_carve_or_piloti_legibility`

사용자 지적 핵심:

- “MASS 다양하게”는 JSON family 숫자만 늘리는 게 아니라, PNG/3D에서 실제로 다른 매스 전략이 보여야 한다.
- 거의 전부 계단형/층상 박스로 보이면 실패다.
- `yfact=clamp(1.0 - 0.12 * progress, 0.76, 1.0)` 같은 한 줄만 문제가 아니라, 전체적으로 코드 상수와 heuristic이 매스를 찍어내면 하드코딩이다.
- LLM agent가 도와준다는 말은 설명 텍스트를 붙이는 게 아니라, agent proposal이 실제 geometry 후보/파라미터/비평 루프에 들어가야 한다는 뜻이다.

정확한 아키텍처 원칙:

1. 법규 envelope는 hard constraint다.
   - LLM이 법규 통과를 판정하거나 무시하면 안 된다.
   - BCR/FAR/height/sunlight/setback/parking count는 deterministic legal engine이 검증한다.

2. LLM/agent의 역할은 디자인 제안이다.
   - typology intent
   - MassDSL/grammar sequence
   - parameter proposal
   - 대안 간 tradeoff
   - 비평/수정 요청
   를 만든다.

3. optimizer/geometry engine의 역할은 solve/clip/reject/rank다.
   - agent proposal을 법규 envelope 안에서 해석한다.
   - 법규를 넘으면 clip 또는 reject한다.
   - 최종 geometry는 evidence와 함께 남긴다.

4. renderer/PNG는 꾸미는 곳이 아니다.
   - PNG가 다양해 보이게 overlay를 그리는 것은 목표가 아니다.
   - `mass_volumes`, `source_geometry`, `section_source_surfaces` 자체가 다른 형상이어야 한다.

5. 하드코딩 heuristic을 줄여야 한다.
   - `bend/embed/extrude/nest`를 단순 pinning하거나 임의 비율로 materialize하면 안 된다.
   - 고정 상수는 법규/수치 안정 bound로만 쓰고, 디자인 비율은 sequence/agent proposal/optimization result에서 와야 한다.
   - sweep도 코드 내부 상수보다 agent proposal + deterministic validation 기록으로 이동해야 한다.

현재 상태 진단:

- MAAS에 MassDSL/grammar critic/research_basis evidence는 붙었지만, 실제 geometry 결정권은 아직 `legal_mesh_optimizer.py`의 deterministic materializer가 많이 갖고 있다.
- 그래서 “멀티에이전트가 실질적으로 설계한다”기보다 “하드코딩 generator에 agent 설명을 붙인 상태”에 가깝다.
- 이 상태를 목표 달성으로 보면 안 된다.

다음 구현 목표:

- MassDSL/grammar/source_geometry proposal을 최종 `mass_volumes` 생성의 1차 source로 승격한다.
- `_section_materialized_polygon()`의 family별 임의 상수를 제거하거나 최소화한다.
- 법규 엔진은 agent proposal을 검증/clip/reject하고, 어떤 제안이 왜 수정됐는지 evidence로 남긴다.
- PNG 검증은 `uniqueFamilies` 같은 숫자뿐 아니라 “계단형 비율”, “동일 footprint 반복”, “보이드/분절/연결/핀/리본/중첩이 실제 volume geometry에 존재하는지”를 검사해야 한다.
- 기본 20장 결과에서 시각적으로도 최소한 다음 계열이 구분되어야 한다:
  - stepback/tower
  - courtyard/void
  - split/bridge
  - overlap/slab
  - diagonal connector
  - terrace ribbon
  - sloped roof
  - bend ribbon
  - embedded void
  - extruded fin
  - nested atrium/stack

## MAAS 논문/구현 재검토 메모

사용자 재지적:

- `upper_ratio: 0.80`, `width_ratio: 0.56` 같은 값을 JSON sequence에 추가하는 것도 하드코딩이다.
- “LLM agent가 설계한다”면 건축언어를 보고 verb 조합과 수치 후보를 제안해야지, 사람이 파일에 preset을 늘리는 방식이면 안 된다.
- 법규는 무조건 deterministic hard constraint여야 한다.

논문/자료 재대조 결론:

- EvoMass 계열은 typology-oriented massing generation + performance evaluation + optimization/exploration 구조다. 고정 sequence 수치를 많이 넣는 방식이 핵심이 아니다.
- SSIEA 계열은 island/steady-state evolutionary search로 다양성과 fitness를 같이 확보하는 구조다. 수치 preset 나열이 아니라 population/search/evaluation loop가 핵심이다.
- Design for Descent/d4descent는 shape grammar를 objective에 맞게 optimize하기 쉽게 만드는 구조다. grammar/objective/optimizer 분리가 핵심이다.

따라서 현재 구현의 문제:

- 논문이 모자란 것이 아니라, 구현이 논문 취지를 `deterministic_sequence_library`와 `parameter_sweep`으로 너무 축소했다.
- `grammar/data/maas_sequences.v0.json`, `_deterministic_fixture_parameter_sweeps()`, `source_geometry/compiler.py`, `morphology_operators.py`의 숫자들은 LLM 판단으로 포장하면 안 된다.
- 최종 20장을 채우려고 numeric sequence를 더 추가하는 것은 금지한다. 그건 목표와 반대다.

다음 구현 기준:

- agent proposal에는 `parameter_source`를 반드시 남긴다.
  - `llm_arch_language_proposal`: LLM/agent가 건축언어와 site/legal context를 보고 제안한 경우.
  - `deterministic_sequence_library`: 기존 preset/fixture에서 온 경우. 이 경우 `requires_llm_authoring=true`로 남겨 목표 미달임을 표시한다.
- geometry compiler는 agent proposal의 verb/parameter를 해석하고, 법규 solver는 clip/reject/rank만 한다.
- deterministic preset은 fallback/test fixture로만 허용한다. 최종 목표 상태에서는 기본 20개 후보의 디자인 파라미터가 agent proposal 또는 optimizer result provenance를 가져야 한다.

2026-07-01 루프 검토 상태:

- 최신 검토 기준으로 PNG/JSON을 억지로 20개 채우는 것은 금지한다.
- 이전에 sequence JSON에 numeric 후보를 추가하는 방식은 “DSL 파일로 옮긴 하드코딩”이므로 폐기했다.
- 현재 올바른 실패 상태는 다음과 같다:
  - source geometry 후보는 14/20 수준에서 멈춘다.
  - legacy fallback은 0으로 밀어내는 방향이 맞다.
  - 20개를 채우려면 LLM/agent proposal 또는 optimizer-generated parameter provenance가 필요하다.
  - deterministic fixture/sweep 후보는 `requires_llm_authoring=true`로 표시해야 한다.
- 다음 PNG 재생성은 “목표 달성 확인”이 아니라 “현재 실패 상태를 시각적으로 확인하는 산출물”이다.

2026-07-01 추가 루프 결과:

- `clone/MAAS/outputs/arr_agent_proposals/maas_arr_massdsl_proposals.v1.json`을 추가했다.
  - ARR 내부 JSON preset을 늘리는 대신, clone/MAAS 쪽 agent proposal artifact로 분리했다.
  - proposal source는 `clone_maas_codex_agent_arch_language_proposal`.
  - 법규 solver 역할은 `validate_clip_or_reject_only`로 고정했다.
- ARR loader/grammar/source compiler가 이 artifact를 읽어 `agent_...` MassDSL 후보를 만든다.
- `source_geometry/compiler.py`에서 `offset`, `array`, `reflect`, `stack` 계열을 여러 `SourceVolume`으로 물리화했다.
  - 이전처럼 대부분 `lower + upper` 두 박스로 접히는 문제를 일부 완화했다.
- 최신 PNG/JSON 산출물:
  - `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
  - `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
- 최신 수치:
  - count 20
  - legalPass 20/20
  - sourceGeometryUsed 20/20
  - legacyFallback 0
  - PNG freshness/색상 검증 pass
  - agent-authored 후보 11/20
  - deterministic grammar 후보 8/20
  - `llmAuthoringGap` 8~9 수준으로 아직 남음
  - uniqueShapes 20은 통과했지만 uniqueFamilies 14, uniqueSections 10으로 gate 실패
- 결론:
  - “20장 PNG”와 “법규 envelope 내 source geometry”는 달성했다.
  - 그러나 논문 기준의 agent-led diversified exploration은 아직 미달이다.
  - 현재 구현은 AIDL/Design-for-Descent식 `agent proposal -> solver validation` 방향으로 이동했지만,
    CAADRIA류 optimization/clustering loop와 visual critic이 없어서 최종 다양성이 충분하지 않다.

논문/방법론과 현재 코드의 차이:

## 2026-07-07 MAAS Mass-Language Review Reset

사용자 최신 지적:

- 현재 PNG는 이전보다 다양성 수치는 좋아졌지만, 일부 메스가 너무 불규칙하다.
- “언어가 섞인다”는 것은 아무 조각을 더 붙이는 것이 아니다.
- `branch + roof`, `bar + courtyard`, `split + diagonal`, `bend + overlap`처럼 두 개 이상의 건축 언어가 읽히는 조합이어야 한다.
- 단순히 `mass_language` 이름을 늘리거나 `source_volume` 개수를 늘려 verifier를 통과하는 것은 연구 목표가 아니다.

업데이트된 목표:

1. 법규 envelope는 계속 hard constraint다.
   - FAR/BCR/height/setback/sunlight/parking은 deterministic solver가 검증한다.
   - LLM은 법규를 판정하지 않고, 설계 언어와 후보 파라미터를 제안한다.

2. 메스 다양성의 기준을 “불규칙성”이 아니라 “체계적 언어 조합”으로 바꾼다.
   - primary_language: 후보의 주된 질서. 예: bar, courtyard, split, bend, nested, roof.
   - secondary_language: 주 언어를 수정하는 보조 질서. 예: notch, bridge, roof cap, court liner, offset spine.
   - 하나의 후보는 최소한 `primary_language + secondary_language + legal_repair_trace`를 evidence로 가져야 한다.

3. 코드에서 임의 helper piece를 늘리는 방식은 중단한다.
   - volume count를 맞추기 위한 조각 추가는 금지한다.
   - 필요한 경우에도 “secondary language overlay”처럼 건축적으로 설명 가능한 부속이어야 한다.
   - PNG가 복잡해지는 것과 설계 언어가 풍부해지는 것은 다르다.

4. 논문은 한 편씩 가져다 붙이지 말고 체계적으로 재검토한다.
   - Paper -> method requirement -> code responsibility -> verifier gate -> PNG evidence 순서로 정리한다.
   - EvoMass/SSIEA는 다양성 보존 search/selection 구조로 읽는다.
   - AIDL/CAD-HLLM 계열은 LLM -> DSL -> solver 검증 구조로 읽는다.
   - Shape grammar / graph grammar 계열은 primary/secondary language composition의 근거로 읽는다.
   - Constraint-aware diffusion/optimization 계열은 hard constraint projection/repair 구조로 읽는다.

다음 루프 원칙:

- 먼저 literature matrix를 보강한다.
- 그 다음 코드 변경은 논문별 requirement가 어느 verifier를 바꾸는지 명확할 때만 한다.
- 새 PNG 검증은 다음을 포함해야 한다:
  - 법규 pass
  - parking mass-stage pass
  - primary/secondary language evidence
  - compositional secondary layer evidence
  - 과도한 irregular fragments 제한
  - 동일 계단/동일 height/동일 role pattern 반복 제한

- AIDL 2025 / CAD command 계열:
  - 요구: LLM이 구조화된 DSL/command를 제안하고 solver가 constraint를 처리.
  - 현재: clone/MAAS agent proposal artifact는 붙었지만 live LLM loop는 아니다.
- Design for Descent / d4descent:
  - 요구: grammar/objective/optimizer 분리와 objective-driven search.
  - 현재: grammar와 legal solver 분리는 일부 됐지만 objective optimization loop는 없다.
- CAADRIA 2025 massing optimization:
  - 요구: shape grammar + multi-objective scoring + clustering/selection.
  - 현재: scoring/selection은 있으나 clustering medoid나 visual diversity critic은 약하다.
- 결론:
  - 논문이 틀린 것이 아니라, 구현이 아직 “proposal artifact + deterministic selector” 단계다.
  - 다음 루프는 missing 9개 agent가 일반 요청에서 왜 selection pool에 충분히 들어오지 않는지 수정하고,
    deterministic grammar 8개를 agent-authored/optimizer-provenance 후보로 대체해야 한다.

추가 문헌 확인 필요 메모:

- 2026-07-01 검색으로 확인한 최신 축:
  - AIDL, "A Solver-Aided Hierarchical Language for LLM-Driven CAD Design" (arXiv 2502.09819 / CGF 2025)
    - LLM은 고수준 계층 DSL을 만들고, 기하/공간 제약은 solver가 맡는다.
    - 우리 코드의 방향성은 맞지만, 현재는 live LLM planner가 아니라 static proposal artifact다.
  - CAD-Assistant (ICCV 2025)
    - VLLM planner + CAD tool execution + geometry state feedback의 반복 구조.
    - 우리 코드에는 tool-execution feedback loop/visual critic이 아직 없다.
  - CAD-HLLM / hierarchical executable CAD generation 계열
    - CAD command를 계층적으로 계획한다.
    - 우리 MassDSL도 계층 계획으로 승격해야 하며, 단순 sequence preset이면 부족하다.
  - CAADRIA 2025 "Performance-Based Urban Massing Generation and Optimization"
    - EvoMass 기반 massing variation + layout variation + performance optimization.
    - 우리 코드에는 performance objective 기반 population/search와 clustering selection이 아직 약하다.
  - CAADRIA 2026 "A Generative Pre-Design Framework..."
    - early-stage problem-framing과 optimization 재해석.
    - 우리 goal은 단순 20개 산출보다 설계 문제 framing + 후보 탐색 루프가 되어야 한다.

- 따라서 다음 판단:
  - 최신 논문을 "봤다" 수준으로 끝내면 안 된다.
  - 각 논문별로 `요구 구조 -> 현재 코드 위치 -> 부족한 구현 -> 테스트/PNG 증거` 표를 만들어야 한다.
  - 특히 AIDL/CAD-Assistant 기준으로는 `LLM/agent proposal -> tool execution -> geometry feedback -> revise` 루프가 필요하다.
  - EvoMass/CAADRIA 기준으로는 `population/search -> legal/performance scoring -> clustering/medoid selection` 루프가 필요하다.
- 위 표는 `docs/ai-session-memory/MAAS_RESEARCH_CODE_MATRIX.md`에 생성했다.

2026-07-01 추가 검증 루프 결과:

- 섹션 프로필 다양성 실패 원인은 법규 solver가 아니라 `_section_profile_from_sequence()`의 우선순위였다.
  - `split`/`cave`가 먼저 나오면 뒤의 `diagonal_connect`, `offset`, `reflect`, `array` 의도가 section profile에 반영되지 않았다.
  - `diagonal_connect`, `terrace_link`, `sloped_roof_mass`는 generic split/cut보다 먼저 section-defining verb로 판정하도록 고쳤다.
  - agent proposal의 `offset`, `reflect`, `array`도 별도 section kind로 기록한다.
- 최신 산출물:
  - `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
  - `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
- 최신 검증:
  - JSON verifier: pass
  - PNG verifier: pass
  - focused Django tests: pass
  - count 20
  - legalPass 20/20
  - parkingCountSatisfied 20/20
  - sourceGeometryUsed 20/20
  - legacyFallback 0
  - agentAuthoredEvidence 19
  - solverAuthoredEvidence 1
  - llmAuthoringGap 0
  - uniqueFamilies 15
  - unique section kinds 15
- 이 통과는 “static agent proposal artifact + deterministic legal solver” 기준의 통과다.
  - 아직 CAD-Assistant식 live `proposal -> execute -> observe -> revise` loop는 아니다.
  - 아직 EvoMass/CAADRIA식 population optimization + clustering/medoid selection loop도 아니다.
  - 따라서 다음 목표는 PNG를 더 찍는 것이 아니라 live loop artifact와 optimizer provenance를 붙이는 것이다.

2026-07-01 LLM loop 구현 메모:

- OpenAI Responses API + Structured Outputs 기반 MassDSL population loop를 구현했다.
  - schema: `arr.maas.llm_massdsl_batch.v1`
  - 최소 language palette 30개
  - 최소 combination rule 10개
  - 최소 raw MassDSL candidate 120개
  - 후보는 `llm_...` sequence로 컴파일되고 `parameter_source=llm_arch_language_proposal`을 가진다.
- 기존 static clone/MAAS artifact는 fallback/test fixture 성격으로 남기고, 새 verifier는 LLM loop artifact 없이는 통과하지 않도록 강화했다.
- 최종 review set 품질 gate:
  - FAR < 20% 또는 BCR < 8%인 LLM 후보는 weak candidate로 표시한다.
  - final 20개에는 weak LLM 후보를 최대 1개만 허용한다.
- 실제 렌더 시도 결과:
  - strict JSON schema 오류는 수정했다.
  - OpenAI API에는 도달했으나 HTTP 429 `insufficient_quota`로 중단됐다.
  - 따라서 최신 LLM-loop PNG/JSON 검증은 아직 외부 quota 때문에 미완료다.
  - 이 상태에서 static fallback으로 pass 처리하면 안 된다.

2026-07-02 implementation loop 메모:

- 사용자가 지적한 핵심은 맞다: `upper_ratio`, `lower_floor_fraction`,
  `atrium_scale`류 수치가 compiler 내부 default로 숨어 있으면 LLM/agent-led
  설계라고 부르면 안 된다.
- 이번 루프 기준:
  - 법규 envelope/BCR/FAR/height/parking은 계속 hard constraint다.
  - LLM/agent는 typology, MassDSL 조합, 설계 수치를 제안한다.
  - ARR compiler/legal solver는 validate/clip/reject와 provenance 기록을 맡는다.
- 구현 변경:
  - source geometry signature에 `parameter_provenance`와
    `parameter_default_count`를 추가했다.
  - LLM 후보는 compiler default가 너무 많으면 final review에서 weak/reject로
    분류된다.
  - final 20 selection은 courtyard/void, array/cluster, split/connector,
    bar/bend/interlock/overlap, branch/pinch/embed/extrude/nest, roof 계열 quota를
    먼저 채운다.
  - stepback/terrace/taper/grade dominant family는 final 20에서 최대 3개로 cap한다.
  - `visual_diversity_evidence.stepback_dominant`를 추가해 PNG/JSON 검증에서
    계단형 과다 여부를 직접 볼 수 있게 했다.
- 새로 clone한 reference code:
  - `clone/aidl`: hierarchical solver-aided DSL reference.
  - `clone/CAD-Assistant`: tool-augmented CAD execution/verification loop reference.
- 아직 남은 목표:
  - 실제 LLM-loop PNG를 다시 생성해서 legalPass 20/20과 visual family quota를
    JSON/PNG로 확인해야 한다.
  - compiler default가 남는 typology는 다음 루프에서 LLM prompt/schema 또는
    legal-derived parameter policy로 더 줄여야 한다.

2026-07-02 hardcoding audit follow-up:

- `source_geometry/compiler.py`에서 남아 있던 raw `params.get(..., default)`
  계열을 provenance helper로 정리했다.
  - `notch/cave/split/bar/branch/pinch/bend/embed/extrude/nest/stack/offset/array/reflect/interlock/overlap/taper/grade/shift/inset/expand`
    의 축, 비율, shift, upper/lower fraction 기본값은 이제 authored/default
    출처가 `source_signature.parameter_provenance`에 남는다.
  - `distance`, `size`, `depth`, `gap`, `spacing`, `face`, `top_ratio` 같은
    alias도 canonical key와 alias key가 같이 기록된다.
- 법규 관련 숫자는 LLM이 정하는 값이 아니다.
  - BCR/FAR/height/parking/envelope는 deterministic legal gate로 유지한다.
  - LLM/agent가 제안할 것은 typology와 설계 파라미터이고, compiler/legal
    solver는 validate/clip/reject와 출처 기록을 담당한다.
- `_final_design_balanced_selection()` 보강:
  - agent/LLM 후보도 source geometry만 있으면 통과하지 않고,
    reviewable architectural mass gate와 parking fail gate를 반드시 통과한다.
  - connector/source-geometry 보강 교체도 stepback cap, 중복 shape cap,
    weak LLM cap, same-family cap을 우회하지 않게 검증한다.
- 새 테스트:
  - 모든 주요 건축언어 verb가 default provenance를 기록하는지 확인.
  - final 20 selection에서 stepback dominant <= 3, weak LLM <= 1, reviewable
    LLM slot >= 4가 유지되는지 확인.

2026-07-02 final loop pass:

- LLM MassDSL loop를 full mode로 실행해서 최신 PNG/JSON을 갱신했다.
  - `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
  - `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
- Strict verifier 결과:
  - JSON verifier: pass
  - PNG verifier: pass
  - count 20
  - legalPass 20/20
  - parkingCountSatisfied 20/20
  - sourceGeometryUsed 20/20
  - legacyFallback 0
  - llmLoopStatus compiled
  - raw candidates 141
  - compiled sequences 140
  - compiled variants 90
  - LLM-authored evidence 19
  - solver-authored legal envelope anchor 1
  - LLM authoring gap 0
  - uniqueFamilies 18
  - uniqueSections 18
  - stepbackLike 1
  - weakLlmCandidates 0
- 구현상 핵심 변경:
  - LLM structured response batch가 깨질 때 retry한다.
  - LLM이 `void_ratio`, `magnitude_ratio`, `pitch_proxy` 같은 건축언어식
    alias를 내도 canonical MAAS parameter로 정규화한다.
  - `typology`/candidate name에서 declared source family를 읽어 source
    signature와 section profile에 반영한다.
  - 필수 family coverage supplement를 LLM population 앞쪽에 추가해
    compile limit 전에 courtyard/void/split/array/offset/reflect/bar/bend/
    interlock/overlap/branch/pinch/embed/extrude/nest/roof 계열이 모두
    법규 solver 검증을 받도록 했다.
- 해석:
  - 법규/BCR/FAR/height/parking/envelope는 계속 deterministic hard gate다.
  - LLM/agent는 설계언어와 파라미터 후보를 제안하고, ARR compiler/legal
    solver가 출처 기록, 보강, clipping/reject, 최종 evidence selection을 맡는다.

2026-07-02 visual stair bias follow-up:

- 사용자가 지적한 “verifier는 통과하지만 눈으로는 아직 계단형이 많다”는
  문제가 맞다.
- 원인:
  - 법규 solver가 만든 `mass_volumes`를 PNG fallback renderer가 모두 층별
    판으로 강하게 그려 비계단 family도 계단처럼 보였다.
  - `step_envelope`가 섞인 LLM 후보가 source family는 `offset`이어도
    시각적으로 stair 후보로 보였다.
- 조치:
  - JS renderer와 Python fallback renderer 모두에서 비계단 family의
    `source_geometry_stack_*` 중간층을 숨기고 첫/마지막 실루엣 위주로 렌더한다.
  - `legal_layered`, `stepback_tower`, 실제 `stepped_tower`는 보존한다.
  - final selection 품질 키에 `step_envelope`/`stepback`/`stair` visual penalty를
    추가했다. 단 `legal_layered`, `sloped_roof`, `nest`는 합법/의도된 단면으로 예외.
- 재검증:
  - PNG verifier: pass
  - JSON verifier: pass
  - raw visual volumes 80 -> rendered visual volumes estimate 73
- 남은 과제:
  - renderer만으로는 한계가 있다. 다음 루프는 materializer 자체에서
    `bar/courtyard/offset/reflect/branch/pinch/embed/extrude` family를 floor-plate
    step이 아닌 연속 실루엣/void/bridge 중심으로 더 강하게 materialize해야 한다.

2026-07-02 materializer stair reduction loop:

- renderer만 줄이는 것이 아니라 backend source geometry compiler를 수정했다.
  - `_layout_volumes()`에서 `stack_spec`가 있어도 source family가
    `nest/stepback_tower/sloped_roof`가 아니면 stack level을 최대 2개로 제한한다.
  - declared LLM family를 volume layout 전에 계산해서 stack cap에 반영한다.
- 결과:
  - JSON verifier: pass
  - PNG verifier: pass
  - legalPass 20/20
  - parkingCountSatisfied 20/20
  - uniqueFamilies 18
  - uniqueSections 18
  - llmAuthoredEvidence 19
  - stack volumes 9 -> 3
  - total rendered/backend volumes 70 -> 64
- 최신 PNG를 직접 확인했다.
  - 계단감은 확실히 줄었다.
  - 남은 강한 계단은 `legal_layered_max`와 `nest`처럼 의도된 단면 쪽이다.
  - 다음 단계는 `legal_layered_max` anchor를 계산용으로만 두고 첫 화면/PNG에서는
    덜 강조하거나 별도 “legal envelope anchor” 스타일로 렌더하는 것이다.

2026-07-02 second visual audit:

- 최신 PNG `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`를 다시 직접 확인했다.
- 건축언어 다양성은 숫자상 18 family / 18 section이고, 화면상으로도
  `array_cluster`, `offset_twin_bar`, `courtyard_atrium`, `reflected_court_pair`,
  `sloped_roof`, `bend_ribbon`, `overlap_slabs`, `nested_stack`, `branch_taper`,
  `diagonal_connector`, `bar_notch_terrace`, `notched_void`, `pinched_waist`,
  `embedded_void`, `extruded_fin`, `split_bridge`, `cross_interlock`이 분리되어 보인다.
- 아직 부족한 부분:
  - `legal_layered_max`는 법규 최대치 anchor라서 계단형 인상이 강하다.
  - `sloped_roof`/`overlap` 일부는 roof/shell 언어가 실제 경사면보다 층판으로 보인다.
  - `void/courtyard/embed`는 법규 envelope 안에 있지만 PNG fallback에서는 void depth가
    아직 약하게 보인다.
- 다음 루프 기준:
  - 법규 envelope/BCR/FAR/height/parking은 계속 hard constraint다.
  - 다양성 개선은 법규 수치를 LLM이 바꾸는 방식이 아니라, LLM/agent가 건축언어 조합을
    더 풍부하게 제안하고 compiler가 roof/void/bridge/split 실루엣을 더 실제 geometry로
    물리화하는 방식으로 해야 한다.

2026-07-02 follow-up fix loop:

- 추가 수정:
  - `source_geometry/compiler.py`
    - `sloped_roof`는 `roof_plinth` + `sloped_roof_plane` role로 물리화한다.
    - `array/offset/reflected_pair/overlap`은 unit마다 base/upper 2단 반복을 만들지 않고
      unit/slab 단일 매스로 내보낸다.
    - `nest/stepback_tower/sloped_roof`가 아닌 stack verb는 다단 stack으로 물리화하지 않는다.
  - `legal_mesh_optimizer.py`
    - authored LLM/agent 후보가 충분하면 `legal_layered_max`를 1번 카드로 고정하지 않고,
      solver provenance anchor로 6번 근처에 유지한다.
  - PNG fallback renderer
    - `sloped_roof_plane`과 `overlap_slab` role을 다른 색/선 두께로 읽히게 했다.
- deterministic fallback PNG 재생성 결과:
  - latest PNG: `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
  - PNG verifier: pass
  - legalPass 20/20
  - parkingCountSatisfied 20/20
  - legal anchor index: 1 -> 6
  - total volumes: 60 -> 57
  - stack volumes: 9 -> 3
- LLM full loop:
  - `MAAS_LLM_TARGET_COUNT=120` full run은 `/design/maas/legal-variants/` 900초 curl timeout으로 실패했다.
  - `MAAS_LLM_TARGET_COUNT=40` quick run도 OpenAI read timeout으로 실패했다.
  - 따라서 이번 최신 PNG는 LLM-authored verifier용 산출물이 아니라 geometry/selection fix 확인용 deterministic fallback 산출물이다.

2026-07-02 LLM timeout fix loop:

- 실패 원인:
  - LLM이 핵심인데 이전 구조는 OpenAI Responses API에 큰 strict JSON batch를 한 번에 요청했다.
  - renderer script가 `MAAS_LLM_BATCH_SIZE`, `MAAS_LLM_BATCH_RETRIES`, `MAAS_LLM_MAX_OUTPUT_TOKENS`를
    backend payload로 넘기지 않아 backend가 기본값 batch_size=30/retries=3으로 실행했다.
  - 그 결과 30-candidate structured JSON batch가 read timeout으로 죽고, required loop가 400을 반환했다.
- 수정:
  - batch schema를 가볍게 했다. batch별 palette/rules 최소값은 낮추고, 전체 aggregate에서 30/10을 맞춘다.
  - OpenAI read timeout을 batch error로 잡고 다음 batch로 넘어가게 했다.
  - timeout coverage repair는 endpoint를 살리는 보조 장치로만 남기고 artifact에 개수를 기록한다.
  - renderer payload에서 `batch_size`, `batch_retries`, `max_output_tokens`를 backend로 넘긴다.
  - artifact에 실제 적용된 `target_count`, `batch_size`, `batch_retries`, `max_output_tokens`,
    `openai_batch_error_count`, `timeout_coverage_repair_count`를 남긴다.
- 최종 검증:
  - 실행 설정: target_count=120, batch_size=3, batch_retries=1, timeout=60s, max_output_tokens=3000.
  - JSON verifier: pass
  - PNG verifier: pass
  - legalPass 20/20
  - parkingCountSatisfied 20/20
  - llmLoopStatus compiled
  - raw candidates 137
  - compiled sequences 137
  - compiled variants 90
  - language palette 311
  - combination rules 87
  - OpenAI batch errors 2
  - timeout coverage repair 17
  - actual OpenAI candidate estimate 120
  - stack volumes 3
  - total volumes 55

2026-07-05 LLM final-selection audit:

- 재검토에서 발견한 문제:
  - 전체 LLM population에는 실제 OpenAI 후보가 충분했지만, final 20 selection이
    `llm_coverage_repair_*` 후보를 실제 OpenAI 후보와 같은 우선순위로 취급했다.
  - 그 결과 이전 최신 산출물은 final 20 중 direct OpenAI shape가 4개뿐이고,
    coverage repair가 15개였다.
- 수정:
  - `legal_mesh_optimizer.py`
    - `llm_coverage_repair` 후보와 direct OpenAI LLM 후보를 분리했다.
    - final selection은 direct OpenAI 후보를 먼저 채우고, coverage repair는 부족한
      family를 메우는 후순위 후보로만 사용한다.
    - unique family가 15 미만이면 중복 family 후보를 빠진 family 후보로 교체한다.
    - 2026-07-09에 이 정책은 superseded 되었다:
      `legal_layered_max` solver anchor는 내부 법규/evidence로 유지하되,
      authored/reviewable 후보가 충분하면 final 20 리뷰 보드에는 강제하지 않는다.
  - `verify-maas-20-alt-json.cjs`
    - actual OpenAI candidate estimate를 검사한다.
    - final 20 direct OpenAI LLM 후보 수와 coverage repair 후보 수를 검사한다.
- 최종 검증:
  - JSON verifier: pass
  - PNG verifier: pass
  - legalPass 20/20
  - parkingCountSatisfied 20/20
  - llmRawCandidates 140
  - llmCompiledSequences 135
  - llmCompiledVariants 90
  - actual OpenAI candidate estimate 123
  - final direct OpenAI LLM 12
  - final coverage repair LLM 7
  - uniqueFamilies 15
  - solverAuthoredEvidence 1
  - legal anchor index 6
  - stack volumes 3
  - total volumes 49

2026-07-06 mass-language decomposition audit:

- 사용자 지적이 맞았다:
  - 최신 산출물은 family/section 숫자는 다양했지만 final 20 중 15개가 `2-volume/2-tier`였다.
  - 원인은 LLM이 낸 `courtyard/split/interlock/branch/embed/extrude` 언어가 부족해서가 아니라,
    `source_geometry/compiler.py`의 `_layout_volumes()`가 대부분의 비스택 언어를 다시
    `lower/upper` 두 덩어리로 접는 구조였다.
  - 방금 처음 넣은 family별 volume decomposition에도 `0.12`, `0.18`, `0.30` 같은 임의
    geometry 상수가 들어가 있었고, 이는 법규 하드코딩은 아니지만 건축언어 해석 하드코딩이다.
- 수정:
  - family별 plan-volume decomposition을 유지하되, 크기/각도/축/분절은 LLM/grammar call의
    `ratio`, `axis`, `angle`, `guest_scale`, `trunk_ratio`, `arm_ratio`, `slab_ratio`,
    `gap_ratio`, `bridge_ratio`, `size`, `length`, `upper_ratio`, `lower_floor_fraction`을 우선 읽는다.
  - 값이 없거나 잘못된 경우에만 bounded fallback을 사용한다.
  - 법규 수치는 LLM이 정하지 않는다. LLM source geometry는 후보 언어만 만들고,
    FAR/BCR/height/parking은 기존 legal optimizer와 verifier가 envelope 안에서 검증한다.
  - JSON verifier에 `twoTierMasses`, `threePlusVolumeMasses`, `sourceVolumeRoleDiversity`
    실패 조건을 추가했다.
- 최종 검증:
  - latest PNG: `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
  - latest JSON: `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
  - JSON verifier: pass
  - PNG verifier: pass
  - legalPass 20/20
  - parkingCountSatisfied 20/20
  - llmLoopStatus compiled
  - raw candidates 141
  - compiled sequences 141
  - compiled variants 90
  - actual OpenAI candidate estimate 124
  - OpenAI batch errors 0
  - final direct OpenAI LLM 15
  - final coverage repair LLM 4
  - twoTierMasses 15 -> 3
  - threePlusVolumeMasses 5 -> 17
  - sourceVolumeRoleDiversity 15 -> 37
- 남은 약점:
  - roof/reflected_pair/offset 일부는 여전히 2-volume이다.
  - coverage repair 중 일부는 parking overlay가 크게 보여 mass 언어가 덜 읽힌다.
  - 다음 루프에서는 roof/offset/reflected_pair도 source decomposition을 더 풍부하게 만들고,
    주차/piloti 시각화는 mass-stage pass와 permit-final review를 분리해서 렌더링해야 한다.

2026-07-06 continued verification loop:

- LLM 사용 확인:
  - 최신 산출물의 `llm_proposal_loop.schema_version`은 `arr.maas.llm_massdsl_batch.v1`.
  - `status=compiled`, `model=gpt-5.4-mini`.
  - raw candidates 138, compiled sequences 138, compiled variants 90.
  - actual OpenAI candidate estimate 121.
  - final direct OpenAI LLM 15, final coverage repair LLM 4.
  - OpenAI batch errors 0.
- 추가 수정:
  - `offset/reflected_pair`가 layout unit을 잃어도 lower/upper fallback으로 떨어지지 않도록
    bridge spine + shared core를 추가했다.
  - `sloped_roof`는 plinth + low/high roof plane으로 분해했다.
  - `nest`는 outer shell + inner volume + liner spine으로 분해했다.
  - `array_cluster`는 unit collapse가 나도 LLM/grammar의 `n/count`, `unit_scale`,
    `spacing_ratio`, `axis`를 읽어 최소 3 cell source volume으로 분해한다.
  - JSON verifier 기준을 `twoTierMasses == 0`까지 강화했다.
- 최종 검증:
  - latest PNG: `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
  - latest JSON: `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
  - JSON verifier: pass
  - PNG verifier: pass
  - legalPass 20/20
  - parkingCountSatisfied 20/20
  - llmLoopStatus compiled
  - raw candidates 138
  - compiled sequences 138
  - compiled variants 90
  - actual OpenAI candidate estimate 121
  - final direct OpenAI LLM 15
  - final coverage repair LLM 4
  - twoTierMasses 0
  - threePlusVolumeMasses 20
  - sourceVolumeRoleDiversity 44
- 남은 약점:
  - PNG에서 마지막 sloped_roof coverage repair는 parking/drive overlay가 강해 mass 언어보다
    주차 검토가 먼저 보인다.
  - 다음 루프에서는 parking/piloti를 mass-stage evidence와 permit-final review로 분리해서
    mass preview에서는 건축언어가 먼저 읽히게 해야 한다.

2026-07-06 research-methodology memory:

- 사용자가 강조한 핵심:
  - 목표는 단순히 PNG를 다양하게 뽑는 것이 아니라, “mass 방법론” 자체가 연구 주제가 되어야 한다.
  - 임의 도형을 많이 넣는 방식은 실패다. 각 mass는 건축언어, 생성 규칙, 설계 파라미터,
    법규 envelope 검증, 시각 증거가 연결되어야 한다.
  - 사용자가 이전에 많이 준 mass 방법론/건축언어 메모리는 계속 기준으로 삼아야 한다.
- 현재 방법론의 올바른 구조:
  - LLM: 건축언어 조합과 의도, 파라미터 후보를 제안한다.
  - Grammar/MassDSL: LLM 제안을 검증 가능한 verb sequence와 source geometry로 컴파일한다.
  - Architectural rules: family별로 shape grammar를 가진다.
    예: courtyard=ring/opening rule, split=wing/gap/bridge rule,
    interlock=crossing bars/knuckle rule, branch=trunk/arm hierarchy rule,
    array=cell count/spacing/rhythm rule, roof=ridge axis/low-high plane rule.
  - Legal optimizer: FAR/BCR/height/parking/sunlight 등 법규 envelope 안으로만 materialize한다.
  - Verifier/PNG: 결과가 왜 그 형태인지 family, rule, params, legal pass, source volumes로 증명한다.
- 금지:
  - 법규 수치를 LLM이 임의 결정하면 안 된다.
  - 컴파일러가 건축언어 파라미터를 고정 상수로 대신 결정하면 안 된다.
  - 단순 lower/upper 2층 fallback으로 architectural language를 접으면 안 된다.
  - “다양해 보이는 도형”만 만들고 생성 규칙/증거를 남기지 않으면 안 된다.
- 다음 구현 방향:
  - 각 family별 rule evidence를 JSON에 명시한다.
    `rule_name`, `rule_inputs`, `llm_authored_params`, `fallback_params`,
    `legal_clipping_action`, `source_volume_roles`, `design_rationale`.
  - PNG 카드에도 최소한 family/rule/source volume count가 읽히게 한다.
  - verifier는 `twoTierMasses`, role diversity뿐 아니라 rule evidence 누락도 실패시킨다.
  - 최종 연구 서술은 “LLM-authored architectural language + rule-based MassDSL compiler
    + legal-envelope constrained optimization + visual/verifiable evidence loop”로 정리한다.

2026-07-06 hardcoding audit:

- 결론:
  - “하드코딩이 없다”는 말은 현재 코드 기준으로 틀리다.
  - 법규 수치(FAR/BCR/height/parking)를 임의로 박아 넣은 하드코딩은 아니다.
  - 하지만 `source_geometry/compiler.py`에는 건축언어를 도형으로 번역하기 위한 fallback,
    clamp range, 비례값, height-band offset이 아직 많다.
- 현재 구조:
  - LLM/grammar 파라미터가 있으면 우선 사용한다.
  - 없거나 invalid이면 compiler fallback을 사용한다.
  - fallback은 법규가 아니라 architectural prior이지만, 지금처럼 코드 안에 박혀 있으면
    “agent가 판단했다”기보다 “compiler가 보정했다”에 가깝다.
- 문제 지점:
  - `_profile_value(... fallback, low, high)`의 fallback/low/high가 코드 상수다.
  - `_height_band()`의 split/top/bottom clamp가 코드 상수다.
  - family별 decomposition의 최소 bar width, ring depth, bridge width, angle fallback,
    cell spacing, source volume count가 일부 코드 상수다.
  - `llm_proposals.py`의 canonical examples와 timeout coverage repair templates도
    fixed prior/template 성격이 강하다.
- 연구 방법론으로 만들려면:
  - 이 값들을 “숨은 하드코딩”이 아니라 명시적 `architectural_rule_prior`로 승격해야 한다.
  - rule prior는 JSON/YAML/registry에 분리하고, 각 prior의 근거를 남겨야 한다.
  - final JSON에는 각 후보마다 `param_source`를 분리해서 기록해야 한다:
    `llm_authored`, `grammar_default`, `rule_prior`, `legal_solver`, `repair_fallback`.
  - verifier는 `rule_prior` 비율이 너무 높거나 `llm_authored` 파라미터가 부족하면 실패해야 한다.
  - PNG/HTML에는 “이 mass가 어떤 rule과 어떤 authored params로 만들어졌는지”가 보여야 한다.
- 다음 구현 방향:
  - compiler 내부 numeric prior를 외부 `architectural_rule_priors` registry로 이동.
  - candidate별 `rule_evidence`를 생성:
    `rule_name`, `family`, `authored_params`, `prior_params`, `invalid_params`,
    `geometry_actions`, `legal_actions`, `volume_roles`.
  - verifier에 hardcoding audit metric 추가:
    `llmAuthoredParamRatio`, `rulePriorParamRatio`, `fallbackParamCount`,
    `missingRuleEvidence`.

2026-07-06 prompt/harness audit and fix:

- 외부 기준 확인:
  - OpenAI Structured Outputs는 schema 준수를 보장하지만, schema가 약하면 도메인 품질은 보장하지 않는다.
  - OpenAI Evals/cookbook 및 LLM eval community 흐름은 spot check/prompt tweak가 아니라
    structured output + dataset/eval + regression gate + trace/diagnosis loop를 요구한다.
  - 최근 eval/harness 논문 흐름도 Define/Test/Diagnose/Fix, CI gate, observability를 강조한다.
- 코드 리뷰 결론:
  - 기존 `llm_proposals.py`는 Structured Outputs를 사용했지만 schema가
    `architectural_language/rationale/calls` 중심이라 rule evidence를 강제하지 못했다.
  - prompt의 canonical examples가 오히려 hidden prior처럼 작동했고,
    verb별 필수 파라미터 누락을 compile 전에 막지 못했다.
  - 최신 JSON에서 `parameter_default_ratio` 평균 0.439, 최대 0.688,
    high-default 후보 14개, rule evidence 0/20이었다.
- 수정:
  - LLM schema에 `rule_name`, `rule_inputs`, `expected_geometry_actions`를 필수로 추가했다.
  - prompt에 verb별 required canonical params를 명시하고,
    누락 시 legal review 전에 reject한다고 명시했다.
  - `_validate_call_params()`를 추가해 LLM/repair candidate의 non-base verb 필수 파라미터를
    compile 전에 검사한다.
  - x/y axis만 허용하고 z-axis extrude를 reject한다.
  - coverage repair templates도 새 required params와 rule evidence를 갖도록 보강했다.
  - JSON verifier에 rule evidence, authored/default parameter ratio, high-default 후보 수를
    regression gate로 추가했다.
- 최종 검증:
  - latest PNG: `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
  - latest JSON: `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
  - JSON verifier: pass
  - PNG verifier: pass
  - legalPass 20/20
  - parkingCountSatisfied 20/20
  - llmLoopStatus compiled
  - raw candidates 142
  - compiled sequences 142
  - rejected sequence count 0
  - actual OpenAI candidate estimate 125
  - final direct OpenAI LLM 17
  - final coverage repair LLM 2
  - twoTierMasses 0
  - threePlusVolumeMasses 20
  - sourceVolumeRoleDiversity 49
  - ruleEvidence 19/19 non-solver candidates
  - authoredParamEvidence 20/20
  - avgParameterDefaultRatio 0.058
  - maxParameterDefaultRatio 0.182
  - highDefaultParamCandidates 0
- 남은 약점:
  - compiler 내부 architectural priors는 아직 코드에 있다.
  - 다음 루프에서는 priors를 `architectural_rule_priors` registry로 분리하고,
    candidate별 `rule_prior_params`와 `llm_authored_params`를 더 구조화해서 저장해야 한다.
  - PNG 카드에서 rule evidence가 아직 직접 보이지 않는다. HTML/PNG card에 rule name과
    authored/default ratio를 노출해야 한다.

2026-07-07 rule-prior registry / harness upgrade:

- `ARR/backend/design/maas/source_geometry/rule_priors.py`를 추가했다.
  - compiler 내부에 숨어 있던 비법규 geometry fallback 수치를 `architectural_rule_priors` registry로 분리했다.
  - 포함 family: courtyard, void_notch, split, diagonal_connect, array_cluster, offset, reflected_pair, slender_bar, bend, interlock, overlap, branch, pinch, embed, extrude, nest, sloped_roof.
  - 각 rule은 required/optional inputs, prior defaults, bounds, height band profile, geometry actions, rationale를 가진다.
- `source_geometry/compiler.py`는 source geometry 생성 시 structured `rule_evidence`를 남긴다.
  - LLM/agent가 낸 값은 `llm_authored_params`.
  - registry fallback 값은 `rule_prior_params`.
  - 잘못된 수치는 `invalid_params`.
  - 법규 truth는 바꾸지 않았다. FAR/BCR/height/parking은 계속 legal optimizer/parking verifier가 hard constraint다.
- `SourceMass.signature()`와 MassDSL proposal에 rule evidence를 복사했다.
- `verify-maas-20-alt-json.cjs`는 새 gate를 추가했다.
  - structured rule evidence required.
  - avgRulePriorParamRatio <= 0.20.
  - maxRulePriorParamRatio <= 0.35.
  - invalid rule params = 0.
  - fallback source geometry = 0.
- prompt/validator 누락도 수정했다.
  - `diagonal_connect`는 이제 `angle`이 required param이다.
  - `courtyard`는 이제 `ratio`, `upper_ratio`, `lower_floor_fraction`이 required param이다.
  - declared family가 이름/노트에만 있고 실제 verb sequence가 그 family를 지원하지 않으면 compiler가 그 declared family를 evidence로 믿지 않는다.
- 최신 산출물:
  - PNG: `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
  - JSON: `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
- 최신 검증 결과:
  - JSON verifier pass.
  - PNG verifier pass.
  - parking verifier pass.
  - legalPass 20/20.
  - parkingCountSatisfied 20/20.
  - sourceGeometryUsed 20/20.
  - legacyFallback 0.
  - structuredRuleEvidence 19/19 non-solver.
  - invalidRuleParamCount 0.
  - avgRulePriorParamRatio 0.033335.
  - maxRulePriorParamRatio 0.25.
  - highRulePriorParamCandidates 0.
  - uniqueFamilies 18.
  - uniqueSections 18.
  - twoTierMasses 0.
  - threePlusVolumeMasses 20.
  - sourceVolumeRoleDiversity 54.
  - finalDirectOpenAILlm 19.
  - finalCoverageRepairLlm 0.
- PNG 육안 확인:
  - 이전처럼 거의 전부 계단형은 아니다.
  - courtyard, array, reflected pair, diagonal connector, sloped roof, offset, extrude, branch, pinch, bend, nest, overlap, interlock, void notch, split, embed가 구분되어 보인다.
  - 남은 한계: 여전히 source geometry가 rectilinear decomposition 중심이라 곡면/비정형 shell/freeform morphology는 부족하다. 다음 루프에서는 grammar action 자체를 polygonal/curvilinear source primitive까지 확장해야 한다.

2026-07-07 paper-code-harness reset:

- 새 기준 문서:
  - `docs/ai-session-memory/MAAS_PAPER_CODE_HARNESS_BLUEPRINT.md`
- 방향:
  - 논문/참조코드의 핵심은 복붙이 아니라 구조다.
  - AIDL처럼 high-level DSL과 solver를 분리한다.
  - CAD-Assistant처럼 plan/execute/observe/revise artifact를 남긴다.
  - d4descent처럼 grammar/objective/optimizer를 분리하고, verifier를 objective gate로 둔다.
  - EvoMass처럼 population/island diversity를 보되, 단순 family count가 아니라 language-pair composition까지 본다.
- 구현된 새 증거:
  - `source_signature.primary_language`
  - `source_signature.secondary_language`
  - `source_signature.composition_rule`
  - `source_signature.composition_layer_roles`
  - `visual_diversity_evidence` mirror fields
  - JSON verifier gates:
    primary/secondary evidence, composition-layer evidence, language-pair diversity,
    composition-layer role diversity, irregular-fragment cap.
- 법규 원칙:
  - FAR/BCR/height/parking은 LLM 판단 대상이 아니다.
  - legal optimizer/parking verifier가 hard gate다.
  - LLM은 건축언어와 파라미터 후보를 제안하고, compiler/solver가 검증한다.

2026-07-07 MAAS memory system update:

- Canonical current handoff:
  - `docs/ai-session-memory/MAAS_MEMORY_INDEX.md`
- Read order before changing MAAS:
  1. `MAAS_MEMORY_INDEX.md`
  2. `MAAS_PAPER_CODE_HARNESS_BLUEPRINT.md`
  3. `MAAS_RESEARCH_CODE_MATRIX.md`
  4. `MAAS_SYSTEMATIC_PAPER_REVIEW_PLAN.md`
  5. `VERIFY.md`
- Latest status is no longer just "family diversity":
  - JSON/PNG/parking verifier pass.
  - `primarySecondaryEvidence=19`
  - `compositionalLayerEvidence=18`
  - `languagePairDiversity=17`
  - `parkingMassStagePass=20/20`
- Next real MAAS work:
  - polygonal/curvilinear/freeform source primitives,
  - explicit `repair_delta`,
  - critic-revision artifact,
  - population clustering/medoid selection.

2026-07-07 MAAS primitive/repair/PPT implementation:

- Implemented:
  - polygonal source roles for diagonal/overlap language,
  - curvilinear bend ribbon role,
  - freeform branch hinge canopy role,
  - `repair_delta` candidate evidence,
  - source-volume repair retention evidence,
  - verifier gates for source primitive evidence and severe repair caps,
  - critic artifact `docs/playwright/design-route-live-verify/maas-critic-revision-latest.json`,
  - presentation PPT `docs/maas-logic-diagram-20260707.pptx`.
- Latest verification:
  - JSON verifier pass.
  - PNG verifier pass.
  - parking verifier pass.
  - `legalPass=20/20`
  - `parkingMassStagePass=20/20`
  - `primarySecondaryEvidence=19`
  - `languagePairDiversity=19`
  - `sourcePrimitiveEvidence=6`
  - `sourcePrimitiveRoleDiversity=10`
  - `repairDeltaEvidence=20`
  - `severeRepairDelta=0`

2026-07-07 MAAS orderliness implementation:

- User critique accepted:
  - massing diversity cannot mean more boxes, more role names, or random helper
    fragments;
  - the final PNG must read as ordered architectural language with a dominant
    gesture, hierarchy, and clean legal envelope fit;
  - parking count/mass-stage checks must remain hard gates, while permit-final
    parking must not be claimed unless separately verified.
- Implementing:
  - `orderliness_evidence` with dominant axis, main mass area ratio, aligned role
    ratio, small fragment count, fragment role count, role hierarchy depth,
    unclear language mix, and score;
  - final review ranking prefers higher orderliness and penalizes helper
    fragments;
  - verifier gates fail low-orderliness or fragment-heavy final sets;
  - versioned failure memory:
    `docs/ai-session-memory/MAAS_FAILURE_EVOLUTION.md`.
- Latest verified result:
  - JSON verifier pass, PNG verifier pass, parking verifier pass.
  - `legalPass=20/20`, `parkingCountSatisfied=20/20`,
    `parkingMassStagePass=20/20`.
  - `parkingPermitPass=0/20`; permit-final approval is not claimed.
  - `llmAuthoringGap=0`, `twoTierMasses=0`,
    `threePlusVolumeMasses=20`.
  - `orderlinessEvidence=20`, `avgOrderlinessScore=0.78`,
    `smallFragmentMasses=0`, `unclearLanguageMix=0`.
  - latest PNG copy: `docs/img_82.png`.

2026-07-09 MAAS competition-grade/fallback discipline update:

- User's current hard target:
  - Final MAAS output must read as architectural-competition-grade massing, not
    merely legal boxes, family counters, or noisy geometric variety.
  - The PNG/3D result must show clean dominant gestures, hierarchy, readable
    podium/ground relation, void/bridge/terrace/roof logic, and disciplined
    silhouettes suitable for presentation.
  - Legal and parking rules remain hard deterministic gates.

- Latest verified implementation status:
  - `gpt-4.1-mini` is sufficient for the current harness; expensive models are
    comparison tools, not a substitute for algorithmic quality gates.
  - Full 120-candidate loop produced JSON verifier pass, parking verifier pass,
    and PNG verifier pass.
  - Latest output:
    `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`.
  - Key metrics from latest pass:
    `legalPass=20/20`, `parkingCountSatisfied=20/20`,
    `parkingMassStagePass=20/20`, `legacyFallback=0`,
    `uniqueFamilies=16`, `massLanguageDiversity=16`,
    `rolePatternMaxCount=2`, `stepbackLike=1`,
    `avgOrderlinessScore=0.91`, `architectureGradePass=20/20`.
  - Remaining caveat:
    one raw LLM candidate was rejected (`array n=2`) and caused one
    non-final coverage repair in the raw pool. The final 20 did not use
    coverage repair. The fix is over-generation margin plus validator rejection,
    not silently mutating bad LLM parameters.

- Engineering discipline going forward:
  - Do not run huge LLM loops for every small code change.
  - Use small dry checks for schema, prompt focus, config propagation, compiler
    validation, and verifier thresholds.
  - Run full PNG generation only after a meaningful generation/selector change.
  - Avoid fallback as normal behavior. Fallback/coverage repair is last-resort
    safety only and should be visible in artifacts.

- Current code direction:
  - LLM batch prompts now include explicit family focus quotas instead of vague
    diversity requests.
  - `terrace_link` is promoted to a first-class LLM family/source language
    (`terrace_ribbon`) instead of only existing in downstream geometry code.
  - LLM over-generation is configurable so invalid candidates can be rejected
    without forcing deterministic repair into the candidate pool.

2026-07-09 MAAS reference-backed VLM correction:

- User critique accepted:
  - VLM must not be a free-floating "LLM knows good massing" judge.
  - The critic must compare candidate massing against real architecture
    reference images and distilled architectural language.
  - ArchDaily/OMA/BIG/reference-book images are preference evidence, while
    legal and parking remain deterministic hard gates.

- Fixed:
  - Preference harness path resolution now loads the real workspace reference
    corpus instead of accidentally reading an empty `ARR/backend/docs/...`
    folder.
  - ArchDaily `DB_MANIFEST` corpus is now loaded in harness runs:
    latest `reference_count=120`.
  - VLM scorer now sends the candidate crop plus up to three matched reference
    images to the model, not only textual reference metadata.
  - Vancouver House/BIG ArchDaily seed was added to the iconic precedent corpus.
  - Reference ontology now maps known precedent pages to massing tags such as
    `torqued_stack`, `stacked_platform`, and `terrace_ribbon`.

- Latest full preference/VLM verification:
  - output:
    `docs/playwright/design-route-live-verify/maas-20-alt-vlm-feedback-run-latest.json`
  - generation feedback:
    `docs/playwright/design-route-live-verify/maas-vlm-generation-feedback-latest.json`
  - `reference_count=120`
  - `vlm_scored_count=20`
  - `preferenceModeSet=["vlm_scored"]`
  - matched/image-backed reference coverage:
    17 candidates have 5 matches, 1 has 4, 1 has 3, 1 has 1.
  - JSON verifier pass after VLM rerank.

- Remaining research caution:
  - Reference matching is now image-backed, but still ontology/tag-driven before
    VLM comparison. A stronger next step is embedding/VLM retrieval over the
    reference image corpus, then pairwise candidate-vs-reference scoring.

2026-07-09 MAAS reference-backed generation audit:

- User critique:
  - If VLM-backed and non-VLM-backed PNGs look similar, the system has not yet
    solved the real design problem.
  - More ArchDaily/reference massing images must influence generation, not only
    post-hoc scoring.

- Implemented after critique:
  - ArchDaily reference corpus expanded with `offices` and `mixed_use`
    collections.
  - Real reference corpus now reports `reference_count=152`.
  - `generation_feedback.py` now exports `reference_precedent_targets`, not only
    generic must-use terms.
  - LLM generation prompt now consumes `reference_precedent_targets` and asks
    for reference-backed MassDSL operations, e.g. Vancouver/BIG torque into
    stronger `pinch/taper/offset/bend/branch`, OMA platform logic into
    `split/overlap/diagonal_connect/sloped_roof`, Mountain/8 House into
    `terrace_link/grade/lift`.
  - Reference-backed full generation was run; latest PNG/JSON passed verifier:
    `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
  - Latest generation metrics:
    `raw_candidate_count=128`, `compiled_sequence_count=126`,
    `compiled_variant_count=120`, `openai_batch_error_count=0`,
    `timeout_coverage_repair_count=0`, `legacyFallback=0`.
  - Latest VLM rerun:
    `docs/playwright/design-route-live-verify/maas-20-alt-vlm-feedback-run-latest.json`
    has `reference_count=152`, `vlm_scored_count=20`,
    `preferenceModeSet=["vlm_scored"]`, VLM score range `0.728..0.865`.

- Honest current limitation:
  - The pipeline is now reference-backed, but the visible massing is still not
    consistently competition-grade.
  - Main bottleneck is not whether VLM is called; it is that the source geometry
    compiler/materializer still converts reference principles into relatively
    mild low-rise plates, ribbons, and stacks.
  - A full run took about 1003 seconds, so future development must use short
    reference-backed smoke runs before full 120-candidate generation.

- Code direction already started:
  - `torqued_stack` formal primitive was strengthened from a mild 3-plate
    rotation into a stronger 4-tier parameter-driven torque with undercut void
    evidence.
  - Next full generation should test this stronger primitive. If PNGs still
    look similar, the next required work is not prompt tuning but new source
    geometry primitives for tower/undercut/platform massing.

2026-07-09 MAAS similarity root-cause fix:

- Root cause found:
  - Many reference-backed candidates were still visually similar because
    `formal_result` short-circuited family-specific source geometry.
  - A `diagonal_connect + torqued_stack`, `courtyard + torqued_stack`, and
    `offset + torqued_stack` all collapsed into nearly the same
    `torqued_plate_0..2 + core` source roles.

- Code fix:
  - `source_geometry/formal_principles.py`
    - `torqued_stack` now compiles to 4 stronger parameter-driven torque tiers
      plus a stabilizing core, using authored `angle` and `shift/distance`
      values.
    - Removed positive "void marker" volume because voids must be carved by
      mass absence/footprint difference, not rendered as extra orange mass.
  - `source_geometry/compiler.py`
    - formal-principle output now receives family accent and secondary-language
      accent through `_compose_secondary_language`.
    - This prevents different LLM families from collapsing into the same
      formal stack.

- Smoke verification without OpenAI/full PNG:
  - `diagonal_connect + torqued_stack` now outputs:
    4 torqued plates + torque core + diagonal bridge + split bridge.
  - `courtyard + torqued_stack` now outputs:
    4 torqued plates + torque core + courtyard liner + diagonal bridge.
  - `offset + torqued_stack` now outputs:
    4 torqued plates + torque core + offset alignment spine + sloped roof cap.
  - Each smoke case produced 7 source volumes instead of the previous 4-role
    collapsed pattern.

2026-07-09 MAAS VLM/reference retrieval audit:

- User concern:
  - VLM-backed and non-VLM-backed generations still looked too similar.
  - Need proof that VLM is actually seeing reference images, and that references
    are diverse instead of only one repeated precedent cluster.

- Code audit result:
  - `preference/vlm_scorer.py` sends the candidate crop as the first image and
    appends up to 3 matched reference images to the OpenAI Responses request.
  - Latest preference artifact has `use_vlm=true`, `vlm_model=gpt-4.1-mini`,
    and all 20 candidates have `vlm_status=scored`.
  - Reference corpus currently loads 152 items:
    144 from ArchDaily API collections and 8 seeded iconic precedents.
  - All 152 references have remote image URLs; 40 also have local downloaded
    image files.

- Retrieval weakness found:
  - Reference tags included generic caption tokens such as articles, years,
    `completed`, `images`, and broad program/site words, which polluted
    reference matching.
  - Candidate matches were too concentrated on seeded iconic references
    (Seattle Library, Vancouver House, Qatar Library, BIG references).

- Code fix:
  - `preference/reference_corpus.py`
    - Added reference tag stopword cleanup for noisy ArchDaily caption tokens.
    - Normalizes stored metadata tags when loading existing `metadata.jsonl`.
    - Adds a diverse reference selector so the first VLM reference set does not
      consist only of seeded iconic precedents.
    - Ensures, when available, at least one `archdaily_api` reference appears
      in the top 3 reference images sent to VLM.

- Verification:
  - `py_compile` passed for the changed MAAS preference/source geometry modules.
  - After the retrieval fix, all 20 latest candidates have at least one
    `archdaily_api` reference within their top 3 matches.
  - This confirms VLM input diversity improved, but it still needs another
    full/targeted generation PNG after the compiler fix to judge visible design
    quality.

2026-07-09 MAAS paper-code deep audit:

- Added paper-alignment audit script:
  - `docs/playwright/design-route-live-verify/audit-maas-paper-alignment.cjs`
- Added memory:
  - `docs/ai-session-memory/MAAS_PAPER_CODE_DEEP_AUDIT_20260709.md`
- Latest audit command:
  - `node docs/playwright/design-route-live-verify/audit-maas-paper-alignment.cjs docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
- Latest verdict:
  - `paper_inspired_not_paper_complete`

- Important correction:
  - Internal JSON/PNG verifiers pass, but this is not the same as paper-complete
    implementation.
  - EvoMass alignment is partial: population exists, but objective vector is
    still FAR/BCR/diversity/orderliness heavy and lacks daylight/solar/user
    preference objectives.
  - CAADRIA 2025 urban massing alignment is partial: parking/layout is checked,
    but massing and layout are not jointly optimized.
  - AIDL/CAD-HLLM alignment is partial: MassDSL/solver separation exists, but
    MassDSL is still mostly a flat call sequence, not a hierarchical component
    graph.
  - Archi-Agents alignment is weak: agent folders/contracts exist, but latest
    JSON lacks a live multi-agent collaboration/revision trace.
  - MASS multi-agent system search is not implemented: no prompt/topology search
    artifact exists.
  - DDADesign/diffusion alignment is weak: latest 20-card JSON is
    `vlm_ready_geometry_proxy`, not current-generation `vlm_scored`; no trained
    diffusion/ControlNet massing prior exists.
  - Constraint-aware generation is partial: deterministic legal repair evidence
    exists, but differentiable/sampling-time projection is not implemented.

- Next code direction:
  - Add `agent_collaboration_trace`.
  - Add objective axes beyond law/capacity.
  - Add medoid/cluster representative selection instead of only quota/repeat
    replacement.
  - Re-run VLM harness after full PNG generation before claiming current VLM
    preference.

2026-07-09 repeated paper/code review pass:

- Re-ran:
  - internal JSON verifier,
  - PNG verifier,
  - paper-alignment audit,
  - VLM/reference artifact audit,
  - agent folder/trace audit,
  - generator selection-code audit.
- Findings:
  - Internal JSON/PNG still pass.
  - Paper audit still says `paper_inspired_not_paper_complete`.
  - VLM path is real, but latest generated JSON is only
    `vlm_ready_geometry_proxy`; the VLM-scored artifact is separate.
  - Agent folder structure and 8-step `agent_trace` exist, but there is no
    critic-to-generator revision trace.
  - K-medoid representative code exists, but prior JSON did not preserve
    medoid selection evidence in final candidates.
- Code fixes:
  - `audit-maas-paper-alignment.cjs` now reads `selection_debug` and agent
    traces correctly.
  - `legal_mesh_optimizer.py` now records `selection_trace` for k-medoid
    representatives and exposes future `final_kmedoid_representatives` /
    `final_selection_trace_evidence` in `selection_debug`.
- Next full generation must prove:
  - current PNG/JSON pass,
  - current VLM harness is rerun,
  - medoid trace survives final selection,
  - remaining gaps are objective/performance axes and revision-loop evidence,
    not hidden verifier bugs.

2026-07-09 MAAS paper-driven code fixes:

- EvoMass/SSIEA objective-axis fix:
  - `legal_mesh_optimizer.py` now computes early massing performance proxies:
    `daylight_perimeter_proxy`, `south_solar_access_proxy`,
    `view_openness_proxy`, `mass_distribution_balance`, and
    `aggregate_performance_proxy`.
  - These values are stored in `paper_alignment_evidence.objective_vector` and
    `performance_proxy_evidence`.
  - `aggregate_performance_proxy` is now part of
    `_design_review_quality_key`, so it affects final candidate ranking.
  - This is explicitly proxy-only, not Radiance/Honeybee/solar simulation.

- Archi-Agents revision-evidence fix:
  - `legal_mesh_optimizer.py` now emits `agent_revision_trace` and attaches
    `agent_revision_evidence` to selected candidates.
  - The trace records how law, parking, grammar critic, preference distiller,
    and geometry agent rules affected final selection.
  - The trace type is `selection_revision_not_geometry_mutation`; the next
    research-grade step is true critic -> MassDSL mutation -> compiler ->
    legal/parking projection -> rerank.
  - `audit-maas-paper-alignment.cjs` now checks revision trace and candidate
    revision evidence instead of only counting agent folders/reviews.

- Modularization correction:
  - Paper/objective/agent evidence logic must not continue growing inside
    `legal_mesh_optimizer.py`.
  - Extracted modules:
    - `ARR/backend/design/maas/performance_objectives.py`
    - `ARR/backend/design/maas/paper_alignment.py`
    - `ARR/backend/design/maas/agent_revision.py`
  - `legal_mesh_optimizer.py` should act as orchestration/glue for these
    concerns, not own their implementation.
  - Next extraction target is final selection/ranking policy into
    `selection_policy.py` or a `selection/` package.

2026-07-09 MAAS selection policy modularization pass 1:

- Added `ARR/backend/design/maas/selection_policy.py`.
- Moved final review-set refinement guards out of `legal_mesh_optimizer.py`:
  - direct LLM-authored minimum,
  - dominant-height guard,
  - repeated role-pattern guard,
  - language/family diversity guard.
- `legal_mesh_optimizer.py` now calls `refine_final_review_set(...)` through
  `FinalReviewRefinementCallbacks`.
- Verification:
  - py_compile passed.
  - smoke on existing latest JSON returned 20 candidates, 15 families, and 15
    research languages.
  - optimizer shrank from 7,971 lines to 7,730 lines.
- Remaining:
  - split `_final_design_balanced_selection`;
  - then move `_select_diverse_features`;
  - keep `selection_debug` in optimizer until selection extraction is stable.

2026-07-09 MAAS selection policy modularization pass 2:

- Moved review-set constraint helpers into `selection_policy.py`:
  - mass-stage parking pass,
  - layout status,
  - source reviewability,
  - unresolved LLM authoring,
  - visible tier count,
  - review-set geometry gate,
  - review-set constraint gate.
- `legal_mesh_optimizer.py` now keeps only thin wrappers where
  `_final_design_balanced_selection` still needs local state.
- Verification:
  - py_compile passed.
  - smoke on existing latest JSON returned 20 candidates, 15 families, and 15
    research languages.
  - optimizer reduced to 7,676 lines.
- Next safe extraction:
  - split the island quota/recovery block from `_final_design_balanced_selection`;
  - avoid moving the whole 2k-line function at once without a stronger callback
    contract.

2026-07-09 MAAS selection policy review:

- Review conclusion:
  - modularization is correct, but the selection logic is not mathematically or
    architecturally "perfect";
  - it remains a heuristic review-sheet policy layered on top of legal/parking
    hard gates.
- Fixed bug:
  - `refine_final_review_set([], ...)` no longer raises `ValueError`.
- Policy cleanup:
  - added `FinalReviewRefinementPolicy` for named thresholds;
  - `review_set_constraints_ok` now receives `max_language_repeat` explicitly.
- Verification:
  - empty-input smoke returns `[]`;
  - latest JSON smoke remains 20 candidates / 15 families / 15 research
    languages;
  - py_compile and paper audit pass.
- Remaining:
  - island quota/recovery and formal/strategy recovery blocks still contain many
    heuristic thresholds inside `_final_design_balanced_selection`;
  - add focused unit tests for empty pools, duplicate-heavy pools, height-crowded
    pools, and weak-LLM-heavy pools before claiming stability.

2026-07-09 MAAS selection policy modularization pass 3:

- Moved pure island/formal helper logic to `selection_policy.py`:
  - island quota counts,
  - duplicate role-pattern counts,
  - island candidate scoring key,
  - formal-principle counts,
  - vertical-strategy counts,
  - formal diversity candidate key.
- Added callback contracts:
  - `IslandQuotaCallbacks`
  - `FormalDiversityCallbacks`
- Removed duplicate formal/recovery replacement helper and now uses one
  `relaxed_review_replace` implementation.
- Verification:
  - py_compile passed;
  - latest JSON smoke remains 20 candidates / 15 families / 15 research
    languages;
  - paper audit passed;
  - optimizer reduced to 7,647 lines.
- Remaining:
  - island quota/recovery mutation loops still remain in
    `_final_design_balanced_selection`;
  - next extraction should introduce a small selection-state object instead of
    passing loose `result`/`replace_result`/`rebuild_seen_state` closures.

2026-07-09 MAAS selection state refactor review:

- Compared against committed `HEAD`:
  - baseline kept `result`, `seen_ids`, `seen_shapes`, and append/replace
    bookkeeping directly inside `_final_design_balanced_selection`;
  - current code centralizes that bookkeeping in
    `selection_policy.SelectionState`.
- Implemented:
  - connected `_final_design_balanced_selection` to `SelectionState`;
  - replaced manual append/rebuild/replace bookkeeping with
    `append_seen`, `rebuild`, and `replace_if_valid`;
  - fixed leftover manual bookkeeping in `force_add_reviewable`.
- Verification:
  - py_compile passed;
  - direct `_final_design_balanced_selection` smoke remains 20 candidates / 15
    families / 15 research languages;
  - paper audit passed.
- Remaining:
  - later recovery loops still perform direct `result[index] = candidate`
    followed by `rebuild_seen_state()`;
  - next pass should move that relaxed replacement behavior into
    `SelectionState` before extracting island/recovery loops.

2026-07-09 MAAS selection state refactor pass 2:

- Added `SelectionState.replace_relaxed(...)` and
  `SelectionState.replace_unchecked(...)`.
- Replaced direct selection result assignment in:
  - formal/recovery relaxed replacement;
  - forced recovery replacement;
  - LLM coverage-repair promotion.
- Verification:
  - py_compile passed;
  - direct `_final_design_balanced_selection` smoke remains 20 candidates / 15
    families / 15 research languages;
  - paper audit passed.
- Architecture direction:
  - `legal_mesh_optimizer.py` is still too large at about 7.6k lines;
  - next real package split should be role-based:
    `selection/`, `orchestration/`, `section_materialization/`,
    `parking_repair/`, and `feature_factory/`;
  - do not keep growing a flat `selection_policy.py` indefinitely.

2026-07-09 MAAS selection package split pass 1:

- Created `ARR/backend/design/maas/selection/` as a real role package:
  - `types.py`
  - `state.py`
  - `constraints.py`
  - `quota.py`
  - `refinement.py`
  - `__init__.py`
- Changed `legal_mesh_optimizer.py` to import selection contracts/helpers from
  `design.maas.selection`.
- Reduced `selection_policy.py` to a 58-line compatibility shim for older
  imports.
- Verification:
  - py_compile passed for optimizer, shim, selection package, and paper/evidence
    modules;
  - `_final_design_balanced_selection` smoke remains 20 candidates / 15 source
    families / 15 research mass languages;
  - paper-alignment audit passed.
- Important limitation:
  - current smoke parking statuses are still
    `needs_drive_connectivity_review` and `needs_mechanical_parking_review`;
    this is mass-stage feasibility, not final permit-grade parking approval.
- Next:
  - extract the remaining `_final_design_balanced_selection` loops into
    `selection/` modules with focused regression tests before changing scoring
    semantics again.

2026-07-09 MAAS selection regression tests pass 1:

- Added `ARR/backend/design/test_maas_selection_policy.py`.
- Covered:
  - `selection_policy.py` compatibility shim re-export;
  - empty final review refinement;
  - duplicate-shape replacement rejection;
  - parking `fail` replacement rejection.
- Verification:
  - `python manage.py test design.test_maas_selection_policy --verbosity 2`
    passed 4/4 tests;
  - py_compile passed for optimizer, selection package, compatibility shim, and
    new test file.
- Next:
  - add language/source-family/weak-LLM crowding tests before extracting the
    remaining island/formal/recovery loops.

2026-07-09 MAAS selection regression tests pass 2:

- Expanded `ARR/backend/design/test_maas_selection_policy.py` from 4 to 9
  tests.
- Added direct checks for:
  - language crowding;
  - source-family crowding;
  - weak LLM `reject_final_review` over-limit;
  - final metric snapshot counts;
  - final structural quota language-repeat rejection.
- Added `ARR/backend/design/maas/selection/final_metrics.py` and
  `FinalMetricCallbacks`.
- Moved final review-set metric calculations out of
  `_final_design_balanced_selection`; optimizer now calls package helpers via
  small wrappers.
- Verification:
  - selection tests passed 9/9;
  - py_compile passed;
  - direct selection smoke remains 20 candidates / 15 families / 15 languages /
    20 shapes;
  - paper audit passed but still reports `paper_inspired_not_paper_complete`.
- Remaining:
  - move one complete island/formal/recovery loop block into `selection/`
    rather than only moving helper calculations.

2026-07-09 MAAS selection island refinement extraction pass 1:

- Added `ARR/backend/design/maas/selection/island_refinement.py`.
- Moved one complete island quota loop out of
  `_final_design_balanced_selection`:
  - island target balancing;
  - duplicate role-pattern replacement;
  - candidate ranking via `IslandQuotaCallbacks`.
- Extended `IslandQuotaCallbacks` with `formal_principle`.
- Added a unit test proving a missing additive island candidate can replace an
  over-generic result item.
- Verification:
  - selection tests passed 10/10;
  - py_compile passed;
  - direct selection smoke remains 20 candidates / 15 families / 15 languages /
    20 shapes;
  - paper audit passed but still says `paper_inspired_not_paper_complete`.
- Paper/code alignment:
  - this clarifies EvoMass/SSIEA-style typology balancing;
  - it is still not true EvoMass: no evolutionary operators, no k-medoid trace,
    no simulated daylight/solar/user-preference objective.
- Next:
  - extract formal-principle / vertical-strategy over-representation into
    `selection/formal_refinement.py`;
  - then add selection trace or k-medoid representative evidence because the
    audit still reports zero for both.

2026-07-09 MAAS selection formal refinement extraction pass 1:

- Added `ARR/backend/design/maas/selection/formal_refinement.py`.
- Moved the formal-principle / vertical-strategy over-representation loop out
  of `_final_design_balanced_selection`.
- Added `enforce_formal_diversity_replacements(...)`.
- Extended `FormalDiversityCallbacks` with `stair_like_risk`.
- Added a unit test for replacing an over-repeated formal principle with a
  different formal language candidate.
- Verification:
  - selection tests passed 11/11;
  - py_compile passed;
  - direct selection smoke remains 20 candidates / 15 families / 15 languages /
    20 shapes;
  - paper audit passed but still says `paper_inspired_not_paper_complete`.
- Optimizer size:
  - `legal_mesh_optimizer.py` moved from 7,487 to 7,427 lines.
- Remaining:
  - extract repair/height/formal-target recovery block;
  - add selection trace or k-medoid representative evidence because paper audit
    still reports `finalSelectionTraceEvidence: 0` and
    `finalKmedoidRepresentatives: 0`.

2026-07-09 MAAS selection initial recovery extraction pass 1:

- Added `ARR/backend/design/maas/selection/recovery_refinement.py`.
- Added `RecoveryRefinementCallbacks`.
- Extracted a larger recovery block from `_final_design_balanced_selection`:
  - severe repair-retention replacement;
  - dominant height replacement;
  - target formal-principle recovery.
- Added a unit test for replacing a severe repair-loss item.
- Verification:
  - selection tests passed 12/12;
  - py_compile passed;
  - direct selection smoke remains 20 candidates / 15 families / 15 languages /
    20 shapes;
  - paper audit passed but still says `paper_inspired_not_paper_complete`.
- Optimizer size:
  - `legal_mesh_optimizer.py` moved from 7,427 to 7,306 lines in this pass.
- Process correction:
  - continue extracting whole behavior stages; 60-line reductions are too small
    for the current optimizer problem.
- Next:
  - extract the next cleanup/recovery stage around clean replacement pool,
    signature priority, replaceable indexes, and repeat-cap candidate checks;
  - then add `selection_trace` or k-medoid representative evidence.

2026-07-09 MAAS final balanced selection extraction pass 1:

- Corrected course after the user flagged that 60-120 line reductions were not
  enough.
- Added `ARR/backend/design/maas/selection/final_balanced.py`.
- Added `BalancedSelectionDeps`.
- Moved the full `_final_design_balanced_selection` orchestration body out of
  `legal_mesh_optimizer.py`.
- `legal_mesh_optimizer.py` now keeps only a thin wrapper that passes explicit
  dependencies to `selection.final_design_balanced_selection(...)`.
- Verification:
  - py_compile passed;
  - selection tests passed 12/12;
  - direct smoke remains 20 candidates / 15 families / 15 languages /
    20 shapes;
  - paper audit passed but still reports `paper_inspired_not_paper_complete`.
- Size:
  - `legal_mesh_optimizer.py`: 7,306 -> 5,481 lines;
  - new `selection/final_balanced.py`: 1,992 lines.
- Remaining:
  - `selection/final_balanced.py` is now the oversized file and must be split by
    stage;
  - add `selection_trace` and/or k-medoid representative evidence to address
    audit gaps, not just code organization.

2026-07-09 MAAS post-extraction review and trace pass:

- Reviewed the extraction:
  - `legal_mesh_optimizer.py` is now much better at 5,481 lines;
  - `selection/final_balanced.py` is the next oversized file at about 2k lines.
- Added `attach_final_selection_trace(...)` in
  `selection/final_balanced.py`.
- Direct Python smoke now reports:
  - 20 candidates;
  - 15 families;
  - 15 languages;
  - 20 candidates with `selection_trace`;
  - 20 `final_balanced_selection` trace events.
- Verification:
  - py_compile passed;
  - selection tests passed 12/12;
  - PNG verifier passed;
  - JSON verifier passed.
- JSON verifier mass quality snapshot:
  - legal pass 20/20;
  - unique shapes 20;
  - unique families 15;
  - parking count satisfied 20/20;
  - parking mass-stage pass 20/20;
  - parking permit pass 0/20;
  - low orderliness 0;
  - severe repair 0;
  - mass language diversity 15;
  - max mass language repeat 2.
- Paper alignment:
  - this improves final selection traceability;
  - it is not k-medoid evidence;
  - cached `maas-20-alt-latest.json` was generated before this trace pass, so
    paper audit still reports selection trace 0 until full regeneration.
- Next:
  - regenerate JSON/PNG through backend route when available;
  - split `selection/final_balanced.py` by stage while preserving trace events.

2026-07-09 MAAS review-board anchor policy and paper-alignment check:

- Rechecked code, tests, PNG, JSON verifier, and paper audit after the final
  selection extraction.
- Current verified state:
  - `legal_mesh_optimizer.py`: 5,481 lines;
  - `selection/final_balanced.py`: about 2k lines and still too large;
  - py_compile passed;
  - selection tests passed 12/12;
  - PNG verifier passed;
  - JSON verifier passed.
- Paper alignment judgment:
  - EvoMass/SSIEA direction is only partially matched: we have typology
    diversity, objective proxies, and selection trace, but not true
    steady-state island evolution with simulation feedback.
  - DDADesign direction is only partially matched: we have massing candidates
    and VLM-ready/proxy preference artifacts, but the latest 20-card JSON is
    not actually VLM-scored.
  - Subtractive massing literature supports our additive/subtractive/hybrid
    language split, but our generator still needs clearer stage-level
    topological operators instead of a long final-selection repair script.
- Implemented a review-board policy correction in
  `selection/final_balanced.py`:
  - `legal_layered_max` remains valid as internal law/envelope evidence;
  - it is no longer supposed to enter the final review board through generic
    backfill when enough authored/reviewable candidates exist;
  - final fallback can still use it only when the non-anchor reviewable pool is
    insufficient.
- Important verification nuance:
  - direct smoke using cached `maas-20-alt-latest.json` still shows one
    `legal_layered_max` because that JSON contains only the already selected
    20 candidates, so there is no larger candidate pool available for a
    non-anchor replacement;
  - the policy needs a full backend generation rerun against the full candidate
    pool before judging the PNG result.
- Remaining quality issue:
  - current PNG is better than earlier but still not presentation-grade
    architectural massing;
  - too much quality is being handled in final selection/recovery;
  - next code work should move design-intent generation upstream into
    grammar/source-geometry/VLM preference stages, then keep final selection
    as evidence curation rather than geometry rescue.

2026-07-09 MAAS VLM top-40 pre-selection implementation:

- Implemented the plan's structure+PNG balance direction.
- Added a pre-final preference loop inside `generate_legal_mass_variants`.
  - Input config: `parking_options.maas_preference_loop`.
  - Defaults: off unless explicitly enabled.
  - `top_k` defaults to 40.
  - `require_vlm=true` uses temporary candidate preview PNGs and the OpenAI VLM
    scorer; failures raise instead of silently claiming proxy as VLM.
  - tests can inject a fake scorer for deterministic/non-network verification.
- Ranking now gives real `vlm_scored` preference evidence priority in
  `_design_review_quality_key`.
- Existing final `attach_paper_alignment_and_preference_evidence` now preserves
  already-attached VLM preference evidence instead of overwriting it with a
  geometry proxy.
- Render harness env flags:
  - `MAAS_PREFERENCE_LOOP_ENABLED=1` for proxy/reference preference loop;
  - `MAAS_PREFERENCE_LOOP_REQUIRE_VLM=1` for actual VLM scoring;
  - `MAAS_PREFERENCE_LOOP_TOP_K=40`;
  - `MAAS_PREFERENCE_VLM_MODEL=...`;
  - `MAAS_PREFERENCE_REFERENCE_ROOT=docs/ai-session-memory/reference-corpus`.
- Verification:
  - py_compile passed;
  - `design.test_maas_preference` + `design.test_maas_selection_policy` passed
    29/29;
  - render script node syntax passed;
  - stale JSON verifier still passes;
  - stale JSON paper audit still says `paper_inspired_not_paper_complete`,
    because the JSON was generated before this new full-pool preference loop.
- Next required proof:
  - run full backend generation with `MAAS_PREFERENCE_LOOP_REQUIRE_VLM=1`;
  - regenerate `maas-20-alt-latest.json/png`;
  - expect final `vlm_scored` candidates and a changed PNG selection.

2026-07-09 MAAS VLM regeneration result:

- Regenerated `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
  and `.png` through the live backend.
- First proof run:
  - `MAAS_LLM_LOOP_REQUIRED=0`,
  - `MAAS_PREFERENCE_LOOP_REQUIRE_VLM=1`,
  - `MAAS_PREFERENCE_LOOP_TOP_K=8`,
  - completed in about 97s,
  - proved actual VLM scoring path: `vlm_scored_count=8`,
  - but JSON verifier failed because LLM population was intentionally off.
- Final verified run:
  - `MAAS_LLM_LOOP_REQUIRED=1`,
  - `MAAS_LLM_TARGET_COUNT=120`,
  - `MAAS_LLM_COMPILE_LIMIT=90`,
  - `MAAS_PREFERENCE_LOOP_REQUIRE_VLM=1`,
  - `MAAS_PREFERENCE_LOOP_TOP_K=8`,
  - completed in 927,457ms.
- Verification after final run:
  - `verify-maas-20-alt-json.cjs`: pass;
  - `verify-maas-png.py`: pass;
  - legal pass 20/20;
  - parking mass-stage pass 20/20;
  - parking permit pass remains 0/20, so do not claim permit-final approval;
  - unique shapes 20;
  - unique families 16;
  - unique sections 16;
  - LLM raw candidates 121;
  - LLM compiled variants 90;
  - final direct OpenAI LLM 18;
  - `legal_layered_max` count 0;
  - final VLM scored count 7/20;
  - preference loop attempted 8 and scored 8 with `gpt-4.1-mini`;
  - DDADesign audit moved to partial with current VLM scored evidence.
- Visual judgment:
  - PNG is better: no dominant legal stair anchor, more language diversity,
    fewer repeated role patterns, and less obvious stair-step dependence.
  - Still not presentation-grade competition massing: several candidates remain
    low/flat or repair-like, and VLM is only influencing 7/20 because top-k was
    reduced for runtime.
- Next:
  - parallelize or batch VLM scoring before trying top 40 again;
  - reduce `coverage_repair_adopted_*` dominance;
  - add a hard final target for `final_vlm_scored_count >= 16` once runtime is
    under control.

2026-07-10 MAAS top-40 VLM + LLM cache verified result:

- Implemented LLM batch/runtime fixes:
  - `generate_llm_massdsl_batch` now supports `batch_workers` and
    `cache_path`;
  - render harness passes `MAAS_LLM_BATCH_WORKERS` and
    `MAAS_LLM_BATCH_CACHE_PATH` through the API payload, not only node env;
  - first full gpt-4.1-mini population wrote
    `docs/ai-session-memory/maas-cache/latest-llm-batch.json`;
  - later loops cache-hit the LLM population, reducing backend generation from
    about 19 minutes to about 2.5 minutes while still compiling 120 LLM
    sequences.
- Implemented final preference guards:
  - VLM pre-final loop scores top 40 with image-backed OpenAI VLM;
  - final set preserves at least 16 VLM-scored candidates;
  - final set preserves at least 18 direct OpenAI LLM candidates;
  - language, height, and formal-principle recovery guards run after VLM
    preservation so one verifier fix does not break another.
- Latest verified output:
  - `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`;
  - `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`.
- Final verification:
  - `verify-maas-20-alt-json.cjs`: pass;
  - `verify-maas-png.py`: pass;
  - legal pass 20/20;
  - parking mass-stage pass 20/20;
  - parking permit pass 0/20, still not permit-final;
  - preference loop attempted 40/40 and VLM scored 40/40;
  - final VLM scored 16/20;
  - final direct OpenAI LLM 18/20;
  - unique families 15;
  - mass language diversity 15;
  - height max repeat 12;
  - formal principle diversity 6;
  - coverage repair in final 0.
- Visual judgment:
  - better than the previous stair/legal-anchor outputs and now backed by
    top-40 image preference scoring;
  - still not complete "competition-grade" architecture. It remains a legal
    massing/research diagram pipeline; next work is critic-to-geometry mutation
    and real EvoMass-style island evolution/performance feedback.

2026-07-10 MAAS modularization checkpoint:

- Split the new preference/review logic out of `legal_mesh_optimizer.py`.
- New modules:
  - `ARR/backend/design/maas/preference/loop.py`
    - VLM preference loop config;
    - candidate preview PNG generation;
    - reference matching;
    - parallel top-k OpenAI VLM scoring;
    - preference evidence attachment.
  - `ARR/backend/design/maas/selection/preference_guards.py`
    - final VLM minimum preservation;
    - direct LLM minimum preservation;
    - height/formal/family/mass-language diversity recovery.
- Updated package exports:
  - `design.maas.preference.__init__`;
  - `design.maas.selection.__init__`.
- `legal_mesh_optimizer.py` is still large, but it now calls these modules via
  explicit callback bundles instead of owning their internals.
- Verification after modularization:
  - py_compile pass;
  - `design.test_maas_preference design.test_maas_selection_policy`: 30/30;
  - cache-hit render pass;
  - `verify-maas-20-alt-json.cjs`: pass;
  - `verify-maas-png.py`: pass;
  - final VLM-scored 16/20;
  - final direct OpenAI LLM 18/20.

2026-07-10 MAAS paper-alignment strict verdict:

- Current MAAS is verified as `paper_inspired_partial_implementation`, not a
  literal paper-complete implementation.
- Code evidence:
  - `ARR/backend/design/maas/paper_alignment.py` emits
    `method_status=paper_inspired_arr_native` and explicitly records
    "Not a literal EvoMass clone.";
  - `ARR/backend/design/maas/agent_revision.py` emits
    `revision_type=selection_revision_not_geometry_mutation`;
  - `ARR/backend/design/maas/selection/island_refinement.py` explicitly says
    the island step is deterministic quota/projection, not true EvoMass
    evolution.
- Latest JSON evidence:
  - 20/20 candidates carry `paper_alignment_evidence`;
  - 20/20 candidates carry `performance_proxy_evidence`;
  - 20/20 candidates carry `agent_revision_evidence`;
  - top-level `agent_revision_trace.revision_type` is
    `selection_revision_not_geometry_mutation`;
  - `evolution_trace` is absent;
  - `agent_search_trace` is absent.
- Paper verdict:
  - EvoMass/SSIEA: partial only. Need real island population evolution,
    mutation/crossover, generation trace, survivor selection, and objective
    vector history.
  - DDADesign: weak partial only. Current VLM ranking/proxy scoring is not
    daylight-map LoRA/diffusion/ControlNet generation.
  - Archi-Agents: partial only. Need critic -> MassDSL mutation -> geometry
    compile -> law/parking recheck -> re-rank loop.
  - MASS: not implemented. Need prompt/topology search or agentic supernet
    trace before claiming MASS alignment.
- Canonical memory:
  - `docs/ai-session-memory/MAAS_PAPER_ALIGNMENT_VERDICT_20260710.md`.

2026-07-10 MAAS first-generation evolution implementation:

- Added the first real paper-critical geometry revision loop:
  - `ARR/backend/design/maas/evolution/island_loop.py`;
  - `ARR/backend/design/maas/evolution/__init__.py`.
- The loop now:
  - takes LLM/grammar MassDSL sequences as seed islands;
  - creates parameter mutations, critic-section mutations, and crossovers;
  - returns evolved variants to the existing legal repair/parking/VLM/final
    selection pipeline;
  - emits `evolution_trace`.
- Updated:
  - `agent_revision.py` now reports
    `revision_type=critic_to_geometry_mutation` when evolved children are
    accepted;
  - `source_geometry/compiler.py` recognizes critic-section evolution
    family overrides and normalizes repeated generic formal principles into
    family-specific architectural principles;
  - `legal_mesh_optimizer.py` includes evolved variants and exposes
    `evolution_trace`;
  - `selection/final_balanced.py` sees the legal candidate pool and restores
    island/family/formal diversity at final review time.
- Latest verified run:
  - JSON verifier: pass;
  - PNG verifier: pass;
  - legal pass 20/20;
  - parking mass-stage pass 20/20;
  - parking permit-final pass 0/20;
  - LLM compiled variants 90;
  - evolved MassDSL variants accepted 45;
  - `agent_revision_trace.revision_type=critic_to_geometry_mutation`;
  - final VLM-scored 16/20;
  - final direct OpenAI LLM 18/20;
  - unique families 15;
  - formal principle diversity 6;
  - additive/subtractive/hybrid/sectional island coverage 4/6/5/4.
- Remaining:
  - still not full EvoMass/SSIEA;
  - next step is multi-generation evolution with objective history,
    survivor/Pareto selection, and stable visual comparison.

2026-07-10 re-review correction:

- After stricter final-selection/taxonomy edits, the latest JSON verifier is no
  longer fully passing.
- Current verifier state:
  - compile pass;
  - 30 Django MAAS selection/preference tests pass;
  - PNG verifier pass;
  - JSON verifier fails on final-set balance only:
    - `uniqueFamilies=14` but target is >=15;
    - `sameHeightMaxCount=13` but target is <=12.
- Key MAAS research signals are still present:
  - legal pass 20/20;
  - parking mass-stage pass 20/20;
  - formal diversity 6;
  - island coverage additive/subtractive/hybrid/sectional = 5/6/5/4;
  - two-tier masses 0;
  - mass-language max repeat 2;
  - evolved legal-pool children 45;
  - selected evolved children 2;
  - `agent_revision_trace.revision_type=critic_to_geometry_mutation`.
- Next implementation target:
  - replace the chained final-selection repair loops with one constraint
    satisfaction pass over the final 20 cards, optimizing family count, height
    histogram, language repeat, role-pattern repeat, formal diversity, and
    island quotas together.

2026-07-10 gpt-5.6-luna selector/VLM guard pass:

- Model routing update:
  - MAAS LLM default changed to `gpt-5.6-luna`;
  - MAAS preference VLM default changed to `gpt-5.6-luna`;
  - render harness now defaults both `MAAS_LLM_MODEL` and
    `MAAS_PREFERENCE_VLM_MODEL` to `gpt-5.6-luna`;
  - `gpt-5.6-luna` was smoke-tested against the OpenAI Responses API and
    returned HTTP 200.
- Runtime blocker fixed:
  - Added `MAAS_DISABLE_PARKING_NEO4J=1` so MAAS can use reviewed local
    structured parking seed rules without hanging on unavailable Neo4j routing.
  - This does not claim permit-final parking approval; it preserves the
    mass-stage parking/count gate used by the current verifier.
- Selector/VLM guard update:
  - Final VLM minimum enforcement had been breaking the prior balanced set.
  - Added projection repair after VLM/direct-LLM guards so VLM-scored candidates
    cannot destroy final diversity metrics.
  - Added canonical family/language normalization for composite massing:
    `reflected_pair`, `tapered_tower`, `branch_fin`, `courtyard_atrium`,
    `notched_void`, and `branch_atrium`.
- Latest verified artifact:
  - JSON: `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`.
  - PNG: `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`.
  - JSON verifier pass and PNG verifier pass.
  - Key metrics:
    `legalPass=20/20`, `parkingCountSatisfied=20/20`,
    `parkingMassStagePass=20/20`, `legacyFallback=0`,
    `uniqueFamilies=15`, `massLanguageDiversity=15`,
    `rolePatternMaxCount=2`, `sameHeightMaxCount=12`,
    `islandCoverage additive/subtractive/hybrid/sectional=4/6/6/4`,
    `formalPrincipleDiversity=8`, `architectureGradePass=20/20`.

2026-07-10 visual failure correction:

- User rejected the latest PNG despite JSON/PNG verifier pass.
- Important next-session memory:
  `docs/ai-session-memory/MAAS_VISUAL_FAILURE_HANDOFF_20260710.md`.
- Current conclusion:
  - `gpt-5.6-luna` and VLM are active, but VLM is currently a reranker, not a
    geometry generator.
  - The source candidate pool is visually weak: too many high surface-count
    cards, too many 6-7 volume fragments, and not enough clean anchor masses.
  - The next fix must add clean-mass readability gates before final VLM rerank:
    penalize or reject `surface_count > 48`, `visible_volume_count > 5`,
    `small_fragment_count > 1`, and over-composed evolution/crossover children.
  - Restore clean rectangular/stepped/podium-tower/courtyard anchors while
    preserving law and parking mass-stage gates.

2026-07-13 conversational revision correction:

- Keep an accepted mass as a stateful component graph and mutate only bounded
  stable-node parameters for local dialogue edits; never regenerate the full
  candidate population for every instruction.
- Every edit must retain legal, parking mass-stage, graph coherence, and
  architectural-order hard constraints. Rejection retains the last accepted
  graph and exposes the failed candidate/diff.
- Text intent translation is implemented. Reference-image provenance is
  recorded honestly, but image-conditioned VLM-to-graph mutation remains a
  distinct next milestone and must not be reported as complete.

2026-07-13 reference-image revision milestone complete:

- The prior pending item is superseded: client/reference images are now read by
  an OpenAI VLM and translated into strict bounded stable-node graph operations.
- VLM output never bypasses deterministic component compilation or legal,
  parking, coherence, and architectural-order hard gates.
- A real ArchDaily-image run modified the latest accepted mass and passed all
  gates. Keep image intent extraction modular and separate from population
  reranking and from direct geometry generation.

2026-07-13 quantitative continual-revision milestone:

- Reference revisions require measured before/after precedent improvement and
  bounded visible-quality regression in addition to all structural hard gates.
- Persist every revision attempt and user accept/reject/undo. Feed only the
  project-scoped operation preference profile back as soft VLM calibration;
  never permit learned preference to override law or parking.
- Treat visual-geometry-equivalent parameter edits as duplicates. The latest
  real ArchDaily probe was correctly rejected: reference +0.06, mass quality
  -0.1174, prior accepted feature retained.

2026-07-13 program-conditioned massing milestone:

- Program use is now a generator/search condition, not presentation metadata:
  housing, cafe, gymnasium, office, cultural, and retail have versioned massing
  profiles; housing/cafe/gym have separate graph-search/archive descriptors.
- The clean same-site six-seed benchmark passes with mean fit 0.9813 and a
  reviewed PNG. Keep law and parking ahead of program/aesthetic scoring.
- ArchDaily DB was expanded/reindexed to 274 unique references and 338 images,
  including dedicated cafe/restaurant and sports-architecture slices.
- RoboGrammar graph-valid expansion and MAP-Elites program niches are encoded
  as search priors. This is a method transfer, not a claim that RoboGrammar
  simulation or GLSO latent training is already running.
- Remaining completion criterion: demonstrate program separation and the same
  visual floor on final legal/parking-selected populations, not only six clean
  seeds. Do not call seed-fit success competition-grade completion.

2026-07-13 program visual loop correction:

- The rejected label-only program benchmark is superseded by data-driven role
  assemblies and a 312-candidate generate/evaluate/select loop. Coordinates,
  height bands, families, and mutation limits are versioned JSON priors rather
  than Python hardcoding or site-specific metre values.
- Latest loop rejected 69 candidates and retained six connected elites with
  minimum spatial architectural score 0.975. The PNG now visibly separates
  housing court/bars, cafe pavilion/threshold, and gym hall/service/entry.
- This resolves identical generic box decomposition for these program seeds.
  Final legal/parking population proof and richer non-rectilinear section/
  surface expression remain distinct completion checks.

2026-07-13 housing 20-mass archive milestone:

- Six housing topologies and bounded rotations now generate a true 20-candidate
  program archive. Latest loop evaluated 510, rejected 59, retained 20 across
  all six families, with spatial score mean 0.976/minimum 0.917.
- `generate_grammar_variants()` now receives these 20 program sequences in the
  real candidate pool; this is not PNG-only benchmark code.
- Latest artifacts: `maas-housing-20-program-archive-latest.{json,png}`.
- Remaining proof is a paid/full site-specific legal + parking + final selector
  rerun using these candidates; do not confuse the normalized legal-footprint
  archive with that final site result.

2026-07-13 creative primitive correction:

- The six-topology archive's wide-base/upper-box convergence is superseded.
  Assembly data/compiler now support normalized polygon plates, vertex
  mutation, and bounded rotation.
- Housing service candidates now contain ten topologies exactly twice each:
  clean anchors plus diagonal, pinwheel, sky bridge, polygonal cantilever, and
  zigzag terrace families. Latest 20-sheet loop evaluated 850/rejected 111;
  mean spatial score 0.9687, minimum 0.914.
- Actual grammar service probe confirms 20 program candidates/10 topologies in
  the 129-candidate pool. Preserve this topology floor through final selection.

2026-07-13 creative pre-legal archive milestone:

- Reference-led exploration now precedes program/legal projection. Buffered
  curved paths plus polygon/rotation primitives support ribbon-campus and
  voxel-cascade language in addition to the prior ten families.
- Latest creative board: 1,020 evaluated, 112 rejected, 20 retained across 12
  languages; spatial mean 0.9741/minimum 0.929.
- Requested 5x4 card output is at `maas-creative-20-card-latest.png`, with
  pending law/parking status shown honestly. Continuous roof shells and neutral
  renaming/extraction of housing-prefixed reusable roles remain follow-up work.

2026-07-13 program-neutral creative-first correction:

- Creative archive selection no longer uses housing program-fit or housing
  role-coverage scoring. Neutral `creative_*` seeds/roles are evaluated on form
  coherence, hierarchy, dominance, coverage, fragments, and effective surface
  complexity before any use, law, or parking projection.
- Real grammar generation now begins with 20 creative candidates spanning 12
  topology languages, then adds the requested building-use seeds. A cafe probe
  returned 131 total candidates with the creative archive first and two cafe
  seeds after it.
- Latest archive evaluated 1,020, retained 20, mean creative score 0.962,
  minimum 0.878. Selected MAAS regression is 56/56.
- Preserve the distinction between raw tessellated surfaces and logical mass
  complexity for buffered paths. Preserve the explicit `legal/parking not run`
  label until downstream hard projection actually succeeds.
- This completes the neutral mass-first pipeline correction, not continuous
  freeform roof/shell generation or a claim that every card is competition
  grade.

2026-07-13 reference-to-geometry closed-loop correction:

- Fixed the real evidence gap: explicit profiled 3D ribbon roof surfaces are
  now generated from path control points and rendered by both VLM preview and
  the 20-card board. Previously both systems saw only flat mass volumes.
- Voxel cascade now supports five connected interlocking blocks; coherence
  permits five but still rejects more than five or small fragments.
- Added eight independent languages beyond the two supplied references:
  bridge canyon, ring stack, fan plates, arc court, cluster village, folded
  spine, cross cantilever, and terrace bowl. The archive now selects 20
  distinct topology names rather than duplicating twelve families.
- Latest run: 1,700 evaluated, 20 selected, creative mean 0.9553, minimum
  0.891, benchmark pass; 58/58 selected tests pass.
- The method is viable, but the board still contains rectilinear anchors and
  is not yet universally competition-grade. Continue the loop on spatial
  smoothness, shell/roof continuity, and VLM-confirmed composition quality.

2026-07-13 architectural-language brain milestone:

- SourceSurface is now operational geometry, not dormant provenance. Profiled
  path roofs are compiled and rendered in both review cards and VLM previews.
- Creative archive now selects 20 distinct languages from 1,700 evaluated
  geometries: 114 rejected, 20 retained, mean 0.9633, minimum 0.934. Do not
  duplicate one language to fill the board.
- LEGO/voxel remains one bounded diversity group. The archive also preserves
  ribbon, arc court, folded spine, canyon bridge, fan plates, ring/courtyard,
  cantilever, terrace, bar, and village-cluster principles.
- Reference VLM principles now feed a topology-replacement language brain.
  Revision history prevents repeating the same topology, and every replacement
  remains subordinate to coherence, law, parking, order, and measured VLM
  improvement gates.
- Selected MAAS regression is 58/58. Remaining frontier is learned/unrestricted
  graph synthesis and higher-resolution structural/freeform surface validation,
  not another hardcoded per-site mass fix.

2026-07-13 stale legal artifact audit:

- The attached `maas-20-alt-latest` image is the older pre-creative legal
  artifact; its JSON has no `creative_mass_evidence` and must not be treated as
  the current 20-language proof.
- Fixed final preference guard consistency: five connected visible volumes are
  allowed everywhere; only more than five is volume fragmentation. Targeted
  selection/preference/creative tests pass 52/52.
- Reference images are breadth examples, not templates to clone.

2026-07-13 creative generator root correction:

- Do not accept renamed component-template count as architectural diversity.
- Creative generation now starts from program-neutral formal MassDSL graphs and
  mutates the full call graph; housing assemblies are not the creative default.
- Diversity acceptance uses measured geometry clusters. Current evidence is 20
  selected / 13 graph families / 16 geometry clusters from 1,700 evaluations,
  mean 0.881, minimum 0.753.
- This is improved but not competition-grade. Finish global organizing-rule
  evaluation and validated VLM topology proposal before claiming mass complete.

2026-07-13 box-bias red gate:

- Primary human evidence is now one isometric view per candidate; four-view
  evidence remains VLM-only diagnostics.
- Strict result is 4/20 sculptural versus 16/20 rectilinear extrusion/stack.
- Benchmark must remain red (`sculptural_geometry_count_below_8_box_bias`) until
  compiler primitives—not labels or selectors—produce at least 8/20 genuine
  bend/branch/folded/continuous-surface candidates.

2026-07-13 visual rollback/recovery:

- The old legal board is objectively more diverse and architecturally legible
  than the new creative archive board. Preserve that stronger baseline.
- Experimental creative archive is off in live generation unless explicitly
  enabled. Proven grammar/agent candidates lead the live pool again.
- Real PNU 20-up was regenerated without GPT. Diversity recovered, but five
  near-duplicate pairs and one underscaled candidate remain the next blockers.

2026-07-13 polygon quality and fundamental generator boundary:

- Compiler cleanup and coherence v2 now repair invalid plans conservatively
  and hard-reject hairline polygons, clipping-spike/short-edge debris, invalid
  plans, and excessive plan vertices. Targeted regression is 49/49.
- This is geometry hygiene, not the final generative advance. The mass goal is
  still blocked by the dominance of rectangular vertical extrusion.
- Next generator milestone is graph-native continuous ribbon/roof fields,
  carved solid/void monoliths, and connection/section continuity, with VLM
  failures mapped back to typed generator mutations. Keep the experimental
  path quarantined until the red box-bias benchmark and direct PNG audit pass.

2026-07-13 first continuous-surface generator milestone:

- Bend no longer aliases to a torqued box stack. It compiles to a normalized,
  graph-native `continuous_ribbon_field` with three connected plan ribbons and
  varying longitudinal/transverse roof heights.
- Folded, terraced-ribbon, torqued, and continuous-ribbon principles emit
  explicit non-flat SourceSurface roofs/facades. Legal SourceVolume proxies are
  retained separately for FAR/BCR/parking projection.
- Raw mesh surface count and effective logical surface count are distinct;
  order gates use the latter without deleting real facade geometry.
- Direct pool evidence: 109 variants, 33 profiled candidates, four surface
  principles, max raw/effective surfaces 49/18, no effective count above 36.
- This is piecewise-linear early massing. Continue toward smooth loft/subdivision
  fields, carved solid/void topology, structural continuity, and full 20-card
  legal/VLM visual acceptance before calling the mass generator complete.

2026-07-13 multi-mass visual loop verdict:

- Six full 20-mass boards were generated and visually inspected. Geometry-
  distance selection removed near duplicates, but strict actual-surface scoring
  leaves only 8/20 sculptural candidates; the competition target is 12/20 and
  board 6 is intentionally red.
- Sculptural evidence no longer trusts family names. It requires materialized
  continuous surface evidence and a real profiled roof.
- VLM critic vocabulary and mutation now support `too_box_like`,
  `weak_form_continuity`, `needs_profiled_surface`, and `needs_carved_void`,
  translating them into ribbon/folded/carved MassDSL geometry before the hard
  law/parking/review gates rerun. Targeted regression is 52/52.
- Next root implementation is additional independent continuous/formal
  operators. Selector quotas and topology labels cannot substitute for missing
  generator capability.

2026-07-13 site-aware architecture-language correction:

- Live architectural-language generation is now owned by
  `LLMArchitectAgent.propose_population`, and the proposal artifact records the
  owning agent and site-geometry status. The top-level orchestrator remains a
  review/router rather than a complete stateful negotiation engine.
- The language agent now receives dominant axis, aspect, compactness,
  concavity/boundary complexity and access context; the compiler generates in
  the same parcel-local frame and restores world geometry.
- Exterior silhouette tortuosity is a hard reject. Folded sections no longer use
  a full-site slab, restoring the missing folded family.
- Strict v9 result: 20 selected, 20 measured geometry languages, 12/20 actual
  profiled surfaces, zero near-duplicate pairs, numeric pass. Direct PNG review
  still marks weak branch/podium cards and repeated folded/ribbon language, so
  do not call the mass problem finished.
- Multi-site benchmark: rotated-long/trapezoid/concave-L, four languages each,
  12/12 compile and remain inside parcel. Next research layer is general
  CAADRIA-style volume/boundary formal variation plus real performance simulation
  and stateful critic/architect/geometry negotiation.

2026-07-13 program-first correction:

- Stop using housing as the default visual target. Validate neighborhood living
  and gymnasium first, with separate capacity policies and program typologies.
- The current accepted evidence is `maas-program-neighborhood-gym-v4.png`.
  The gym has a real graph-authored ridge; the neighborhood set is clean but is
  still below competition grade.
- Every future loop must inspect PNG. A high program/VLM score cannot rescue a
  tangled form: program proposals are capped at 4 source volumes and 28 raw
  surfaces. The rejected v3 neighborhood ribbon is the regression example.
## MAAS continuation checkpoint — 2026-07-13

- Do not accept fixed coordinate templates as agent/site-conditioned design.
- Finish and verify the site-design-field graph path, then render and directly inspect neighborhood-living and gymnasium PNGs.
- Adopt research mechanisms only when executable: explicit graph edits, bounded multi-path render/evaluate selection, and geometry/legal/collision rewards.
- Continue splitting the giant legal optimizer into candidate-generation, parking-projection, and preference-selection stages without changing hard legal/parking outcomes.
- Current work is not yet competition-grade and not complete.

### Visual failure correction — 2026-07-14

- Graph-author subtraction semantics and root-sibling support rebasing are now
  implemented and regression-tested; stale surface VLM cache reuse is fixed.
- The latest strict live loop is
  `maas-neighborhood-vlm-a2a-v29-rebased-support`: 2/20 survive. This is an
  honest `automatic_visual_floor_failed` result, not completion.
- Its main PNG still shows all 20 reviewed candidates with green/red decision
  badges and rejection reasons. Accepted-only output is diagnostic and must
  never replace the full 20-card comparison board.
- Do not restore the rejected rectangular cards or relax duplicate/box gates.
- Next objective: one fresh bounded live author batch driven by v29 rejection
  evidence, then raw PNG -> VLM/topology mutation -> strict final PNG. Require
  real open-court/canyon, branch/cluster, fold/shell, terraced landform,
  split-bridge and ribbon silhouettes before legal projection.
- Cross-program neighborhood/gym benchmark and targeted legal/parking hard
  gates pass. They do not prove architecture-competition visual quality.
### Mass-Brain boundary (2026-07-13 audit)

- Keep `D:/Data/Mass-Brain` shadow-only until context-aware graph compatibility,
  typed parameter bounds, topology-changing assistant edits, and blind PNG
  comparison are implemented.
- Use it now for append-only graph/evaluation/feedback memory, not as evidence
  that the 20-mass visual objective is solved.

2026-07-13 legal + design dual-objective checkpoint:

- Real gpt-5.4-mini author/VLM A2A is connected; it is no longer a rerank-only
  claim. v4-v6 remain visual failures and must not be marked complete.
- Capacity is a hard gate before visual ranking: neighborhood normalized FAR
  utilization >= 0.55; the real small PNU policy remains >= 0.70 unless the
  explicit brief selects another documented mode.
- The final legal review key now places image-backed VLM preference before soft
  program proxy differences, after law/parking/capacity hard gates.
- Preserve both raw/effective complexity: raw <= 48, effective <= 28, visible
  volumes <= 4. Do not eliminate continuous geometry merely because it needs
  profiled render faces.
- v6: 782 clean, 587 capacity-pass, 24 VLM parents, 17 children, only 19 above
  the 0.55 visual floor. Status is automatic visual floor failed.
- Next acceptance requires 20/20 visual-floor pass plus real PNU legal/parking
  pass and measured geometry retention after projection. PNG review is mandatory.

2026-07-13 reference-first v8 checkpoint:

- Actual ArchDaily/local reference images are now distilled before authoring
  and are also included in candidate VLM scoring. The active bottleneck is not
  proof of missing VLM data; it is graph-to-geometry retention, limited formal
  operators, and duplicate-forcing final selection.
- `split_bridge_connector` was repaired from four colliding boxes into two
  inhabited wings plus one short connector. v8 restores visible bridge/canyon
  and stepped-capacity languages but remains a visual failure due to repeated
  topologies and residual base-plus-upper-box cards.
- Never relax geometry distance merely to print 20 cards. The strict selector
  now records duplicate pairs and measured geometry-language count; fewer than
  20 is a valid failed generation that must trigger a bounded new author batch.
- Reference distillation v3 ran successfully on 12 images and produced 10
  recipes with two cluster, two stepped and two hybrid civic languages. A new
  v3-authored population and its geometry have not yet been visually validated.
- Current full evidence is `maas-neighborhood-vlm-a2a-v8.png/.json`; status is
  `automatic_visual_floor_failed`, not competition-grade and not complete.

2026-07-13 FAR + reference retrieval correction:

- v8 mean normalized FAR utilization is 0.7332; only 2/20 reach 0.90. It is not
  a full-capacity creative archive.
- Neighborhood research generation now uses capacity-first minimum 0.70 and
  target 0.90; capacity fit participates in selection, and at least 8/20 must
  meet target. Design-led programs retain their separate lower target.
- The ArchDaily DB already contains 274 projects/338 images. v3 selected six
  sports images, so retrieval concentration—not raw corpus size—was corrected.
- v4 stratified retrieval was executed successfully across 11 collections,
  including iconic BIG/OMA and massing-diversity references. Its 10 language
  recipes are ready, but a v4-authored full PNG has not yet been run or accepted.

### Durable archive + repeatability checkpoint (2026-07-14, v53)

- Current best mass-stage evidence is
  `maas-neighborhood-vlm-a2a-v53-full-frontier-repeatability-contract`:
  20/20, `review_required`, capacity target 9/8, 20 geometry languages, seven
  language groups and zero near duplicates.
- The visible archive and mutation-parent frontier are now separate. Final
  selection uses 14 persisted + 6 fresh candidates and preserves language,
  FAR, distance, authored and fresh/persisted constraints through rebalance.
- A 30-parent VLM frontier is the current verified quality setting. The reduced
  20-parent repeat returned 19 or missed capacity and is not equivalent.
- VLM scores are geometry-keyed and atomically persisted per completed
  candidate. The full loop is an offline archive-improvement job, not a
  synchronous service request.
- This is a stable clean mass-stage baseline, not competition-grade completion.
  Remaining priority is graph-native curved/continuous sheet and roof language,
  then cross-program testing, then real PNU legal/parking projection with
  geometry-retention measurement.

### Real PNU conditioning checkpoint (2026-07-14)

- PNU `1168011800104170004` now resolves live through VWorld and conditions the
  graph author/compiler in a local metric parcel frame; Neo4j is not required
  for this geometry path.
- v53 archive adaptation on the 264.13 m2 parcel is 20/20 within site and 16/20
  at normalized FAR utilization >= 0.90. This is site-fit evidence, not a claim
  of full legal/parking projection or competition-grade authorship.
- Next representation objective is variable-width curved sweep, branched field
  and continuous roof loft driven by typed graph parameters and parcel flow.
  `docs/images.jpg` supplies principles only; never hardcode its coordinates.

### Real PNU full-loop checkpoint (2026-07-14, v58)

- v58 is the current project-site mass-stage checkpoint for PNU
  `1168011800104170004`: live 264.13 m2 parcel, actual east road frontage,
  parcel/access-aware VLM, 20/20, FAR target 13/8, six language groups and zero
  near duplicates.
- Green in the candidate preview is the parcel; thick blue is the verified
  primary road frontage. Site/access geometry is part of VLM cache identity.
- Direct PNG review still finds excessive rectilinear bars/podiums. The next
  design representation work remains variable-width sweep, branched lane
  field and continuous roof loft. Legal/parking projection is still `not_run`.

### Rotation-invariant diversity correction (2026-07-14, in progress)

- The user correctly rejected v58's `zero near duplicates`: the prior distance
  metric was tied to world/site coordinates and treated a rotated or reflected
  copy of one mass language as novel.
- Intrinsic morphology is now isolated in
  `program_massing/morphology.py`: center, principal-frame alignment, uniform
  scale normalization, planar rotation/reflection matching and layered 3D
  symmetric difference. Search/selection consumes the policy through one
  function so a learned embedding or voxel metric can replace it later.
- GRL is integrated through the separate `grl_contract.py` adapter only as an
  evidence/lineage viewer. It is not the geometry generator and can be replaced
  without changing MassDSL/compiler/search.
- Do not call this verified until a same-PNU v59 full 20-card run is compared
  with v58 on intrinsic duplicate count, language distribution, FAR capacity,
  VLM quality and direct PNG review. An honest result may contain fewer than 20
  if the old board depended on pose-only duplicates.

### Editable field representation checkpoint (2026-07-14, v59-v66)

- v59 verifies rotation/reflection-invariant selection but returns 18/20; this
  is the correct failure, not a reason to refill with the same language.
- The mass graph can now author parcel-conditioned `parallel` or `branched`
  fields with variable plan width and continuous height profile. It compiles
  to separate conservative law/FAR proxy volumes and path-aligned quad-strip
  review/VLM surfaces.
- v65 real-PNU probe passes 6/6; branched FAR is 0.6459-0.7435 without generic
  box refill. The PNG is materially smoother than v64 but remains a
  representation checkpoint, not competition-grade completion.
- Fresh author populations must pass field topology coverage (parallel >= 1,
  branched >= 1). The first v66 author cache has no branched graph, so the next
  completed full loop must remain visually failed unless a genuinely new
  authored batch closes that deficit.
- v66 completed at 18/20 with FAR 12/8 and zero intrinsic repeats, but direct
  PNG review remains box-dominant and only one profiled continuous field is
  visible. Its status is correctly `automatic_visual_floor_failed`.
- v67 recompiles the cached author with the current field materializer: 19/20,
  FAR 12/8, no intrinsic repeats, but author parallel/branched is 3/0 and final
  selected is 1/0. Keep both topology audits as hard visual-floor gates.
- Preserve module boundaries: morphology policy, archive policy, GRL audit,
  parametric sweep, site design field, formal materializer and law/parking
  projection must remain replaceable independently.

### v74 visual failure correction (2026-07-14)

- Graph-native primary role is now the executable source-family authority;
  labels and optional support operations cannot turn a primary bend into an
  offset/array box recipe.
- Branched fields use one unioned clean legal/FAR solid plus editable profiled
  trunk/arm surfaces. Same-PNU v74 retains parallel 1 and branched 1 with zero
  measured duplicate pairs and 10 capacity-target candidates.
- v74 is still an honest 17/20 visual/technical fail. The accepted PNG remains
  too rectilinear, folded 1 and stepped 1 are missing, and legal/parking is
  `not_run`. Do not mark massing complete or competition-grade from this result.

### v79 strict language-evidence checkpoint (2026-07-14)

- Implement bounded adaptive author/compile/VLM replenishment with persistent
  graph/VLM caches and honest no-padding behavior.
- Bind box and weak-void critic failures; require real stepped progression and
  coherent non-uniform cluster fields.
- Extend typed MassDSL array grammar with parcel-relative hierarchy and stagger
  parameters. Do not replace this with named-form or parcel-coordinate
  templates.
- Preserve monotonic best-so-far across adaptive rounds. The current stricter
  best is v79 round 1 at 18/20; round 2 regressed and must not replace it.
- Current board is improved but still not competition-grade. Next priority is
  expressive graph-native section/surface/ground operations, then deterministic
  legal/FAR/parking projection with geometry-retention measurement.

### v85 closed-loop graph-mutation checkpoint (2026-07-15)

- The VLM now receives the actual executable component graph from
  `source_signature`, not an empty top-level placeholder, and structural edits
  target real node ids instead of invented `root` nodes.
- Reference retrieval reserves an image-backed counterfactual formal principle;
  VLM revision supports bounded typed bend control-point mutation; review
  selection preserves editable genotypes; critic archive and portfolio search
  are non-destructive and constraint-aware.
- The best real-PNU board is v85 at an honest 19/20, capacity target 10/8, all
  seven language groups and zero intrinsic silhouette repeats. v86 also reached
  19 but was not visually better and lost a cluster quota.
- This is meaningful progress, not completion. Several candidates remain
  conservative rectilinear masses, no accepted improved control-point child is
  yet proven, and legal/parking projection remains `not_run`.
- Do not add blind reference data, weaken gates, or refill with rotated boxes.
  Next close the capacity-bearing continuous-field/control-point admission gap,
  produce one genuinely distinct twentieth mass, then project law/FAR/parking
  and measure geometry retention.

### v90 technical 20-card closure (2026-07-15)

- Add bounded measured FAR feedback for authored bend fields. Preserve authored
  control points and topology; change only occupiable lane count, width and
  vertical overlap, with explicit provenance and at most two iterations.
- Preserve fresh authored exact graphs before search mutation. The previous
  boundary silently erased authored curve paths before VLM review.
- Prove the typed VLM geometry loop: a real branched-bend child improved from
  VLM 0.4233 to 0.575 with program score 0.959 and survived final selection.
- Expand the final bounded portfolio beam without weakening any compatibility
  gate. v90 reaches honest 20/20, capacity 11/8, seven language groups and zero
  silhouette repeats on the live project PNU.
- Keep the visual verdict strict: v90 is cleaner and diverse but still mostly
  rectilinear, not ArchDaily/BIG/OMA or competition-grade. Legal/parking remains
  `not_run`. Next work is graph-native roof-loft, non-orthogonal sectional fold
  and ground/void field representation, followed by deterministic legal/FAR/
  parking projection and geometry-retention measurement.

### v94 agent section-genotype checkpoint (2026-07-15)

- Add a graph-native site-conditioned section loft driven by 4-6 agent-authored
  normalized controls, not parcel coordinates or named roof templates.
- Keep one conservative law/FAR proxy separate from the continuous review/VLM
  mesh; remove cumulative helper boxes and keep the review mesh under the
  clean-surface budget.
- Treat section controls as real search and VLM-editable genotype data. Final
  portfolio search must reserve every available editable field while remaining
  feasible when the author population under-supplies them.
- v92 proves one true section loft can survive the full PNU loop. v93-v94 reach
  17/20 and v94 meets capacity 8/8, but both still miss a second continuous and
  cluster field. They are failed checkpoints, not completion.
- Post-v94 generic smooth/linear section interpolation is unit-tested but not
  yet full-loop PNG verified. Next run must use a fresh structurally validated
  author population and require multiple primary controlled section fields.
- Keep the visual standard strict: the current board remains mostly
  rectilinear and is not ArchDaily/BIG/OMA or competition-grade. Do not move to
  permit-complete claims until massing is visually accepted and deterministic
  law/FAR/parking geometry retention is measured.

### v98 oblique-envelope capability checkpoint (2026-07-15)

- Add a reusable agent-authored polygon-ring envelope, not a library of named
  museum forms. Bottom/shoulder/top rings can create wedge, lean, diagonal
  undercut and shifted polygon silhouettes while one conservative proxy remains
  available for law/FAR projection.
- Do not turn all 20 candidates into polygons. Final portfolio selection must
  keep `oblique_envelope` between one and two and preserve the other mass
  languages.
- Validate LLM plan controls as a real non-self-crossing polygon with scalar
  top heights. Invalid section-like point lists must be rejected before they
  silently fall back to a box.
- v98 proves one true oblique envelope survives the real PNU author/search/VLM
  loop: one volume, 15 surfaces, FAR/capacity fit 1.0. The mixed board is 20/20
  with zero measured repeat pairs, but visual status still fails because clean
  stepped capacity is only 2/3.
- Do not call v98 competition-grade or permit-complete. Next close the third
  stepped-capacity survivor without padding a weak cake-tier box, then run
  deterministic law/FAR/parking projection and geometry-retention measurement.
