/**
 * McpPage - MCP server management, tool browser, and test workbench
 * Three sections: Server list (left), Tool browser (right), Test workbench (bottom full-width)
 * Uses real WebSocket connections to AutoGen Studio MCP bridge.
 */

import { memo, useState, useCallback, useMemo } from 'react'
import { Card, Badge, Button } from '@/shared/ui'
import {
  Wrench,
  Plus,
  Play,
  Server,
  Trash2,
  RefreshCw,
  Terminal,
  Globe,
  Zap,
  ChevronRight,
  Loader2,
} from 'lucide-react'
import { useMcpStore } from './mcpStore'
import type { McpServer, McpTool, McpServerStatus } from './mcpStore'
import { McpServerDialog } from './McpServerDialog'
import { McpWebSocket } from '@/shared/api/mcpWs'
import type { McpWsMessage } from '@/shared/api/mcpWs'

// --------------- Sub-components ---------------

const STATUS_STYLES: Record<McpServerStatus, { dot: string; label: string }> = {
  connected: { dot: 'bg-(--color-semantic-success)', label: 'Connected' },
  connecting: { dot: 'bg-(--color-semantic-warning)', label: 'Connecting...' },
  disconnected: { dot: 'bg-(--color-text-tertiary)', label: 'Disconnected' },
  error: { dot: 'bg-(--color-semantic-error)', label: 'Error' },
}

const TYPE_ICONS: Record<string, typeof Terminal> = {
  stdio: Terminal,
  sse: Globe,
  streamable_http: Zap,
}

const TYPE_LABELS: Record<string, string> = {
  stdio: 'Stdio',
  sse: 'SSE',
  streamable_http: 'HTTP',
}

function ServerStatusDot({ status }: { status: McpServerStatus }) {
  const style = STATUS_STYLES[status]
  return (
    <span className="flex items-center gap-1.5" title={style.label}>
      <span className={`w-2 h-2 rounded-full ${style.dot}`} />
      <span className="text-xs text-(--color-text-tertiary)">{style.label}</span>
    </span>
  )
}

interface ServerCardProps {
  server: McpServer
  isSelected: boolean
  isConnecting: boolean
  onSelect: () => void
  onRemove: () => void
  onCheckHealth: () => void
}

const ServerCard = memo(function ServerCard({ server, isSelected, isConnecting, onSelect, onRemove, onCheckHealth }: ServerCardProps) {
  const TypeIcon = TYPE_ICONS[server.type] ?? Server

  return (
    <div
      role="button"
      tabIndex={0}
      aria-pressed={isSelected}
      onClick={onSelect}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect() } }}
      className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
        isSelected
          ? 'ring-2 ring-(--color-accent-primary) border-(--color-accent-primary) bg-(--color-background-secondary)'
          : 'border-(--color-border-default) hover:border-(--color-accent-primary)'
      }`}
    >
      <TypeIcon className="w-5 h-5 text-(--color-text-secondary) flex-shrink-0" />

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium truncate">{server.name}</p>
          <span className="flex-shrink-0">
            <Badge variant="outline">{TYPE_LABELS[server.type]}</Badge>
          </span>
        </div>
        <div className="flex items-center gap-3 mt-1">
          <ServerStatusDot status={server.status} />
          {server.tools.length > 0 && (
            <span className="text-xs text-(--color-text-tertiary)">
              {server.tools.length} tool{server.tools.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-1 flex-shrink-0">
        <button
          onClick={(e) => { e.stopPropagation(); onCheckHealth() }}
          disabled={isConnecting}
          aria-label={`Check health of ${server.name}`}
          title={server.status === 'connected' ? 'Disconnect' : 'Connect'}
          className="p-1.5 rounded hover:bg-(--color-background-secondary) text-(--color-text-tertiary) hover:text-(--color-text-primary) focus:outline-none focus:ring-2 focus:ring-(--color-accent-primary) transition-colors disabled:opacity-50"
        >
          {isConnecting ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <RefreshCw className="w-3.5 h-3.5" />
          )}
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); onRemove() }}
          aria-label={`Remove ${server.name}`}
          title="Remove server"
          className="p-1.5 rounded hover:bg-(--color-semantic-error-light) text-(--color-text-tertiary) hover:text-(--color-semantic-error) focus:outline-none focus:ring-2 focus:ring-(--color-semantic-error) transition-colors"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  )
})

interface ToolCardProps {
  tool: McpTool
  isSelected: boolean
  onSelect: () => void
}

const ToolCard = memo(function ToolCard({ tool, isSelected, onSelect }: ToolCardProps) {
  return (
    <div
      role="button"
      tabIndex={0}
      aria-pressed={isSelected}
      onClick={onSelect}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect() } }}
      className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
        isSelected
          ? 'ring-2 ring-(--color-accent-primary) border-(--color-accent-primary) bg-(--color-background-secondary)'
          : 'border-(--color-border-default) hover:border-(--color-accent-primary)'
      }`}
    >
      <Wrench className="w-4 h-4 text-(--color-text-tertiary) flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium font-mono">{tool.name}</p>
        <p className="text-xs text-(--color-text-tertiary) truncate">{tool.description}</p>
      </div>
      <ChevronRight className="w-4 h-4 text-(--color-text-tertiary) flex-shrink-0" />
    </div>
  )
})

