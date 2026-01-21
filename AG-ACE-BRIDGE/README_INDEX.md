# AG-ACE-BRIDGE README INDEX

프로젝트 문서 목록. 24/7 AI Project Factory의 전체 구조와 문서를 안내합니다.

## 프로젝트 개요

AG-ACE-BRIDGE는 Auto-Claude (24/7 자율 코딩)와 AG (멀티에이전트)를 연결하는 통합 브릿지입니다.

```
┌─────────────────────────────────────────────────────────────────┐
│                    AG-ACE-BRIDGE                                 │
│               24/7 AI PROJECT FACTORY                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Task Queue → Orchestrator → Pipeline → Result → New Tasks     │
│                    │              │                             │
│              ┌─────┴─────┐  ┌────┴────┐                        │
│              │Auto-Claude│  │   AG    │                        │
│              │ (4 agents)│  │(13 agents)│                       │
│              └───────────┘  └─────────┘                        │
│                                                                 │
│  Total: 17 Coordinated Agents                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**핵심 특징:**
- 24/7 자율 운영 (무한 루프)
- 17개 에이전트 조율
- 5가지 오케스트레이션 패턴
- Graphiti ↔ Neo4j 메모리 동기화

---

## 문서 구조

### 루트 레벨

| 파일 | 설명 |
|------|------|
| [README.md](README.md) | 프로젝트 메인 README |
| [README_INDEX.md](README_INDEX.md) | 이 파일 - 문서 목록 |
| [.env.example](.env.example) | 환경 변수 템플릿 |
| [requirements.txt](requirements.txt) | Python 의존성 |
| [pyproject.toml](pyproject.toml) | 프로젝트 설정 |

### 문서 폴더 (docs/)

| 경로 | 설명 |
|------|------|
| [docs/README.md](docs/README.md) | 문서 폴더 개요 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | **상세 아키텍처 설계서** ⭐ |
| [docs/PATTERNS.md](docs/PATTERNS.md) | 오케스트레이션 패턴 설명 |
| [docs/API.md](docs/API.md) | API 문서 |

### 소스 코드 (src/)

| 경로 | 모듈 | 역할 |
|------|------|------|
| [src/README.md](src/README.md) | **소스 개요** | 4계층 아키텍처 설명 |
| [src/coordinator/README.md](src/coordinator/README.md) | **Coordinator** | 24/7 오케스트레이터 |
| [src/pipeline/README.md](src/pipeline/README.md) | **Pipeline** | 실행 흐름 패턴 |
| [src/adapters/README.md](src/adapters/README.md) | **Adapters** | 에이전트 연결 |
| [src/memory/README.md](src/memory/README.md) | **Memory** | 메모리 동기화 |
| [src/registry/README.md](src/registry/README.md) | **Registry** | 에이전트 레지스트리 |
| [src/utils/README.md](src/utils/README.md) | **Utils** | 설정, 모델, 로깅 |

### 테스트 (tests/)

| 경로 | 설명 |
|------|------|
| [tests/README.md](tests/README.md) | 테스트 가이드 |

---

## 아키텍처 다이어그램

### 4계층 구조

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: COORDINATOR (중앙 조율)                                │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│ │TaskQueue │ │AgentSel. │ │Pipeline  │ │Orchestra.│           │
│ │(SQLite)  │ │(Match)   │ │Builder   │ │(24/7)    │           │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
├─────────────────────────────────────────────────────────────────┤
│ Layer 2: PIPELINE (실행 흐름)                                   │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐                        │
│ │Sequential│ │Parallel  │ │Critic    │                        │
│ │Pipeline  │ │Fan-Out   │ │Loop      │                        │
│ └──────────┘ └──────────┘ └──────────┘                        │
├─────────────────────────────────────────────────────────────────┤
│ Layer 3: ADAPTERS (에이전트 연결)                               │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐                        │
│ │AutoClaude│ │AGAutogen │ │AGLaw     │                        │
│ │SDK       │ │HTTP      │ │Domain    │                        │
│ └──────────┘ └──────────┘ └──────────┘                        │
├─────────────────────────────────────────────────────────────────┤
│ Layer 4: MEMORY (메모리 동기화)                                 │
│ ┌──────────┐              ┌──────────┐                        │
│ │Graphiti  │ ◄─────────►  │Neo4j     │                        │
│ │(LadybugDB)│    Sync     │(Knowledge)│                       │
│ └──────────┘              └──────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

### 사용된 패턴

| 패턴 | 출처 | 용도 |
|------|------|------|
| Coordinator/Dispatcher | Microsoft | 중앙 오케스트레이터 |
| Sequential Pipeline | Google ADK | Auto-Claude 흐름 |
| Parallel Fan-Out/Gather | Microsoft | AG 병렬 실행 |
| Generator-Critic Loop | Google ADK | QA Loop |
| Handoff | Microsoft | 에이전트 간 전환 |

---

## 에이전트 목록 (17개)

### Auto-Claude (4개)

| 에이전트 | 기능 | 핵심 역할 |
|----------|------|-----------|
| `planner` | planning, subtask-decomposition | 구현 계획 |
| `coder` | implementation, 24/7-autonomous | **24/7 코딩** |
| `qa_reviewer` | testing, e2e, validation | 품질 검증 |
| `qa_fixer` | debugging, issue-resolution | 이슈 수정 |

### AG autogen_a2a_kit (8개)

| 에이전트 | 기능 |
|----------|------|
| `research` | information-gathering, web-search |
| `analyst` | data-analysis, pattern-detection |
| `writer` | documentation, content-creation |
| `reviewer` | feedback, quality-assessment |
| `coordinator` | orchestration, task-routing |
| ... | (3개 더) |

### AG law-domain (5개)

| 에이전트 | 기능 |
|----------|------|
| `case_analyzer` | case-law, precedent-analysis |
| `legal_researcher` | statute-search, regulation |
| `risk_assessor` | risk-evaluation, liability |
| `compliance_checker` | compliance, regulation-check |
| `document_drafter` | legal-docs, contracts |

---

## 빠른 시작

### 설치

```bash
cd D:/Data/25_ACE/AG-ACE-BRIDGE
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

