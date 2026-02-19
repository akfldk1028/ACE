# 25_ACE Project - Claude Code Context

## Project Overview

AutoGen Studio SaaS platform with custom frontend, multi-agent orchestration, and A2A protocol support.

```
25_ACE/
├── AG-frontend/          # SaaS Frontend (Vite 7 + React 19 + TS 5.9 + Tailwind v4)
├── AG/Auto-Claude/       # Electron app + CLI 24/7 Hub (20 agents)
├── AG/autogen_a2a_kit/   # AutoGen + A2A agents + SDK
├── JSON_MODULES/         # 98 AutoGen component JSON files
└── venv/                 # Python virtual environment
```

## AG-frontend (Primary Active Development)

### Stack
- **Vite 7.3** + **React 19** + **TypeScript 5.9** + **Tailwind v4.1**
- **Zustand** (state) + **TanStack Query v5** (server state) + **React Router v7**
- **@xyflow/react** + **dagre** (agent flow visualization)

### Commands
```bash
cd AG-frontend
npm run dev          # localhost:5173 (proxy -> :8081)
npm run build        # tsc -b && vite build (~3s)
npx tsc --noEmit     # Type check only
npx vitest run       # Unit tests (26 tests)
npx playwright test  # E2E tests (235 tests, 31s)
```

### Proxy & WebSocket
- `/api/*` proxied to `http://localhost:8081` (AutoGen Studio)
- `ws: true` REQUIRED in vite proxy for Playground WebSocket execution
- NEVER call `http://localhost:8081` directly from browser (CORS blocked)

### 8 Pages (lazy-loaded)
Team Builder(`/build`), Playground(`/`), MCP, A2A Agents(`/agents`), Gallery, History(`/history`), Deploy, Settings

## Coding Conventions (MUST FOLLOW)

### React Patterns
- `React.memo()` on ALL list item / card components
- State updater pattern: `setState(prev => ...)` to avoid stale closures
- `pushToHistory` inside `setDraft` updater (not outside)
- DnD keys: name-based stable identity, NOT index-based
- Keyboard shortcuts: guard with `e.target instanceof HTMLTextAreaElement || HTMLInputElement`

### TypeScript
- `erasableSyntaxOnly`: class fields not in constructor params
- Union type casting: `as unknown as Record<string, unknown>` (no direct cast)
- Pure functions: `getTeamName()` / `getTeamPattern()` - NOT hooks, no `use` prefix

### CSS / Theme
- Use semantic tokens: `text-(--color-semantic-warning)` NOT `text-amber-500`
- Badge has no `className` prop - wrap in `<span className>` instead
- 7 themes x 2 modes (light/dark)

### Imports
- Path alias: `@/` -> `src/`
- Use `dagre` not `@dagrejs/dagre` (CJS compat issue with Vite)
- ARIA: Never `aria-hidden="true"` on backdrop (hides ALL children). Use `role="dialog" aria-modal="true"`

## API Contract Rules

These are AutoGen Studio backend specifics - do NOT assume standard REST:

| Operation | Correct | Wrong |
|-----------|---------|-------|
| Team update | `POST /api/teams/` (id in body, upsert) | `PUT /api/teams/:id` |
| Session messages | Use `GET /api/sessions/:id/runs` | No `/messages` endpoint |
| A2A register | `{ url }` field | `{ agent_url }` |
| A2A health single | `{ status: bool }` | Not `{ healthy }` |
| A2A health all | `{ agents: [{ is_online }] }` | Not `{ agents: [{ healthy }] }` |
| Health check | `{ status: true }` (boolean) | Not string |
| Validate | Tries instantiation, fails without API key | `is_valid: false` expected |

## AutoGen Studio

- Runs on port **8081**
- SQLite DB: `~/.autogenstudio/autogen04203.db`
- API: `GET /api/teams/`, `GET /api/sessions/`, `GET /api/sessions/{id}/runs`
- AssistantAgent v2: needs `reflect_on_tool_use: false` + `tool_call_summary_format: "{result}"`

## Windows Environment

- Always use `encoding='utf-8'` (default cp949 breaks everything)
- Chrome profile lock: kill chrome.exe and remove SingletonLock files

## Testing

- **E2E**: 235 Playwright tests (25 files) - run with backend on port 8081
- **Unit**: 26 vitest tests (3 files) - pure logic tests
- Before committing: `npx tsc --noEmit && npm run build && npx playwright test`
