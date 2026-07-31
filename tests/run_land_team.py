"""
Land Regulation Team - Actual Agent Collaboration Test
=======================================================
Runs the 3-agent SelectorGroupChat and captures all agent conversations.

Services required:
  - ARR Django :8000
  - law-domain-agents :8011
  - Neo4j :7687

Run: C:/Python313/python tests/run_land_team.py
"""
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# ============================================================
# Tool functions (same logic as MCP tools, sync wrappers)
# ============================================================

def search_land_zones() -> str:
    """21개 용도지역의 건폐율/용적률 규제 목록을 조회합니다."""
    import requests
    try:
        resp = requests.get("http://127.0.0.1:8000/land/zones/", timeout=30)
        resp.raise_for_status()
        return json.dumps(resp.json(), ensure_ascii=False, indent=2)
    except requests.exceptions.ConnectionError:
        return json.dumps({"error": "ARR Django 서버 미실행 (http://127.0.0.1:8000)"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def analyze_land_regulation(pnu_or_address: str, input_type: str = "pnu",
                            zones_json: str = "[]", include_law: bool = True) -> str:
    """PNU/주소/용도지역으로 건폐율, 용적률, 건축제한, 관련 법조항을 분석합니다."""
    import requests
    try:
        zones = json.loads(zones_json) if zones_json else []
    except json.JSONDecodeError:
        zones = []
    payload = {
        "input": pnu_or_address,
        "input_type": input_type,
        "zones": zones,
        "include_law": include_law
    }
    try:
        resp = requests.post("http://127.0.0.1:8000/land/analyze/", json=payload, timeout=30)
        resp.raise_for_status()
        return json.dumps(resp.json(), ensure_ascii=False, indent=2)
    except requests.exceptions.ConnectionError:
        return json.dumps({"error": "ARR Django 서버 미실행"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def resolve_land_pnu(input_val: str, input_type: str = "pnu") -> str:
    """주소를 PNU 코드로 변환하거나 PNU 코드를 검증/파싱합니다."""
    import requests
    payload = {"input": input_val, "input_type": input_type}
    try:
        resp = requests.post("http://127.0.0.1:8000/land/resolve/", json=payload, timeout=30)
        resp.raise_for_status()
        return json.dumps(resp.json(), ensure_ascii=False, indent=2)
    except requests.exceptions.ConnectionError:
        return json.dumps({"error": "ARR Django 서버 미실행"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def search_law_articles(query: str, limit: int = 10) -> str:
    """Neo4j 법률 DB에서 관련 법조항을 검색합니다 (법률+시행령+시행규칙)."""
    import requests
    payload = {"query": query, "limit": limit}
    try:
        resp = requests.post("http://127.0.0.1:8011/api/search", json=payload, timeout=30)
        resp.raise_for_status()
        return json.dumps(resp.json(), ensure_ascii=False, indent=2)
    except requests.exceptions.ConnectionError:
        return json.dumps({"error": "법률 검색 서버 미실행 (http://127.0.0.1:8011)"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


# ============================================================
# Build team programmatically
# ============================================================

async def run_team(task: str):
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.teams import SelectorGroupChat
    from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
    from autogen_core.tools import FunctionTool

    # Load API key from .env
    import os
    env_path = Path(__file__).parent.parent / "AG" / "autogen_a2a_kit" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("OPENAI_API_KEY="):
                os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()

    from autogen_ext.models.openai import OpenAIChatCompletionClient
    model = OpenAIChatCompletionClient(model="gpt-4o-mini")

    # Tools
    tool_zones = FunctionTool(search_land_zones, description="21개 용도지역의 건폐율/용적률 규제 목록 조회")
    tool_analyze = FunctionTool(analyze_land_regulation, description="PNU/주소/용도지역으로 건폐율, 용적률, 건축제한, 법조항 분석")
    tool_resolve = FunctionTool(resolve_land_pnu, description="주소→PNU 변환 또는 PNU 검증/파싱")
    tool_law = FunctionTool(search_law_articles, description="Neo4j 법률 DB에서 관련 법조항 하이브리드 검색 (법률+시행령+시행규칙)")

    # Agents
    land_analyst = AssistantAgent(
        name="land_analyst",
        description="토지 규제 데이터를 조회하고 건폐율/용적률/건축제한을 분석하는 에이전트",
        system_message=(
            "You are a Korean land regulation analyst. Given land information (PNU code, address, or zoning), "
            "you analyze building regulations including 건폐율 (BCR), 용적률 (FAR), and building restrictions. "
            "Use the land analysis tools to get regulation data. Always respond in Korean. "
            "When calling analyze_land_regulation, pass zones as a JSON array string in zones_json parameter, "
            "e.g. zones_json='[\"제1종일반주거지역\"]'."
        ),
        model_client=model,
        tools=[tool_zones, tool_analyze, tool_resolve],
        reflect_on_tool_use=False,
        tool_call_summary_format="{result}",
    )

    law_researcher = AssistantAgent(
        name="law_researcher",
        description="국토계획법/건축법 등 관련 법조항을 검색하고 법적 근거를 설명하는 에이전트",
        system_message=(
            "You are a Korean law article researcher specializing in land use regulation laws "
            "(국토계획법, 건축법). Search for relevant law articles using the search tool. "
            "The search returns results from 법률(법), 시행령, 시행규칙 3종류. "
            "Always cite specific article numbers (조/항) and explain in Korean."
        ),
        model_client=model,
        tools=[tool_law],
        reflect_on_tool_use=False,
        tool_call_summary_format="{result}",
    )

    report_writer = AssistantAgent(
        name="report_writer",
        description="토지 규제 분석 결과와 법조항 연구를 종합하여 구조화된 보고서를 작성하는 에이전트",
        system_message=(
            "You are a regulation report writer. Synthesize land regulation analysis and law article research "
            "into a clear, structured report in Korean. Include: "
            "1) 토지 정보, 2) 건폐율/용적률 제한, 3) 법적 근거 (법률/시행령/시행규칙 구분), "
            "4) 건축 시 주의사항. When complete, end with TERMINATE."
        ),
        model_client=model,
    )

    # Termination
    termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(max_messages=20)

    # Team
    team = SelectorGroupChat(
        participants=[land_analyst, law_researcher, report_writer],
        model_client=model,
        selector_prompt=(
            "You select which agent should handle each step. "
            "For land data and regulation numbers, pick land_analyst. "
            "For finding specific law articles (법률/시행령/시행규칙), pick law_researcher. "
            "For final summary report, pick report_writer.\n\n"
            "{roles}\n{history}\n\nReturn ONLY the agent name."
        ),
        termination_condition=termination,
        allow_repeated_speaker=False,
    )

    # Run and collect messages
    log_lines = []
    log_lines.append(f"Land Regulation Team - Agent Collaboration Log")
    log_lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_lines.append(f"Task: {task}")
    log_lines.append(f"Team: SelectorGroupChat (land_analyst, law_researcher, report_writer)")
    log_lines.append("=" * 80)
    log_lines.append("")

    print(f"\n{'='*80}")
    print(f"  TASK: {task}")
    print(f"{'='*80}\n")

    t0 = time.time()
    msg_count = 0

    async for message in team.run_stream(task=task):
        # message can be various types
        msg_type = type(message).__name__

        if hasattr(message, 'source') and hasattr(message, 'content'):
            msg_count += 1
            source = message.source
            content = str(message.content) if message.content else ""

            # Print to console
            print(f"\n--- [{msg_count}] {source} ---")
            if len(content) > 500:
                print(content[:500] + "...")
            else:
                print(content)

            # Log
            log_lines.append(f"[{msg_count}] Agent: {source}")
            log_lines.append(f"Type: {msg_type}")
            log_lines.append(f"Content:")
            for line in content.split("\n"):
                log_lines.append(f"  {line}")
            log_lines.append("")
        elif hasattr(message, 'messages'):
            # TaskResult
            elapsed = time.time() - t0
            log_lines.append("=" * 80)
            log_lines.append(f"COMPLETED in {elapsed:.1f}s, {msg_count} messages")
            print(f"\n{'='*80}")
            print(f"COMPLETED in {elapsed:.1f}s, {msg_count} messages")

    # Write log
    log_path = Path(__file__).parent / "collaboration_log.txt"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    print(f"\nLog written to: {log_path}")


async def main():
    task = (
        "서울 강남구의 제1종일반주거지역 토지에 대해 분석해주세요. "
        "PNU 코드는 1168011200101280003입니다. "
        "건폐율, 용적률, 관련 법조항(법률, 시행령, 시행규칙 모두)을 조사하고 "
        "종합 보고서를 작성해주세요."
    )
    await run_team(task)


if __name__ == "__main__":
    asyncio.run(main())
