# 인간 평가 키트 요약 (교수님 전달용)

## 개요
멀티에이전트 시스템의 G-Eval 자동 채점 결과를 검증하기 위한 인간 평가 자료입니다.
Experiment 02 (품질 궤적 분석)에서 추출한 30개 샘플에 대해 5개 차원의 수동 평가를 요청드립니다.

## 샘플 분포

### 패턴별 분포 (5개 패턴 × 6개 샘플)
| 패턴 | 카테고리 | 샘플 수 | 설명 |
|------|---------|---------|------|
| rr3 | A (Flat) | 6 | 라운드로빈 3-에이전트 |
| sel3 | B1 (Centralized) | 6 | 셀렉터 3-에이전트 |
| swm3 | B2 (Decentralized) | 6 | 스웜 3-에이전트 |
| refl2 | C (Feedback) | 6 | 리플렉션 2-에이전트 |
| debate3 | C (Feedback) | 6 | 디베이트 3-에이전트 |

### G-Eval 자동 채점 점수 구간별 분포
| 점수 구간 | 샘플 수 | 비율 |
|----------|---------|------|
| 높음 (4-5점) | 10 | 33% |
| 중간 (3점) | 10 | 33% |
| 낮음 (1-2점) | 10 | 33% |

> 층화 추출(stratified sampling)로 점수 범위 전체를 균등 커버합니다.

### 과제 유형별 분포
| 유형 | 샘플 수 |
|------|---------|
| technical | 12 |
| factual | 8 |
| creative | 6 |
| analytical | 4 |

## 평가 방법

### 5개 평가 차원 (1-5점 척도)
1. **정확성 (Accuracy)**: 사실과 주장의 정확도
2. **완전성 (Completeness)**: 과제의 모든 부분을 얼마나 철저히 다루는가
3. **일관성 (Coherence)**: 논리적 흐름과 일관성
4. **유용성 (Usefulness)**: 실용적이고 행동 가능한 가치
5. **종합 (Overall)**: 위 요소를 종합한 전체 품질

### 점수 기준
| 점수 | 의미 |
|------|------|
| 5 | 우수 - 포괄적, 정확, 체계적 |
| 4 | 양호 - 대체로 완성도 높음, 소소한 부족 |
| 3 | 보통 - 기본 내용은 있으나 중요 측면 누락 |
| 2 | 미흡 - 상당한 오류 또는 누락 |
| 1 | 매우 미흡 - 근본적으로 부정확하거나 무관 |

## 파일 위치

| 파일 | 경로 | 용도 |
|------|------|------|
| 평가 시트 (빈칸) | `results/exp02/human_eval_sheet.csv` | 평가자가 점수 기입 |
| 평가 지침 | `results/exp02/human_eval_instructions.md` | 상세 평가 가이드 |
| 정답 키 (G-Eval) | `results/exp02/human_eval_answer_key.csv` | 자동 채점 결과 (평가 후 비교용) |

## 평가 절차
1. `human_eval_sheet.csv`를 열어 각 샘플의 과제와 응답을 읽음
2. 5개 차원에 대해 1-5 정수 점수 기입
3. (선택) comments 열에 간단한 코멘트 추가
4. **정답 키는 평가 완료 전까지 보지 않음**
5. 완료 후 저장하고 분석 스크립트 실행:
   ```bash
   C:/Python313/python analyze_human_eval.py
   ```

## 예상 소요 시간
- **30~45분** (샘플당 1~1.5분)
- 응답이 truncated된 경우 있음 → 제시된 내용만 평가

## LLM 교차 검증 (자동)
- 별도로 GPT-4o-mini를 사용한 40개 샘플 교차 검증도 병행 진행 중
- 결과: `results/exp02/cross_validation.csv`, `cross_validation_summary.csv`
- Pearson/Spearman 상관계수 + Cohen's weighted kappa 산출

## 분석 목적
- G-Eval (Claude 기반) 자동 채점의 **신뢰성 검증**
- 인간 평가와의 일치도가 r > 0.7이면 "strong agreement"
- 논문 Section 4.2.1 (Evaluation Validation)에 결과 반영
