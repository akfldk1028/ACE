// ============================================================
// MCP WebSocket Client for AutoGen Studio MCP bridge
// Protocol: ws://host/api/mcp/ws/{session_id}?server_params=<base64>
// Follows ExecutionWebSocket pattern from ws.ts
// ============================================================

export interface McpWsMessage {
  type:
    | 'initialized'
    | 'operation_result'
    | 'operation_error'
    | 'mcp_activity'
    | 'error'
    | 'pong'
  session_id?: string
  capabilities?: Record<string, unknown>
  operation?: string
  data?: unknown
  error?: string
  activity_type?: string
  message?: string
}

export type McpMessageListener = (msg: McpWsMessage) => void

interface McpWebSocketOptions {
  sessionId: string
  serverParams: Record<string, unknown>
  onMessage: McpMessageListener
  onClose?: () => void
  onError?: (error: string) => void
}

function getWebSocketBaseUrl(): string {
  const url = '/api'
  let baseUrl = url.replace(/(^\w+:|^)\/\//, '')
  if (baseUrl.startsWith('localhost')) {
    baseUrl = baseUrl.replace('/api', '')
  } else if (baseUrl === '/api') {
    baseUrl = window.location.host
  } else {
    baseUrl = baseUrl.replace('/api', '').replace(/\/$/, '')
  }
  return baseUrl
}

export class McpWebSocket {
  private ws: WebSocket | null = null
  private sessionId: string
  private serverParams: Record<string, unknown>
  private onMessage: McpMessageListener
  private listeners: Set<McpMessageListener> = new Set()
  private onClose?: () => void
  private onError?: (error: string) => void
  private pingInterval: ReturnType<typeof setInterval> | null = null

  constructor(opts: McpWebSocketOptions) {
    this.sessionId = opts.sessionId
    this.serverParams = opts.serverParams
    this.onMessage = opts.onMessage
    this.onClose = opts.onClose
    this.onError = opts.onError
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const baseUrl = getWebSocketBaseUrl()
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const paramsBase64 = btoa(JSON.stringify(this.serverParams))
      const url = `${protocol}//${baseUrl}/api/mcp/ws/${this.sessionId}?server_params=${encodeURIComponent(paramsBase64)}`

      let resolved = false

      this.ws = new WebSocket(url)

      this.ws.onopen = () => {
        this.pingInterval = setInterval(() => {
          if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'ping' }))
          }
        }, 30_000)
      }

      this.ws.onmessage = (event) => {
        try {
          const msg: McpWsMessage = JSON.parse(event.data)
          if (msg.type === 'initialized' && !resolved) {
            resolved = true
            resolve()
          }
          // Dispatch to primary handler + any registered listeners
          this.onMessage(msg)
          for (const listener of this.listeners) {
            listener(msg)
          }
        } catch (err) {
          console.warn('[MCP WS] Non-JSON message ignored:', event.data, err)
        }
      }

      this.ws.onclose = () => {
        this.cleanup()
        this.onClose?.()
      }

      this.ws.onerror = () => {
        if (!resolved) {
          resolved = true
          reject(new Error('MCP WebSocket connection error'))
        }
        this.onError?.('MCP WebSocket connection error')
      }

      // Timeout for initialization
      setTimeout(() => {
        if (!resolved) {
          resolved = true
          reject(new Error('MCP WebSocket initialization timeout'))
        }
      }, 15_000)
    })
  }

  /** Register a one-shot or persistent message listener */
  addListener(listener: McpMessageListener): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  listTools() {
    this.send({ type: 'operation', operation: 'list_tools' })
  }

  callTool(toolName: string, args: Record<string, unknown>) {
    this.send({ type: 'operation', operation: 'call_tool', tool_name: toolName, arguments: args })
  }

  listResources() {
    this.send({ type: 'operation', operation: 'list_resources' })
  }

  readResource(uri: string) {
    this.send({ type: 'operation', operation: 'read_resource', uri })
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  disconnect() {
    this.cleanup()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  private send(data: Record<string, unknown>) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  private cleanup() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
    this.listeners.clear()
  }
}
