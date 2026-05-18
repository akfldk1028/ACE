# AG-light Server + Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** AG/ 4.7GB를 AG-light로 완전 대체. Python 통합서버(MCP+Bus+Memory+Cohub) + 하네스(4 에이전트+4 스킬) 구축.

**Architecture:** Worker(TS, 이미 완성)가 법제처API+규제계산 담당. Python FastAPI 서버가 MCP 도구+에이전트 협업 인프라 담당. .claude/ 하네스가 에이전트 팀 정의.

**Tech Stack:** Python 3.13, FastAPI, FastMCP, httpx, Docker

---

## File Map

### server/ (Python 통합서버)
| File | Responsibility | Source |
|------|---------------|--------|
| `server/main.py` | FastAPI 엔트리 (MCP+Bus+Memory 통합, :8200) | NEW |
| `server/mcp/__init__.py` | 패키지 | NEW |
| `server/mcp/tools.py` | MCP 도구 ~20개 (AutoGen Studio 제거) | SLIM from `AG-cli/mcp/autogen_studio_server.py` |
| `server/agents/__init__.py` | 패키지 | NEW |
| `server/agents/message_bus.py` | 에이전트간 대화 라우팅 | COPY from `AG-cli/mcp/message_bus.py` |
| `server/agents/shared_memory.py` | 정보 공유 + 이벤트 | COPY from `AG-cli/mcp/shared_memory.py` |
| `server/agents/collaborative.py` | CollaborativeAgent | COPY from `AG-cli/agents/base_collaborative.py` |
| `server/cohub/__init__.py` | 패키지 | NEW |
| `server/cohub/model_factory.py` | Claude CLI → 모델 클라이언트 | COPY from `AG_Cohub/model_factory.py` |
| `server/cohub/loader.py` | JSON 팀 로더 | COPY from `AG_Cohub/cohub_loader.py` |
| `server/cohub/sdk/*.py` | Claude SDK (7 files) | COPY from `AG_Cohub/sdk/` |
| `server/requirements.txt` | Python 의존성 | NEW |
| `server/Dockerfile` | Docker 빌드 | NEW |

### data/ (공유 데이터)
| File | Responsibility | Source |
|------|---------------|--------|
| `data/teams/*.json` | 19개 팀 JSON | MOVE from `JSON_MODULES/teams/` |
| `data/patterns/*.json` | 14개 협업 패턴 | COPY from `AG_Cohub/patterns/` |

### .claude/ (하네스)
| File | Responsibility |
|------|---------------|
| `.claude/agents/land-analyst.md` | 토지 규제 분석 에이전트 정의 |
| `.claude/agents/legal-interpreter.md` | 법률 해석 에이전트 정의 |
| `.claude/agents/design-advisor.md` | 건축 설계 자문 에이전트 정의 |
| `.claude/agents/qa-reviewer.md` | 품질 검증 에이전트 정의 |
| `.claude/skills/land-analysis/skill.md` | 토지 분석 워크플로우 |
| `.claude/skills/law-research/skill.md` | 법조항 연구 워크플로우 |
| `.claude/skills/regulation-check/skill.md` | 생성-검증 루프 |
| `.claude/skills/orchestrator/skill.md` | 팀 오케스트레이션 |

---

## Task 1: server/ 디렉토리 + 파일 복사

**Files:**
- Create: `server/main.py`, `server/requirements.txt`, `server/Dockerfile`
- Create: `server/mcp/__init__.py`, `server/agents/__init__.py`, `server/cohub/__init__.py`
- Copy: `server/agents/message_bus.py`, `server/agents/shared_memory.py`, `server/agents/collaborative.py`
- Copy: `server/cohub/model_factory.py`, `server/cohub/loader.py`, `server/cohub/sdk/` (7 files)

- [ ] **Step 1: 디렉토리 생성 + 파일 복사**

