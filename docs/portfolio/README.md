---
name: Portfolio — 25_ACE 프로젝트 포트폴리오 자료
description: 4장 포트폴리오 + 아키텍처 다이어그램 + NotebookLM 소스. 발표/면접/회사 제출용.
type: project
originSessionId: 5fb8be34-8660-4347-81b7-6bf5ae10ee85
---
## 한 줄

주소 한 줄 → 건축법규 42개 + §119 지반레벨 + 8종 규제선 + GA 매스 최적화 자동.

## 폴더 구조

```
portfolio/
├── README.md              (이 파일)
├── overview.md            ⭐ 1페이지 요약 — 한눈에 보기
├── architecture.md        ⭐ 2페이지 아키텍처 — 4서비스 + 기술스택 + 데이터 흐름
├── core-modules.md        3페이지 핵심 모듈 — 법규/datum/envelope/매스
├── agent-validation.md    4페이지 에이전트 + 검증 — Hermes/MCP/A2A/Playwright
├── notebooklm-source.md   NotebookLM 업로드용 통합 소스 (4 페이지 압축)
└── differentiation.md     차별화 포인트 + 비교표 + 활용 시나리오
```

## 사용

### A. 직접 4페이지 보기
`docs/portfolio/PORTFOLIO_4PAGE.md` (이미 생성됨)

### B. NotebookLM에 업로드
`portfolio/notebooklm-source.md` 파일을 NotebookLM에 source로 추가 →
"4페이지 포트폴리오로 정리해줘" 프롬프트.

### C. 개별 페이지 사용
각 `*.md` 파일이 독립적으로 1페이지 분량.

## 산출물 통계 (2026-04-28 기준)

| 항목 | 수치 |
|---|---|
| 9 commits (datum elevation 시리즈) | Phase 1~2D-3 |
| 178+ tests pass (39 datum + 167 land 회귀) | 100% |
| 라이브 검증 PNU | 8개 (강남/성북/한남/여의도/우동/평창/대관령) |
| 정확도 측정 | 도시 11m / 해안 3.7m / 산 63m (18 landmark) |
| LOCKED SPEC | Session 14 (12회+ 사용자 검증) |
| Neo4j 법령 | 58 법령 31K nodes, 임베딩 100% |
| 4서비스 라이브 배포 | CF Pages × 2 + Worker + Railway |
| MCP tools | ACE Server 57 tools (17 카테고리) |

## 핵심 메시지

한국 건축법 시행령 §119/§86을 **AI로 자동 분석 + 시각화**한 첫 시스템.
9 commits로 datum 평면 완성, 178+ tests 통과, Playwright 라이브 검증,
LOCKED SPEC 12회+ 사용자 검증 박제.

## Differentiation

| 기존 | 25_ACE |
|---|---|
| 수동 법규 검색 | **자동** Neo4j 7-stage hybrid search |
| 단순 평탄지 envelope | **§119 6 케이스** datum (산악/도로/인접지 자동) |
| 정적 법규 데이터 | **LLM 동적 추출** + 18 landmark 정확도 검증 |
| 1차원 시각 | **Z축 일치** + DatumInfoCard + 3D envelope |
| 로컬 단일 사용자 | **MCP 57 tools + A2A + Telegram bot** 멀티에이전트 |
