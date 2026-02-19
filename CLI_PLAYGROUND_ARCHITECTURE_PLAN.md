# CLI Playground Replication - Architecture Plan

**Date**: 2026-02-09  
**Status**: PLAN MODE (Design Only - No Implementation Yet)  
**Objective**: Design a CLI tool that replicates the AG-frontend Playground execution pipeline

---

## 1. Current Playground Pipeline (from exploration)

### 1.1 User Input Flow
```
User Input (PlaygroundPage.tsx)
  ↓
Task + Team Config + Files
  ↓
api.createSession() → REST POST /api/sessions
  ↓
Session Created { id, team_id, user_id }
  ↓
api.createRun() → REST POST /api/runs
  ↓
Run Created { id, session_id, status: 'pending' }
  ↓
ExecutionWebSocket.connect(ws://host/api/ws/runs/{runId}?token=...)
  ↓
ws.startExecution({ type: 'start', task, team_config, files })
```

### 1.2 WebSocket Streaming & Message Processing
```
Server Streams Messages via ws://host/api/ws/runs/{runId}
  ↓ (onMessage callback fires for each message)
ExecutionStore.addWSMessage(msg) processes 7 message types:
  
  - 'message_chunk'      → Accumulate streaming text into streamingChunks
  - 'llm_call_event'     → Extract JSON + token usage, add to turns[]
  - 'message'            → Full agent message, reset streaming
  - 'input_request'      → Pause execution, wait for user input
  - 'completion'/'result'→ Final result, calculate summary stats
  - 'error'              → Error state
  
  ↓ (State updates trigger UI re-render)
UI Displays: turns[], streamingChunks, status, error
```

### 1.3 Data Structures (from executionStore.ts)

**ExecutionState** (Zustand store):
```typescript
{
  isRunning: boolean
  currentRunId: string | null
  currentSessionId: number | null
  turns: AgentTurn[]              // All messages in conversation
  status: 'idle' | 'connecting' | 'running' | 'completed' | 'error'
  error: string | null
  streamingChunks: string         // Current streaming text accumulation
  streamingSource: string | null  // Which agent is currently streaming
  inputRequest: { prompt, source } | null  // Pause for user input
  runSummary: RunSummary | null   // Final statistics
}

AgentTurn {
  source: string              // Agent name or 'user'
  content: string             // Message text or JSON (for llm_call_event)
  timestamp: string           // ISO timestamp
  messageType: 'user' | 'agent' | 'llm_event'
  tokensIn?: number
  tokensOut?: number
}

RunSummary {
  stopReason: string | null
  duration: number | null
  totalTokensIn: number
  totalTokensOut: number
  turnCount: number
  agentTurnCount: number
  terminatedBy: string | null
}
```

### 1.4 API Endpoints Used

| Operation | Method | Endpoint | Payload | Response |
|-----------|--------|----------|---------|----------|
| Create Session | POST | /api/sessions | `{ team_id, user_id }` | `{ id, team_id, user_id }` |
| Create Run | POST | /api/runs | `{ session_id, task, files, team_config }` | `{ id, session_id, status }` |
| Get Sessions | GET | /api/sessions | - | `{ sessions: [...] }` |
| Get Session Runs | GET | /api/sessions/{id}/runs | - | `{ runs: [...] }` |
| WebSocket | WS | /api/ws/runs/{runId}?token=... | `{ type: 'start', task, team_config, files }` | Streaming messages |
| Get Teams | GET | /api/teams | - | `{ teams: [...] }` |
| Validate Team | POST | /api/teams/validate | `{ component }` | `{ is_valid: boolean, error?: string }` |

### 1.5 Authentication
- Token stored in `localStorage['auth_token']` (browser)
- Passed in `Authorization: Bearer {token}` header for REST calls
- Passed in WebSocket query param: `?token={token}`

---

## 2. Proposed CLI Tool Design

### 2.1 Architecture (4-Layer Model - inspired by Auto-Claude)