```bash
cd D:/Data/25_ACE/AG-light

# 디렉토리 생성
mkdir -p server/mcp server/agents server/cohub/sdk

# agents/ 복사
cp "D:/Data/25_ACE/AG/autogen_a2a_kit/AG-cli/mcp/message_bus.py" server/agents/
cp "D:/Data/25_ACE/AG/autogen_a2a_kit/AG-cli/mcp/shared_memory.py" server/agents/
cp "D:/Data/25_ACE/AG/autogen_a2a_kit/AG-cli/agents/base_collaborative.py" server/agents/collaborative.py

# cohub/ 복사
cp "D:/Data/25_ACE/AG/autogen_a2a_kit/AG_Cohub/model_factory.py" server/cohub/
cp "D:/Data/25_ACE/AG/autogen_a2a_kit/AG_Cohub/cohub_loader.py" server/cohub/loader.py
cp "D:/Data/25_ACE/AG/autogen_a2a_kit/AG_Cohub/sdk/"*.py server/cohub/sdk/

# __init__.py 생성
touch server/mcp/__init__.py server/agents/__init__.py server/cohub/__init__.py
```

- [ ] **Step 2: requirements.txt 작성**

```
# server/requirements.txt
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
httpx>=0.27.0
mcp[cli]>=1.27.0
websockets>=13.0
python-dotenv>=1.0.0
```

- [ ] **Step 3: Dockerfile 작성**

```dockerfile
# server/Dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8200
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8200"]
```

- [ ] **Step 4: cohub/sdk import 경로 수정**

`server/cohub/model_factory.py`에서 import 경로 수정:
```python
# 변경 전
from .sdk.config import AgentConfig, ToolProfile
from .sdk.client import ClaudeSDK, SDKResult

# 변경 후 (동일 — cohub/sdk/ 구조 유지)
from .sdk.config import AgentConfig, ToolProfile
from .sdk.client import ClaudeSDK, SDKResult
```
경로가 동일하므로 변경 불필요. 확인만.

- [ ] **Step 5: Commit**

```bash
git add server/
git commit -m "feat(ag-light): scaffold server/ with agents, cohub, sdk copied from AG"
```

---

## Task 2: MCP 도구 슬림화 (57→~20)

**Files:**
- Create: `server/mcp/tools.py`
- Reference: `AG/autogen_a2a_kit/AG-cli/mcp/autogen_studio_server.py` (1,955줄)

- [ ] **Step 1: autogen_studio_server.py 분석 — 유지할 도구 목록 확정**

유지할 도구 (~20개):
```
# 법 검색 (4) — Worker /law/* 호출
law_search, law_search_domain, law_domains, law_health

# 토지 (5) — Worker /land/* 호출
arr_land_analyze, arr_land_agent_analyze, arr_land_resolve, arr_land_zones, arr_land_stats

# 협업 (5) — 내부 MessageBus
send_message, broadcast_message, get_conversation_log, get_agent_conversation, get_bus_status

# 메모리 (6) — 내부 SharedMemory
store_decision, get_all_decisions, publish_event, get_events, get_shared_data, acquire_lock

# 유틸 (2)
health_check, get_version
```

제거 (~37개): execute_team, stream_team, execute_in_session, list/get/create/update/delete teams, sessions, gallery, A2A agents, validate, test, settings, api_spec, schema, locks 등.

- [ ] **Step 2: tools.py 작성 — 원본에서 유지할 도구만 추출**

원본 `autogen_studio_server.py`에서 해당 도구 함수들을 복사하되:
- `_get_http()`, `_call_api()` 헬퍼는 Worker URL 호출용으로 유지
- AutoGen Studio WebSocket 코드 (`_execute_via_ws`) 제거
- `AUTOGEN_STUDIO_URL` 환경변수 → `WORKER_URL` (AG-light Worker)
- `MESSAGE_BUS_URL`, `SHARED_MEMORY_URL` → 내부 함수 호출 (같은 프로세스)

```python
# server/mcp/tools.py 구조
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ag-light")

WORKER_URL = os.getenv("WORKER_URL", "https://law-light-api.xxx.workers.dev")

# ── 법 검색 (Worker 호출) ──
@mcp.tool()
async def law_search(query: str, limit: int = 10) -> str: ...

# ── 토지 (Worker 호출) ──
@mcp.tool()
async def arr_land_analyze(input: str, input_type: str = "auto", ...) -> str: ...

# ── 협업 (내부 MessageBus) ──
@mcp.tool()
async def send_message(from_agent: str, to_agent: str, content: str) -> str: ...

# ── 메모리 (내부 SharedMemory) ──
@mcp.tool()
async def store_decision(key: str, decision: str, rationale: str = "") -> str: ...
```

