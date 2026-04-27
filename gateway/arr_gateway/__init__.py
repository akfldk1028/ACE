"""Hermes plugin entry point — ARR (건축법규/토지분석) tools + skills.

register(ctx)에서 다음 등록:
1. tools — Hermes LLM이 호출할 도구
2. skills — LLM 시스템 프롬프트에 포함될 행동 playbook

⚠️ skills/ 디렉토리에 SKILL.md만 두는 것으로는 Hermes가 못 봄.
   반드시 ctx.register_skill()로 명시 등록해야 함.
"""
from __future__ import annotations

from pathlib import Path

from . import schemas, tools

# Plugin 디렉토리 루트 (arr_gateway/ 의 parent = gateway/)
_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_SKILLS_DIR = _PLUGIN_ROOT / "skills"


def _load_skill(name: str) -> str | None:
    """skills/<name>/SKILL.md 파일 읽기. 없으면 None."""
    skill_path = _SKILLS_DIR / name / "SKILL.md"
    if not skill_path.exists():
        return None
    try:
        return skill_path.read_text(encoding="utf-8")
    except OSError:
        return None


def register(ctx) -> None:
    """Hermes plugin registration entry point.

    Hermes가 plugin 발견 시 호출. ctx는 register_tool / register_skill / register_hook
    등을 제공하는 컨텍스트 객체.
    """
    # === Tools ===
    ctx.register_tool(
        name="land_analyst",
        toolset="arr",
        schema=schemas.LAND_ANALYST,
        handler=tools.land_analyst,
    )

    # === Skills (LLM 행동 playbook) ===
    # SKILL.md 파일을 읽어서 내용 자체를 Hermes에 등록.
    # Hermes가 LLM 시스템 프롬프트 빌드 시 포함시킴.
    for skill_name in ("land-analysis",):
        content = _load_skill(skill_name)
        if content is not None:
            ctx.register_skill(skill_name, content)
