# A2A Discovery - 에이전트 자동 발견
"""
두 가지 방식으로 A2A 에이전트를 발견합니다:
1. AutoGen Studio Registry API 조회 (우선)
2. a2a_demo 폴더 직접 스캔 (fallback)
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

import httpx

from .client import A2AAgent, A2AClient


class A2ADiscovery:
    """
    A2A 에이전트 자동 발견 서비스.

    AutoGen Studio가 실행 중이면 Registry API를 사용하고,
    아니면 a2a_demo 폴더를 직접 스캔합니다.
    """

    # 알려진 A2A 에이전트 포트 (기본값)
    KNOWN_AGENTS = {
        "poetry_agent": {"port": 8003, "description": "시/문학 생성"},
        "philosophy_agent": {"port": 8004, "description": "철학적 분석"},
        "history_agent": {"port": 8005, "description": "역사 정보"},
        "calculator_agent": {"port": 8006, "description": "수학 계산"},
        "math_agent": {"port": 8007, "description": "수학 문제 해결"},
        "graphics_agent": {"port": 8008, "description": "그래픽 처리"},
        "gpu_agent": {"port": 8009, "description": "GPU 연산"},
        "gui_test_agent": {"port": 8120, "description": "GUI 자동화 (PyAutoGUI)"},
    }

    def __init__(
        self,
        autogen_studio_url: str = "http://localhost:8081",
        a2a_demo_path: Optional[str] = None
    ):
        """
        Args:
            autogen_studio_url: AutoGen Studio 서버 URL
            a2a_demo_path: a2a_demo 폴더 경로 (None이면 자동 탐색)
        """
        self.autogen_studio_url = autogen_studio_url.rstrip("/")
        self.a2a_demo_path = a2a_demo_path or self._find_a2a_demo_path()
        self._cached_agents: Dict[str, A2AAgent] = {}

    def _find_a2a_demo_path(self) -> Optional[str]:
        """a2a_demo 폴더 경로 자동 탐색"""
        possible_paths = [
            # 현재 프로젝트 기준
            Path(__file__).parent.parent.parent.parent.parent.parent / "AG" / "autogen_a2a_kit" / "a2a_demo",
            # 절대 경로들
            Path("D:/Data/25_ACE/AG/autogen_a2a_kit/a2a_demo"),
            Path("D:/Data/22_AG/autogen_a2a_kit/a2a_demo"),
            # 환경 변수
            Path(os.environ.get("A2A_DEMO_PATH", "")) if os.environ.get("A2A_DEMO_PATH") else None,
        ]

        for path in possible_paths:
            if path and path.exists() and path.is_dir():
                return str(path)
        return None

    async def discover_from_autogen_studio(self) -> List[A2AAgent]:
        """AutoGen Studio Registry API에서 에이전트 목록 조회"""
        try:
            url = f"{self.autogen_studio_url}/api/a2a/registry"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                agents = []
                for agent_data in data.get("agents", []):
                    agent = A2AAgent(
                        name=agent_data["name"],
                        display_name=agent_data.get("display_name", agent_data["name"]),
                        url=agent_data["url"],
                        description=agent_data.get("description", ""),
                        skills=agent_data.get("skills", []),
                        is_online=agent_data.get("is_online", False),
                        timeout=agent_data.get("timeout", 300),
                    )
                    agents.append(agent)
                    self._cached_agents[agent.name] = agent

                return agents

        except Exception as e:
            print(f"AutoGen Studio 연결 실패, 폴더 스캔으로 전환: {e}")
            return []

    def discover_from_folder(self) -> List[A2AAgent]:
        """a2a_demo 폴더에서 에이전트 스캔"""
        if not self.a2a_demo_path:
            return self._get_known_agents()

        a2a_demo = Path(self.a2a_demo_path)
        if not a2a_demo.exists():
            return self._get_known_agents()

        skip_dirs = {"action", "root_agent", "remote_agent", "remote_prime_checker", "__pycache__"}
        agents = []

        for agent_dir in a2a_demo.iterdir():
            if not agent_dir.is_dir() or agent_dir.name in skip_dirs:
                continue

            agent_py = agent_dir / "agent.py"
            if not agent_py.exists():
                continue

            try:
                content = agent_py.read_text(encoding="utf-8")

                # 에이전트 정보 파싱
                name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', content)
                port_match = re.search(r'port\s*[=:]\s*(\d+)', content)

                agent_name = name_match.group(1) if name_match else agent_dir.name
                agent_desc = desc_match.group(1) if desc_match else f"A2A Agent: {agent_name}"
                agent_port = port_match.group(1) if port_match else self.KNOWN_AGENTS.get(agent_dir.name, {}).get("port", 8000)

                agent = A2AAgent(
                    name=agent_name,
                    display_name=agent_name.replace("_", " ").title(),
                    url=f"http://localhost:{agent_port}",
                    description=agent_desc,
                    skills=[],
                    is_online=False,  # 나중에 체크
                )
                agents.append(agent)
                self._cached_agents[agent.name] = agent

            except Exception as e:
                print(f"Failed to parse {agent_py}: {e}")

        return agents if agents else self._get_known_agents()

    def _get_known_agents(self) -> List[A2AAgent]:
        """알려진 기본 에이전트 목록 반환"""
        agents = []
        for name, info in self.KNOWN_AGENTS.items():
            agent = A2AAgent(
                name=name,
                display_name=name.replace("_", " ").title(),
                url=f"http://localhost:{info['port']}",
                description=info["description"],
                skills=[],
                is_online=False,
            )
            agents.append(agent)
            self._cached_agents[name] = agent
        return agents

    async def discover_all(self) -> List[A2AAgent]:
        """
        모든 방법으로 에이전트 발견 (우선순위):
        1. AutoGen Studio Registry
        2. a2a_demo 폴더 스캔
        3. 알려진 기본 목록
        """
        # 1. AutoGen Studio 시도
        agents = await self.discover_from_autogen_studio()
        if agents:
            return agents

        # 2. 폴더 스캔
        return self.discover_from_folder()

    async def check_agent_status(self, agent: A2AAgent) -> bool:
        """에이전트 온라인 상태 확인"""
        client = A2AClient(agent.url, timeout=5)
        is_online = await client.is_online()
        agent.is_online = is_online
        return is_online

    async def check_all_status(self, agents: List[A2AAgent]) -> Dict[str, bool]:
        """모든 에이전트 상태 확인"""
        results = {}
        for agent in agents:
            results[agent.name] = await self.check_agent_status(agent)
        return results

    def get_agent(self, name: str) -> Optional[A2AAgent]:
        """캐시에서 에이전트 조회"""
        return self._cached_agents.get(name)

    def get_online_agents(self) -> List[A2AAgent]:
        """온라인 에이전트만 반환"""
        return [a for a in self._cached_agents.values() if a.is_online]


# 싱글톤 인스턴스
_discovery: Optional[A2ADiscovery] = None


def get_discovery() -> A2ADiscovery:
    """Discovery 싱글톤 인스턴스 반환"""
    global _discovery
    if _discovery is None:
        _discovery = A2ADiscovery()
    return _discovery


async def discover_agents() -> List[A2AAgent]:
    """에이전트 발견 간편 함수"""
    discovery = get_discovery()
    return await discovery.discover_all()


async def get_online_agents() -> List[A2AAgent]:
    """온라인 에이전트 목록 반환"""
    discovery = get_discovery()
    agents = await discovery.discover_all()
    await discovery.check_all_status(agents)
    return discovery.get_online_agents()
