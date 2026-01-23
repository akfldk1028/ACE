# Server Module

AG-ACE-BRIDGE의 웹 서버 컴포넌트입니다.

## 개요

24/7 AI Project Factory를 위한 웹 대시보드와 API를 제공합니다.

## 파일 구조

```
src/server/
├── __init__.py      # 모듈 export
├── dashboard.py     # 대시보드 서버 (FastAPI)
└── README.md        # 이 문서
```

## Dashboard

### 기능

- **실시간 모니터링**: WebSocket을 통한 실시간 상태 업데이트
- **Orchestrator 제어**: Start/Stop/Pause/Resume
- **에이전트 상태**: Auto-Claude, A2A 에이전트 상태 확인
- **메트릭**: 처리된 태스크, 성공/실패 수, 큐 크기
- **Activity Log**: 최근 활동 로그

### 실행

```bash
# 대시보드만 실행
python main.py --dashboard

# 대시보드 + 오케스트레이터 함께 실행
python main.py

# 또는 직접 실행
python -m src.server.dashboard
```

### 접속

- Dashboard: http://localhost:8080

## API Endpoints

### Status

```http
GET /api/status
```

오케스트레이터 상태 조회.

**Response:**
```json
{
  "state": "running",
  "uptime_seconds": 3600,
  "metrics": {
    "tasks_processed": 10,
    "tasks_succeeded": 8,
    "tasks_failed": 2
  },
  "queue_stats": {
    "pending": 5,
    "running": 1,
    "completed": 8,
    "failed": 2
  }
}
```

### Control

```http
POST /api/start    # 오케스트레이터 시작
POST /api/stop     # 오케스트레이터 중지
POST /api/pause    # 일시 정지
POST /api/resume   # 재개
```

### A2A Health Check

```http
GET /api/a2a/health
```

A2A 에이전트 상태 확인.

**Response:**
```json
{
  "poetry_agent": true,
  "philosophy_agent": true,
  "history_agent": false,
  "calculator_agent": true,
  "gui_test_agent": false
}
```

### WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8080/ws');
ws.onmessage = (event) => {
    const status = JSON.parse(event.data);
    console.log('Status:', status);
};
```

2초마다 상태 업데이트를 받습니다.

## 설정

환경변수 (`.env`):

```bash
# Dashboard 포트
BRIDGE_PORT=8080

# SharedMemory URL (AG-CLI)
SHARED_MEMORY_URL=http://localhost:8101
```

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                     Dashboard (FastAPI)                          │
│                     http://localhost:8080                        │
├─────────────────────────────────────────────────────────────────┤
│  Routes:                                                         │
│  - GET  /          → 대시보드 HTML                               │
│  - GET  /api/status → 상태 조회                                  │
│  - POST /api/start  → 시작                                       │
│  - POST /api/stop   → 중지                                       │
│  - GET  /api/a2a/health → A2A 상태                              │
│  - WS   /ws         → 실시간 업데이트                            │
├─────────────────────────────────────────────────────────────────┤
│                        Orchestrator                              │
│            (24/7 Task Processing Loop)                          │
├─────────────────────────────────────────────────────────────────┤
│  Adapters:                                                       │
│  - Auto-Claude (OAuth)                                          │
│  - AG A2A (8003-8006)                                           │
│  - AG Autogen (HTTP)                                            │
│  - AG Law Domain (FastAPI)                                      │
└─────────────────────────────────────────────────────────────────┘
```

## 의존성

```
fastapi>=0.104.0
uvicorn>=0.24.0
websockets>=12.0
```