### 실행 (24/7 Project Factory)

```bash
# 방법 1: 24/7 Factory 시작 (프로젝트 드롭 → 자동 실행)
python run_24_7.py

# 방법 2: 프로젝트 제출
python run_24_7.py submit --spec my-project.yaml

# 방법 3: 예제 스펙 생성 후 실행
python run_24_7.py example
cp projects/examples/example_api_project.yaml projects/queue/
python run_24_7.py

# 프로젝트 상태 확인
python run_24_7.py list
python run_24_7.py status <project-id>
```

### 프로젝트 자동 실행 방법

1. **YAML 스펙 파일 작성** (또는 예제 복사)
2. **`projects/queue/` 폴더에 드롭**
3. **자동 실행** - 17개 에이전트가 협업하여 프로젝트 완성

```
projects/queue/my-api.yaml → 자동 감지 → 17 Agents → 완성!
```

---

## 관련 프로젝트

| 프로젝트 | 경로 | 문서 |
|----------|------|------|
| Auto-Claude | `D:/Data/25_ACE/Auto-Claude` | [README_INDEX](../Auto-Claude/README_INDEX.md) |
| AG | `D:/Data/25_ACE/AG` | [README_INDEX](../AG/agent/README_INDEX.md) |
| 25_ACE | `D:/Data/25_ACE` | [ARCHITECTURE](../ARCHITECTURE.md) |

---

## 구현 현황

| 컴포넌트 | 상태 | 파일 |
|----------|------|------|
| 폴더 구조 | ✅ 완료 | - |
| 데이터 모델 | ✅ 완료 | `src/utils/models.py` |
| 설정 관리 | ✅ 완료 | `src/utils/config.py` |
| 로깅 시스템 | ✅ 완료 | `src/utils/logger.py` |
| 기본 어댑터 | ✅ 완료 | `src/adapters/base.py` |
| Auto-Claude 어댑터 | ✅ 완료 | `src/adapters/auto_claude.py` |
| AG Autogen 어댑터 | ✅ 완료 | `src/adapters/ag_autogen.py` |
| AG Law Domain 어댑터 | ✅ 완료 | `src/adapters/ag_law_domain.py` |
| 에이전트 기능 정의 | ✅ 완료 | `src/registry/capabilities.py` |
| 에이전트 레지스트리 | ✅ 완료 | `src/registry/agent_registry.py` |
| TaskQueue | ✅ 완료 | `src/coordinator/task_queue.py` |
| Agent Selector | ✅ 완료 | `src/coordinator/agent_selector.py` |
| Pipeline Builder | ✅ 완료 | `src/coordinator/pipeline_builder.py` |
| Orchestrator | ✅ 완료 | `src/coordinator/orchestrator.py` |
| Sequential Pipeline | ✅ 완료 | `src/pipeline/sequential.py` |
| Parallel Pipeline | ✅ 완료 | `src/pipeline/parallel.py` |
| Critic Loop | ✅ 완료 | `src/pipeline/critic_loop.py` |
| README 문서 | ✅ 완료 | 각 폴더 |
| **Project Spec** | ✅ 완료 | `src/project/spec.py` |
| **Project Watcher** | ✅ 완료 | `src/project/watcher.py` |
| **Project CLI** | ✅ 완료 | `src/project/cli.py` |
| **run_24_7.py** | ✅ 완료 | `run_24_7.py` |
| Memory Sync | ⏳ 구현 예정 | `src/memory/*.py` |

---

## 변경 이력

- 2025-01-21: 24/7 Project Factory 추가 (Watcher, CLI, run_24_7.py)
- 2025-01-21: 프로젝트 생성, 아키텍처 설계, README 작성
