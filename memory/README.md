# MassAgent AI Memory & Cross-Agent Context

이 디렉토리는 **MassAgent**, **Claude Code**, **OpenAI Codex**, **Google DeepMind Gemini**가 상호 협업할 때 참조하는 **단일 진실 원천(SSOT) 메모리 저장소**입니다.

---

## 1. 메모리 문서 색인 (Index)

1. **[01_SCORING_AGENT_SOTA_RESEARCH.md](./01_SCORING_AGENT_SOTA_RESEARCH.md)**:
   - 최신 학술 논문(SOTA) 정밀 분석:
     - **EvoMass (FoAR 2024)**: 하드 제약과 다목적 적합도 분리.
     - **CADLoop (CVPRW 2026)**: VLM 비평과 심볼릭 컴파일러 AST 변이의 닫힌 루프.
     - **VisionReward (2024)**: 구조화된 다차원 QA 체크리스트 및 가중치 보상.
   - 영어 원문, 학술 번역, 중학 수학/논리 비유 포함.

2. **[02_TWO_TIER_SCORING_ARCHITECTURE.md](./02_TWO_TIER_SCORING_ARCHITECTURE.md)**:
   - 2단계 하이브리드(Two-Tier Neuro-Symbolic) 심사 아키텍처:
     - Tier 1: 결정론적 하드 게이트 (Overhang=0, 법정 주차, 구조 자립성).
     - Tier 2: VLM 심사위원단 8대 루브릭 (`gesture_clarity`, `hierarchy`, `non_stair_silhouette`, `void_publicness`, `repair_integrity`, `precedent_resonance`, `program_appropriateness`, `section_program_fit`).
     - 포트폴리오 보드 시블링 중복 평가 및 CADLoop AST 변이 피드백.
     - `design/test_maas_preference.py` 54개 전수 테스트 통과 증빙.

3. **[03_ROOF_AND_PILOTI_CATALOG.md](./03_ROOF_AND_PILOTI_CATALOG.md)**:
   - 박공 지붕(Gable), 망사르드 지붕(Mansard), 버터플라이 지붕(Butterfly), 필로티 하부 개방(Piloti Undercroft) 기하학 및 법규 산정 기준.

4. **[04_5_ARCHITECTURAL_MASTERS_PROPOSALS.md](./04_5_ARCHITECTURAL_MASTERS_PROPOSALS.md)**:
   - 의정부 민락동 대지 위 5대 건축 거장(OMA, BIG, SANAA, MVRDV, ZHA) 매스 제안 지표, 조형 원리 및 SOTA AI 점수 매트릭스.

---

## 2. 관련 핵심 파일 링크
- 최상위 컨텍스트: `../CLAUDE.md`, `../GEMINI.md`
- 백엔드 평가 모듈: `D:/Data/25_ACE/ARR/backend/design/maas/preference/`
- 웹 인터랙티브 뷰어: `http://localhost:8089/mass_3_proposals_presentation.html`
