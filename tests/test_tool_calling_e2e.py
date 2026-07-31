"""
E2E test: model_factory.py tool calling via AutoGen.

단일 AssistantAgent + 1 FunctionTool (search_laws)로 테스트.
AutoGen 런타임에서 tool call → arguments 파싱 → function 실행 → 결과 반환 확인.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "AG", "autogen_a2a_kit"))

async def main():
    try:
        from autogen_agentchat.agents import AssistantAgent
        from autogen_agentchat.conditions import MaxMessageTermination
        from autogen_agentchat.teams import RoundRobinGroupChat
        from autogen_core.tools import FunctionTool
        from AG_Cohub.model_factory import ClaudeCLIChatCompletionClient
    except ImportError as e:
        print(f"Import error: {e}")
        sys.exit(1)

    # Real tool calling law-domain-agents (:8011)
    def search_laws(query: str, limit: int = 5) -> str:
        """법조항을 검색합니다. query는 검색어, limit는 결과 수."""
        import urllib.request, urllib.parse, json as _j
        url = "http://localhost:8011/api/search"
        data = _j.dumps({"query": query, "limit": limit}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = _j.loads(resp.read().decode("utf-8"))
            articles = result.get("results", [])
            if not articles:
                return f"'{query}' 검색 결과 없음"
            lines = [f"'{query}' 검색 결과 {len(articles)}건:"]
            for a in articles[:limit]:
                title = a.get("title", "")
                content = a.get("content", "")[:100]
                score = a.get("score", 0)
                lines.append(f"- {title} (score={score:.3f}): {content}")
            return "\n".join(lines)
        except Exception as e:
            return f"검색 실패: {e}"

    tool = FunctionTool(search_laws, description="법조항을 검색합니다. query는 검색어, limit는 결과 수.")

    print(f"Tool schema: {tool.schema}")
    print(f"Tool name: {tool.schema.get('name')}")
    print(f"Tool params: {tool.schema.get('parameters', {}).get('properties', {}).keys()}")
    print()

    client = ClaudeCLIChatCompletionClient(model="claude-sonnet-4-5-20250929")

    agent = AssistantAgent(
        name="law_searcher",
        description="법조항 검색 테스트 에이전트",
        system_message=(
            "당신은 법조항 검색 에이전트입니다. "
            "사용자가 법규 관련 질문을 하면 search_laws 도구를 사용하여 검색하세요. "
            "도구 결과를 받으면 간단히 요약하고 TERMINATE를 출력하세요."
        ),
        model_client=client,
        tools=[tool],
        reflect_on_tool_use=False,
        tool_call_summary_format="{result}",
    )

    termination = MaxMessageTermination(max_messages=6)
    team = RoundRobinGroupChat(
        participants=[agent],
        termination_condition=termination,
    )

    task = "제1종일반주거지역의 건폐율과 용적률 관련 법조항을 검색해주세요."
    print(f"Task: {task}")
    print("=" * 60)

    t0 = asyncio.get_event_loop().time()
    result = await team.run(task=task)

    elapsed = asyncio.get_event_loop().time() - t0
    print("=" * 60)
    print(f"Elapsed: {elapsed:.1f}s")
    print(f"Messages: {len(result.messages)}")
    print()

    for i, msg in enumerate(result.messages):
        source = getattr(msg, 'source', '?')
        content = str(getattr(msg, 'content', ''))
        # Check for tool calls
        if hasattr(msg, 'content') and isinstance(msg.content, list):
            for item in msg.content:
                if hasattr(item, 'name') and hasattr(item, 'arguments'):
                    print(f"[msg {i}] {source}: TOOL_CALL name={item.name} args={item.arguments}")
                    continue
        # Truncate long text
        display = content[:200] + "..." if len(content) > 200 else content
        print(f"[msg {i}] {source}: {display}")

    # Check if any tool was actually called with non-empty arguments
    tool_called = False
    for msg in result.messages:
        if hasattr(msg, 'content') and isinstance(msg.content, list):
            for item in msg.content:
                if hasattr(item, 'arguments') and item.arguments != "{}":
                    tool_called = True
                    print(f"\nOK: Tool called with arguments: {item.arguments}")

    if not tool_called:
        print("\nFAIL: No tool was called with non-empty arguments")


if __name__ == "__main__":
    asyncio.run(main())
