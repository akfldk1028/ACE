// ============================================================
// WebSocket Client for AutoGen Studio execution streaming
// Protocol: ws://host/api/ws/runs/{run_id}?token={auth_token}
// Matches AutoGen Studio chat.tsx setupWebSocket() 1:1
// ============================================================

import type { AgentMessageConfig, TaskResult, RunStatus } from '@/shared/types/datamodel'

// Matches AutoGen Studio WebSocketMessage from datamodel.ts
export interface WSMessage {
  type:
    | 'message'
    | 'result'
    | 'completion'
    | 'input_request'
    | 'error'
    | 'llm_call_event'
    | 'message_chunk'
  data?: AgentMessageConfig | TaskResult
  status?: RunStatus
  error?: string
  timestamp?: string
  // Convenience fields flattened from data for 'message' type
  source?: string
  content?: string
}

export interface FileAttachment {
  name: string
  type: string
  content: string
}

interface ExecutionWSOptions {
  runId: number | string
  onMessage: (msg: WSMessage) => void
  onClose?: () => void
  onError?: (error: string) => void
}

// AutoGen Studio getBaseUrl() logic - handles /api, localhost, and full URLs
function getWebSocketBaseUrl(url: string): string {
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

export class ExecutionWebSocket {
  private ws: WebSocket | null = null
  private runId: number | string
  private onMessage: (msg: WSMessage) => void
  private onClose?: () => void
  private onError?: (error: string) => void
  private pingInterval: ReturnType<typeof setInterval> | null = null

  constructor(opts: ExecutionWSOptions) {
    this.runId = opts.runId
    this.onMessage = opts.onMessage
    this.onClose = opts.onClose
    this.onError = opts.onError
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const serverUrl = '/api' // matches getServerUrl()
      const baseUrl = getWebSocketBaseUrl(serverUrl)
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const authToken = localStorage.getItem('auth_token')
      const tokenParam = authToken ? `?token=${encodeURIComponent(authToken)}` : ''
      const url = `${protocol}//${baseUrl}/api/ws/runs/${this.runId}${tokenParam}`

      this.ws = new WebSocket(url)

      this.ws.onopen = () => {
        this.pingInterval = setInterval(() => {
          if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'ping' }))
          }
        }, 30_000)
        resolve()
      }

    this.ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data)
        this.onMessage(msg)
      } catch {
        // ignore non-JSON messages (pong, etc.)
      }
    }

    this.ws.onclose = () => {
      this.cleanup()
      this.onClose?.()
    }

    this.ws.onerror = () => {
      reject(new Error('WebSocket connection error'))
      this.onError?.('WebSocket connection error')
    }
    })
  }

  // Matches AutoGen Studio socket.onopen send: { type: "start", task, files, team_config }
  startExecution(task: string, teamConfig?: unknown, files?: FileAttachment[]) {
    if (this.ws?.readyState !== WebSocket.OPEN) return
    this.ws.send(JSON.stringify({
      type: 'start',
      task,
      files: files ?? [],
      team_config: teamConfig ?? null,
    }))
  }

  sendInput(input: string) {
    if (this.ws?.readyState !== WebSocket.OPEN) return
    this.ws.send(JSON.stringify({
      type: 'input_response',
      response: input,
    }))
  }

  stop(reason?: string) {
    if (this.ws?.readyState !== WebSocket.OPEN) return
    this.ws.send(JSON.stringify({
      type: 'stop',
      reason: reason ?? undefined,
    }))
  }

  disconnect() {
    this.cleanup()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  private cleanup() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
  }
}
