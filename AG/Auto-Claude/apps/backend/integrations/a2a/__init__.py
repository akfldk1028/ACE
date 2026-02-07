# A2A Integration - AutoGen Studio A2A Agent Registry Client
"""
AutoGen Studio A2A 에이전트 레지스트리와 통합합니다.
동적으로 등록된 에이전트를 발견하고 호출할 수 있습니다.
"""

from .client import A2AClient, A2AAgent
from .discovery import A2ADiscovery

__all__ = ["A2AClient", "A2AAgent", "A2ADiscovery"]
