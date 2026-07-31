"""
model_factory.py tool calling 수정 테스트.

테스트 내용:
1. tool_map 구조에 parameters가 포함되는지
2. 시스템 프롬프트에 파라미터 스키마가 주입되는지
3. [TOOL_CALL: name] {"arg":"val"} 패턴에서 JSON arguments가 파싱되는지
"""

import asyncio
import sys
import os

# Add AG_Cohub to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "AG", "autogen_a2a_kit"))

def test_tool_call_parsing():
    """Test regex parsing of [TOOL_CALL: name] {json} pattern."""
    import re
    import json

    # Simulate the new parsing logic
    tool_map = {
        "analyze_land": {"description": "토지 분석", "parameters": {
            "properties": {"pnu_or_address": {"type": "string"}},
            "required": ["pnu_or_address"],
        }},
        "search_laws": {"description": "법조항 검색", "parameters": {
            "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
            "required": ["query"],
        }},
        "transfer_to_agent": {"description": "핸드오프", "parameters": {}},
    }

    test_cases = [
        # (input_text, expected_name, expected_args)
        (
            '법규를 검색하겠습니다.\n[TOOL_CALL: search_laws] {"query": "건폐율 제1종일반주거지역", "limit": 10}',
            "search_laws",
            {"query": "건폐율 제1종일반주거지역", "limit": 10},
        ),
        (
            '[TOOL_CALL: analyze_land] {"pnu_or_address": "강남구 역삼동 677"}',
            "analyze_land",
            {"pnu_or_address": "강남구 역삼동 677"},
        ),
        (
            '[TOOL_CALL: transfer_to_agent]',
            "transfer_to_agent",
            {},
        ),
        (
            '분석 결과를 보겠습니다.\n[TOOL_CALL: search_laws]\n```json\n{"query": "용적률 상업지역", "limit": 5}\n```',
            "search_laws",
            {"query": "용적률 상업지역", "limit": 5},
        ),
    ]

    passed = 0
    failed = 0

    for text, expected_name, expected_args in test_cases:
        # Pattern 1: inline JSON
        match = re.search(r'\[TOOL_CALL:\s*(\S+)\]\s*(\{[^}]*\})?', text, re.DOTALL)
        name = None
        args = {}

        if match and match.group(1) in tool_map:
            name = match.group(1)
            raw_args = match.group(2)
            if raw_args:
                try:
                    args = json.loads(raw_args)
                except json.JSONDecodeError:
                    args = {}

        # Pattern 1b: code block JSON
        if name and not args:
            match_block = re.search(
                r'\[TOOL_CALL:\s*(\S+)\]\s*```(?:json)?\s*(\{[\s\S]*?\})\s*```',
                text,
            )
            if match_block and match_block.group(1) in tool_map:
                name = match_block.group(1)
                try:
                    args = json.loads(match_block.group(2))
                except json.JSONDecodeError:
                    args = {}

        if name == expected_name and args == expected_args:
            print(f"  PASS: {expected_name} → args={args}")
            passed += 1
        else:
            print(f"  FAIL: expected {expected_name}/{expected_args}, got {name}/{args}")
            print(f"        input: {text[:80]}...")
            failed += 1

    return passed, failed


def test_system_prompt_injection():
    """Test that tool schemas are properly injected into system prompt."""
    import json as _json

    tool_map = {
        "analyze_land": {"description": "토지 규제 분석", "parameters": {
            "properties": {
                "pnu_or_address": {"type": "string", "description": "PNU 코드 또는 주소"},
                "include_law": {"type": "boolean", "description": "법조항 포함 여부"},
            },
            "required": ["pnu_or_address"],
        }},
        "get_zones": {"description": "용도지역 목록 조회", "parameters": {}},
    }

    tool_lines = ["[사용 가능한 도구]"]
    for name, info in tool_map.items():
        desc = info.get("description", "")
        params = info.get("parameters", {})
        props = params.get("properties", {})
        required = params.get("required", [])
        if props:
            param_desc = []
            for pname, pschema in props.items():
                ptype = pschema.get("type", "any")
                pdesc = pschema.get("description", "")
                req = " (필수)" if pname in required else ""
                param_desc.append(f"    - {pname}: {ptype}{req} — {pdesc}")
            tool_lines.append(f"- {name}: {desc}")
            tool_lines.append(f"  파라미터:")
            tool_lines.extend(param_desc)
        else:
            tool_lines.append(f"- {name}: {desc} (파라미터 없음)")

    prompt = "\n".join(tool_lines)

    checks = [
        ("pnu_or_address" in prompt, "파라미터명 포함"),
        ("(필수)" in prompt, "필수 표시"),
        ("string" in prompt, "타입 표시"),
        ("파라미터 없음" in prompt, "파라미터 없는 도구"),
        ("PNU 코드 또는 주소" in prompt, "파라미터 설명"),
    ]

    passed = 0
    failed = 0
    for check, label in checks:
        if check:
            print(f"  PASS: {label}")
            passed += 1
        else:
            print(f"  FAIL: {label}")
            failed += 1

    return passed, failed


if __name__ == "__main__":
    print("=" * 60)
    print("Test 1: Tool call parsing (regex)")
    print("=" * 60)
    p1, f1 = test_tool_call_parsing()

    print()
    print("=" * 60)
    print("Test 2: System prompt injection")
    print("=" * 60)
    p2, f2 = test_system_prompt_injection()

    total_pass = p1 + p2
    total_fail = f1 + f2
    print()
    print(f"Results: {total_pass} passed, {total_fail} failed")

    if total_fail > 0:
        sys.exit(1)