```
┌─────────────────────────────────────────────────────────────┐
│  CLI Interface Layer                                         │
│  ├─ Command Parser (run, submit, status, view-session)     │
│  └─ Output Formatter (streaming, table, JSON, export)      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌─────────────────────────▼────────────────────────────────────┐
│  Orchestration Layer                                         │
│  ├─ HeadlessExecutor (replaces PlaygroundPage)             │
│  ├─ SessionManager (session/run lifecycle)                 │
│  └─ ExecutionStateMachine (replaces Zustand store)         │
└────────────────────────┬────────────────────────────────────┘
                         │
┌─────────────────────────▼────────────────────────────────────┐
│  Communication Layer                                         │
│  ├─ APIClient (REST calls to AutoGen Studio :8081)         │
│  ├─ WebSocketExecutor (streaming + message processor)      │
│  └─ InputHandler (stdin/prompt for input_request)          │
└────────────────────────┬────────────────────────────────────┘
                         │
┌─────────────────────────▼────────────────────────────────────┐
│  Backend Layer (AutoGen Studio)                              │
│  ├─ REST API (:8081/api/...)                               │
│  └─ WebSocket (:8081/api/ws/runs/...)                      │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 CLI Command Structure

```bash
# Run a task directly (interactive mode)
python cli.py run \
  --task "Write a Python function" \
  --team-id 1 \
  --team-file team.json \
  [--session-id existing_session] \
  [--file file1.txt] \
  [--interactive]

# Submit a project for execution (batch mode)
python cli.py submit \
  --project-path ./my-project \
  --team-id 1

# List sessions
python cli.py list sessions [--team-id 1]

# View session details
python cli.py view session {session-id}

# View run results
python cli.py view run {run-id}

# Continue interrupted session
python cli.py resume --session-id {id}

# Export results
python cli.py export \
  --session-id {id} \
  --format json|markdown|csv \
  --output output.json
```

### 2.3 Key Components

#### 2.3.1 HeadlessExecutor (replaces PlaygroundPage.tsx)
```python
class HeadlessExecutor:
    def __init__(self, api_client, auth_token):
        self.api = api_client
        self.auth_token = auth_token
        self.state_machine = ExecutionStateMachine()
        
    async def execute_task(self, task, team_id, files=None, session_id=None):
        """
        Main entry point for task execution.
        Returns: (final_turns, summary)
        """
        # 1. Create or reuse session
        if not session_id:
            session = await self.api.create_session(team_id)
            session_id = session['id']
        
        # 2. Get team config
        teams = await self.api.get_teams()
        team_config = next((t for t in teams if t['id'] == team_id), None)
        
        # 3. Create run
        run = await self.api.create_run(session_id, task, files)
        
        # 4. Connect WebSocket and stream
        await self.stream_execution(run['id'], task, team_config, files)
        
        # 5. Return results
        return self.state_machine.turns, self.state_machine.run_summary
    
    async def stream_execution(self, run_id, task, team_config, files):
        """Stream execution via WebSocket"""
        # Creates ExecutionWebSocket, processes each message via 
        # state_machine.process_message(msg)
        pass
