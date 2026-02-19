# 논문 강화 로드맵

> 최종 갱신: 2026-02-19 (비판적 검토 반영)
> 목적: "멀티 에이전트 종료 역학" 논문의 비판적 약점 해결 및 top-venue 수준으로 강화

---

## 0. 교수 피드백 (2026-02-13, 4가지 핵심 지적) — ✅ ALL ADDRESSED

### 지적 1: U(t)가 0으로 수렴해야 한다 ✅ RESOLVED
- **문제**: 기존 U(t) = Q(t) - lambda*C(t)는 C(t) 증가 시 음의 무한대로 발산.
- **해결**: ΔU(t) = ΔQ(t) - λ·ΔC(t)로 재정의 → 자연 수렴 보장
- **완료**: adaptive_condition.py 업데이트, exp02 사전검증, 논문 Section 4.5 반영 (EN+KR)
- **핵심 발견**: ΔU(t) → 0 수렴까지 1.1~2.4턴, λ-비민감 (ΔQ 포화가 지배적 신호)

### 지적 2: 도메인별 분석 필요 ✅ TASK SUITE DONE, EXPERIMENT RUNNING
- **해결**: 25개 과제, 9개 도메인 (science, CS, history, philosophy, law_politics, gaming, engineering, business, medicine)
- **완료**: task_suite.json 갱신, analyze_domain_pattern.py 분석 스크립트 작성
- **진행중**: exp01 v2 실행 (~33/200, 16%)

### 지적 3: Category B를 B1 + B2로 분리 ✅ RESOLVED
- **해결**: B1(Star/sel3,sel4) + B2(Mesh/swm3,swm4) 5범주 체계
- **완료**: config.py, 논문 전체 (EN+KR+summary), 그래프, 통계 모두 반영

### 지적 4: 범주에 학술적 근거 필요 ✅ RESOLVED
- **해결**: 5범주 분류 + MAS 토폴로지 인용 (Masterman 2025, Du ICML 2024, 등)
- **완료**: Section 3, Table 1, fig1_taxonomy 모두 갱신

---

## 1. 현재 상태 평가

### 있는 것 ✅
- exp01 v1 (패턴 효율): 780회 완료, 13패턴 5범주 비용 구조 규명
- exp02 (품질 궤적): 100회 완료, 276개 턴별 스코어, 3가지 궤적 형태 발견
- ΔU(t) 사전검증: exp02 데이터에서 한계효용 수렴 확인 (Findings 21-23, Tables 13-14)
- 5범주 통계 완료: Kruskal-Wallis df=4, 10 pairwise comparisons, A≈B2 발견 (p=0.857)
- 23개 발견 + 14개 테이블 (논문 영문+한글 모두 갱신 완료)
- 논문 초안 (영문 + 한글 + 교수 요약) 전체 6섹션 + 부록
- config.py에 B1/B2 분리 + 8개 대표 패턴 + 25개 과제 반영 완료
- 그래프 18개 생성 (fig1~fig8 + marginal utility + heatmap + pareto)
- domain 분석 스크립트 준비 완료 (analyze_domain_pattern.py)
- exp05 retry 로직 구현 완료 (runner.py: 3-retry + crash detection + circuit breaker)
- adaptive_condition.py ΔU(t) 업데이트 완료

### 진행중 🔄
- **exp01 v2**: 33/200 (16%), background task, zero errors, est. ~3h remaining

### 남은 것 (논문 완성에 필수)
- **exp01 v2 완료 후**: 도메인 × 패턴 교차 분석 (스크립트 준비됨)
- **exp05 v2**: ΔU(t) → 0 적응적 종료 검증 (200회) — retry 로직 추가됨, SDK 안정성 테스트 필요
- **도메인 분석 결과 → 논문 반영**: Section 4.1.6 (new) + Section 5.1 가이드라인

### 실패한 것 (해결책 마련됨)
- **exp05 v1**: 712/720 에러 (exit code 3221226091 = Windows SDK 프로세스 크래시)
- **해결**: runner.py에 3-retry + exponential backoff + crash detection + circuit breaker 추가
- **검증 필요**: exp01 v2 완료 후 파일럿 테스트로 확인

---

## 2. 심사위원 예상 질문 & 대응

