# 01. 프로젝트 개요

## 프로젝트 목표

**25_ACE**는 AutoGen 멀티-에이전트 시스템과 Claude Code를 통합한 자동화 개발 파이프라인입니다.

### 핵심 목표
1. **JSON 모듈화**: 패턴, 모델, 에이전트, 팀을 JSON으로 완전 모듈화
2. **패턴 테스트**: 14개 AutoGen 패턴이 모두 정상 동작하는지 검증
3. **코드 생성**: Calculator 앱을 에이전트 협업으로 모듈화된 코드로 생성
4. **교수님 요구사항**: 각 패턴이 제대로 동작해야 함, 모듈화가 중요

---

## 프로젝트 구조

```
D:\Data\25_ACE\
│
├── AG/                              # AutoGen 관련
│   ├── Auto-Claude/                 # Auto-Claude CLI (메인 소스)
│   │   ├── src/                     # Python 소스 코드
│   │   │   ├── adapters/            # 에이전트 어댑터
│   │   │   ├── agents/              # Auto-Claude 에이전트
│   │   │   ├── coordinator/         # 오케스트레이터
│   │   │   ├── pipeline/            # 실행 파이프라인
│   │   │   └── registry/            # 에이전트 레지스트리
│   │   └── tests/                   # 테스트 코드 (작성 중)
│   │
│   └── autogen_a2a_kit/             # AutoGen + A2A 통합
│       └── AG_Cohub/                # 패턴 라이브러리
│           ├── patterns/            # 14개 패턴 정의
│           ├── loader/              # Provider 로더
│           └── index.json           # 마스터 인덱스
│
├── AG-frontend/                        # ★ SaaS Frontend (Vite 7 + React 19 + Tailwind v4)
│
├── JSON_MODULES/                    # ★ JSON 모듈 통합 (98개 파일)
│   ├── patterns/                    # 14개 패턴
│   ├── models/                      # 7개 모델
│   ├── agents/                      # 12개 에이전트
│   ├── teams/                       # 20개 팀
│   ├── templates/                   # 5개 템플릿
│   ├── providers/                   # Provider 설정
│   └── README.md                    # 구조 설명
│
├── HANDOFF/                         # ★ 핸드오프 문서 (현재 폴더)
│
└── maintenance/                     # 유지보수 스크립트
```

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| **멀티-에이전트** | AutoGen 0.4.3, A2A Protocol |
| **LLM** | Claude Opus 4.5, Sonnet 4.5 (OAuth), GPT-4o-mini |
| **백엔드** | Python 3.13, FastAPI, SQLite |
| **프론트엔드** | AG-frontend/ (Vite 7 + React 19 + Tailwind v4), AutoGen Studio (backend API) |
| **테스트** | Playwright MCP, pytest |

---

## 주요 서비스 포트

| 서비스 | 포트 | 설명 |
|--------|------|------|
| AutoGen Studio | 8081 | 메인 UI |
| MessageBus | 8100 | 에이전트 메시지 버스 |
| SharedMemory | 8101 | 공유 메모리 서버 |
| A2A Poetry | 8003 | 시 생성 에이전트 |
| A2A Philosophy | 8004 | 철학 에이전트 |
| A2A History | 8005 | 역사 에이전트 |
| A2A Calculator | 8006 | 계산기 에이전트 |
| A2A GUI Test | 8120 | GUI 테스트 에이전트 |
| Claude CLI A2A | 9018 | Claude CLI 에이전트 |

---

## Git 상태

- **현재 브랜치**: `DK-BB`
- **메인 브랜치**: `master`
- **상태**: 다수 파일 수정/추가됨 (커밋 전)

```bash
# 최근 커밋
9dbced1 feat: Code review fixes + maintenance system + AutoGen 6-team setup
86997fb chore: add auto-claude entries to .gitignore
2503ac1 fix: Critical bugs in 24/7 auto-trigger + scalability improvements
```