```

#### 2.3.2 ExecutionStateMachine (replaces Zustand store)
```python
class ExecutionStateMachine:
    """
    Headless version of executionStore.ts
    Manages state transitions without React
    """
    def __init__(self):
        self.is_running = False
        self.status = 'idle'  # 'idle'|'connecting'|'running'|'completed'|'error'
        self.turns = []       # AgentTurn[]
        self.error = None
        self.streaming_chunks = ''
        self.streaming_source = None
        self.input_request = None
        self.run_summary = None
        
    def process_message(self, msg: dict):
        """
        Process incoming WebSocket message.
        Identical logic to executionStore.addWSMessage()
        """
        msg_type = msg.get('type')
        
        if msg_type == 'message_chunk':
            # Accumulate streaming text
            self.streaming_chunks += msg.get('data', {}).get('content', '')
            self.streaming_source = msg.get('source', self.streaming_source)
            self.status = 'running'
            
        elif msg_type == 'llm_call_event':
            # Extract LLM call JSON with token usage
            data = msg.get('data', {})
            self.turns.append({
                'source': 'llm_call_event',
                'content': json.dumps(data),
                'timestamp': msg.get('timestamp'),
                'messageType': 'llm_event',
                'tokensIn': data.get('response', {}).get('usage', {}).get('prompt_tokens'),
                'tokensOut': data.get('response', {}).get('usage', {}).get('completion_tokens'),
            })
            self.status = 'running'
            
        elif msg_type == 'message':
            # Full message from agent
            data = msg.get('data', {})
            self.turns.append({
                'source': data.get('source', 'agent'),
                'content': data.get('content', ''),
                'timestamp': msg.get('timestamp'),
                'messageType': self._infer_message_type(data),
                'tokensIn': data.get('models_usage', {}).get('prompt_tokens'),
                'tokensOut': data.get('models_usage', {}).get('completion_tokens'),
            })
            self.streaming_chunks = ''
            self.streaming_source = None
            self.status = 'running'
            
        elif msg_type == 'input_request':
            # Pause for user input
            data = msg.get('data', {})
            self.input_request = {
                'prompt': data.get('prompt', 'Please provide input'),
                'source': data.get('source', 'agent')
            }
            self.status = 'running'
            
        elif msg_type in ('completion', 'result'):
            # Final completion
            data = msg.get('data', {})
            task_result = data.get('task_result', {})
            
            self.run_summary = {
                'stopReason': task_result.get('stop_reason'),
                'duration': data.get('duration'),
                'totalTokensIn': sum(t.get('tokensIn', 0) for t in self.turns),
                'totalTokensOut': sum(t.get('tokensOut', 0) for t in self.turns),
                'turnCount': len(self.turns),
                'agentTurnCount': len([t for t in self.turns if t['messageType'] == 'agent']),
                'terminatedBy': self._get_last_agent(),
            }
            self.status = 'completed'
            self.is_running = False
            self.streaming_chunks = ''
            self.streaming_source = None
            self.input_request = None
            
        elif msg_type == 'error':
            self.status = 'error'
            self.error = msg.get('error', 'Unknown error')
            self.is_running = False
```

#### 2.3.3 WebSocketExecutor (replaces ws.ts ExecutionWebSocket class)
```python
class WebSocketExecutor:
    """
    WebSocket client for streaming execution.
    Mirrors ExecutionWebSocket from ws.ts
    """
    def __init__(self, run_id, auth_token, base_url='ws://localhost:8081'):
        self.run_id = run_id
        self.auth_token = auth_token
        self.url = f"{base_url}/api/ws/runs/{run_id}?token={auth_token}"
        self.ws = None
        self.message_callback = None
        
    async def connect(self):
        """Establish WebSocket connection"""
        import websockets
        self.ws = await websockets.connect(self.url)
        asyncio.create_task(self._read_messages())
        
    async def start_execution(self, task, team_config, files=None):
        """Send start message"""
        msg = {
            'type': 'start',
            'task': task,
            'team_config': team_config,
            'files': files or []
        }
        await self.ws.send(json.dumps(msg))
        
    async def send_input(self, input_text):
        """Send input response to input_request"""
        msg = {
            'type': 'input_response',
            'response': input_text
        }
        await self.ws.send(json.dumps(msg))
        
    async def stop(self, reason='user_stopped'):
        """Stop execution"""
        msg = {
            'type': 'stop',
            'reason': reason
        }
        await self.ws.send(json.dumps(msg))
        
    async def _read_messages(self):
        """Read and process incoming messages"""
        async for raw_msg in self.ws:
            try:
                msg = json.loads(raw_msg)
                if self.message_callback:
                    self.message_callback(msg)
            except json.JSONDecodeError:
                print(f"Failed to parse WebSocket message: {raw_msg}")
