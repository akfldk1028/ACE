"""LLM-facing tool schemas (Hermes flat dict format — NOT OpenAI wrapper).

Hermes register_tool spec (docs):
    schema = {"name": "...", "description": "...", "parameters": {...}}

OpenAI 형식의 {"type": "function", "function": {...}} wrapper는 사용 X.
"""

LAND_ANALYST = {
    "name": "land_analyst",
    "description": (
        "한국 토지 규제 분석. PNU 19자리 또는 주소(예: '강남구 역삼동 677') 입력하면 "
        "용도지역, 건폐율, 용적률, 높이제한, 42규제, 관련 법조항을 반환한다. "
        "사용 시점: 사용자가 PNU 또는 한국 주소로 토지/건축 규제를 알고 싶을 때. "
        "사용 안 함: 매스 생성/평면 배치/시방서 작성 — 이건 별도 도구 필요."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "pnu_or_address": {
                "type": "string",
                "description": (
                    "PNU 19자리 (예: '1168010100106770003') 또는 한국 주소 "
                    "(예: '강남구 역삼동 677', '서울시 강남구 역삼로 123')"
                ),
            }
        },
        "required": ["pnu_or_address"],
    },
}