- [ ] **Step 3: main.py 작성 — FastAPI 통합 엔트리**

```python
# server/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn, os

from mcp.tools import mcp
from agents.message_bus import MessageBusRouter
from agents.shared_memory import SharedMemoryRouter

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Bus + Memory 초기화
    yield
    # Shutdown: 정리

app = FastAPI(title="AG-light Server", lifespan=lifespan)

# Bus + Memory를 FastAPI 라우터로 마운트
app.include_router(MessageBusRouter, prefix="/bus")
app.include_router(SharedMemoryRouter, prefix="/memory")

# MCP: streamable-http
# mcp.mount_to_fastapi(app, path="/mcp")  # FastMCP HTTP 모드

@app.get("/health")
async def health():
    return {"status": True, "service": "ag-light-server"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8200")))
```

- [ ] **Step 4: message_bus.py, shared_memory.py → FastAPI 라우터 적응**

원본은 standalone aiohttp 서버. FastAPI 라우터로 변환:
- `aiohttp.web.Application` → `fastapi.APIRouter`
- `aiohttp.web.WebSocketResponse` → `fastapi.WebSocket`
- 핵심 로직(MessageStore, SharedMemoryStore)은 그대로 유지

- [ ] **Step 5: 타입체크 + 실행 테스트**

```bash
cd server
pip install -r requirements.txt
python -c "from mcp.tools import mcp; print(f'{len(mcp.list_tools())} tools')"
python main.py  # :8200 시작 확인
```

- [ ] **Step 6: Commit**

```bash
git add server/
git commit -m "feat(ag-light): MCP tools (20), FastAPI main with Bus+Memory integration"
```

---

## Task 3: data/ — JSON_MODULES + patterns 이동

**Files:**
- Create: `data/teams/` (19 JSON files from JSON_MODULES)
- Create: `data/patterns/` (14 JSON files from AG_Cohub)

- [ ] **Step 1: 복사**

```bash
cd D:/Data/25_ACE/AG-light
mkdir -p data/teams data/patterns

cp D:/Data/25_ACE/JSON_MODULES/teams/*.json data/teams/
cp D:/Data/25_ACE/AG/autogen_a2a_kit/AG_Cohub/patterns/*.json data/patterns/
```

- [ ] **Step 2: cohub/loader.py 경로 수정**

```python
# server/cohub/loader.py 내의 데이터 경로를
# 기존: JSON_MODULES/teams/ 또는 AG_Cohub/patterns/
# 변경: ../data/teams/ 및 ../data/patterns/
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
TEAMS_DIR = DATA_DIR / "teams"
PATTERNS_DIR = DATA_DIR / "patterns"
```

- [ ] **Step 3: 검증**

```bash
ls data/teams/*.json | wc -l   # 19
ls data/patterns/*.json | wc -l  # 14
python -c "from server.cohub.loader import load_team; print(load_team('039_Land_Swarm'))"
```

- [ ] **Step 4: Commit**

```bash
git add data/
git commit -m "feat(ag-light): move teams (19) + patterns (14) to data/"
```

---

## Task 4: docker-compose.yml

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: docker-compose.yml 작성**

```yaml
# AG-light docker-compose.yml
services:
  server:
    build: ./server
    ports:
      - "8200:8200"
    environment:
      WORKER_URL: ${WORKER_URL:-https://law-light-api.workers.dev}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data:ro
```

- [ ] **Step 2: 빌드 + 실행 테스트**

```bash
docker compose build
docker compose up -d
curl http://localhost:8200/health
```

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml
git commit -m "feat(ag-light): docker-compose for server"
```

---

## Task 5: .claude/agents/ — 하네스 에이전트 정의

**Files:**
- Create: `.claude/agents/land-analyst.md`
- Create: `.claude/agents/legal-interpreter.md`
- Create: `.claude/agents/design-advisor.md`
- Create: `.claude/agents/qa-reviewer.md`

- [ ] **Step 1: land-analyst.md**

```markdown
---
name: land-analyst
model: opus
subagent_type: general-purpose
---