// --------------- Helpers ---------------

function buildSchemaTemplate(schema: Record<string, unknown>): string {
  const properties = schema.properties as Record<string, Record<string, unknown>> | undefined
  if (!properties) return '{}'
  const template: Record<string, unknown> = {}
  for (const [key, prop] of Object.entries(properties)) {
    switch (prop.type) {
      case 'string': template[key] = ''; break
      case 'number': template[key] = 0; break
      case 'boolean': template[key] = false; break
      case 'array': template[key] = []; break
      case 'object': template[key] = {}; break
      default: template[key] = null
    }
  }
  return JSON.stringify(template, null, 2)
}

// --------------- Main Page ---------------

export function McpPage() {
  const servers = useMcpStore((s) => s.servers)
  const selectedServerId = useMcpStore((s) => s.selectedServerId)
  const selectedToolName = useMcpStore((s) => s.selectedToolName)
  const connectingId = useMcpStore((s) => s.connectingId)
  const connections = useMcpStore((s) => s.connections)
  const selectServer = useMcpStore((s) => s.selectServer)
  const selectTool = useMcpStore((s) => s.selectTool)
  const removeServer = useMcpStore((s) => s.removeServer)
  const updateServerStatus = useMcpStore((s) => s.updateServerStatus)
  const setConnection = useMcpStore((s) => s.setConnection)
  const removeConnection = useMcpStore((s) => s.removeConnection)
  const setConnecting = useMcpStore((s) => s.setConnecting)

  const [dialogOpen, setDialogOpen] = useState(false)
  const [toolInput, setToolInput] = useState('')
  const [testOutput, setTestOutput] = useState<string | null>(null)
  const [executing, setExecuting] = useState(false)

  const selectedServer = useMemo(
    () => servers.find((s) => s.id === selectedServerId) ?? null,
    [servers, selectedServerId],
  )

  const selectedTool = useMemo(
    () => selectedServer?.tools.find((t) => t.name === selectedToolName) ?? null,
    [selectedServer, selectedToolName],
  )

  const isSelectedConnected = selectedServer?.status === 'connected' && selectedServerId != null && connections[selectedServerId] != null

  // When a tool is selected, pre-fill the input with a schema template
  const handleSelectTool = useCallback((name: string) => {
    selectTool(name)
    setTestOutput(null)
    const server = useMcpStore.getState().servers.find((s) => s.id === useMcpStore.getState().selectedServerId)
    const tool = server?.tools.find((t) => t.name === name)
    if (tool) {
      setToolInput(buildSchemaTemplate(tool.inputSchema))
    } else {
      setToolInput('{}')
    }
  }, [selectTool])

  const handleSelectServer = useCallback((id: string) => {
    selectServer(id)
    setTestOutput(null)
    setToolInput('')
  }, [selectServer])

  const handleRemoveServer = useCallback((id: string) => {
    removeServer(id)
    setTestOutput(null)
    setToolInput('')
  }, [removeServer])

  // Real WebSocket health check / connect / disconnect
  const handleCheckHealth = useCallback(async (server: McpServer) => {
    // If already connected, disconnect
    if (server.status === 'connected' && connections[server.id]) {
      removeConnection(server.id)
      updateServerStatus(server.id, 'disconnected', [])
      return
    }

    setConnecting(server.id)
    updateServerStatus(server.id, 'connecting')

    const sessionId = crypto.randomUUID()

    const ws = new McpWebSocket({
      sessionId,
      serverParams: server.params,
      onMessage: (msg: McpWsMessage) => {
        if (msg.type === 'initialized') {
          // Connection established, now list tools
          ws.listTools()
        } else if (msg.type === 'operation_result' && msg.operation === 'list_tools') {
          const tools = (msg.data as { tools?: McpTool[] })?.tools ?? []
          updateServerStatus(server.id, 'connected', tools)
          setConnecting(null)
        } else if (msg.type === 'operation_error') {
          console.warn('[MCP] Operation error:', msg.error)
        }
      },
      onClose: () => {
        updateServerStatus(server.id, 'disconnected', [])
        setConnecting(null)
      },
      onError: (error) => {
        console.error('[MCP] WebSocket error:', error)
        updateServerStatus(server.id, 'error', [])
        setConnecting(null)
      },
    })

    try {
      await ws.connect()
      setConnection(server.id, ws)
    } catch (err) {
      console.error('[MCP] Connection failed:', err)
      updateServerStatus(server.id, 'error', [])
      setConnecting(null)
    }
  }, [connections, removeConnection, updateServerStatus, setConnecting, setConnection])

  const handleOpenDialog = useCallback(() => setDialogOpen(true), [])
  const handleCloseDialog = useCallback(() => setDialogOpen(false), [])

  // Real tool execution via WebSocket
  const handleExecuteTest = useCallback(() => {
    if (!selectedTool || !selectedServerId) return

    const conn = connections[selectedServerId]
    if (!conn || !conn.isConnected) {
      setTestOutput(JSON.stringify({ error: 'Not connected to server. Click the refresh button to connect first.' }, null, 2))
      return
    }

    let parsed: Record<string, unknown>
    try {
      parsed = JSON.parse(toolInput)
    } catch {
      setTestOutput(JSON.stringify({ error: 'Invalid JSON input' }, null, 2))
      return
    }

    setExecuting(true)
    setTestOutput(null)

    const toolName = selectedTool.name

    // Register a one-shot listener for the call_tool result
    const removeListener = conn.addListener((msg: McpWsMessage) => {
      if (msg.type === 'operation_result' && msg.operation === 'call_tool') {
        setTestOutput(JSON.stringify({
          status: 'success',
          tool: toolName,
          result: msg.data,
        }, null, 2))
        setExecuting(false)
        removeListener()
      } else if (msg.type === 'operation_error' && msg.operation === 'call_tool') {
        setTestOutput(JSON.stringify({
          status: 'error',
          tool: toolName,
          error: msg.error,
        }, null, 2))
        setExecuting(false)
        removeListener()
      }
    })

    conn.callTool(toolName, parsed)

    // Timeout fallback
    setTimeout(() => {
      removeListener()
      setExecuting((prev) => {
        if (prev) {
          setTestOutput(JSON.stringify({ error: 'Tool execution timed out (30s)' }, null, 2))
        }
        return false
      })
    }, 30_000)
  }, [selectedTool, selectedServerId, connections, toolInput])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-display-medium">MCP</h1>
          <p className="text-body-medium text-(--color-text-secondary) mt-1">
            Model Context Protocol workbench
          </p>
        </div>
        <Button onClick={handleOpenDialog}>
          <Plus className="w-4 h-4 mr-2" />
          Add Server
        </Button>
      </div>

      {/* Main grid: Servers + Tools */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Section 1: MCP Servers */}
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <Server className="w-5 h-5 text-(--color-text-secondary)" />
            <h2 className="text-heading-small">MCP Servers</h2>
            <span className="text-xs text-(--color-text-tertiary) ml-auto">
              {servers.length} server{servers.length !== 1 ? 's' : ''}
            </span>
          </div>

          {servers.length === 0 ? (
            <div className="text-center py-8">
              <Server className="w-12 h-12 mx-auto text-(--color-text-tertiary) mb-3" />
              <p className="text-body-small text-(--color-text-tertiary)">
                No MCP servers configured
              </p>
              <p className="text-xs text-(--color-text-tertiary) mt-1">
                Add a server to get started
              </p>
              <Button variant="secondary" size="sm" className="mt-3" onClick={handleOpenDialog}>
                <Plus className="w-3.5 h-3.5 mr-1.5" />
                Add Server
              </Button>
            </div>
          ) : (
            <div className="space-y-2">
              {servers.map((server) => (
                <ServerCard
                  key={server.id}
                  server={server}
                  isSelected={selectedServerId === server.id}
                  isConnecting={connectingId === server.id}
                  onSelect={() => handleSelectServer(server.id)}
                  onRemove={() => handleRemoveServer(server.id)}
                  onCheckHealth={() => handleCheckHealth(server)}
                />
              ))}
            </div>
          )}
        </Card>

        {/* Section 2: Available Tools */}
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <Wrench className="w-5 h-5 text-(--color-text-secondary)" />
            <h2 className="text-heading-small">Available Tools</h2>
            {selectedServer && selectedServer.tools.length > 0 && (
              <span className="text-xs text-(--color-text-tertiary) ml-auto">
                {selectedServer.tools.length} tool{selectedServer.tools.length !== 1 ? 's' : ''}
              </span>
            )}
          </div>

          {!selectedServer ? (
            <div className="text-center py-8">
              <Wrench className="w-12 h-12 mx-auto text-(--color-text-tertiary) mb-3" />
              <p className="text-body-small text-(--color-text-tertiary)">
                Select a server to browse tools
              </p>
            </div>
          ) : selectedServer.status === 'connecting' ? (
            <div className="text-center py-8">
              <Loader2 className="w-12 h-12 mx-auto text-(--color-text-tertiary) mb-3 animate-spin" />
              <p className="text-body-small text-(--color-text-tertiary)">
                Connecting to server...
              </p>
            </div>
          ) : selectedServer.status !== 'connected' ? (
            <div className="text-center py-8">
              <RefreshCw className="w-12 h-12 mx-auto text-(--color-text-tertiary) mb-3" />
              <p className="text-body-small text-(--color-text-tertiary)">
                Server is not connected
              </p>
              <p className="text-xs text-(--color-text-tertiary) mt-1">
                Click the refresh button to connect and discover tools
              </p>
            </div>
          ) : selectedServer.tools.length === 0 ? (
            <div className="text-center py-8">
              <Wrench className="w-12 h-12 mx-auto text-(--color-text-tertiary) mb-3" />
              <p className="text-body-small text-(--color-text-tertiary)">
                No tools discovered
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {selectedServer.tools.map((tool) => (
                <ToolCard
                  key={tool.name}
                  tool={tool}
                  isSelected={selectedToolName === tool.name}
                  onSelect={() => handleSelectTool(tool.name)}
                />
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Section 3: Test Workbench */}
      <Card>
        <div className="flex items-center gap-3 mb-4">
          <Play className="w-5 h-5 text-(--color-text-secondary)" />
          <h2 className="text-heading-small">Test Workbench</h2>
        </div>

        {!selectedTool ? (
          <p className="text-body-medium text-(--color-text-tertiary)">
            Select a tool above to test it interactively.
          </p>
        ) : (
          <div className="space-y-4">
            {/* Selected tool info */}
            <div className="flex items-center gap-3 p-3 rounded-lg bg-(--color-background-secondary)">
              <Wrench className="w-4 h-4 text-(--color-accent-primary) flex-shrink-0" />
              <div className="min-w-0">
                <p className="text-sm font-medium font-mono">{selectedTool.name}</p>
                <p className="text-xs text-(--color-text-tertiary)">{selectedTool.description}</p>
              </div>
            </div>

            {/* Input schema info */}
            {'properties' in selectedTool.inputSchema && selectedTool.inputSchema.properties != null && (
              <div>
                <p className="text-xs font-medium text-(--color-text-secondary) mb-1">Parameters</p>
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(selectedTool.inputSchema.properties as Record<string, Record<string, unknown>>).map(
                    ([paramName, paramDef]) => {
                      const required = Array.isArray(selectedTool.inputSchema.required) &&
                        (selectedTool.inputSchema.required as string[]).includes(paramName)
                      return (
                        <span key={paramName} className="flex items-center gap-1">
                          <Badge variant={required ? 'primary' : 'outline'}>
                            {paramName}: {String(paramDef.type ?? 'any')}
                          </Badge>
                        </span>
                      )
                    },
                  )}
                </div>
              </div>
            )}

            {/* JSON input */}
            <div>
              <label htmlFor="tool-input" className="text-sm font-medium text-(--color-text-secondary) mb-1 block">
                Input (JSON)
              </label>
              <textarea
                id="tool-input"
                value={toolInput}
                onChange={(e) => setToolInput(e.target.value)}
                rows={6}
                spellCheck={false}
                className="w-full px-4 py-3 rounded-md border border-(--color-border-default) bg-(--color-surface-card) text-(--color-text-primary) text-sm font-mono focus:outline-none focus:border-(--color-accent-primary) focus:ring-2 focus:ring-(--color-accent-primary)/20 placeholder:text-(--color-text-tertiary) resize-y"
                placeholder='{ "param": "value" }'
              />
            </div>

            {/* Execute */}
            <div className="flex items-center gap-3">
              <Button
                variant="primary"
                onClick={handleExecuteTest}
                disabled={!isSelectedConnected || executing}
              >
                {executing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
                    Executing...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-1.5" />
                    Execute
                  </>
                )}
              </Button>
              {!isSelectedConnected && (
                <span className="text-xs text-(--color-text-tertiary)">
                  Connect to server first to execute tools
                </span>
              )}
            </div>

            {/* Output */}
            {testOutput !== null && (
              <div>
                <p className="text-sm font-medium text-(--color-text-secondary) mb-1">Output</p>
                <pre className="w-full px-4 py-3 rounded-md border border-(--color-border-default) bg-(--color-background-secondary) text-(--color-text-primary) text-sm font-mono overflow-x-auto max-h-64 overflow-y-auto">
                  {testOutput}
                </pre>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Add Server Dialog */}
      <McpServerDialog open={dialogOpen} onClose={handleCloseDialog} />
    </div>
  )
}
