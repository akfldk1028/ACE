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