# Land Analyst (토지규제분석가)

## 핵심 역할
PNU 또는 주소를 받아 AG-light Worker의 /land/analyze API를 호출하고,
건폐율/용적률/높이제한 등 핵심 규제 수치를 정리하여 보고.

## 작업 원칙
1. 항상 Worker API를 통해 데이터 조회 (직접 계산하지 않음)
2. 응답의 regulations 필드에서 핵심 수치 추출
3. 41개 규제 중 비null 항목만 보고
4. zone_info의 unmatched가 있으면 경고

## 도구
- WebFetch: AG-light Worker /land/analyze, /land/resolve, /land/zones

## 입력/출력 프로토콜
- 입력: "주소: 강남구 역삼동 677" 또는 "PNU: 1168010100106770003"
- 출력: 용도지역, BCR%, FAR%, 높이제한m, 일조 적용 여부, restrictions 목록

## 팀 통신 프로토콜
- → legal-interpreter: "BCR {n}%, FAR {n}% 확인. {zone_name}. 관련 조항 검색 필요."
- ← legal-interpreter: 법적 근거 수신 시 보고서에 반영
```

- [ ] **Step 2: legal-interpreter.md**

```markdown
---
name: legal-interpreter
model: opus
subagent_type: general-purpose
---

# Legal Interpreter (법률해석가)

