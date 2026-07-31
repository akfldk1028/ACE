# 코드 갭 분석: 종료 판단 데이터 수집 현황

> 연구 문서(termination-criteria-research.md) 기준으로 우리 코드가 뭘 수집하고 뭘 빠뜨리는지 분석
> 작성일: 2026-02-09

---

## 1. 백엔드가 보내는 데이터 (사용 가능한 전체 데이터)

AutoGen Studio 백엔드는 실행 완료 시 WebSocket으로 다음을 전송:

```json
{
  "type": "result",
  "status": "complete",
  "data": {
    "task_result": {
      "messages": [...],
      "stop_reason": "Maximum messages reached" // ← 종료 이유!
    },
    "usage": "",        // ← 총 사용량
    "duration": 12.5    // ← 실행 시간(초)
  }
}
```

REST API (`GET /api/sessions/{id}/runs`)도 동일한 `team_result` 반환.
DB에도 `Run.team_result` JSON 컬럼으로 전부 저장됨.

---

## 2. 현재 프론트엔드 수집 현황

### 수집하고 있는 것 ✅

| 데이터 | 위치 | 상태 |
|--------|------|------|
| 에이전트별 메시지 | `executionStore.turns[]` | ✅ 수집 중 |
| 메시지별 토큰 수 | `AgentTurn.tokensIn/tokensOut` | ✅ 수집 중 |
| 메시지 소스 (어떤 에이전트) | `AgentTurn.source` | ✅ 수집 중 |
| 타임스탬프 | `AgentTurn.timestamp` | ✅ 수집 중 |
| 메시지 타입 구분 | `AgentTurn.messageType` (user/agent/llm_event) | ✅ 수집 중 |
| LLM 호출 상세 (모델명, 토큰) | `llm_call_event` 파싱 | ✅ 수집 중 |
| 실행 상태 | `status` (idle/running/completed/error) | ✅ 수집 중 |
| 스트리밍 소스 | `streamingSource` | ✅ 수집 중 |
| 마지막 에이전트 | Flow Monitor "by {agent}" | ✅ 표시 중 |

### 수집하지 않는 것 ❌ (연구에서 필요한 핵심 데이터)

| 데이터 | 백엔드 제공? | 프론트엔드 상태 | 연구 중요도 |
|--------|-------------|----------------|------------|
| **stop_reason** (종료 이유) | ✅ `data.task_result.stop_reason` | ❌ **버림** (line 131-138) | 🔴 핵심 |
| **duration** (실행 시간) | ✅ `data.duration` | ❌ **버림** | 🔴 핵심 |
| **총 토큰 합계** | ✅ 개별 메시지에서 합산 가능 | ❌ **합산 안함** | 🟡 중요 |
| **턴 수** (메시지 카운트) | ✅ `turns.length`에서 도출 가능 | ❌ **명시적 저장 안함** | 🟡 중요 |
| **finish_reason** (모델 종료 이유) | ✅ LLM 응답에 포함 | ❌ **파싱 안함** | 🟡 중요 |
| **StopMessage 구분** | ✅ 메시지 타입으로 구분 가능 | ❌ **agent와 동일 취급** | 🟡 중요 |
| **team_result 전체** | ✅ 백엔드에서 전송 | ❌ **무시** | 🔴 핵심 |

---

## 3. 핵심 문제: `completion`/`result` 메시지 처리

### 현재 코드 (executionStore.ts:131-139)

```typescript
if (msg.type === 'completion' || msg.type === 'result') {
  return {
    status: 'completed' as const,
    isRunning: false,
    streamingChunks: '',
    streamingSource: null,
    inputRequest: null,
    // ⚠️ msg.data 완전히 무시!
    // msg.data.task_result.stop_reason 버림!
    // msg.data.duration 버림!
  }
}
```

### 문제점

`msg.data`에 `TaskResult` + `TeamResult` 전체가 들어오는데 **전부 버리고** status만 'completed'로 바꿈.

---

## 4. REST API에서도 누락

### 현재 코드 (useExecution.ts:22-47)

```typescript
function messagesFromRuns(runs) {
  for (const run of runs.runs) {
    for (const msg of run.messages) {
      // 메시지 내용만 추출
      // ⚠️ run.team_result 완전히 무시!
      // ⚠️ run.team_result.task_result.stop_reason 버림!
      // ⚠️ run.team_result.duration 버림!
      // ⚠️ run.status 버림!
    }
  }
}
```

---

## 5. 수집 가능한 연구 메트릭 (코드 수정 시)

### 즉시 수집 가능 (백엔드 이미 제공)

| 메트릭 | 소스 | 용도 |
|--------|------|------|
| `stop_reason` | `msg.data.task_result.stop_reason` | 어떤 조건이 종료 트리거했는지 |
| `duration` | `msg.data.duration` | 패턴별 실행 시간 비교 |
| `총 토큰` | `turns.reduce(sum tokensIn+tokensOut)` | 패턴별 비용 비교 |
| `턴 수` | `turns.filter(agent).length` | 에이전트 협업 깊이 |
| `종료 에이전트` | `마지막 agent turn의 source` | 누가 최종 결정했는지 |
| `StopMessage` | `msg.type === 'message' && content includes TERMINATE/APPROVED` | 종료 키워드 감지 |

### 추가 구현 필요 (프론트엔드 로직)

| 메트릭 | 구현 방법 | 연구 논문 |
|--------|-----------|-----------|
| G-Eval 품질 점수 | LLM-as-Judge API 호출 (별도) | EMNLP 2023 |
| 자기 일관성 | 동일 태스크 N회 실행 후 답변 비교 | Wang 2023 |
| 토론 안정성 (KS) | 라운드별 에이전트 응답 분포 변화 추적 | arXiv:2510.12697 |
| 반복 감지 | 동일 에이전트의 유사 응답 카운팅 | NeurIPS 2023 Reflexion |

---

## 6. 결론

### 현재 상태: 연구용 데이터 수집 약 40%

```
수집 중:     메시지 내용, 개별 토큰, 소스, 타임스탬프, 메시지 타입
버리는 중:   stop_reason, duration, team_result, 총계, StopMessage 구분
미구현:      G-Eval, 자기일관성, KS-statistic, 반복감지
```

### 최소 수정으로 80%까지 올릴 수 있는 것

1. **executionStore.ts**: `completion`/`result` 메시지에서 `stop_reason`, `duration` 추출
2. **executionStore.ts**: 실행 완료 시 총 토큰 합계 계산
3. **useExecution.ts**: `run.team_result`에서 `stop_reason`, `duration` 읽기
4. **PlaygroundPage.tsx**: 종료 시 stop_reason + duration + 토큰 합계 표시
5. **Flow Monitor**: End 노드에 stop_reason 텍스트 표시 (현재 "by {agent}"만 있음)

### 향후 연구 실험 (추가 개발 필요)

1. 실행 결과 로깅 시스템 (JSON 파일 또는 DB 저장)
2. 패턴별 비교 대시보드
3. G-Eval 자동 평가 파이프라인
4. 다회 실행 자기일관성 측정
