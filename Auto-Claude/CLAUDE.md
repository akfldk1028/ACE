# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---
## ★★★ 핵심 메모리 (절대 잊지 말 것!) ★★★

### 8101 SharedMemory 사용 금지! (2026-01-25 확정)
- **8101 포트는 사용하지 않음!** 모든 SharedMemory 관련 코드 제거됨
- **8081 AutoGen Studio만 사용!**
- browser-mock.ts의 sharedMemory* 함수들은 빈 값만 반환 (호출해도 네트워크 요청 안 함)

### CORS 문제 해결 규칙
| 모드 | API 호출 방법 | 파일 |
|------|--------------|------|
| Electron | `window.electronAPI.*` | a2a-handlers.ts (Main Process) |
| Browser | `fetch('/api/autogen/...')` | browser-mock.ts (Vite 프록시) |
| ❌ 금지 | `fetch('http://localhost:8081/...')` | 브라우저 CORS로 차단됨! |

### Vite 프록시 설정 (electron.vite.config.ts)
```typescript
'/api/autogen' → 'http://localhost:8081/api'
```
---

## Project Overview

Auto Claude is a multi-agent autonomous coding framework that builds software through coordinated AI agent sessions. It uses the Claude Agent SDK to run agents in isolated workspaces with security controls.

**CRITICAL: All AI interactions use the Claude Agent SDK (`claude-agent-sdk` package), NOT the Anthropic API directly.**

## Project Structure

```
autonomous-coding/
├── apps/
│   ├── backend/           # Python backend/CLI - ALL agent logic lives here
│   │   ├── core/          # Client, auth, security
│   │   ├── agents/        # Agent implementations
│   │   ├── spec_agents/   # Spec creation agents
│   │   ├── integrations/  # Graphiti, Linear, GitHub
│   │   └── prompts/       # Agent system prompts
│   └── frontend/          # Electron desktop UI
├── guides/                # Documentation
├── tests/                 # Test suite
└── scripts/               # Build and utility scripts
```

**When working with AI/LLM code:**
- Look in `apps/backend/core/client.py` for the Claude SDK client setup
- Reference `apps/backend/agents/` for working agent implementations
- Check `apps/backend/spec_agents/` for spec creation agent examples
- NEVER use `anthropic.Anthropic()` directly - always use `create_client()` from `core.client`

**Frontend (Electron Desktop App):**
- Built with Electron, React, TypeScript
- AI agents can perform E2E testing using the Electron MCP server
- When bug fixing or implementing features, use the Electron MCP server for automated testing
- See "End-to-End Testing" section below for details

## Commands

### Setup

**Requirements:**
- Python 3.12+ (required for backend)
- Node.js (for frontend)

```bash
# Install all dependencies from root
npm run install:all

# Or install separately:
# Backend (from apps/backend/)
cd apps/backend && uv venv && uv pip install -r requirements.txt

# Frontend (from apps/frontend/)
cd apps/frontend && npm install

# Authenticate (token auto-saved to Keychain)
claude
# Then type: /login
# Press Enter to open browser and complete OAuth
```

### Creating and Running Specs
```bash
cd apps/backend

# Create a spec interactively
python spec_runner.py --interactive

# Create spec from task description
python spec_runner.py --task "Add user authentication"

# Force complexity level (simple/standard/complex)
python spec_runner.py --task "Fix button" --complexity simple

# Run autonomous build
python run.py --spec 001

# List all specs
python run.py --list
```

### Workspace Management
```bash
cd apps/backend

# Review changes in isolated worktree
python run.py --spec 001 --review

# Merge completed build into project
python run.py --spec 001 --merge

# Discard build
python run.py --spec 001 --discard
```

### QA Validation
```bash
cd apps/backend

# Run QA manually
python run.py --spec 001 --qa

# Check QA status
python run.py --spec 001 --qa-status
```

### Testing
```bash
# Install test dependencies (required first time)
cd apps/backend && uv pip install -r ../../tests/requirements-test.txt

# Run all tests (use virtual environment pytest)
apps/backend/.venv/bin/pytest tests/ -v

# Run single test file
apps/backend/.venv/bin/pytest tests/test_security.py -v

# Run specific test
apps/backend/.venv/bin/pytest tests/test_security.py::test_bash_command_validation -v

# Skip slow tests
apps/backend/.venv/bin/pytest tests/ -m "not slow"

# Or from root
npm run test:backend
```

