# AG-ACE-BRIDGE 사용자 액션 가이드

현재 모든 서비스가 실행중입니다. 아래 가이드를 따라 사용하세요.

---

## 1. Auto-Claude UI (Electron 앱)

화면에 떠 있는 **Auto-Claude** 데스크톱 앱입니다.

### 주요 기능
| 버튼/메뉴 | 설명 |
|----------|------|
| **New Spec** | 새 프로젝트 스펙 생성 |
| **Run Build** | 자율 빌드 실행 |
| **Settings** | API 키, 모델 설정 |

### 사용 흐름
```
1. 좌측 사이드바에서 프로젝트 선택 또는 "+" 클릭
2. "Create New Spec" 버튼 클릭
3. 태스크 설명 입력 (예: "Add user authentication")
4. "Generate Spec" 클릭 → AI가 스펙 자동 생성
5. "Start Build" 클릭 → 자율 코딩 시작
```

---

## 2. AutoGen Studio (http://localhost:8081)

브라우저에서 http://localhost:8081 접속

### 주요 탭
| 탭 | 설명 | 버튼 |
|---|------|------|
| **Playground** | 에이전트 테스트 | "New Session" → 대화 시작 |
| **Build** | 에이전트/팀 빌더 | "New Team" → 팀 구성 |
| **Gallery** | 템플릿 갤러리 | 템플릿 클릭 → 가져오기 |
| **Deploy** | 배포 관리 | - |
| **Settings** | API 키 설정 | API 키 입력 |

### 첫 사용 순서
```
1. Settings 탭 → OpenAI API Key 입력
2. Build 탭 → "Teams" 선택 → 기본 팀 확인
3. Playground 탭 → "New Session" 클릭
4. 왼쪽에서 팀 선택 (예: "Round Robin Team")
5. 채팅창에 질문 입력 → Enter
```

### A2A 에이전트 사용 (외부 에이전트 연결)
```
1. Build 탭 → "Agents" → "New Agent"
2. Agent Type: "Remote A2A Agent"
3. URL 입력: http://localhost:8003 (poetry_agent)
4. "Save" → 팀에 추가 가능
```

---

## 3. AG-ACE Dashboard (http://localhost:8080)

브라우저에서 http://localhost:8080 접속

### 대시보드 화면
| 섹션 | 설명 |
|------|------|
| **Status** | 전체 시스템 상태 (녹색=정상) |
| **Agents** | 연결된 에이전트 목록 |
| **Tasks** | 실행중인 태스크 |
| **Logs** | 실시간 로그 |

### WebSocket 연결
- 자동으로 실시간 업데이트 됨
- 에이전트 실행 상태가 실시간 반영

---

## 4. A2A 에이전트 직접 테스트

### Calculator Agent (http://localhost:8006)
```bash
# Agent Card 확인
curl http://localhost:8006/.well-known/agent.json

# 계산 요청
curl -X POST http://localhost:8006/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"message/send","params":{"message":{"role":"user","parts":[{"text":"Calculate 2 + 3 * 4"}]}},"id":"1"}'
```

### Poetry Agent (http://localhost:8003)
```bash
# 시 요청
curl -X POST http://localhost:8003/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"message/send","params":{"message":{"role":"user","parts":[{"text":"Write a poem about spring"}]}},"id":"1"}'
```

---

## 5. 전체 워크플로우 예시

### 예시: 새 기능 개발

```
1. [Auto-Claude UI] "Create New Spec" 클릭
2. 태스크 입력: "Add login feature with JWT authentication"
3. "Generate Spec" → AI가 요구사항 분석
4. "Start Build" → 자율 코딩 시작
   - Planner Agent: 계획 수립
   - Coder Agent: 코드 작성
   - QA Reviewer: 검토
   - QA Fixer: 수정
5. [AG-ACE Dashboard] 진행 상황 실시간 모니터링
6. 완료 시 Auto-Claude UI에서 결과 확인
```

### 예시: AutoGen Studio에서 커스텀 팀 만들기

```
1. [AutoGen Studio] Build 탭 → "Teams"
2. "New Team" 클릭
3. Team Type: "Round Robin" 선택
4. Agents 추가:
   - Assistant Agent (기본)
   - Remote A2A Agent (URL: http://localhost:8003)
5. "Save Team"
6. Playground 탭 → 새 세션 → 방금 만든 팀 선택
7. 대화 시작!
```

---

## 포트 요약

| 서비스 | URL | 용도 |
|--------|-----|------|
| Auto-Claude UI | 데스크톱 앱 | 자율 코딩 |
| AutoGen Studio | http://localhost:8081 | 에이전트 빌더 |
| AG-ACE Dashboard | http://localhost:8080 | 모니터링 |
| SharedMemory | http://localhost:8101 | 상태 공유 |
| poetry_agent | http://localhost:8003 | 시/문학 |
| philosophy_agent | http://localhost:8004 | 철학 |
| history_agent | http://localhost:8005 | 역사 |
| calculator_agent | http://localhost:8006 | 계산 |

---

## 문제 해결

### "연결 실패" 에러
→ 해당 서비스가 실행중인지 확인

### API 키 에러
→ Settings에서 OpenAI/Anthropic API 키 설정

### 에이전트 응답 없음
→ A2A 에이전트 서버가 실행중인지 확인 (포트 8003-8006)
