"""
Configuration management for AG-ACE-BRIDGE

Loads settings from environment variables and .env file.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Bridge Settings
    bridge_port: int = 8080
    bridge_log_level: str = "INFO"

    # Auto-Claude Connection
    auto_claude_path: str = "D:/Data/25_ACE/Auto-Claude/apps/backend"
    graphiti_enabled: bool = True
    anthropic_api_key: Optional[str] = None

    # AG Connection
    ag_autogen_url: str = "http://localhost:8000"
    ag_law_domain_url: str = "http://localhost:8001"

    # Neo4j (AG Memory)
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: Optional[str] = None

    # Task Queue
    queue_db_path: str = "./data/tasks.db"
    queue_max_retries: int = 3
    task_queue_db: str = "./data/tasks.db"

    # Projects (24/7 Factory)
    projects_dir: str = "./projects"

    # Pipeline Settings
    max_qa_iterations: int = 5
    default_priority: str = "medium"
    stage_timeout_seconds: int = 300

    # Orchestrator
    orchestrator_poll_interval: float = 1.0  # seconds
    orchestrator_batch_size: int = 1

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


def get_auto_claude_backend_path() -> Path:
    """Get the path to Auto-Claude backend"""
    settings = get_settings()
    return Path(settings.auto_claude_path)


def get_queue_db_path() -> Path:
    """Get the path to task queue database"""
    settings = get_settings()
    path = Path(settings.queue_db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
