# AG-light 전체 설계 — 에이전트 플랫폼 + 하네스

## 1. 목적

AG/ 4.7GB를 **AG-light**로 완전 대체. 건축법규 전용 에이전트 플랫폼.
- 런타임 2개: Worker(TS) + Python 통합서버
- AutoGen Studio 의존 제거
- Harness 패턴으로 에이전트 팀 설계

## 2. 폴더 구조

```
AG-light/
│
├── worker/                          # ── 런타임 1: Cloudflare Worker (TS) ──
│   ├── src/
│   │   ├── index.ts                 #   Hono entry (Env: LAW_OC, VWORLD_API_KEY, OPENAI_API_KEY)
│   │   ├── routes/
│   │   │   ├── health.ts            #   GET /health
│   │   │   ├── search.ts            #   POST /search (Vectorize + 법제처 RRF)
│   │   │   ├── land.ts              #   POST /land/analyze, /resolve, GET /zones
│   │   │   └── law.ts               #   POST /law/search, /text, /article, /ordinance
│   │   ├── services/                #   ARR land/ 포팅 (4 files)
│   │   ├── lib/                     #   korean-law-mcp 원본 (7 files)
│   │   └── data/
│   │       └── zoning-limits.json   #   21개 용도지역 규제
│   ├── wrangler.toml
│   ├── tsconfig.json
│   └── package.json
│
├── server/                          # ── 런타임 2: Python 통합서버 (FastAPI) ──
│   ├── main.py                      #   엔트리: MCP + Bus + Memory 통합, uvicorn :8200
│   │
│   ├── mcp/                         #   MCP 도구 (Claude Code 인터페이스)
│   │   ├── __init__.py
│   │   └── tools.py                 #   ~20 도구 (법규+토지+협업, AutoGen Studio 제거)
│   │
│   ├── agents/                      #   에이전트 협업 인프라
│   │   ├── __init__.py
│   │   ├── message_bus.py           #   에이전트간 대화 라우팅
│   │   ├── shared_memory.py         #   정보 공유 + 이벤트
│   │   └── collaborative.py         #   CollaborativeAgent (Claude CLI 기반)
│   │
│   ├── cohub/                       #   모델 + 팀 로더
│   │   ├── __init__.py
│   │   ├── model_factory.py         #   Claude CLI → 모델 클라이언트
│   │   ├── loader.py                #   JSON 팀 로더
│   │   └── sdk/                     #   Claude SDK (6 files, 929줄)
│   │
│   ├── requirements.txt
│   └── Dockerfile
│
├── .claude/                         # ── 하네스: 에이전트 + 스킬 정의 ──
│   ├── agents/
│   │   ├── land-analyst.md          #   토지 규제 분석 에이전트
│   │   ├── legal-interpreter.md     #   법률 해석 에이전트
│   │   ├── design-advisor.md        #   건축 설계 자문 에이전트
│   │   └── qa-reviewer.md           #   경계면 교차 검증 에이전트
│   │
│   └── skills/
│       ├── land-analysis/
│       │   └── skill.md             #   토지 분석 워크플로우
│       ├── law-research/
│       │   └── skill.md             #   법조항 검색+해석 워크플로우
│       ├── regulation-check/
│       │   └── skill.md             #   생성-검증 루프 (매스→법규 적합)
│       └── orchestrator/
│           └── skill.md             #   팀 오케스트레이션
│
├── data/                            # ── 공유 데이터 ──
│   ├── teams/                       #   19개 팀 JSON (JSON_MODULES에서 이동)
│   │   ├── 038_Land_Regulation.json
│   │   ├── 039_Land_Swarm.json
│   │   ├── 040_Land_Light.json
│   │   └── cohub_*.json
│   └── patterns/                    #   15개 협업 패턴 JSON
│       ├── 01_sequential.json
│       └── ...
│
├── scripts/
│   └── build-vectors.ts             #   임베딩 파이프라인
│
├── docker-compose.yml               #   server 실행
├── package.json                     #   npm scripts
└── README.md
```

## 3. 하네스 설계

### 3-1. 아키텍처 패턴: 파이프라인 + 생성-검증

```
[오케스트레이터]
    │
    ├── Phase 1: 팬아웃 분석
    │   ├── land-analyst (Worker /land/analyze 호출)
    │   └── legal-interpreter (Worker /search + /law/* 호출)
    │       (병렬, SendMessage로 발견 공유)
    │
    ├── Phase 2: 생성-검증 루프 (설계 자문 시)
    │   ├── design-advisor (매스 파라미터 제안)
    │   └── qa-reviewer (법규 적합 검증 → 위반 시 피드백 → 재생성)
    │
    └── Phase 3: 종합
        └── 오케스트레이터가 결과 종합 → 보고서
```

### 3-2. 에이전트 정의 (4개)

**land-analyst** — 토지 규제 분석
- 역할: PNU/주소 → Worker /land/analyze → 규제 수치 정리
- 도구: Worker API 호출 (fetch)
- 산출물: 용도지역, BCR/FAR, 높이제한, 규제 목록