### Q1: "에이전트 많으면 비용 증가는 당연한 결과 아닌가?"
**대응**:
- 비자명 발견 강조: swm3(3명)이 rr2(2명)보다 12% 저렴
- 스케일링 방향이 토폴로지마다 정반대 (B1=서브리니어 vs B2=슈퍼리니어)
- debate에서 팀 성장 시 에이전트당 출력 감소 (협력적 증폭의 반대)
- B1/B2 분리로 "같은 에이전트 수, 다른 토폴로지 → 반대 스케일링" 명확히 보여줌

### Q2: "이건 벤치마크이지 과학인가?"
**대응**:
- 한계효용 수렴(ΔU → 0)이라는 이론적 프레임워크 제시
- exp01 관찰 → 한계효용 모델 유도 → exp02 사전검증 + exp05 통제검증 = 과학적 방법론
- 5범주 분류가 MAS 토폴로지 이론에 근거 (임의적 분류 아님)

### Q3: "ΔU(t)가 기여인가? 한계효용 개념 아닌가?"
**대응**:
- 한계효용 개념 자체는 경제학에서 차용. 기여는 "MAS 종료에 적용한 것"
- **토폴로지별 수렴 속도가 다름**을 실험적으로 입증 (refl2: 즉시 수렴 vs debate3: 발산)
- 기존 U(t)의 발산 문제를 지적하고 수렴 보장 공식으로 대체한 것이 이론적 기여
- **λ-비민감성** 발견: ΔQ 포화가 지배적 → λ 튜닝 불필요 = 실용적 가치

### Q4: "단일 모델로 일반화 가능한가?"
**대응**:
- 대표 패턴 3~4개(rr3, sel3, refl2, deb3)를 GPT-4o-mini로 재현 (optional)
- "스케일링 방향(서브/슈퍼리니어)"이 모델 불문 동일한지 확인
- 절대값은 달라도 상대적 순위/방향이 동일하면 충분

### Q5: "도메인 일반화가 되는가?"
**대응**:
- 9개 도메인 x 8개 패턴 교차 분석 (exp01 v2 진행중)
- 도메인 불변 패턴 vs 도메인 특화 패턴 식별
- 도메인별 가이드라인 제공 = 실용적 임팩트

---

## 3. 보강 작업 (우선순위 순)

### [P0-BLOCKER] SDK 안정성 해결 ✅ MITIGATION DONE
- exp05 runner.py에 retry 로직 추가 (3-retry + exponential backoff + circuit breaker)
- crash detection (exit code 3221226091) + cooldown (15s/30s)
- consecutive failure tracking (5 failures → 60s pause)
- **검증 필요**: exp01 v2 완료 후 exp05 파일럿 테스트

### [P0] 과제 스위트 v2 작성 ✅ DONE
- task_suite.json에 25개 과제, 9개 도메인 (medicine 포함) 반영 완료
- 도메인당 2~4개 과제 (난이도 혼합)

### [P0] exp01 v2 실행 🔄 IN PROGRESS (33/200, 16%)
- 8 패턴 x 25 과제 = 200회, background task b1453c9
- rr3 완료 (25/25, 0 errors), sel3 진행중
- Est. ~3h remaining

### [P0] ΔU(t) 검증 ✅ DONE
- compute_marginal_utility.py 실행 완료
- 산출물: marginal_utility.csv, marginal_utility_summary.csv
- 그래프: fig_marginal_utility.png, fig_marginal_utility_heatmap.png, fig_utility_U_vs_dU.png
- Findings 21-23, Tables 13-14 논문 반영 완료 (EN+KR)

### [P0] exp05 v2 실행 ⏳ WAITING (exp01 v2 완료 후)
- 200회: 8 패턴 x 25 과제 x 1 반복
- adaptive_condition.py ΔU(t) 업데이트 완료
- runner.py retry 로직 추가 완료
- 종료 조건: ΔU(t) ≤ epsilon → patience 연속 턴 후 종료
- 파일럿 테스트 선행 필요

