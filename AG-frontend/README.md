# AG-frontend

AutoGen Studio SaaS Frontend. Multi-agent 오케스트레이션 + 토지 규제 분석 UI.

## Stack

- Vite 7.3 + React 19 + TypeScript 5.9 + Tailwind v4.1
- Zustand (state) + TanStack Query v5 (server state) + React Router v7
- @xyflow/react + dagre (agent flow visualization)

## Dev

```bash
npm run dev          # localhost:5173 (proxy → :8081)
npm run build        # tsc -b && vite build (~3s)
npx tsc --noEmit     # Type check
npx vitest run       # Unit tests (26 tests)
npx playwright test  # E2E tests (235 tests, 31s)
```

## Pages (8, lazy-loaded)

| Path | Page | Description |
|------|------|-------------|
| `/` | Playground | 팀 실행, WebSocket 스트리밍 |
| `/build` | Team Builder | 에이전트/모델/도구 시각적 편집 |
| `/agents` | A2A Agents | 외부 에이전트 등록/관리 |
| `/mcp` | MCP | MCP 서버 연결 |
| `/gallery` | Gallery | 팀 템플릿 갤러리 |
| `/history` | History | 세션/실행 기록 |
| `/deploy` | Deploy | 배포 관리 |
| `/settings` | Settings | 설정 |

## Proxy

```
/api/*  → http://localhost:8081  (AutoGen Studio, ws: true)
/arr/*  → http://localhost:8000  (ARR Django backend)
```

## ARR Integration

`src/shared/api/arrClient.ts` — typed `landAPI`:

```typescript
landAPI.analyze(data)   // POST /arr/land/analyze/
landAPI.resolve(data)   // POST /arr/land/resolve/
landAPI.zones()         // GET  /arr/land/zones/
landAPI.stats()         // GET  /arr/land/stats/
```

## Tests

- **E2E**: 235 Playwright tests (25 files), backend 필요
- **Unit**: 26 vitest tests (3 files), pure logic
- **Themes**: 7 themes x 2 modes (light/dark)

## Before Commit

```bash
npx tsc --noEmit && npm run build && npx playwright test
```