**legal-interpreter** — 법률 해석
- 역할: 규제 키워드 → Worker /search + /law/text → 조문 해석
- 도구: Worker API 호출 (fetch)
- 산출물: 법적 근거, 예외 조항, 완화 가능성

**design-advisor** — 건축 설계 자문
- 역할: 규제 조건 → 매스 파라미터 제안 → ARR /design/jobs/ 호출
- 도구: ARR Backend API 호출
- 산출물: 최적 매스 옵션, Pareto front

**qa-reviewer** — 품질 검증
- 역할: 경계면 교차 비교 (API 응답 vs 기대 스키마, 규제 vs 매스)
- Harness 핵심: "존재 확인이 아니라 경계면 교차 비교"
- 산출물: 위반 목록, 수정 제안

### 3-3. 스킬 정의 (4개)

**land-analysis** — 토지 분석 워크플로우
- 트리거: "토지 분석", "건폐율", "PNU", "주소 분석"
- 워크플로우: 주소→PNU→용도지역→규제계산→법조항→보고서

**law-research** — 법조항 연구
- 트리거: "법조항", "건축법", "시행령", "조례"
- 워크플로우: 키워드→의미검색→원문조회→해석

**regulation-check** — 생성-검증 루프
- 트리거: "규제 검증", "법규 적합", "매스 검증"
- 워크플로우: 매스→규제대조→위반시피드백→재생성(max 3회)

**orchestrator** — 팀 오케스트레이션
- 트리거: "종합 분석", "전체 보고서"
- 워크플로우: Phase 1(분석) → Phase 2(검증) → Phase 3(종합)

### 3-4. 팀 통신 프로토콜

```
land-analyst ──SendMessage──→ legal-interpreter
  "BCR 60%, FAR 200% 확인. 제1종일반주거. 관련 조항 검색 필요."

legal-interpreter ──SendMessage──→ land-analyst
  "시행령 §84① 확인. 건폐율 60% 정확. 단, 조례 완화 가능성 확인 필요."

qa-reviewer ──SendMessage──→ design-advisor
  "BCR 위반: footprint 62% > 60%. upper_scale 0.95→0.90 조정 권장."
```

## 4. MCP 도구 (~20개)

### 유지 (AG-light 전용)
| 카테고리 | 도구 | 호출 대상 |
|---------|------|----------|
| 법 검색 (4) | law_search, law_search_domain, law_domains, law_health | Worker /law/* |
| 토지 (5) | arr_land_analyze, arr_land_agent_analyze, arr_land_resolve, arr_land_zones, arr_land_stats | Worker /land/* |
| 협업 (5) | send_message, broadcast, get_log, get_conversation, get_bus_status | 내부 MessageBus |
| 메모리 (6) | store/get/get_all decisions, publish/get events, store_decision | 내부 SharedMemory |
| 유틸 (2) | health_check, get_version | 내부 |

### 제거 (~37개)
- execute_team, stream_team, execute_in_session (AutoGen Studio)
- list/get/create/update/delete teams/sessions/gallery (CRUD)
- A2A agents (register/unregister/health)
- validate/test component
- settings, api_spec, schema, locks

## 5. 데이터 흐름

```
Claude Code
  ↓ MCP (stdio 또는 :8200)
AG-light Server (Python)
  ├── MCP tools → Worker API 호출 (법규/토지)
  ├── MessageBus → 에이전트간 대화
  ├── SharedMemory → 정보 공유
  └── Cohub → JSON 팀 로드 + 실행
       ↓
Worker (Cloudflare)
  ├── /law/* → 법제처 API (law.go.kr)
  ├── /search → Vectorize + 법제처 키워드 RRF
  └── /land/* → 규제 계산 (static JSON + Vworld)
       ↓
ARR Backend (별도 배포)
  ├── /design/* → 매스 최적화 (NSGA-II)
  ├── /land/* → setback_geometry (Shapely)
  └── Neo4j → 7-stage 의미 검색 (보조)
```

## 6. 배포

```bash
# 1. Worker (Cloudflare, 무료)
cd worker && wrangler deploy

# 2. Server (Docker, Fly.io ~$5/월)
docker compose up -d

# 3. ARR Backend (별도, Fly.io ~$5/월)
# 매스+평면+setback이 필요할 때만
```

## 7. AG/ 대비 제거된 것

| 제거 | 크기 | 이유 |
|------|------|------|
| autogen_source | 1.2G | npm install로 대체 |
| venv | 1.4G + 1.1G | Docker로 대체 |
| 22 demo agents | 35MB | 건축 무관 |
| AutoGen Studio 의존 | ~30 도구 | Studio 제거 |
| AG-Research | 71M | 논문, 별도 |
| law-domain-agents (전체) | 2.0G | ARR이 담당 |

**AG 4.7GB → AG-light ~5MB (코드만)**
