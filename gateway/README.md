# ARR Gateway — Hermes Plugin

ARR (건축법규/토지분석) 도구를 Hermes Agent에 노출하는 plugin.

## 구조

```
gateway/
├── pyproject.toml          # entry-point: hermes_agent.plugins → arr-gateway
├── plugin.yaml             # manifest (provides_tools, requires_env)
├── README.md               # 이 파일
├── SOUL.md                 # ⭐ Agent 정체성/규칙 (Hermes 시스템 프롬프트 자동 주입)
├── skills/
│   └── land-analysis/
│       └── SKILL.md        # ⭐ 분석 사이클 playbook (LLM 행동 흐름)
└── arr_gateway/
    ├── __init__.py         # register(ctx) — Hermes에 도구 등록
    ├── schemas.py          # LLM-facing 도구 schema (flat dict, NOT OpenAI wrapper)
    └── tools.py            # 핸들러 — args dict + **kwargs → JSON string 반환
```

## 도메인 specialization 3 layer (Hermes 본체 수정 X)

| Layer | 무엇 | 우리 파일 |
|-------|------|---------|
| **Plugin tools** (Python) | 도메인 능력 | `arr_gateway/tools.py` |
| **SOUL.md** (Markdown) | 정체성/honesty rules | `SOUL.md` |
| **skills/SKILL.md** (Markdown) | 행동 사이클 | `skills/land-analysis/SKILL.md` |

→ Hermes upstream 코드 1줄도 안 고침. ClickAround도 같은 패턴.

## 도구 (현재 1개, 점진 확장)

| 도구 | 설명 | 호출 대상 |
|------|------|----------|
| `land_analyst` | 토지 규제 분석 (PNU/주소 → BCR/FAR/42규제) | AG-light Worker `/land/analyze` |

## 환경 변수

| KEY | 기본값 | 설명 |
|-----|--------|------|
| `AGLIGHT_URL` | `https://law-light-api.clickaround8.workers.dev` | AG-light Cloudflare Worker URL |

`~/.hermes/.env`에서 override 가능.

## 설치

```bash
# Hermes 설치된 환경에서
cd /home/ubuntu/gateway
pip install -e .

# 등록 확인
hermes plugins list   # arr-gateway 표시되어야 함
```

## 호출 흐름

```
Telegram 사용자 메시지 ("강남 역삼동 677 분석")
  ↓
Hermes Gateway (LLM = Qwen-plus 등)
  ↓ 도구 선택 (land_analyst)
arr_gateway/tools.land_analyst({"pnu_or_address": "강남 역삼동 677"})
  ↓ httpx POST
AG-light Worker (CF, ~5초)
  ↓
Vworld API + Vectorize + 법제처 API
  ↓ 응답 (BCR, FAR, 규제, 법조항)
JSON string 반환 → Hermes LLM이 자연어 가공 → Telegram 답변
```

## 다음 추가 예정 (별도 plan)

- legal_interpreter (법조항 검색)
- validator (규제 검증)
- mass_optimizer (NSGA-II 매스 최적화, Celery 비동기)
- floor_planner (5종 평면)
- spec_writer / structural_reviewer / cost_estimator / schedule_planner / document_summarizer

자세한 명세: `D:/DevCache/claude-data/projects/D--Data-25-ACE/memory/agent-architecture/agents-roster.md`

## 박제 (메모리 참조)

- 채택 결정: `memory/agent-architecture/decision.md`
- 인프라 (VM `158.180.66.165`): `memory/agent-architecture/infrastructure.md`
- 추상화 패턴: `memory/agent-architecture/execution-pattern.md`
- 원칙 3개 (N agent ≠ N server / 통일 추상화 / N agent ≠ N bot): `memory/agent-architecture/principle.md`

## ⚠️ Schema 형식 함정 (재발 방지)

OpenAI function-calling 형식의 `{"type": "function", "function": {...}}` wrapper는 사용 X.
Hermes는 flat dict: `{"name": "...", "description": "...", "parameters": {...}}`.

자세한 건 `arr_gateway/schemas.py` 상단 docstring + Hermes 공식 docs `/docs/guides/build-a-hermes-plugin`.