```

#### 2.3.4 Output Formatters

```python
class OutputFormatter:
    """Format execution results for CLI output"""
    
    @staticmethod
    def format_streaming(turn, is_chunk=False):
        """Display streaming text in real-time"""
        if is_chunk:
            print(turn['content'], end='', flush=True)
        else:
            source = turn['source']
            content = turn['content']
            print(f"\n[{source}]: {content}")
    
    @staticmethod
    def format_summary(run_summary):
        """Format final summary as table"""
        print("\n" + "="*60)
        print("EXECUTION SUMMARY")
        print("="*60)
        print(f"Duration:        {run_summary['duration']}s")
        print(f"Messages:        {run_summary['turnCount']}")
        print(f"Agent Turns:     {run_summary['agentTurnCount']}")
        print(f"Stop Reason:     {run_summary['stopReason']}")
        print(f"Terminated By:   {run_summary['terminatedBy']}")
        print(f"Tokens In:       {run_summary['totalTokensIn']}")
        print(f"Tokens Out:      {run_summary['totalTokensOut']}")
        print("="*60)
    
    @staticmethod
    def format_json(turns, summary):
        """Export as JSON"""
        return {
            'turns': turns,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def format_markdown(turns, summary):
        """Export as Markdown"""
        # Markdown with headers for each turn
        pass
```

---

## 3. Integration Options

### 3.1 Option A: Standalone CLI Tool
**Pros:**
- Clean separation of concerns
- No coupling to existing Auto-Claude infrastructure
- Can be independently tested and deployed
- Simple API surface

**Cons:**
- Duplicates some CLI infrastructure from Auto-Claude
- Separate maintenance burden
- No shared agent registry with Auto-Claude

**Recommendation**: Start here for MVP

### 3.2 Option B: Extend Auto-Claude CLI
**Pros:**
- Reuses existing 4-layer architecture
- Shares agent registry, adapters
- Single CLI entry point for all functionality
- Integrates with existing 24/7 hub

**Cons:**
- More complex initial integration
- Must work within existing CLI patterns
- Larger refactoring scope

**Recommendation**: Phase 2 enhancement

### 3.3 Option C: Library + CLI Wrapper
**Pros:**
- `ag_cli_executor` library (reusable)
- `ag-cli-playground` CLI wrapper
- Can be used programmatically or via CLI
- Both standalone and integrated approaches

**Cons:**
- More complex project structure
- Requires API stability documentation

**Recommendation**: Phase 2 refactoring

---

## 4. Implementation Roadmap

### Phase 1: MVP (7-10 days)
- **Week 1**:
  - [ ] Create `AG-cli/playgrounds/` directory structure
  - [ ] Implement `HeadlessExecutor` class
  - [ ] Implement `ExecutionStateMachine` (copy logic from executionStore.ts)
  - [ ] Implement `WebSocketExecutor` (async WebSocket with JSON protocol)
  - [ ] Implement basic `OutputFormatter` (streaming + summary)

- **Week 2**:
  - [ ] Create CLI entry point with argparse
  - [ ] Implement `run` command (main task execution)
  - [ ] Implement `list sessions` command
  - [ ] Implement `view session` command
  - [ ] Add authentication (token from env or file)
  - [ ] Add unit tests for state machine
  - [ ] E2E test: execute single task, verify results match Playground

### Phase 2: Features (10-14 days)
- [ ] Implement `submit` command (batch project execution)
- [ ] Implement `resume` command (continue interrupted sessions)
- [ ] Add input handling for `input_request` (stdin or interactive prompts)
- [ ] Implement export formatters (JSON, Markdown, CSV)
- [ ] Add session history and filtering
- [ ] Add verbose/debug logging
- [ ] Performance profiling

### Phase 3: Integration (7-10 days)
- [ ] Integrate with Auto-Claude CLI (extend existing infrastructure)
- [ ] Refactor as shared library + CLI wrapper
- [ ] Add shared agent registry support
- [ ] Document CLI interface and API
- [ ] Create examples and tutorials

---

## 5. File Structure (Phase 1)

```
AG-cli/
├── playgrounds/
│   ├── __init__.py
│   ├── executor.py          # HeadlessExecutor class
│   ├── state_machine.py     # ExecutionStateMachine class
│   ├── websocket.py         # WebSocketExecutor class
│   ├── formatter.py         # OutputFormatter class
│   ├── api_client.py        # REST API client wrapper
│   └── cli.py               # CLI entry point (argparse)
├── tests/
│   ├── test_state_machine.py
│   ├── test_executor.py
│   └── test_e2e.py
└── examples/
    ├── simple_task.py
    └── batch_project.py
```

---

## 6. Key Design Decisions

1. **Async/Await Pattern**: Use `asyncio` for WebSocket streaming (matches Python async/await conventions)

2. **State Machine Over Store**: Replace Zustand with stateful class (no React dependency)

3. **Same Message Processing Logic**: Copy `addWSMessage()` logic exactly from executionStore.ts to ensure parity

4. **Authentication**: Support multiple auth methods:
   - Environment variable: `AUTOGEN_STUDIO_TOKEN`
   - File: `~/.ag-cli/config.json` with token
   - CLI argument: `--token <token>`

5. **Output Modes**:
   - `--stream`: Real-time streaming output (default)
   - `--json`: JSON output (for piping/scripting)
   - `--quiet`: Only final result

6. **Error Handling**: Propagate WebSocket errors, connection errors, and API errors with helpful messages

7. **Session Reuse**: Support both single-run (stateless) and multi-turn (stateful session)

---

## 7. Success Criteria

1. **Feature Parity**: CLI tool produces identical results to Playground for same input
2. **Execution Equivalence**: 
   - Same WebSocket messages received
   - Same state transitions
   - Same token counts and summaries
3. **Performance**: Handle streaming at same speed as browser
4. **Error Handling**: Gracefully handle connection errors, input errors, API errors
5. **Testing**: 
   - 100% of state machine logic covered by unit tests
   - E2E test: execute sample task, compare turns/summary with Playground
   - Performance test: verify streaming throughput

---

## 8. Dependencies

### New Python Packages
```
websockets>=12.0          # AsyncIO WebSocket client
click>=8.1.0              # Alternative to argparse (optional)
rich>=13.0                # Pretty CLI output
```

### Existing Projects
- AutoGen Studio API (port 8081)
- Existing AG-cli infrastructure (Message Bus, SharedMemory)

---

## 9. Open Questions

1. **Input Request Handling**: How to handle `input_request` messages in CLI context?
   - Option A: Block and read from stdin
   - Option B: Provide `--input` flag with pre-defined inputs
   - Option C: Fail with error and require manual re-submission

2. **File Upload**: How to handle file uploads in CLI?
   - Option A: Pass file paths as arguments
   - Option B: Support stdin piping
   - Option C: Copy files to temporary location

3. **Session Persistence**: Store session metadata locally or query from backend?
   - Option A: Query backend (GET /api/sessions)
   - Option B: Local cache (JSON file)
   - Option C: Hybrid (cache with sync option)

4. **Integration Scope**: Standalone tool vs. extension to Auto-Claude CLI?
   - Recommend: Phase 1 = Standalone, Phase 2 = Integrate

---

## 10. References

### Frontend Source Files (Read-Only)
- `AG-frontend/src/features/playground/PlaygroundPage.tsx` (761 lines)
- `AG-frontend/src/features/playground/executionStore.ts` (232 lines)
- `AG-frontend/src/shared/api/ws.ts` (156 lines)
- `AG-frontend/src/shared/api/client.ts` (299 lines)

### Existing Infrastructure
- `AG-cli/mcp/message_bus.py` - Pattern for service communication
- `AG-cli/agents/base_collaborative.py` - Pattern for async agent coordination
- `AG/Auto-Claude/cli.py` - Existing 4-layer CLI architecture

### AutoGen Studio Backend
- Runs on `:8081`
- REST API: `/api/teams/`, `/api/sessions/`, `/api/runs/`
- WebSocket: `/api/ws/runs/{runId}`

---

**NEXT STEP**: Wait for user confirmation on:
1. Proceed with Phase 1 implementation
2. Preferred integration approach (Standalone vs. Extend Auto-Claude)
3. Decision on open questions (input handling, file upload, session persistence)
