"""
워크플로우 실행 테스트

AutoGen Studio에서 설계한 워크플로우가 Auto-Claude 어댑터를 통해 실행되는지 검증합니다.

테스트 흐름:
1. calculator_workflow.json 로드
2. PatternRegistry에 등록
3. ProjectExecutor로 실행
4. 각 노드가 해당 Auto-Claude 어댑터로 실행되는지 확인

실행:
    python -m pytest tests/test_workflow_execution.py -v
    또는
    python tests/test_workflow_execution.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.registry.pattern_registry import PatternRegistry
from src.designer.project_executor import ProjectExecutor
from src.designer.pattern_matcher import PatternMatcher
from src.designer.project_designer import ProjectSpec, ProjectStatus
from src.watcher.pattern_watcher import PatternEvent, PatternEventType


class MockAdapter:
    """테스트용 Mock 어댑터"""
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.calls = []
    
    async def execute(self, task, context):
        """Mock 실행 - 호출 기록만 저장"""
        self.calls.append({
            "task_id": task.id,
            "description": task.description,
            "context": context,
        })
        
        # Mock 결과 반환
        class MockResult:
            success = True
            output = {
                "agent": self.agent_type,
                "task_id": task.id,
                "message": f"Mock execution by {self.agent_type}",
            }
        
        return MockResult()


async def test_workflow_execution():
    """워크플로우 실행 테스트"""
    print("\n" + "="*60)
    print("워크플로우 실행 테스트")
    print("="*60)
    
    # 1. 워크플로우 로드
    workflow_path = Path(__file__).parent.parent / "patterns" / "calculator_workflow.json"
    
    if not workflow_path.exists():
        print(f"[FAIL] 워크플로우 파일 없음: {workflow_path}")
        return False
    
    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow_data = json.load(f)
    
    print(f"[OK] 워크플로우 로드: {workflow_data['name']}")
    print(f"   노드 수: {len(workflow_data['nodes'])}")
    
    # 2. PatternRegistry에 등록
    registry = PatternRegistry()
    await registry.initialize()
    
    event = PatternEvent(
        event_type=PatternEventType.CREATED,
        file_path=str(workflow_path),
        pattern_name=workflow_data["name"],
        pattern_data=workflow_data,
    )

    pattern = await registry.register(event)
    print(f"[OK] 패턴 등록: {pattern.id}")
    
    # 3. Mock 어댑터 생성
    adapters = {
        "AUTO_CLAUDE_PLANNER": MockAdapter("AUTO_CLAUDE_PLANNER"),
        "AUTO_CLAUDE_CODER": MockAdapter("AUTO_CLAUDE_CODER"),
        "AUTO_CLAUDE_QA_REVIEWER": MockAdapter("AUTO_CLAUDE_QA_REVIEWER"),
        "AUTO_CLAUDE_QA_FIXER": MockAdapter("AUTO_CLAUDE_QA_FIXER"),
    }
    print("[OK] Mock 어댑터 생성")
    
    # 4. ProjectExecutor 생성
    matcher = PatternMatcher(registry)
    executor = ProjectExecutor(
        registry=registry,
        matcher=matcher,
        adapters=adapters,
        auto_create_patterns=False,
    )
    print("[OK] ProjectExecutor 생성")
    
    # 5. 테스트 프로젝트 생성
    project = ProjectSpec(
        id="test_calc_project",
        name="Calculator Test Project",
        description="계산기 앱 테스트 프로젝트",
        request="계산기 앱 개발",
        goals=["계산기 앱 구현"],
        status=ProjectStatus.DRAFT,
        phases=[
            {
                "id": "phase_1",
                "name": "Development",
                "tasks": [
                    {
                        "id": "task_calc",
                        "description": "계산기 앱 개발",
                        "agent_type": "AUTO_CLAUDE_CODER",
                    }
                ],
            }
        ],
        metadata={"test": True},
    )
    
    # 6. 패턴 매칭
    matches = await matcher.match_project(project)
    print(f"[OK] 패턴 매칭 완료: {len(matches)} 태스크")
    
    for task_id, match in matches.items():
        if match.pattern_id:
            print(f"   {task_id} → {match.pattern_name} (confidence: {match.confidence:.2f})")
        else:
            print(f"   {task_id} → 직접 실행")
    
    # 7. 프로젝트 실행
    print("\n>> 프로젝트 실행 시작...")
    result = await executor.execute(project)
    
    print(f"\n[OK] 프로젝트 실행 완료")
    print(f"   상태: {result.status.value}")
    print(f"   성공률: {result.overall_success_rate*100:.1f}%")
    
    # 8. 어댑터 호출 확인
    print("\n>> 어댑터 호출 확인:")
    total_calls = 0
    for agent_type, adapter in adapters.items():
        if adapter.calls:
            print(f"   {agent_type}: {len(adapter.calls)} 호출")
            for call in adapter.calls:
                print(f"      - {call['task_id']}: {call['description'][:50]}...")
            total_calls += len(adapter.calls)
    
    if total_calls == 0:
        print("   [WARN] 어댑터 호출 없음 (패턴 매칭 실패 가능)")
    
    print("\n" + "="*60)
    print("테스트 완료")
    print("="*60)
    
    return result.status == ProjectStatus.COMPLETED


async def test_pattern_workflow_nodes():
    """패턴 워크플로우 노드 실행 테스트"""
    print("\n" + "="*60)
    print("패턴 워크플로우 노드 실행 테스트")
    print("="*60)
    
    # 1. 워크플로우 로드
    workflow_path = Path(__file__).parent.parent / "patterns" / "calculator_workflow.json"
    
    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow_data = json.load(f)
    
    # 2. Registry 초기화 및 패턴 등록
    registry = PatternRegistry()
    await registry.initialize()
    
    event = PatternEvent(
        event_type=PatternEventType.CREATED,
        file_path=str(workflow_path),
        pattern_name=workflow_data["name"],
        pattern_data=workflow_data,
    )
    pattern = await registry.register(event)
    
    # 3. Mock 어댑터
    adapters = {
        "AUTO_CLAUDE_PLANNER": MockAdapter("AUTO_CLAUDE_PLANNER"),
        "AUTO_CLAUDE_CODER": MockAdapter("AUTO_CLAUDE_CODER"),
        "AUTO_CLAUDE_QA_REVIEWER": MockAdapter("AUTO_CLAUDE_QA_REVIEWER"),
        "AUTO_CLAUDE_QA_FIXER": MockAdapter("AUTO_CLAUDE_QA_FIXER"),
    }
    
    # 4. Executor
    executor = ProjectExecutor(
        registry=registry,
        adapters=adapters,
    )
    
    # 5. _execute_pattern 직접 호출 테스트
    task_dict = {
        "id": "test_task",
        "description": "계산기 앱 개발",
        "agent_type": "AUTO_CLAUDE_CODER",
    }
    
    print(f"\n>> _execute_pattern 직접 호출...")
    print(f"   패턴 ID: {pattern.id}")
    print(f"   노드 수: {len(workflow_data['nodes'])}")
    
    result = await executor._execute_pattern(pattern.id, task_dict)
    
    print(f"\n[OK] 워크플로우 실행 완료")
    print(f"   실행 방법: {result.get('method')}")
    print(f"   실행된 노드: {result.get('nodes_executed')}")
    
    # 6. 노드별 실행 확인
    if "results" in result:
        print("\n>> 노드별 실행 결과:")
        for node_result in result["results"]:
            print(f"   {node_result['node_id']}: {node_result['agent_type']}")
    
    # 7. 어댑터 호출 순서 확인
    print("\n>> 어댑터 호출 순서:")
    call_order = []
    for agent_type, adapter in adapters.items():
        for call in adapter.calls:
            call_order.append((agent_type, call["task_id"]))
    
    for i, (agent, task_id) in enumerate(call_order, 1):
        print(f"   {i}. {agent}")
    
    # 의존성 순서 확인 (planner → coder → qa_reviewer → qa_fixer)
    expected_order = ["AUTO_CLAUDE_PLANNER", "AUTO_CLAUDE_CODER", 
                      "AUTO_CLAUDE_QA_REVIEWER", "AUTO_CLAUDE_QA_FIXER"]
    actual_order = [agent for agent, _ in call_order]
    
    if actual_order == expected_order:
        print("\n[OK] 의존성 순서 정확!")
    else:
        print(f"\n[WARN] 의존성 순서 불일치")
        print(f"   기대: {expected_order}")
        print(f"   실제: {actual_order}")
    
    print("\n" + "="*60)
    
    return result.get("method") == "workflow" and result.get("nodes_executed") == 4


if __name__ == "__main__":
    print("AG-ACE-BRIDGE 워크플로우 실행 테스트")
    print("="*60)
    print("개념: AutoGen Studio에서 설계 → Auto-Claude에서 24/7 실행")
    print("="*60)
    
    # 테스트 실행
    success1 = asyncio.run(test_pattern_workflow_nodes())
    success2 = asyncio.run(test_workflow_execution())
    
    if success1 and success2:
        print("\n[OK] 모든 테스트 통과!")
        sys.exit(0)
    else:
        print("\n[FAIL] 일부 테스트 실패")
        sys.exit(1)
