# ag_cli -- AG-CLI Tools (from autogen_a2a_kit/AG-cli)

MCP-based infrastructure layer providing shared memory, message bus, and Claude CLI execution. These servers run as background services that agents connect to for coordination.

## Structure

```
ag_cli/
  agents/
    collaborative_agent.py   -- A2A-capable collaborative agent base class
  mcp/
    shared_memory_server.py  -- Key-value store MCP server (port 8101)
    message_bus_server.py    -- Pub/sub message bus MCP server (port 8100)
  tools/
    claude_cli_executor.py   -- Wraps Claude CLI for programmatic invocation
```

## Key Classes / Functions

| Name | Location | Description |
|---|---|---|
| `CollaborativeAgent` | agents/ | Base agent with say/ask/listen messaging and Claude CLI work() |
| `SharedMemoryServer` | mcp/ | MCP server on port 8101 -- store, get, delete, list, events |
| `MessageBus` | mcp/ | MCP server on port 8100 -- publish, subscribe, broadcast |
| `ClaudeCLIExecutor` | tools/ | `execute(prompt, workdir)` -- runs Claude CLI subprocess |

## Usage

```python
# Start the MCP servers (typically via separate terminals)
# SharedMemory: python -m ag_cli.mcp.shared_memory_server  (port 8101)
# MessageBus:   python -m ag_cli.mcp.message_bus_server     (port 8100)

from ag_cli.agents.collaborative_agent import CollaborativeAgent

agent = CollaborativeAgent(name="my-agent", folder="my_work", expertise="Python")
await agent.say("Starting task", to="orchestrator")
result = await agent.work("Write unit tests", context={"api_spec": spec})
await agent.share("test_results", result)
```

## Notes

- SharedMemoryServer and MessageBus are the backbone for multi-agent coordination.
- `ClaudeCLIExecutor` spawns `claude` CLI processes with timeout and output capture.
- Agents discover each other through the SharedMemory registry.
- Start servers in order: MessageBus (8100) -> SharedMemory (8101) -> agents.