### [P1] 5범주 구조로 논문 전면 갱신 ✅ DONE
- Section 3: 5범주 분류도 + 학술 인용 ✅
- Section 4.1.2: B1/B2 별도 소절 ✅
- Section 4.1.5: 5범주 Kruskal-Wallis (df=4, 10 pairwise) ✅
- Section 4.5: ΔU(t) 사전검증 (Findings 21-23) ✅
- RQ5: 한계효용 수렴 공식 ✅
- 영문 + 한글 + 교수요약 모두 완료 ✅

### [P1] 도메인 교차 분석 & 가이드라인 ⏳ WAITING
- analyze_domain_pattern.py 스크립트 준비 완료
- exp01 v2 완료 후 실행 → 히트맵 + Kruskal-Wallis + 도메인 findings
- Section 4.1.6 (new) + Section 5.1 가이드라인 확장

### [P2] 그래프 전면 재생성 ✅ MOSTLY DONE
- fig1: 5범주 분류 다이어그램 ✅ (2/13)
- fig2: B1 Star + B2 Mesh 아키텍처 ✅ (2/13)
- fig3: 실험 설계 개요 ✅ (2/13, 25-task/8-pattern/ΔU(t) 반영)
- fig4: 8 대표 패턴 효율 비교 ✅ (2/13)
- fig5: 품질 궤적 + 종료 후회 ✅ (2/13)
- fig8: 파레토 프론티어 ✅ (2/13)
- fig_marginal_utility: ΔU(t) 수렴 곡선 ✅ (2/13)
- **AWAITING**: fig_domain_pattern (도메인 히트맵, exp01 v2 후)

### [P3] 교차 모델 검증 (방어용, optional)
- GPT-4o-mini로 대표 3패턴(rr3, swm3, refl2) x 25과제 x 1반복 = 75회
- 확인: 스케일링 방향, 상대적 효율 순위가 동일한지
- 소요: 1일 + 비용 $10-20

---

## 4. 투고 전략 (2026-02-19 재검토)

### ~~Plan A: COLM 2026~~ → Venue Fit 문제
- COLM은 언어 모델 학습/스케일링/아키텍처에 초점
- 본 논문은 MAS 오케스트레이션 연구 → venue mismatch
- 여전히 제출 가능하나 리젝 리스크 높음

### Plan A (신규): AAMAS 2026
- International Conference on Autonomous Agents and Multi-Agent Systems
- MAS 연구 전문 venue, 토폴로지/종료 연구가 핵심 주제
- CFP 마감일 확인 필요
- P0 약점(하이브리드 실험, 인간 평가) 해결 후 제출

### Plan B: ACL/EMNLP 2026 Workshop
- LLM 에이전트 관련 워크숍 다수
- 현재 상태로도 제출 가능 (약점 인정 + limitations 솔직 기술)

### Plan C: COLM 2026 (backup)
- Abstract: 2026-03-26, Full: 2026-03-31
- P0-P1 해결 후 시도 가능

### Plan D: 국내 학회
- 한국정보과학회/한국소프트웨어공학회
- 한글 논문 초안 이미 완성

---

## 5. 일정 (COLM 기준, 실제 진행 반영)

| 기간 | 작업 | 상태 |
|------|------|------|
| 2/13 | 교수 피드백 반영: 5범주, ΔU(t), 25-task, 논문 전면 갱신 | ✅ 완료 |
| 2/13 | exp01 v2 실행 시작 (200회) | 🔄 진행중 (33/200) |
| 2/13~14 | exp01 v2 완료 대기 + 도메인 분석 | 다음 |
| 2/14~15 | exp05 파일럿 테스트 (retry 로직 검증) | 대기 |
| 2/15~17 | exp05 v2 전체 실행 (200회) | 대기 |
| 2/17~18 | 도메인 분석 + exp05 결과 → 논문 반영 | 대기 |
| 2/19~20 | 그래프 최종 생성 + 논문 정제 | 대기 |
| 2/21~3/4 | 최종 검토 + ACL Workshop 제출 (Plan B) | 대기 |
| 3/5~25 | 논문 정제 + 교차 모델 검증 (optional) | 대기 |
| 3/26 | COLM Abstract 제출 | 목표 |
| 3/31 | COLM Full Paper 제출 | 목표 |

---

## 6. 실험 규모 비교 (v1 vs v2)