### Spec Validation
```bash
python apps/backend/validate_spec.py --spec-dir apps/backend/specs/001-feature --checkpoint all
```

### Releases
```bash
# 1. Bump version on your branch (creates commit, no tag)
node scripts/bump-version.js patch   # 2.8.0 -> 2.8.1
node scripts/bump-version.js minor   # 2.8.0 -> 2.9.0
node scripts/bump-version.js major   # 2.8.0 -> 3.0.0

# 2. Push and create PR to main
git push origin your-branch
gh pr create --base main

# 3. Merge PR → GitHub Actions automatically:
#    - Creates tag
#    - Builds all platforms
#    - Creates release with changelog
#    - Updates README
```

See [RELEASE.md](RELEASE.md) for detailed release process documentation.

## Architecture

### Core Pipeline

**Spec Creation (spec_runner.py)** - Dynamic 3-8 phase pipeline based on task complexity:
- SIMPLE (3 phases): Discovery → Quick Spec → Validate
- STANDARD (6-7 phases): Discovery → Requirements → [Research] → Context → Spec → Plan → Validate
- COMPLEX (8 phases): Full pipeline with Research and Self-Critique phases

**Implementation (run.py → agent.py)** - Multi-session build:
1. Planner Agent creates subtask-based implementation plan
2. Coder Agent implements subtasks (can spawn subagents for parallel work)
3. QA Reviewer validates acceptance criteria (can perform E2E testing via Electron MCP for frontend changes)
4. QA Fixer resolves issues in a loop (with E2E testing to verify fixes)

### Key Components (apps/backend/)

