# A2A Tools - Auto-Claude 에이전트용 A2A 도구
"""
Auto-Claude의 코더/플래너 에이전트가 A2A 에이전트를 호출할 수 있는 도구.
"""
from typing import Any, Dict, List

from .client import A2AClient, call_a2a_agent
from .discovery import discover_agents, get_discovery, get_online_agents


async def list_a2a_agents() -> List[Dict[str, Any]]:
    """
    사용 가능한 A2A 에이전트 목록을 반환합니다.

    Returns:
        에이전트 목록 (name, url, description, is_online)
    """
    discovery = get_discovery()
    agents = await discovery.discover_all()
    await discovery.check_all_status(agents)

    return [
        {
            "name": a.name,
            "display_name": a.display_name,
            "url": a.url,
            "description": a.description,
            "is_online": a.is_online,
        }
        for a in agents
    ]


async def call_agent(agent_name: str, message: str) -> Dict[str, Any]:
    """
    A2A 에이전트를 호출합니다.

    Args:
        agent_name: 에이전트 이름 (예: poetry_agent, math_agent)
        message: 에이전트에게 보낼 메시지

    Returns:
        {"success": bool, "response": str, "agent": str}
    """
    discovery = get_discovery()

    # 에이전트 찾기
    agent = discovery.get_agent(agent_name)
    if not agent:
        # 캐시에 없으면 다시 발견
        await discovery.discover_all()
        agent = discovery.get_agent(agent_name)

    if not agent:
        return {
            "success": False,
            "response": f"에이전트 '{agent_name}'을 찾을 수 없습니다.",
            "agent": agent_name,
        }

    # 온라인 체크
    client = A2AClient(agent.url, timeout=agent.timeout)
    if not await client.is_online():
        return {
            "success": False,
            "response": f"에이전트 '{agent_name}'이 오프라인입니다. 서버를 먼저 시작하세요.",
            "agent": agent_name,
        }

    # 메시지 전송
    result = await client.send_message(message)

    return {
        "success": result["success"],
        "response": result.get("text", result.get("error", "Unknown response")),
        "agent": agent_name,
    }


# Claude Agent SDK MCP 도구로 등록할 함수들
def create_a2a_tools() -> List[Dict[str, Any]]:
    """
    Auto-Claude 에이전트에서 사용할 A2A 도구 정의 반환.

    이 도구들은 Claude Agent SDK의 tool permissions에 추가됩니다.
    """
    return [
        {
            "name": "list_a2a_agents",
            "description": "사용 가능한 A2A 에이전트 목록을 조회합니다. 시, 수학, 철학, GPU 등 전문 에이전트를 확인할 수 있습니다.",
            "function": list_a2a_agents,
        },
        {
            "name": "call_a2a_agent",
            "description": "A2A 프로토콜로 전문 에이전트를 호출합니다. agent_name과 message를 지정하세요. 예: poetry_agent에게 시 작성 요청",
            "function": call_agent,
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "호출할 에이전트 이름 (예: poetry_agent, math_agent, gpu_agent)",
                    },
                    "message": {
                        "type": "string",
                        "description": "에이전트에게 보낼 메시지/요청",
                    },
                },
                "required": ["agent_name", "message"],
            },
        },
    ]


# MCP 서버 설정용 도구 스키마
A2A_MCP_TOOLS = {
    "list_a2a_agents": {
        "description": "사용 가능한 A2A 에이전트 목록 조회",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    "call_a2a_agent": {
        "description": "A2A 프로토콜로 전문 에이전트 호출 (시, 수학, GPU 등)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": "에이전트 이름 (poetry_agent, math_agent 등)",
                },
                "message": {
                    "type": "string",
                    "description": "에이전트에게 보낼 메시지",
                },
            },
            "required": ["agent_name", "message"],
        },
    },
}