| 항목 | v1 (완료) | v2 (진행중) | 변경 이유 |
|------|-----------|-------------|-----------|
| 패턴 수 | 13개 전체 | 8개 대표 | 불필요한 변형 제거 |
| 과제 수 | 20개 (4범주) | 25개 (9도메인) | 도메인 다양성 필요 |
| 반복 | 3회 | 1회 | 통계 검정보다 도메인 폭 우선 |
| exp01 총 | 780회 | 200회 | 8x25x1 = 200 |
| exp05 총 | 720회 (실패) | 200회 | 8x25x1 = 200 |
| 범주 | 4개 (A/B/C/D) | 5개 (A/B1/B2/C/D) | B를 분리 |
| 종료 공식 | U(t) = Q-λC | ΔU(t) = ΔQ-λΔC | 수렴 보장 |

---

## 7. 논문 강도 자가 점검표 (2026-02-19 비판적 재평가)

| 기준 | Session 8 | 비판적 재평가 | 목표 | 미해결 과제 |
|------|-----------|-------------|------|-----------|
| 연구 갭 실재성 | ★★★★★ | ★★★★★ | 유지 | - |
| 실험 규모 | ★★★★☆ | ★★★★☆ | ★★★★★ | 하이브리드 800회 추가 필요 |
| 발견의 비자명성 | ★★★★★ | ★★★★☆ | ★★★★★ | trivial findings 제거 필요 |
| 이론적 깊이 (ΔU) | ★★★★☆ | **★★★☆☆** | ★★★★☆ | 7/8 실패 → 진단 도구로 재정립 완료, 하이브리드 검증 미완 |
| 방법론 기여 | ★★★★☆ | **★★★☆☆** | ★★★★☆ | 하이브리드 미구현, 기존 방법 비교 없음 |
| 실용적 가치 | ★★★★☆ | ★★★★☆ | ★★★★★ | 가이드라인 유효 |
| 평가 신뢰도 | ★★★☆☆ | **★★☆☆☆** | ★★★★☆ | κ=0.244, 1인 평가자. **CI 추가 완료 (2/19)** |
| 일반화 가능성 | ★★★☆☆ | **★★☆☆☆** | ★★★★☆ | n=5 상관, 소형 모델만 |
| 학술적 근거 | ★★★★☆ | ★★★★☆ | 유지 | - |
| 수렴 보장 | ★★★★★ | ★★★★★ | 유지 | - |
| 논문 구조/분량 | N/A | **★★★☆☆** | ★★★★☆ | **Finding 압축 매핑 완료 (2/19)**. 본문 39개 유지 + Appendix D에 15개 요약 |
| Venue Fit | N/A | **★★★★☆** | ★★★★★ | **VENUE_ANALYSIS.md 완료 (2/19)**. COLM Topic 16에 multi-agent 명시. AutoGen도 COLM 2024. |

### 비판적 약점 대응 우선순위

| 우선순위 | 약점 | 해결 방법 | 소요 |
|---------|------|----------|------|
| **P0** | 하이브리드(keyword+ΔU) 미검증 | adaptive_condition.py 수정: keyword 우선 + ΔU fallback 조건 → 800회 실행 | 1-2일 |
| **P0** | 단일 인간 평가자 (κ 미산출) | 제2 평가자 섭외 + 30 샘플 재평가 + Cohen's κ 보고 | 1일 |
| ~~P1~~ | ~~신뢰구간 부재~~ | **완료 (2026-02-19)**: Table 12/18에 ±std/CI, Appendix C (C1-C3). EN/KR/LaTeX 반영. | ✅ |
| ~~P1~~ | ~~Finding 39개 과다~~ | **완료 (2026-02-19)**: Appendix D에 15개 핵심 발견 매핑. EN/KR 반영. | ✅ |
| **P1** | 교차 모델 n=5 제한 | GPT-4o로 8패턴 추가 검증 (200회) | 1일 + $20 |
| ~~P2~~ | ~~Venue 결정~~ | **완료 (2026-02-19)**: VENUE_ANALYSIS.md 작성. COLM 2026 (Mar 31) 1순위, EMNLP 2026 2순위. | ✅ |
| **P2** | LaTeX 동기화 | paper_draft.md 변경 → main.tex 반영 | 2-3시간 |
