# AG-CLI Agents
"""
협업 에이전트들

- base_collaborative.py: 대화 기능이 포함된 베이스 클래스
"""
from .base_collaborative import (
    CollaborativeAgent,
    MessageBusClient,
    SharedMemoryClient,
    create_a2a_agent
)

__version__ = "0.1.0"
__all__ = [
    "CollaborativeAgent",
    "MessageBusClient",
    "SharedMemoryClient",
    "create_a2a_agent"
]
