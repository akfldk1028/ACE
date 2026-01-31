"""
AutoGen → Auto-Claude Spec 변환기
=================================

AutoGen Studio 워크플로우를 Auto-Claude Spec 형식으로 변환.

★ 모델 동기화 (2026-01-24):
   - AutoGen Studio는 다양한 모델 지원 (GPT-4, Claude, Gemini, Ollama 등)
   - Auto-Claude는 Claude Agent SDK 전용 (Claude만 사용)
   - 변환 시 원본 모델 정보를 추출하고 경고 표시
   - Claude 등가 모델로 자동 매핑

사용법:
    converter = AutogenToSpec(auto_claude_path="D:/Data/25_ACE/Auto-Claude")
    spec_path = await converter.convert(
        task_description="계산기 앱 만들어줘",
        workflow_name="calculator_app"
    )
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import re


# ★ 모델 매핑 테이블: AutoGen 모델 → Claude 등가 모델
MODEL_MAPPING = {
    # OpenAI → Claude
    "gpt-4": "claude-sonnet-4-5-20250929",
    "gpt-4-turbo": "claude-sonnet-4-5-20250929",
    "gpt-4o": "claude-sonnet-4-5-20250929",
    "gpt-4o-mini": "claude-haiku-3-5-20241022",
    "gpt-3.5-turbo": "claude-haiku-3-5-20241022",
    "o1": "claude-opus-4-5-20251101",
    "o1-mini": "claude-sonnet-4-5-20250929",
    "o1-preview": "claude-opus-4-5-20251101",

    # Google → Claude
    "gemini-pro": "claude-sonnet-4-5-20250929",
    "gemini-1.5-pro": "claude-sonnet-4-5-20250929",
    "gemini-1.5-flash": "claude-haiku-3-5-20241022",
    "gemini-2.0-flash": "claude-sonnet-4-5-20250929",

    # Anthropic (그대로 사용)
    "claude-3-opus": "claude-opus-4-5-20251101",
    "claude-3-sonnet": "claude-sonnet-4-5-20250929",
    "claude-3-haiku": "claude-haiku-3-5-20241022",
    "claude-3.5-sonnet": "claude-sonnet-4-5-20250929",
    "claude-3.5-haiku": "claude-haiku-3-5-20241022",
    "claude-opus-4-5": "claude-opus-4-5-20251101",
    "claude-sonnet-4-5": "claude-sonnet-4-5-20250929",

    # Ollama/Local → Claude (기본 Sonnet)
    "llama3": "claude-sonnet-4-5-20250929",
    "llama3.1": "claude-sonnet-4-5-20250929",
    "llama3.2": "claude-sonnet-4-5-20250929",
    "mistral": "claude-sonnet-4-5-20250929",
    "mixtral": "claude-sonnet-4-5-20250929",
    "codellama": "claude-sonnet-4-5-20250929",
    "deepseek-coder": "claude-sonnet-4-5-20250929",
}


class AutogenToSpec:
    """AutoGen 워크플로우 → Auto-Claude Spec 변환기."""

    def __init__(
        self,
        auto_claude_path: str = "D:/Data/25_ACE/Auto-Claude",
        project_path: Optional[str] = None
    ):
        """
        Args:
            auto_claude_path: Auto-Claude 프로젝트 경로
            project_path: 타겟 프로젝트 경로 (None이면 Auto-Claude 자체)
        """
        self.auto_claude_path = Path(auto_claude_path)
        self.project_path = Path(project_path) if project_path else self.auto_claude_path
        self.specs_dir = self.project_path / ".auto-claude" / "specs"

    # ========================================
    # ★ 모델 동기화 메서드 (2026-01-24)
    # ========================================

    def _extract_model_config(
        self,
        autogen_workflow: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        AutoGen 워크플로우에서 모델 설정 추출.

        Args:
            autogen_workflow: AutoGen 워크플로우 JSON

        Returns:
            모델 설정 딕셔너리:
            {
                "original_model": "gpt-4",
                "original_provider": "openai",
                "claude_equivalent": "claude-sonnet-4-5-20250929",
                "model_switched": True,
                "warning": "Model switched from GPT-4 to Claude Sonnet 4.5"
            }
        """
        if not autogen_workflow:
            return {
                "original_model": None,
                "original_provider": None,
                "claude_equivalent": "claude-sonnet-4-5-20250929",
                "model_switched": False,
                "warning": None
            }

        # 모델 정보 추출 시도
        original_model = None
        original_provider = None

        # 1. 워크플로우 레벨 model_client 확인
        if "model_client" in autogen_workflow:
            model_client = autogen_workflow["model_client"]
            original_model = model_client.get("model", model_client.get("model_id"))
            original_provider = model_client.get("provider", model_client.get("api_type"))

        # 2. llm_config 확인
        if not original_model and "llm_config" in autogen_workflow:
            llm_config = autogen_workflow["llm_config"]
            if isinstance(llm_config, dict):
                original_model = llm_config.get("model")
                # config_list에서 추출
                config_list = llm_config.get("config_list", [])
                if config_list and isinstance(config_list, list):
                    first_config = config_list[0]
                    if isinstance(first_config, dict):
                        original_model = first_config.get("model", original_model)

        # 3. 노드별 에이전트에서 추출
        if not original_model and "nodes" in autogen_workflow:
            for node in autogen_workflow.get("nodes", []):
                if "model_client" in node:
                    mc = node["model_client"]
                    original_model = mc.get("model", mc.get("model_id"))
                    original_provider = mc.get("provider")
                    break
                if "llm_config" in node:
                    lc = node["llm_config"]
                    if isinstance(lc, dict):
                        original_model = lc.get("model")
                        break

        # 4. agents 배열에서 추출
        if not original_model and "agents" in autogen_workflow:
            for agent in autogen_workflow.get("agents", []):
                if "model_client" in agent:
                    mc = agent["model_client"]
                    original_model = mc.get("model", mc.get("model_id"))
                    original_provider = mc.get("provider")
                    break

        # Claude 등가 모델 찾기
        claude_equivalent = self._get_claude_equivalent(original_model)
        model_switched = original_model and not self._is_claude_model(original_model)

        # 경고 메시지 생성
        warning = None
        if model_switched:
            warning = f"⚠️ Model switched: {original_model} → {claude_equivalent} (Auto-Claude uses Claude SDK only)"

        return {
            "original_model": original_model,
            "original_provider": original_provider,
            "claude_equivalent": claude_equivalent,
            "model_switched": model_switched,
            "warning": warning
        }

    def _get_claude_equivalent(self, model: Optional[str]) -> str:
        """
        주어진 모델의 Claude 등가 모델 반환.

        Args:
            model: 원본 모델 이름

        Returns:
            Claude 모델 ID
        """
        if not model:
            return "claude-sonnet-4-5-20250929"  # 기본값

        model_lower = model.lower().strip()

        # 정확한 매핑 확인
        if model_lower in MODEL_MAPPING:
            return MODEL_MAPPING[model_lower]

        # 부분 매칭
        for key, value in MODEL_MAPPING.items():
            if key in model_lower or model_lower in key:
                return value

        # Claude 모델 패턴
        if "claude" in model_lower:
            if "opus" in model_lower:
                return "claude-opus-4-5-20251101"
            elif "haiku" in model_lower:
                return "claude-haiku-3-5-20241022"
            else:
                return "claude-sonnet-4-5-20250929"

        # GPT 패턴
        if "gpt-4" in model_lower or "gpt4" in model_lower:
            if "mini" in model_lower:
                return "claude-haiku-3-5-20241022"
            return "claude-sonnet-4-5-20250929"
        if "gpt-3" in model_lower or "gpt3" in model_lower:
            return "claude-haiku-3-5-20241022"

        # Gemini 패턴
        if "gemini" in model_lower:
            if "flash" in model_lower:
                return "claude-haiku-3-5-20241022"
            return "claude-sonnet-4-5-20250929"

        # 기본값: Sonnet (범용)
        return "claude-sonnet-4-5-20250929"

    def _is_claude_model(self, model: Optional[str]) -> bool:
        """모델이 Claude 모델인지 확인."""
        if not model:
            return False
        return "claude" in model.lower()

    def _get_next_spec_number(self) -> str:
        """다음 Spec 번호 반환 (001, 002, ...)."""
        if not self.specs_dir.exists():
            return "001"

        existing = []
        for folder in self.specs_dir.iterdir():
            if folder.is_dir():
                parts = folder.name.split("-", 1)
                if parts[0].isdigit():
                    existing.append(int(parts[0]))

        if not existing:
            return "001"
        return f"{max(existing) + 1:03d}"

    def _sanitize_name(self, name: str) -> str:
        """폴더 이름에 적합하게 변환."""
        # 한글 → 영어 변환 (간단 매핑)
        korean_to_english = {
            "계산기": "calculator",
            "앱": "app",
            "만들": "create",
            "어줘": "",
            "줘": "",
        }

        result = name.lower()
        for kr, en in korean_to_english.items():
            result = result.replace(kr, en)

        # 특수문자 제거, 공백 → 하이픈
        result = re.sub(r'[^\w\s-]', '', result)
        result = re.sub(r'\s+', '-', result.strip())
        result = re.sub(r'-+', '-', result)

        # 빈 문자열이면 기본값
        if not result or result == "-":
            result = "project"

        return result[:50]  # 최대 50자

    def _create_requirements_json(
        self,
        task_description: str,
        workflow_type: str = "feature"
    ) -> Dict[str, Any]:
        """requirements.json 생성."""
        return {
            "task_description": task_description,
            "workflow_type": workflow_type,
            "services_involved": ["main"],
            "complexity": "standard",
            "created_at": datetime.now().isoformat(),
            "source": "ag-ace-bridge"
        }

    def _create_context_json(
        self,
        task_description: str,
        files_to_modify: Optional[list] = None,
        files_to_reference: Optional[list] = None
    ) -> Dict[str, Any]:
        """context.json 생성."""
        return {
            "task_description": task_description,
            "files_to_modify": files_to_modify or [],
            "files_to_reference": files_to_reference or [],
            "scoped_services": ["main"],
            "created_at": datetime.now().isoformat()
        }

    def _create_spec_md(
        self,
        task_description: str,
        workflow_name: str,
        goals: Optional[list] = None
    ) -> str:
        """spec.md 생성."""
        goals_text = ""
        if goals:
            goals_text = "\n".join(f"- {goal}" for goal in goals)
        else:
            goals_text = f"- {task_description}"

        return f"""# {workflow_name}

## Overview

{task_description}

## Workflow Type

feature

## Task Scope

이 프로젝트는 AG-ACE-BRIDGE를 통해 자동 생성되었습니다.

### Goals

{goals_text}

## Success Criteria

1. 모든 기능이 정상 작동
2. 테스트 통과
3. 코드 품질 검증 완료

## QA Acceptance Criteria

- [ ] 기능 구현 완료
- [ ] 테스트 작성 및 통과
- [ ] 코드 리뷰 완료

---

*Generated by AG-ACE-BRIDGE at {datetime.now().isoformat()}*
"""

    def _create_implementation_plan(
        self,
        task_description: str,
        workflow_name: str,
        phases: Optional[list] = None
    ) -> Dict[str, Any]:
        """implementation_plan.json 생성."""
        if not phases:
            # 기본 phases
            phases = [
                {
                    "phase": 1,
                    "name": "Planning",
                    "chunks": [
                        {
                            "id": "1.1",
                            "description": "프로젝트 구조 분석 및 계획 수립",
                            "status": "pending"
                        }
                    ]
                },
                {
                    "phase": 2,
                    "name": "Implementation",
                    "chunks": [
                        {
                            "id": "2.1",
                            "description": task_description,
                            "status": "pending"
                        }
                    ]
                },
                {
                    "phase": 3,
                    "name": "Testing",
                    "chunks": [
                        {
                            "id": "3.1",
                            "description": "테스트 작성 및 실행",
                            "status": "pending"
                        }
                    ]
                }
            ]

        return {
            "feature": workflow_name,
            "workflow_type": "feature",
            "phases": phases,
            "created_at": datetime.now().isoformat(),
            "source": "ag-ace-bridge"
        }

    def convert(
        self,
        task_description: str,
        workflow_name: Optional[str] = None,
        autogen_workflow: Optional[Dict[str, Any]] = None,
        goals: Optional[list] = None
    ) -> Path:
        """
        AutoGen 워크플로우를 Auto-Claude Spec으로 변환.

        ★ 모델 동기화 (2026-01-24):
           AutoGen 워크플로우의 모델 설정을 추출하고, 비-Claude 모델인 경우 경고를 표시합니다.
           Auto-Claude는 Claude Agent SDK만 사용하므로, 실행 시 Claude 모델로 자동 매핑됩니다.

        Args:
            task_description: 태스크 설명 (예: "계산기 앱 만들어줘")
            workflow_name: 워크플로우 이름 (None이면 자동 생성)
            autogen_workflow: AutoGen 워크플로우 JSON (선택)
            goals: 목표 목록 (선택)

        Returns:
            생성된 Spec 폴더 경로
        """
        # ★ 모델 설정 추출 및 경고
        model_config = self._extract_model_config(autogen_workflow)
        if model_config["warning"]:
            print(f"[AutogenToSpec] {model_config['warning']}")

        # Spec 번호 및 이름
        spec_number = self._get_next_spec_number()

        if not workflow_name:
            workflow_name = self._sanitize_name(task_description)
        else:
            workflow_name = self._sanitize_name(workflow_name)

        spec_folder_name = f"{spec_number}-{workflow_name}"
        spec_path = self.specs_dir / spec_folder_name

        # 폴더 생성
        spec_path.mkdir(parents=True, exist_ok=True)

        # AutoGen 워크플로우에서 phases 추출 (있으면)
        phases = None
        if autogen_workflow and "nodes" in autogen_workflow:
            phases = self._convert_autogen_nodes(autogen_workflow["nodes"])

        # 파일 생성
        # 1. requirements.json (★ 모델 정보 포함)
        requirements = self._create_requirements_json(task_description)
        requirements["model_config"] = {
            "original_model": model_config["original_model"],
            "original_provider": model_config["original_provider"],
            "execution_model": model_config["claude_equivalent"],
            "model_switched": model_config["model_switched"],
        }
        with open(spec_path / "requirements.json", "w", encoding="utf-8") as f:
            json.dump(requirements, f, ensure_ascii=False, indent=2)

        # 2. context.json (★ 모델 정보 포함)
        context = self._create_context_json(task_description)
        context["model_info"] = {
            "original": model_config["original_model"],
            "execution": model_config["claude_equivalent"],
            "note": "Auto-Claude uses Claude Agent SDK. Original model was mapped to Claude equivalent."
        }
        with open(spec_path / "context.json", "w", encoding="utf-8") as f:
            json.dump(context, f, ensure_ascii=False, indent=2)

        # 3. spec.md (★ 모델 경고 포함)
        spec_md = self._create_spec_md(task_description, workflow_name, goals)
        if model_config["model_switched"]:
            model_note = f"""
## Model Information

> ⚠️ **Model Mapping Notice**
>
> Original model in AutoGen Studio: `{model_config['original_model']}`
> Execution model in Auto-Claude: `{model_config['claude_equivalent']}`
>
> Auto-Claude uses the Claude Agent SDK exclusively. The original model has been
> automatically mapped to an equivalent Claude model for execution.

"""
            # spec.md의 첫 번째 ## 뒤에 모델 정보 삽입
            parts = spec_md.split("## Overview", 1)
            if len(parts) == 2:
                spec_md = parts[0] + model_note + "## Overview" + parts[1]
        with open(spec_path / "spec.md", "w", encoding="utf-8") as f:
            f.write(spec_md)

        # 4. implementation_plan.json
        plan = self._create_implementation_plan(task_description, workflow_name, phases)
        plan["model_config"] = model_config
        with open(spec_path / "implementation_plan.json", "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)

        # 5. AutoGen 원본 저장 (있으면)
        if autogen_workflow:
            with open(spec_path / "autogen_workflow.json", "w", encoding="utf-8") as f:
                json.dump(autogen_workflow, f, ensure_ascii=False, indent=2)

        # 6. ★ 모델 동기화 정보 저장
        model_sync_info = {
            "sync_timestamp": datetime.now().isoformat(),
            "source": "autogen-studio",
            "target": "auto-claude",
            **model_config
        }
        with open(spec_path / "model_sync.json", "w", encoding="utf-8") as f:
            json.dump(model_sync_info, f, ensure_ascii=False, indent=2)

        print(f"[AutogenToSpec] Spec 생성 완료: {spec_path}")
        if model_config["model_switched"]:
            print(f"[AutogenToSpec] ⚠️ Model: {model_config['original_model']} → {model_config['claude_equivalent']}")
        return spec_path

    def _convert_autogen_nodes(self, nodes: list) -> list:
        """AutoGen 노드를 Auto-Claude phases로 변환."""
        phases = []
        phase_num = 1

        for node in nodes:
            agent_type = node.get("agent", "unknown")
            task = node.get("task", node.get("description", ""))
            node_id = node.get("id", f"node_{phase_num}")

            # 에이전트 타입에 따라 phase 이름 결정
            phase_name = "Implementation"
            if "planner" in agent_type.lower():
                phase_name = "Planning"
            elif "qa" in agent_type.lower() or "review" in agent_type.lower():
                phase_name = "Testing"
            elif "fixer" in agent_type.lower():
                phase_name = "Fixing"

            phases.append({
                "phase": phase_num,
                "name": phase_name,
                "chunks": [
                    {
                        "id": f"{phase_num}.1",
                        "description": task or f"{agent_type} 실행",
                        "status": "pending",
                        "agent_type": agent_type
                    }
                ]
            })
            phase_num += 1

        return phases


if __name__ == "__main__":
    # 테스트
    converter = AutogenToSpec()
    spec_path = converter.convert(
        task_description="간단한 계산기 앱 만들어줘",
        workflow_name="calculator_app",
        goals=[
            "기본 사칙연산 구현",
            "테스트 작성",
            "CLI 인터페이스"
        ]
    )
    print(f"생성된 Spec: {spec_path}")
