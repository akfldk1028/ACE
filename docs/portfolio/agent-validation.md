---
name: Page 4 — Agent System & Validation
description: Hermes + MCP + A2A 멀티에이전트 + 178+ tests 검증 + 9 commits + Roadmap.
type: project
originSessionId: 5fb8be34-8660-4347-81b7-6bf5ae10ee85
---
## Agent Architecture (2026-04-26~28 결정)

**Hermes (Nous Research) 채택** + 통일 skill 추상화 + Telegram bot persona별 분리:

```
사용자 (Telegram @DK_arch_bot)
       ↓
Hermes Gateway (Oracle VM Always-Free)
       ↓
LLM (Qwen-plus via DashScope)
       ↓ skill dispatch
┌─────────────────┬─────────────────┐
│ Light Skills    │ Heavy Skills     │
│ (즉시 응답)     │ (Celery enqueue) │
├─────────────────┼─────────────────┤
│ 법규 검색        │ 매스 최적화 GA   │
│ 토지 분석        │ 평면 생성        │
│ datum 계산       │ 시방서 생성      │
│ 규제선 조회      │ 견적 산출        │
└─────────────────┴─────────────────┘
       ↓ 일부 호출
ARR Backend (Django, Railway)
       ↓
ACE MCP Server (57 tools)
       ↓
AutoGen Studio + AG-CLI Multi-Agent
```

## ACE MCP (57 Tools, 17 Categories)

| 카테고리 | Tools |
|---|---|
| 법조항 검색 | `law_search`, `arr_law_search`, `law_search_domain`, `law_domains` |
| 토지 분석 | `arr_land_analyze`, `arr_land_resolve`, `arr_land_zones`, `arr_land_stats` |
| AutoGen 팀 | `create_team`, `execute_team`, `stream_team`, `update_team`, `delete_team` |
| 세션 관리 | `create_session`, `delete_session`, `list_sessions`, `get_session_runs` |
| A2A 에이전트 | `register_a2a_agent`, `unregister_a2a_agent`, `check_a2a_health`, `list_a2a_agents` |
| Message Bus | `publish_event`, `get_events`, `get_bus_status`, `broadcast_message` |
| SharedMemory | `get_shared_data`, `store_decision`, `get_all_decisions`, `acquire_lock` |
| ... | (총 17 categories, 57 tools) |

## A2A Protocol

- JSON-RPC 2.0 compliant
- Agent card discovery: `/.well-known/agent-card/{slug}.json`
- Bidirectional messaging
- Multi-agent collaboration
- Worker-to-worker direct communication

## Validation Framework

| 검증 | 방법 | 결과 |
|---|---|---|
| **단위 테스트** | Django TestCase | 39 datum + 27 zoning + 100+ regulation = **178+ pass** |
| **회귀 테스트** | `python manage.py test land` | **167 pass** |
| **CLI 검증** | `verify_datum_multi.py` (8 PNU) | 8/8 ✅ |
| **정확도 측정** | `verify_elevation_accuracy.py` (18 landmark) | 도시 11m, 해안 3.7m |
| **LOCKED SPEC** | `test_envelope_walls_slanted_unchanged_by_datum` | byte-identical ✅ |
| **시각 검증** | Playwright (자동) | 카드 + envelope 표시 ✅ |
| **E2E 라이브** | 강남 역삼동 677 | BCR=80%, FAR=1300%, 42규제 ✅ |

## 9 Commits (Phase 1~2D-3)

```
8443395 fix(design): Phase 2D-3 — Z축 일치 + 시각 helper 개선
1b408ce feat(frontend): Phase 2D-2 — datum 독립 노출 (envelope 미적용 zone)
98f9c6d feat(frontend): Phase 2D — datum 시각 카드 (land + design)
c49e09f feat(verify): Open-Meteo 90m DEM 정확도 검증 CLI
44a5e5f feat(datum): Phase 2C — 라이브 8 PNU 검증 + 임계값 조정
8894423 feat(verify): verify_datum_119 CLI envelope 통합
d67d1a4 feat(datum): Phase 2B — 호출 체인 + frontend 3-state
09023de feat(envelope): Phase 2A — datum metadata LOCKED SPEC 호환
5fcc39d feat(datum): Phase 1 — Open-Meteo + 6 케이스 dispatcher
```

## Roadmap

| Phase | 상태 | 내용 |
|---|---|---|
| 1~2D-3 | ✅ DONE | datum 평면 + envelope + UI 카드 + Z축 fix |
| 임계값 조정 | ✅ DONE | 90m DEM 노이즈 흡수 (FLAT 2.0, SLOPE 8.0) |
| **3 (NGII 5m)** | TODO | 산악지 정밀화 (90m → 5m, 18배 정밀) |
| **§86 정북인접** | TODO | views.py에서 인접 polygon 추출 |
| **§119 도로 활성** | TODO | views.py에서 centerline 추출 |
| **4 (3m 분할)** | TODO | §119② 단서 polygon segmentation |
| **Hermes 통합** | TODO | Telegram bot → ARR backend 직접 호출 |

## 차별화

| 기존 시스템 | 25_ACE |
|---|---|
| 사용자 수동 법규 검색 | **자동** Neo4j 7-stage hybrid search |
| 단순 평탄지 envelope | **§119 6 케이스** datum (산악/도로/인접지 자동) |
| 정적 법규 데이터 | **LLM 동적 추출** + 18 landmark 정확도 검증 |
| Cesium 1차원 시각 | **Z축 일치** + DatumInfoCard 카드 + 3D envelope |
| 로컬 단일 사용자 | **MCP 57 tools + A2A + Telegram bot** 멀티에이전트 |

## 핵심 메시지

한국 건축법 시행령 §119/§86을 **AI로 자동 분석 + 시각화**한 첫 시스템.
9 commits로 datum 평면 완성, 178+ tests 통과, Playwright 라이브 검증,
LOCKED SPEC 12회+ 사용자 검증 박제.

**Tech**: React + Django + Neo4j + Cesium + NSGA-II GA + Hermes Agents.

**검증 가능**: `tools/verify_datum_multi.py` 또는 `localhost:5173/design` 직접 라이브.