## 핵심 역할
규제 키워드를 받아 AG-light Worker의 /search + /law/* API로 관련 법조항을 검색하고,
법적 근거를 해석하여 보고.

## 작업 원칙
1. /search (hybrid mode)로 의미 검색 먼저
2. 발견된 법령의 /law/text로 전문 확인
3. 조/항/호 단위까지 정밀 인용
4. 예외 조항, 완화 가능성도 검토

## 도구
- WebFetch: AG-light Worker /search, /law/search, /law/text, /law/article, /law/ordinance

## 입력/출력 프로토콜
- 입력: land-analyst의 규제 키워드 (e.g., "제1종일반주거지역 건폐율")
- 출력: 법조항 인용 (법률명 제N조 제N항), 해석, 예외/완화

## 팀 통신 프로토콜
- ← land-analyst: 규제 수치 + 용도지역 수신
- → land-analyst: 법적 근거 전달
- → qa-reviewer: 검증 요청 시 법 데이터 제공
```

- [ ] **Step 3: design-advisor.md**

```markdown
---
name: design-advisor
model: opus
subagent_type: general-purpose
---

# Design Advisor (건축설계자문가)

## 핵심 역할
규제 조건을 받아 건축 매스 파라미터를 제안하고,
ARR Backend의 /design/jobs/ API로 최적화를 실행.

## 작업 원칙
1. land-analyst의 BCR/FAR/높이 제한을 constraint로 변환
2. 용도에 맞는 목적함수 선택 (주거→채광, 상업→외부공간)
3. 알고리즘 추천 (Additive/Subtractive/Grid)
4. Pareto front에서 상위 3개 설계 추출

## 도구
- WebFetch: ARR Backend /design/jobs/, /design/auto-constraints/

## 입력/출력 프로토콜
- 입력: 규제 조건 (BCR%, FAR%, height_m, sunlight, setback)
- 출력: 최적 설계 3안 (BCR%, FAR%, 층수, footprint 면적)

## 팀 통신 프로토콜
- ← land-analyst: 규제 수치
- → qa-reviewer: 설계안 검증 요청
- ← qa-reviewer: 위반 피드백 수신 → constraint 강화 → 재실행
```

- [ ] **Step 4: qa-reviewer.md**

```markdown
---
name: qa-reviewer
model: opus
subagent_type: general-purpose
---

# QA Reviewer (품질검증가)

## 핵심 역할
경계면 교차 비교: 설계안의 수치를 법규 제한과 대조하여 위반 항목을 찾아내고,
구체적 수정 제안을 제공.

## 작업 원칙
1. "존재 확인"이 아니라 "경계면 교차 비교"
2. 설계 수치 (BCR, FAR, height) vs 규제 상한값 비교
3. 위반 시 구체적 수정량 제안 (e.g., "BCR 62% → 60%: upper_scale 0.95→0.90")
4. 3회 이상 위반 반복 시 근본 원인 분석

## 도구
- Bash: 계산 검증 스크립트 실행
- WebFetch: Worker API로 규제값 재확인

## 입력/출력 프로토콜
- 입력: {design_metrics, regulation_limits}
- 출력: {violations: [{field, actual, limit, suggestion}], passed: bool}

## 팀 통신 프로토콜
- ← design-advisor: 설계안 수치 수신
- → design-advisor: 위반 목록 + 수정 제안 전달
- ← legal-interpreter: 필요 시 법 조문 확인 요청
```

- [ ] **Step 5: Commit**

```bash
git add .claude/agents/
git commit -m "feat(ag-light): harness agent definitions (4 agents)"
```

---

## Task 6: .claude/skills/ — 하네스 스킬 정의

**Files:**
- Create: `.claude/skills/land-analysis/skill.md`
- Create: `.claude/skills/law-research/skill.md`
- Create: `.claude/skills/regulation-check/skill.md`
- Create: `.claude/skills/orchestrator/skill.md`

- [ ] **Step 1: land-analysis/skill.md**

```markdown
---
name: land-analysis
description: "토지 규제 분석 워크플로우. PNU/주소 입력 → 용도지역+BCR/FAR+법조항 종합 보고. '토지 분석', '건폐율', 'PNU', '주소 분석', '규제 확인' 시 사용."
---

# 토지 규제 분석

## 워크플로우

1. **입력 파싱**: PNU(19자리) 또는 주소 판별
2. **규제 조회**: Worker POST /land/analyze 호출
3. **법조항 검색**: Worker POST /search (hybrid mode)
4. **보고서 작성**: 5개 섹션 형식

## API 호출

Worker URL: 환경변수 `WORKER_URL` 또는 wrangler.toml의 도메인

```bash
# 규제 조회
curl -X POST ${WORKER_URL}/land/analyze \
  -H "Content-Type: application/json" \
  -d '{"input": "강남구 역삼동 677", "zones": ["제1종일반주거지역"]}'

# 법조항 검색
curl -X POST ${WORKER_URL}/search \
  -d '{"query": "제1종일반주거지역 건폐율", "limit": 5}'
```

## 보고서 형식

1. **대상지 정보**: PNU, 주소, 용도지역
2. **핵심 규제**: BCR/FAR/높이제한 + 법적 근거
3. **주요 제약**: 일조, 가각전제, 인접대지 이격
4. **개발 가능성**: 최대 건축면적/연면적 추산
5. **실무 참고**: 조례 확인 필요 사항
```

- [ ] **Step 2: law-research/skill.md**

```markdown
---
name: law-research
description: "법조항 연구 워크플로우. 키워드→의미검색→원문조회→해석. '법조항', '건축법', '시행령', '조례', '판례' 시 사용."
---

# 법조항 연구

## 워크플로우

1. **키워드 추출**: 사용자 질문에서 법률 키워드 식별
2. **의미 검색**: Worker POST /search (hybrid)
3. **원문 조회**: Worker POST /law/text (MST로)
4. **조문 상세**: Worker POST /law/article (항/호/목)
5. **자치법규**: Worker POST /law/ordinance (필요 시)
6. **해석 정리**: 조/항/호 인용 + 예외/완화 분석

## API 호출 체인

```
/search {"query": "건폐율"}
  → 결과에서 MST 획득
  → /law/text {"mst": "...", "jo": "제84조"}
  → /law/article {"mst": "...", "jo": "제84조", "hang": "1"}
```
```

- [ ] **Step 3: regulation-check/skill.md**

```markdown
---
name: regulation-check
description: "생성-검증 루프. 매스/설계안을 법규 제한과 대조하여 위반 항목 검출+자동 수정 제안. '규제 검증', '법규 적합', '매스 검증' 시 사용."
---

# 생성-검증 루프

## 워크플로우

1. **설계안 수신**: design-advisor로부터 매스 메트릭스
2. **규제값 조회**: Worker /land/analyze 최신 규제
3. **교차 비교**:
   - BCR: footprint_area / site_area ≤ bcr_pct
   - FAR: total_floor_area / site_area ≤ far_pct
   - Height: max_height ≤ height_limit_m
   - Setback: min_distance ≥ adjacent_setback_m
4. **위반 시**: 구체적 수정량 계산 → design-advisor에 피드백
5. **반복**: max 3회. 3회 실패 시 근본 원인 보고.

## 검증 로직

```python
violations = []
if metrics["bcr"] > regs["bcr_pct"]:
    violations.append({
        "field": "bcr",
        "actual": metrics["bcr"],
        "limit": regs["bcr_pct"],
        "suggestion": f"upper_scale을 {metrics['bcr']/regs['bcr_pct']:.2f}배 축소"
    })
```
```

- [ ] **Step 4: orchestrator/skill.md**

```markdown
---
name: orchestrator
description: "팀 오케스트레이션. 종합 토지 분석 시 land-analyst→legal-interpreter→(design-advisor→qa-reviewer)→보고서. '종합 분석', '전체 보고서', '토지 종합' 시 사용."
---

# 오케스트레이션

## Phase 구조

### Phase 1: 팬아웃 분석 (병렬)
- land-analyst: /land/analyze 호출 → 규제 수치
- legal-interpreter: /search + /law/* → 법조항 해석
- 두 에이전트가 SendMessage로 발견 공유

### Phase 2: 설계 검증 (조건부, 설계 요청 시만)
- design-advisor: 매스 파라미터 제안 → ARR /design/
- qa-reviewer: 규제 적합 검증 → 위반 시 피드백 루프 (max 3)

### Phase 3: 종합
- 모든 결과를 5개 섹션 보고서로 통합
- 보고서 완료 후 TERMINATE

## 팀 구성

```
TeamCreate:
  name: "land-regulation-team"
  members: [land-analyst, legal-interpreter, design-advisor, qa-reviewer]
```
```

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/
git commit -m "feat(ag-light): harness skill definitions (4 skills)"
```

---

## Task 7: package.json + README 정리

**Files:**
- Modify: `package.json`
- Create: `README.md`

- [ ] **Step 1: package.json 업데이트**

```json
{
  "name": "ag-light",
  "private": true,
  "description": "건축법규 에이전트 플랫폼 — Worker(TS) + Server(Python) + Harness",
  "scripts": {
    "dev:worker": "cd worker && wrangler dev",
    "dev:server": "cd server && uvicorn main:app --reload --port 8200",
    "deploy:worker": "cd worker && wrangler deploy",
    "deploy:server": "docker compose up -d",
    "deploy:all": "npm run deploy:server && npm run deploy:worker",
    "build-vectors": "npx tsx scripts/build-vectors.ts"
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add package.json
git commit -m "chore(ag-light): update package.json with server scripts"
```

---

## Task 8: 최종 검증

- [ ] **Step 1: 파일 구조 확인**

```bash
find AG-light -not -path "*/node_modules/*" -not -name "package-lock.json" -type f | sort
# 예상: ~60 files (worker 25 + server 15 + data 33 + .claude 8 + root 5)
```

- [ ] **Step 2: Worker 타입체크**

```bash
cd worker && npx tsc --noEmit
# 0 errors
```

- [ ] **Step 3: Server import 확인**

```bash
cd server && python -c "
from cohub.model_factory import ClaudeCLIChatCompletionClient
from cohub.loader import load_team_json
from agents.message_bus import MessageStore
from agents.shared_memory import SharedMemoryStore
print('All imports OK')
"
```

- [ ] **Step 4: 크기 비교**

```bash
echo "AG-light:" && du -sh AG-light --exclude=node_modules
echo "AG (original):" && du -sh AG
```

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat(ag-light): complete platform — worker + server + harness + data"
```