**Core Infrastructure:**
- **core/client.py** - Claude Agent SDK client factory with security hooks and tool permissions
- **core/security.py** - Dynamic command allowlisting based on detected project stack
- **core/auth.py** - OAuth token management for Claude SDK authentication
- **agents/** - Agent implementations (planner, coder, qa_reviewer, qa_fixer)
- **spec_agents/** - Spec creation agents (gatherer, researcher, writer, critic)

**Memory & Context:**
- **integrations/graphiti/** - Graphiti memory system (mandatory)
  - `queries_pkg/graphiti.py` - Main GraphitiMemory class
  - `queries_pkg/client.py` - LadybugDB client wrapper
  - `queries_pkg/queries.py` - Graph query operations
  - `queries_pkg/search.py` - Semantic search logic
  - `queries_pkg/schema.py` - Graph schema definitions
- **graphiti_config.py** - Configuration and validation for Graphiti integration
- **graphiti_providers.py** - Multi-provider factory (OpenAI, Anthropic, Azure, Ollama, Google AI)
- **agents/memory_manager.py** - Session memory orchestration

**Workspace & Security:**
- **cli/worktree.py** - Git worktree isolation for safe feature development
- **context/project_analyzer.py** - Project stack detection for dynamic tooling
- **auto_claude_tools.py** - Custom MCP tools integration

**Integrations:**
- **linear_updater.py** - Optional Linear integration for progress tracking
- **runners/github/** - GitHub Issues & PRs automation
- **Electron MCP** - E2E testing integration for QA agents (Chrome DevTools Protocol)
  - Enabled with `ELECTRON_MCP_ENABLED=true` in `.env`
  - Allows QA agents to interact with running Electron app
  - See "End-to-End Testing" section for details

### Agent Prompts (apps/backend/prompts/)

| Prompt | Purpose |
|--------|---------|
| planner.md | Creates implementation plan with subtasks |
| coder.md | Implements individual subtasks |
| coder_recovery.md | Recovers from stuck/failed subtasks |
| qa_reviewer.md | Validates acceptance criteria |
| qa_fixer.md | Fixes QA-reported issues |
| spec_gatherer.md | Collects user requirements |
| spec_researcher.md | Validates external integrations |
| spec_writer.md | Creates spec.md document |
| spec_critic.md | Self-critique using ultrathink |
| complexity_assessor.md | AI-based complexity assessment |

### Spec Directory Structure

Each spec in `.auto-claude/specs/XXX-name/` contains:
- `spec.md` - Feature specification
- `requirements.json` - Structured user requirements
- `context.json` - Discovered codebase context
- `implementation_plan.json` - Subtask-based plan with status tracking
- `qa_report.md` - QA validation results
- `QA_FIX_REQUEST.md` - Issues to fix (when rejected)

### Branching & Worktree Strategy

Auto Claude uses git worktrees for isolated builds. All branches stay LOCAL until user explicitly pushes:

```
main (user's branch)
└── auto-claude/{spec-name}  ← spec branch (isolated worktree)
```

**Key principles:**
- ONE branch per spec (`auto-claude/{spec-name}`)
- Parallel work uses subagents (agent decides when to spawn)
- NO automatic pushes to GitHub - user controls when to push
- User reviews in spec worktree (`.worktrees/{spec-name}/`)
- Final merge: spec branch → main (after user approval)

**Workflow:**
1. Build runs in isolated worktree on spec branch
2. Agent implements subtasks (can spawn subagents for parallel work)
3. User tests feature in `.worktrees/{spec-name}/`
4. User runs `--merge` to add to their project
5. User pushes to remote when ready

### Contributing to Upstream

**CRITICAL: When submitting PRs to AndyMik90/Auto-Claude, always target the `develop` branch, NOT `main`.**

**Correct workflow for contributions:**
1. Fetch upstream: `git fetch upstream`
2. Create feature branch from upstream/develop: `git checkout -b fix/my-fix upstream/develop`
3. Make changes and commit with sign-off: `git commit -s -m "fix: description"`
4. Push to your fork: `git push origin fix/my-fix`
5. Create PR targeting `develop`: `gh pr create --repo AndyMik90/Auto-Claude --base develop`

**Verify before PR:**
```bash
# Ensure only your commits are included
git log --oneline upstream/develop..HEAD
```

### Security Model

Three-layer defense:
1. **OS Sandbox** - Bash command isolation
2. **Filesystem Permissions** - Operations restricted to project directory
3. **Command Allowlist** - Dynamic allowlist from project analysis (security.py + project_analyzer.py)

Security profile cached in `.auto-claude-security.json`.

### Claude Agent SDK Integration

**CRITICAL: Auto Claude uses the Claude Agent SDK for ALL AI interactions. Never use the Anthropic API directly.**

**Client Location:** `apps/backend/core/client.py`

The `create_client()` function creates a configured `ClaudeSDKClient` instance with:
- Multi-layered security (sandbox, permissions, security hooks)
- Agent-specific tool permissions (planner, coder, qa_reviewer, qa_fixer)
- Dynamic MCP server integration based on project capabilities
- Extended thinking token budget control

**Example usage in agents:**
```python
from core.client import create_client

# Create SDK client (NOT raw Anthropic API client)
client = create_client(
    project_dir=project_dir,
    spec_dir=spec_dir,
    model="claude-sonnet-4-5-20250929",
    agent_type="coder",
    max_thinking_tokens=None  # or 5000/10000/16000
)

# Run agent session
response = client.create_agent_session(
    name="coder-agent-session",
    starting_message="Implement the authentication feature"
)
```

**Why use the SDK:**
- Pre-configured security (sandbox, allowlists, hooks)
- Automatic MCP server integration (Context7, Linear, Graphiti, Electron, Puppeteer)
- Tool permissions based on agent role
- Session management and recovery
- Unified API across all agent types

**Where to find working examples:**
- `apps/backend/agents/planner.py` - Planner agent
- `apps/backend/agents/coder.py` - Coder agent
- `apps/backend/agents/qa_reviewer.py` - QA reviewer
- `apps/backend/agents/qa_fixer.py` - QA fixer
- `apps/backend/spec_agents/` - Spec creation agents

### Memory System

**Graphiti Memory (Mandatory)** - `integrations/graphiti/`

Auto Claude uses Graphiti as its primary memory system with embedded LadybugDB (no Docker required):

- **Graph database with semantic search** - Knowledge graph for cross-session context
- **Session insights** - Patterns, gotchas, discoveries automatically extracted
- **Multi-provider support:**
  - LLM: OpenAI, Anthropic, Azure OpenAI, Ollama, Google AI (Gemini)
  - Embedders: OpenAI, Voyage AI, Azure OpenAI, Ollama, Google AI
- **Modular architecture:** (`integrations/graphiti/queries_pkg/`)
  - `graphiti.py` - Main GraphitiMemory class
  - `client.py` - LadybugDB client wrapper
  - `queries.py` - Graph query operations
  - `search.py` - Semantic search logic
  - `schema.py` - Graph schema definitions

**Configuration:**
- Set provider credentials in `apps/backend/.env` (see `.env.example`)
- Required env vars: `GRAPHITI_ENABLED=true`, `ANTHROPIC_API_KEY` or other provider keys
- Memory data stored in `.auto-claude/specs/XXX/graphiti/`

**Usage in agents:**
```python
from integrations.graphiti.memory import get_graphiti_memory

memory = get_graphiti_memory(spec_dir, project_dir)
context = memory.get_context_for_session("Implementing feature X")
memory.add_session_insight("Pattern: use React hooks for state")
```

## Development Guidelines

### Frontend Internationalization (i18n)

**CRITICAL: Always use i18n translation keys for all user-facing text in the frontend.**

The frontend uses `react-i18next` for internationalization. All labels, buttons, messages, and user-facing text MUST use translation keys.

**Translation file locations:**
- `apps/frontend/src/shared/i18n/locales/en/*.json` - English translations
- `apps/frontend/src/shared/i18n/locales/fr/*.json` - French translations

**Translation namespaces:**
- `common.json` - Shared labels, buttons, common terms
- `navigation.json` - Sidebar navigation items, sections
- `settings.json` - Settings page content
- `dialogs.json` - Dialog boxes and modals
- `tasks.json` - Task/spec related content
- `errors.json` - Error messages (structured error information with substitution support)
- `onboarding.json` - Onboarding wizard content
- `welcome.json` - Welcome screen content

**Usage pattern:**
```tsx
import { useTranslation } from 'react-i18next';

// In component
const { t } = useTranslation(['navigation', 'common']);

// Use translation keys, NOT hardcoded strings
<span>{t('navigation:items.githubPRs')}</span>  // ✅ CORRECT
<span>GitHub PRs</span>                          // ❌ WRONG
```

**Error messages with substitution:**

```tsx
// For error messages with dynamic content, use interpolation
const { t } = useTranslation(['errors']);

// errors.json: { "task": { "parseError": "Failed to parse: {{error}}" } }
<span>{t('errors:task.parseError', { error: errorMessage })}</span>
```

**When adding new UI text:**
1. Add the translation key to ALL language files (at minimum: `en/*.json` and `fr/*.json`)
2. Use `namespace:section.key` format (e.g., `navigation:items.githubPRs`)
3. Never use hardcoded strings in JSX/TSX files

### Cross-Platform Development

**CRITICAL: This project supports Windows, macOS, and Linux. Platform-specific bugs are the #1 source of breakage.**

#### The Problem

When developers on macOS fix something using Mac-specific assumptions, it breaks on Windows. When Windows developers fix something, it breaks on macOS. This happens because:

1. **CI only tested on Linux** - Platform-specific bugs weren't caught until after merge
2. **Scattered platform checks** - `process.platform === 'win32'` checks were spread across 50+ files
3. **Hardcoded paths** - Direct paths like `C:\Program Files` or `/opt/homebrew/bin` throughout code

#### The Solution

**1. Centralized Platform Abstraction**

All platform-specific code now lives in dedicated modules:

- **Frontend:** `apps/frontend/src/main/platform/`
- **Backend:** `apps/backend/core/platform/`

**Import from these modules instead of checking `process.platform` directly:**

```typescript
// ❌ WRONG - Direct platform check
if (process.platform === 'win32') {
  // Windows logic
}

// ✅ CORRECT - Use abstraction
import { isWindows, getPathDelimiter } from './platform';

if (isWindows()) {
  // Windows logic
}
```

**2. Multi-Platform CI**

CI now tests on **all three platforms** (Windows, macOS, Linux). A PR cannot merge unless all platforms pass:

```yaml
# .github/workflows/ci.yml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
```

**3. Platform Module API**

The platform module provides:

| Function | Purpose |
|----------|---------|
| `isWindows()` / `isMacOS()` / `isLinux()` | OS detection |
| `getPathDelimiter()` | Get `;` (Windows) or `:` (Unix) |
| `getExecutableExtension()` | Get `.exe` (Windows) or `` (Unix) |
| `findExecutable(name)` | Find executables across platforms |
| `getBinaryDirectories()` | Get platform-specific bin paths |
| `requiresShell(command)` | Check if .cmd/.bat needs shell on Windows |

**4. Path Handling Best Practices**

```typescript
// ❌ WRONG - Hardcoded Windows path
const claudePath = 'C:\\Program Files\\Claude\\claude.exe';

// ❌ WRONG - Hardcoded macOS path
const brewPath = '/opt/homebrew/bin/python3';

// ❌ WRONG - Manual path joining
const fullPath = dir + '/subdir/file.txt';

// ✅ CORRECT - Use platform abstraction
import { findExecutable, joinPaths } from './platform';

const claudePath = await findExecutable('claude');
const fullPath = joinPaths(dir, 'subdir', 'file.txt');
```

**5. Testing Platform-Specific Code**

```typescript
// Mock process.platform for testing
import { isWindows } from './platform';

// In tests, use jest.mock or similar
jest.mock('./platform', () => ({
  isWindows: () => true  // Simulate Windows
}));
```

**6. When You Need Platform-Specific Code**

If you must write platform-specific code:

1. **Add it to the platform module** - Not scattered in your feature code
2. **Write tests for all platforms** - Mock `process.platform` to test each case
3. **Use feature detection** - Check for file/path existence, not just OS name
4. **Document why** - Explain the platform difference in comments

**7. Submitting Platform-Specific Fixes**

When fixing a platform-specific bug:

1. Ensure your fix doesn't break other platforms
2. Test locally if you have access to other OSs
3. Rely on CI to catch issues you can't test
4. Consider adding a test that mocks other platforms

**Example: Adding a New Tool Detection**

```typescript
// ✅ CORRECT - Add to platform/paths.ts
export function getMyToolPaths(): string[] {
  if (isWindows()) {
    return [
      joinPaths('C:', 'Program Files', 'MyTool', 'tool.exe'),
      // ... more Windows paths
    ];
  }
  return [
    joinPaths('/usr', 'local', 'bin', 'mytool'),
    // ... more Unix paths
  ];
}

// ✅ CORRECT - Use in your code
import { findExecutable, getMyToolPaths } from './platform';

const toolPath = await findExecutable('mytool', getMyToolPaths());
```

### End-to-End Testing (Electron App)

**IMPORTANT: When bug fixing or implementing new features in the frontend, AI agents can perform automated E2E testing using the Electron MCP server.**

The Electron MCP server allows QA agents to interact with the running Electron app via Chrome DevTools Protocol:

**Setup:**
1. Start the Electron app with remote debugging enabled:
   ```bash
   npm run dev  # Already configured with --remote-debugging-port=9222
   ```

2. Enable Electron MCP in `apps/backend/.env`:
   ```bash
   ELECTRON_MCP_ENABLED=true
   ELECTRON_DEBUG_PORT=9222  # Default port
   ```

**Available Testing Capabilities:**

QA agents (`qa_reviewer` and `qa_fixer`) automatically get access to Electron MCP tools:

1. **Window Management**
   - `mcp__electron__get_electron_window_info` - Get info about running windows
   - `mcp__electron__take_screenshot` - Capture screenshots for visual verification

2. **UI Interaction**
   - `mcp__electron__send_command_to_electron` with commands:
     - `click_by_text` - Click buttons/links by visible text
     - `click_by_selector` - Click elements by CSS selector
     - `fill_input` - Fill form fields by placeholder or selector
     - `select_option` - Select dropdown options
     - `send_keyboard_shortcut` - Send keyboard shortcuts (Enter, Ctrl+N, etc.)
     - `navigate_to_hash` - Navigate to hash routes (#settings, #create, etc.)

3. **Page Inspection**
   - `get_page_structure` - Get organized overview of page elements
   - `debug_elements` - Get debugging info about buttons and forms
   - `verify_form_state` - Check form state and validation
   - `eval` - Execute custom JavaScript code

4. **Logging**
   - `mcp__electron__read_electron_logs` - Read console logs for debugging

**Example E2E Test Flow:**

```python
# 1. Agent takes screenshot to see current state
agent: "Take a screenshot to see the current UI"
# Uses: mcp__electron__take_screenshot

# 2. Agent inspects page structure
agent: "Get page structure to find available buttons"
# Uses: mcp__electron__send_command_to_electron (command: "get_page_structure")

# 3. Agent clicks a button to navigate
agent: "Click the 'Create New Spec' button"
# Uses: mcp__electron__send_command_to_electron (command: "click_by_text", args: {text: "Create New Spec"})

# 4. Agent fills out a form
agent: "Fill the task description field"
# Uses: mcp__electron__send_command_to_electron (command: "fill_input", args: {placeholder: "Describe your task", value: "Add login feature"})

# 5. Agent submits and verifies
agent: "Click Submit and verify success"
# Uses: click_by_text → take_screenshot → verify result
```

**When to Use E2E Testing:**

- **Bug Fixes**: Reproduce the bug, apply fix, verify it's resolved
- **New Features**: Implement feature, test the UI flow end-to-end
- **UI Changes**: Verify visual changes and interactions work correctly
- **Form Validation**: Test form submission, validation, error handling

**Configuration in `core/client.py`:**

The client automatically enables Electron MCP tools for QA agents when:
- Project is detected as Electron (`is_electron` capability)
- `ELECTRON_MCP_ENABLED=true` is set
- Agent type is `qa_reviewer` or `qa_fixer`

**Note:** Screenshots are automatically compressed (1280x720, quality 60, JPEG) to stay under Claude SDK's 1MB JSON message buffer limit.

## Running the Application

**As a standalone CLI tool**:
```bash
cd apps/backend
python run.py --spec 001
```

**With the Electron frontend**:
```bash
npm start        # Build and run desktop app
npm run dev      # Run in development mode (includes --remote-debugging-port=9222 for E2E testing)
```

**For E2E Testing with QA Agents:**
1. Start the Electron app: `npm run dev`
2. Enable Electron MCP in `apps/backend/.env`: `ELECTRON_MCP_ENABLED=true`
3. Run QA: `python run.py --spec 001 --qa`
4. QA agents will automatically interact with the running app for testing

**Project data storage:**
- `.auto-claude/specs/` - Per-project data (specs, plans, QA reports, memory) - gitignored

## A2A Integration & AutoGen Studio 연동

Auto-Claude는 AutoGen Studio(8081)와 실시간 협업합니다.

**★ 중요: 8101 SharedMemory는 사용하지 않음! 8081 직접 연결만 사용!**

### 실행 모드별 아키텍처 (★ 2026-01-25 확정)

#### 1. Electron 모드 (npm run dev → Electron 앱)
```
┌─────────────────────────────────────────────────────────────────┐
│                    AutoGen Studio (8081)                         │
└───────────────────────┬─────────────────────────────────────────┘
                        │ HTTP (CORS 무시 - Node.js)
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Main Process (a2a-handlers.ts) - 유일한 8081 호출점              │
│  ├── getAutogenLatest() → 8081 직접                             │
│  └── getAutogenRunsDetailed() → 8081 직접                       │
└───────────────────────┬─────────────────────────────────────────┘
                        │ IPC (electronAPI)
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Renderer Process (React UI)                                      │
│  └── window.electronAPI.getAutogenLatest() 사용                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 2. 브라우저 모드 (localhost:5173 직접 접속)
```
┌─────────────────────────────────────────────────────────────────┐
│                    AutoGen Studio (8081)                         │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Vite Dev Server (5173) - 프록시로 CORS 해결                      │
│  └── /api/autogen/* → http://localhost:8081/api/*               │
│      (electron.vite.config.ts에서 설정)                          │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Browser (React UI) - window.electronAPI 없음                     │
│  └── browser-mock.ts가 fetch('/api/autogen/...') 사용            │
│      ★ 직접 fetch('http://localhost:8081/...') 금지! (CORS)     │
└─────────────────────────────────────────────────────────────────┘
```

### ★ CORS 문제 해결 규칙 (절대 잊지 말 것!)

| 모드 | API 호출 방법 | 이유 |
|------|--------------|------|
| Electron | `window.electronAPI.*` | Main Process가 Node.js로 8081 직접 호출 (CORS 없음) |
| Browser | `fetch('/api/autogen/...')` | Vite 프록시가 8081로 중계 (CORS 회피) |
| ❌ 금지 | `fetch('http://localhost:8081/...')` | 브라우저 CORS 정책으로 차단됨! |

### 핵심 파일 (수정 시 주의!)

| 파일 | 역할 | 주의사항 |
|------|------|----------|
| `electron.vite.config.ts` | Vite 프록시 설정 | `/api/autogen` → 8081 매핑 |
| `browser-mock.ts` | 브라우저 모드 폴백 | 반드시 `/api/autogen/...` 사용 |
| `a2a-handlers.ts` | Electron Main Process | 8081 직접 호출 가능 |
| `AutogenStatusBadge.tsx` | AutoGen 상태 표시 | electronAPI 우선, 없으면 프록시 |

### Agent Terminals 협업 패널 (★ 핵심!)

Agent Terminals 탭에서 AutoGen Studio 대화가 실시간으로 스트리밍됩니다:

- **터미널 없을 때**: AutoGen 협업 뷰가 풀스크린으로 표시
- **터미널 있을 때**: 툴바의 "AutoGen" 버튼으로 사이드바 토글
- **2초마다 자동 폴링**: IPC 통해 Main Process가 8081 호출

### 핵심 파일

| 파일 | 역할 |
|------|------|
| `a2a-handlers.ts` | Main Process에서 8081 호출 (유일한 호출점) |
| `a2a-api.ts` | Preload API (IPC 노출) |
| `AutogenCollabPanel.tsx` | Agent Terminals 협업 패널 |
| `TerminalGrid.tsx` | 터미널 그리드 + 협업 패널 통합 |

### AG-ACE-BRIDGE에서 트리거 (★ Bridge Module - 2026-01-24)

AG-ACE-BRIDGE의 Bridge Module을 통해 Auto-Claude를 프로그래밍 방식으로 실행할 수 있습니다:

```python
# AG-ACE-BRIDGE에서 실행
from src.bridge import WorkflowExecutor

executor = WorkflowExecutor()

# AI 모드: Auto-Claude의 모든 기능 활용
result = executor.execute_full_pipeline_sync(
    task_description="계산기 앱 만들어줘",
    complexity="standard",  # simple, standard, complex
    auto_merge=False        # True면 완료 후 자동 병합
)

# 파이프라인:
# 1. spec_runner.py → AI가 Spec 생성
# 2. run.py → Planner → Coder → QA 파이프라인
# 3. Git Worktree에서 안전하게 빌드
```

### Required Servers

```powershell
# AutoGen Studio (8081)
cd D:\Data\25_ACE\AG\autogen_a2a_kit
autogenstudio ui --host 127.0.0.1 --port 8081
```

### Sync Flow

1. AutoGen Studio(8081)에서 워크플로우 실행
2. Main Process(a2a-handlers.ts)가 IPC로 8081 직접 조회
3. Renderer가 IPC 결과를 UI에 표시
4. Vite 프록시는 dev 모드에서만 작동 (Electron 모드에서는 IPC 사용)

### ★ Agent → Task Flow (2026-01-25 확정)

AutoGen Studio에서 Agent 설계 → Auto-Claude에서 Task 표시 흐름:

#### Step 1: AutoGen Studio에서 Agent 설계
```
http://localhost:8081 → Teams → Create Team
- Agent 추가 (예: Calculator, Researcher)
- Model 설정 (Claude, GPT 등)
- Tools 연결
```

#### Step 2: AutoGen Studio에서 Workflow 실행
```
Sessions → New Session → Run
- Task 입력 (예: "5 + 3은?")
- Team 실행
- 결과 저장 (status: "complete")
```

#### Step 3: Auto-Claude가 결과 폴링
```typescript
// a2a-handlers.ts
const sessionsResponse = await fetch('http://localhost:8081/api/sessions/?user_id=guestuser@gmail.com');
const runsResponse = await fetch('http://localhost:8081/api/sessions/{id}/runs/?user_id=guestuser@gmail.com');
```

#### Step 4: Auto-Claude UI에 표시
| 컴포넌트 | 위치 | 표시 내용 |
|----------|------|-----------|
| `AutogenStatusBadge` | 사이드바 | 연결 상태 + "NEW" 배지 |
| `AutogenCollabPanel` | Agent Terminals 탭 | 실시간 대화 스트리밍 |
| `AutogenResultsWidget` | 하단 좌측 플로팅 | 최신 결과 요약 |

#### Step 5: (선택) AG-ACE-BRIDGE로 Spec 생성
```typescript
// AutogenCollabPanel.tsx의 "Create Spec from AutoGen" 폼
await window.electronAPI.workflowExecute(task, complexity, autoMerge);

// 파이프라인:
// spec_runner.py → Spec 생성
// run.py → Planner → Coder → QA
// 결과 → Kanban Board에 Task로 표시
```

#### 핵심 데이터 구조
```typescript
interface AutogenResult {
  workflow_name: string;  // "session_123"
  task: string;           // "5 + 3은?"
  result: string;         // "8"
  agents_used: string[];  // ["calculator_agent"]
  status: string;         // "complete"
  timestamp: string;      // ISO8601
  source?: string;        // "autogen-studio-direct"
}
```

### 추가 문서

상세 문서는 `.claude/MEMORY.md` 참조
