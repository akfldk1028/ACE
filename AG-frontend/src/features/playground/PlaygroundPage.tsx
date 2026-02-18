import { memo, useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { useQueryClient } from '@tanstack/react-query'
import { Button, Input, Badge } from '@/shared/ui'
import { useTeams, getTeamName } from '@/features/teams/useTeams'
import { useTeamStore } from '@/features/teams/teamStore'
import { useExecutionStore } from './executionStore'
import type { MessageType, RunSummary } from './executionStore'
import { useSessions, useSessionMessages, filterSessionsByTeam } from './useExecution'
import { ExecutionWebSocket } from '@/shared/api/ws'
import type { FileAttachment } from '@/shared/api/ws'
import { api } from '@/shared/api'
import {
  Send, Square, Bot, User, AlertCircle, MessageSquare, History,
  ChevronRight, ChevronDown, Cpu, Zap, ExternalLink, Clock, BarChart3, StopCircle,
} from 'lucide-react'
import { cn } from '@/shared/lib/utils'
import { FileUpload } from './FileUpload'
import { LiveAgentFlow } from './LiveAgentFlow'
import { broadcastFlowState, onFlowPresence } from './flowChannel'
import { useToolApproval, ToolApprovalCard, parseToolApproval, useToolApprovalStore } from '@/features/tool-approval'
import { useAutoScroll, stripThinkTags, ThinkingIndicator } from '@/features/streaming'
import { ScheduleIndicator, SchedulePanel, useScheduleStore } from '@/features/schedule'

// ---------- Markdown-lite renderer ----------
// Splits content by ``` code fences and renders code blocks with styling

function renderContent(text: string) {
  const parts = text.split(/(```[\s\S]*?```)/g)
  return parts.map((part, i) => {
    if (part.startsWith('```') && part.endsWith('```')) {
      const inner = part.slice(3, -3)
      const newlineIdx = inner.indexOf('\n')
      const lang = newlineIdx > 0 ? inner.slice(0, newlineIdx).trim() : ''
      const code = newlineIdx > 0 ? inner.slice(newlineIdx + 1) : inner
      return (
        <div key={i} className="my-2 rounded-lg overflow-hidden border border-(--color-border-default)">
          {lang && (
            <div className="px-3 py-1 text-xs font-mono bg-(--color-background-secondary) text-(--color-text-tertiary) border-b border-(--color-border-default)">
              {lang}
            </div>
          )}
          <pre className="px-4 py-3 text-sm font-mono bg-(--color-background-primary) text-(--color-text-primary) overflow-x-auto leading-relaxed">
            <code>{code}</code>
          </pre>
        </div>
      )
    }
    // Render inline code `...`
    const inlineParts = part.split(/(`[^`]+`)/g)
    return (
      <span key={i}>
        {inlineParts.map((ip, j) =>
          ip.startsWith('`') && ip.endsWith('`') ? (
            <code key={j} className="px-1.5 py-0.5 rounded bg-(--color-background-secondary) text-sm font-mono text-(--color-accent-primary)">
              {ip.slice(1, -1)}
            </code>
          ) : (
            <span key={j}>{ip}</span>
          ),
        )}
      </span>
    )
  })
}

// ---------- LLM Event Card (collapsible technical details) ----------

const LlmEventCard = memo(function LlmEventCard({
  content,
  timestamp,
  tokensIn,
  tokensOut,
}: {
  content: string
  timestamp: string
  tokensIn?: number
  tokensOut?: number
}) {
  const [expanded, setExpanded] = useState(false)

  // Parse model name from JSON content
  let model = ''
  try {
    const parsed = JSON.parse(content)
    model = parsed?.response?.model ?? ''
  } catch { /* ignore */ }

  const totalTokens = (tokensIn ?? 0) + (tokensOut ?? 0)

  return (
    <div className="mx-10 my-1">
      <button
        type="button"
        onClick={() => setExpanded((p) => !p)}
        className="flex items-center gap-2 w-full px-3 py-1.5 rounded-md text-xs
          bg-(--color-background-secondary) hover:bg-(--color-background-primary)
          border border-(--color-border-default) transition-colors group"
      >
        {expanded ? (
          <ChevronDown className="w-3 h-3 text-(--color-text-tertiary)" />
        ) : (
          <ChevronRight className="w-3 h-3 text-(--color-text-tertiary)" />
        )}
        <Cpu className="w-3 h-3 text-(--color-text-tertiary)" />
        <span className="text-(--color-text-tertiary)">LLM Call</span>
        {model && (
          <span className="font-mono text-(--color-accent-primary)">{model}</span>
        )}
        {totalTokens > 0 && (
          <span className="flex items-center gap-1 ml-auto text-(--color-text-tertiary)">
            <Zap className="w-3 h-3" />
            {tokensIn ?? 0}+{tokensOut ?? 0} tokens
          </span>
        )}
        <span className="text-(--color-text-tertiary) ml-2">
          {timestamp ? new Date(timestamp).toLocaleTimeString() : ''}
        </span>
      </button>
      {expanded && (
        <pre className="mt-1 px-4 py-3 rounded-md border border-(--color-border-default) bg-(--color-background-primary) text-xs font-mono text-(--color-text-secondary) overflow-x-auto max-h-64 overflow-y-auto leading-relaxed">
          {(() => {
            try { return JSON.stringify(JSON.parse(content), null, 2) }
            catch { return content }
          })()}
        </pre>
      )}
    </div>
  )
})

// ---------- Agent Message Card ----------

const AgentTurnCard = memo(function AgentTurnCard({
  source,
  content,
  timestamp,
  messageType,
  tokensIn,
  tokensOut,
  isStreaming,
}: {
  source: string
  content: string
  timestamp: string
  messageType: MessageType
  tokensIn?: number
  tokensOut?: number
  isStreaming?: boolean
}) {
  // LLM events get their own compact card
  if (messageType === 'llm_event') {
    return <LlmEventCard content={content} timestamp={timestamp} tokensIn={tokensIn} tokensOut={tokensOut} />
  }

  const isUser = messageType === 'user'

  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      {/* Avatar */}
      <div className={cn(
        'w-9 h-9 rounded-full flex items-center justify-center shrink-0 shadow-sm',
        isUser
          ? 'bg-(--color-accent-primary) text-white'
          : 'bg-gradient-to-br from-(--color-accent-primary)/20 to-(--color-accent-primary)/5 text-(--color-accent-primary)'
      )}>
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-5 h-5" />}
      </div>

      {/* Message bubble */}
      <div className={cn(
        'max-w-[80%] rounded-2xl',
        isUser
          ? 'bg-(--color-accent-primary) text-white px-4 py-3'
          : 'bg-(--color-surface-card) shadow-sm border border-(--color-border-default) px-5 py-4',
      )}>
        {/* Header */}
        <div className={cn(
          'flex items-center gap-2 mb-2',
          isUser ? 'text-white/80' : '',
        )}>
          <span className={cn(
            'text-xs font-semibold',
            isUser ? 'text-white' : 'text-(--color-accent-primary)',
          )}>{source}</span>
          <span className={cn(
            'text-xs',
            isUser ? 'text-white/60' : 'text-(--color-text-tertiary)',
          )}>
            {timestamp ? new Date(timestamp).toLocaleTimeString() : 'now'}
          </span>
          {!isUser && tokensIn != null && tokensOut != null && (
            <span className="text-xs text-(--color-text-tertiary) flex items-center gap-1 ml-auto">
              <Zap className="w-3 h-3" />
              {tokensIn}+{tokensOut}
            </span>
          )}
        </div>

        {/* Content */}
        <div className={cn(
          'text-sm leading-relaxed whitespace-pre-wrap',
          isUser ? 'text-white' : 'text-(--color-text-primary)',
        )}>
          {isUser ? content : renderContent(content)}
          {isStreaming && <span className="animate-pulse text-(--color-accent-primary)">|</span>}
        </div>
      </div>
    </div>
  )
})

// Format session name for dropdown display
function formatSessionLabel(session: { id?: number; name: string; created_at?: string }): string {
  const date = session.created_at ? new Date(session.created_at).toLocaleDateString() : ''
  const time = session.created_at ? new Date(session.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''
  const name = session.name || `Session ${session.id ?? '?'}`
  return date ? `${name} (${date} ${time})` : name
}

// ---------- Run Summary Card ----------

const RunSummaryCard = memo(function RunSummaryCard({ summary }: { summary: RunSummary }) {
  const totalTokens = summary.totalTokensIn + summary.totalTokensOut
  const durationStr = summary.duration != null ? `${summary.duration.toFixed(1)}s` : '-'

  return (
    <div className="mx-4 my-3 rounded-lg border border-(--color-border-default) bg-(--color-surface-card) p-4">
      <div className="flex items-center gap-2 mb-3">
        <StopCircle className="w-4 h-4 text-(--color-semantic-success)" />
        <span className="text-sm font-semibold text-(--color-text-primary)">Execution Complete</span>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {/* Stop Reason */}
        <div className="space-y-1">
          <div className="flex items-center gap-1 text-xs text-(--color-text-tertiary)">
            <BarChart3 className="w-3 h-3" />
            Stop Reason
          </div>
          <p className="text-sm font-medium text-(--color-text-primary) truncate" title={summary.stopReason ?? 'Unknown'}>
            {summary.stopReason ?? 'Unknown'}
          </p>
        </div>
        {/* Duration */}
        <div className="space-y-1">
          <div className="flex items-center gap-1 text-xs text-(--color-text-tertiary)">
            <Clock className="w-3 h-3" />
            Duration
          </div>
          <p className="text-sm font-medium text-(--color-text-primary)">{durationStr}</p>
        </div>
        {/* Tokens */}
        <div className="space-y-1">
          <div className="flex items-center gap-1 text-xs text-(--color-text-tertiary)">
            <Zap className="w-3 h-3" />
            Tokens
          </div>
          <p className="text-sm font-medium text-(--color-text-primary)">
            {totalTokens > 0 ? `${summary.totalTokensIn}+${summary.totalTokensOut}` : '-'}
          </p>
        </div>
        {/* Terminated By */}
        <div className="space-y-1">
          <div className="flex items-center gap-1 text-xs text-(--color-text-tertiary)">
            <Bot className="w-3 h-3" />
            Last Agent
          </div>
          <p className="text-sm font-medium text-(--color-text-primary) truncate" title={summary.terminatedBy ?? '-'}>
            {summary.terminatedBy ?? '-'}
          </p>
        </div>
      </div>
      {/* Turn counts */}
      <div className="mt-2 text-xs text-(--color-text-tertiary)">
        {summary.agentTurnCount} agent turns / {summary.turnCount} total messages
      </div>
    </div>
  )
})

export function PlaygroundPage() {
  const { t } = useTranslation()
  const [task, setTask] = useState('')
  const [files, setFiles] = useState<FileAttachment[]>([])
  const { data: teams } = useTeams()
  const { data: allSessions, isLoading: sessionsLoading } = useSessions()
  const { selectedTeamId, selectTeam } = useTeamStore()
  const queryClient = useQueryClient()
  const {
    turns,
    status,
    isRunning,
    error,
    streamingChunks,
    streamingSource,
    inputRequest,
    currentSessionId,
    runSummary,
    startExecution,
    addWSMessage,
    submitInput,
    setSession,
    setTurns,
    setRunSummary,
    clearSession,
  } = useExecutionStore()
  const wsRef = useRef<ExecutionWebSocket | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  const selectedTeam = teams?.find((t) => t.id === selectedTeamId)
  const [flowPoppedOut, setFlowPoppedOut] = useState(false)
  const thinkingStartRef = useRef<number | null>(null)

  // Track thinking start time
  const isThinking = isRunning && !streamingSource && turns.length > 0
  if (isThinking && thinkingStartRef.current === null) {
    thinkingStartRef.current = Date.now()
  } else if (!isThinking) {
    thinkingStartRef.current = null
  }

  // Filter sessions by selected team
  const teamSessions = useMemo(
    () => filterSessionsByTeam(allSessions ?? [], selectedTeamId),
    [allSessions, selectedTeamId],
  )

  // Load messages for selected session (only when session is selected and not running)
  const { turns: sessionTurns, isLoading: messagesLoading, runSummary: sessionRunSummary } = useSessionMessages(
    !isRunning && currentSessionId ? currentSessionId : null,
  )

  // When session messages load, populate the turns and summary (only if idle/completed and no live turns)
  useEffect(() => {
    if (sessionTurns.length > 0 && !isRunning && turns.length === 0) {
      setTurns(sessionTurns)
      if (sessionRunSummary) setRunSummary(sessionRunSummary)
    }
  }, [sessionTurns, isRunning, turns.length, setTurns, sessionRunSummary, setRunSummary])

  // When team changes, disconnect WS and clear session
  useEffect(() => {
    wsRef.current?.disconnect()
    wsRef.current = null
    clearSession()
  }, [selectedTeamId, clearSession])

  useEffect(() => {
    return () => { wsRef.current?.disconnect() }
  }, [])

  useAutoScroll(scrollRef, [turns, streamingChunks])

  // Build flow payload (memoized to avoid rebuilding on every render)
  const flowPayload = useMemo(() => ({
    type: 'flow-sync' as const,
    teamId: selectedTeamId,
    teamComponent: selectedTeam?.component ?? null,
    teamProvider: selectedTeam?.component?.provider ?? '',
    turns,
    status,
    isRunning,
    streamingSource,
    streamingChunks,
    stopReason: runSummary?.stopReason ?? null,
  }), [selectedTeamId, selectedTeam, turns, status, isRunning, streamingSource, streamingChunks, runSummary])

  // Always broadcast state changes to Flow window
  useEffect(() => {
    broadcastFlowState(flowPayload)
  }, [flowPayload])

  // Detect Flow window presence via periodic alive pings
  const flowTimeoutRef = useRef<ReturnType<typeof setTimeout>>(undefined)
  useEffect(() => {
    const unsub = onFlowPresence(() => {
      setFlowPoppedOut(true)
      broadcastFlowState(flowPayload)
      // Reset timeout - if no ping in 3s, flow window is gone
      clearTimeout(flowTimeoutRef.current)
      flowTimeoutRef.current = setTimeout(() => setFlowPoppedOut(false), 3000)
    })
    return () => {
      unsub()
      clearTimeout(flowTimeoutRef.current)
    }
  }, [flowPayload])

  const handlePopOutFlow = useCallback(() => {
    const w = window.open('/flow', 'ag-flow', 'width=900,height=700')
    if (w) {
      setFlowPoppedOut(true)
      // Detect when the popup window is closed
      const check = setInterval(() => {
        if (w.closed) {
          setFlowPoppedOut(false)
          clearInterval(check)
        }
      }, 1000)
    }
  }, [])

  const handleSessionChange = useCallback((value: string) => {
    if (value === 'new') {
      clearSession()
      return
    }
    const sessionId = value ? Number(value) : null
    if (sessionId !== null) {
      setSession(sessionId)
      // Clear current turns so session history can load
      setTurns([])
    } else {
      clearSession()
    }
  }, [clearSession, setSession, setTurns])

  const handleRun = useCallback(async () => {
    if (!task.trim() || !selectedTeamId) return

    try {
      let sessionId = currentSessionId

      // If no existing session, create a new one
      if (sessionId === null) {
        const session = await api.createSession(selectedTeamId)
        sessionId = session.id ?? 0
        setSession(sessionId)
        // Invalidate sessions list so the dropdown updates
        queryClient.invalidateQueries({ queryKey: ['sessions'] })
      }

      const run = await api.createRun(sessionId)

      startExecution(String(run.run_id), sessionId)

      const ws = new ExecutionWebSocket({
        runId: run.run_id,
        onMessage: (msg) => {
          // Intercept input_request to check for tool approval patterns
          if (msg.type === 'input_request') {
            const data = msg.data as Record<string, unknown> | undefined
            const prompt = (data?.prompt as string) ?? ''
            const source = (data?.source as string) ?? (msg.source as string) ?? 'agent'
            const parsed = parseToolApproval(prompt, source)
            if (parsed) {
              const result = useToolApprovalStore.getState().enqueue(parsed)
              if (result === 'auto-approved') {
                // Tool in always-allow cache — auto-respond
                ws.sendInput('APPROVE')
              }
              // Don't pass to store — handled by tool-approval UI
              return
            }
          }
          addWSMessage(msg)
        },
        onClose: () => {
          useExecutionStore.getState().completeExecution()
          // Invalidate session runs so history reloads
          queryClient.invalidateQueries({ queryKey: ['sessions', sessionId, 'runs'] })
          queryClient.invalidateQueries({ queryKey: ['sessions'] })
        },
        onError: () => useExecutionStore.getState().setError('WebSocket connection lost'),
      })

      await ws.connect()
      wsRef.current = ws
      ws.startExecution(task, selectedTeam?.component, files.length > 0 ? files : undefined)
      setTask('')
      setFiles([])
    } catch (err) {
      useExecutionStore.getState().setError(String(err))
    }
  }, [task, selectedTeamId, selectedTeam, currentSessionId, files, startExecution, addWSMessage, setSession, queryClient])

  const handleStop = useCallback(() => {
    wsRef.current?.stop()
    wsRef.current?.disconnect()
  }, [])

  const handleSendInput = useCallback(() => {
    if (!task.trim() || !wsRef.current) return
    wsRef.current.sendInput(task)
    submitInput()
    setTask('')
  }, [task, submitInput])

  // Tool approval integration
  const sendToolResponse = useCallback((response: string) => {
    wsRef.current?.sendInput(response)
  }, [])
  const {
    pending: pendingApproval,
    queueLength: approvalQueueLength,
    handleApprove,
    handleApproveAlways,
    handleReject,
  } = useToolApproval(sendToolResponse)

  // Schedule panel
  const scheduleOpen = useScheduleStore((s) => s.panelOpen)
  const toggleSchedule = useScheduleStore((s) => s.togglePanel)
  const closeSchedule = useCallback(() => useScheduleStore.getState().setPanelOpen(false), [])

  const handleFilesChange = setFiles

  const handlePaste = useCallback((e: React.ClipboardEvent) => {
    // Handle image paste from clipboard
    const items = Array.from(e.clipboardData.items)
    const imageItems = items.filter((item) => item.type.startsWith('image/'))

    if (imageItems.length > 0) {
      e.preventDefault()
      const imageFiles: File[] = []
      for (const item of imageItems) {
        const file = item.getAsFile()
        if (file) imageFiles.push(file)
      }
      if (imageFiles.length > 0) {
        // Read images and add to files
        Promise.all(
          imageFiles.map(async (file) => {
            const reader = new FileReader()
            return new Promise<FileAttachment>((resolve, reject) => {
              reader.onload = () => {
                resolve({
                  name: file.name || `pasted-image-${Date.now()}.png`,
                  type: file.type,
                  content: (reader.result as string).split(',')[1],
                })
              }
              reader.onerror = () => reject(reader.error)
              reader.readAsDataURL(file)
            })
          }),
        ).then((newAttachments) => {
          setFiles((prev) => [...prev, ...newAttachments])
        }).catch(() => { /* Silently ignore paste read failures */ })
      }
      return
    }

    // Handle large text paste -> auto-convert to file attachment
    const pastedText = e.clipboardData.getData('text/plain')
    if (pastedText.length > 1500) {
      e.preventDefault()
      const content = btoa(unescape(encodeURIComponent(pastedText)))
      setFiles((prev) => [
        ...prev,
        {
          name: `pasted-text-${Date.now()}.txt`,
          type: 'text/plain',
          content,
        },
      ])
    }
  }, [])

  const isInputMode = inputRequest !== null

  return (
    <div className="flex flex-col h-full -m-6">
      {/* Top bar: Team selector + Session selector + Status */}
      <div className="flex items-center gap-3 p-4 border-b border-(--color-border-default) bg-(--color-surface-card) flex-wrap">
        {/* Team selector */}
        <span className="text-label text-(--color-text-secondary)">{t('playground.team')}</span>
        <select
          aria-label="Select a team"
          className="h-9 px-3 rounded-md border border-(--color-border-default) bg-(--color-surface-card) text-sm text-(--color-text-primary)"
          value={selectedTeamId ?? ''}
          onChange={(e) => selectTeam(e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">{t('playground.selectTeam')}</option>
          {teams?.map((t) => (
            <option key={t.id} value={t.id}>
              {getTeamName(t)}
            </option>
          ))}
        </select>

        {/* Separator */}
        <div className="w-px h-6 bg-(--color-border-default)" aria-hidden="true" />

        {/* Session selector */}
        <span className="text-label text-(--color-text-secondary)">
          <History className="w-4 h-4 inline-block mr-1 align-text-bottom" aria-hidden="true" />
          {t('playground.session')}
        </span>
        <select
          aria-label="Select a session"
          className="h-9 px-3 rounded-md border border-(--color-border-default) bg-(--color-surface-card) text-sm text-(--color-text-primary) max-w-[280px]"
          value={currentSessionId ?? 'new'}
          onChange={(e) => handleSessionChange(e.target.value)}
          disabled={!selectedTeamId || isRunning}
        >
          <option value="new">
            {t('playground.newSession')}
          </option>
          {teamSessions.map((s) => (
            <option key={s.id} value={s.id}>
              {formatSessionLabel(s)}
            </option>
          ))}
        </select>

        {/* Loading indicator for sessions */}
        {(sessionsLoading || messagesLoading) && (
          <div className="w-4 h-4 border-2 border-(--color-accent-primary) border-t-transparent rounded-full animate-spin" aria-label="Loading sessions" />
        )}

        {/* Status badge */}
        {status !== 'idle' && (
          <Badge variant={status === 'running' ? 'success' : status === 'error' ? 'error' : 'default'}>
            {status}
          </Badge>
        )}

        {/* Pop Out Flow button */}
        {selectedTeam && !flowPoppedOut && (
          <button
            type="button"
            onClick={handlePopOutFlow}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs border border-(--color-border-default) hover:bg-(--color-background-secondary) text-(--color-text-secondary) hover:text-(--color-text-primary) transition-colors"
            aria-label="Open flow in new window"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            {t('playground.popOutFlow')}
          </button>
        )}

        {/* Schedule indicator */}
        <ScheduleIndicator onClick={toggleSchedule} />

        {/* Session indicator */}
        {currentSessionId !== null && (
          <span className="text-body-small text-(--color-text-tertiary) ml-auto">
            Session #{currentSessionId}
          </span>
        )}
      </div>

      {/* Live Agent Flow visualization (hidden when popped out to separate window) */}
      {selectedTeam && !flowPoppedOut && (
        <LiveAgentFlow
          team={selectedTeam}
          turns={turns}
          streamingSource={streamingSource}
          isRunning={isRunning}
          status={status}
          stopReason={runSummary?.stopReason}
        />
      )}

      {/* Pop-out indicator bar (when flow is in separate window) */}
      {selectedTeam && flowPoppedOut && (
        <div className="flex items-center gap-2 px-4 py-2 border-b border-(--color-border-default) bg-(--color-accent-primary)/5 text-xs text-(--color-accent-primary)">
          <ExternalLink className="w-3.5 h-3.5" />
          <span>{t('playground.flowInWindow')}</span>
          <button
            type="button"
            onClick={() => setFlowPoppedOut(false)}
            className="ml-auto text-xs underline hover:no-underline"
          >
            {t('playground.showInline')}
          </button>
        </div>
      )}

      {/* Chat area */}
      <div ref={scrollRef} className="flex-1 overflow-auto p-6 space-y-4 bg-(--color-background-primary)">
        {turns.length === 0 && !isRunning && status !== 'error' && !messagesLoading && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Bot className="w-16 h-16 mx-auto text-(--color-text-tertiary) mb-4" />
              <h2 className="text-heading-medium text-(--color-text-secondary)">
                {currentSessionId ? t('playground.emptySession') : t('playground.readyTitle')}
              </h2>
              <p className="text-body-medium text-(--color-text-tertiary) mt-2">
                {currentSessionId
                  ? t('playground.emptySessionDesc')
                  : t('playground.readyDesc')}
              </p>
            </div>
          </div>
        )}

        {/* Loading state for session history */}
        {messagesLoading && turns.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="w-8 h-8 border-2 border-(--color-accent-primary) border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-body-medium text-(--color-text-tertiary)">{t('playground.loadingHistory')}</p>
            </div>
          </div>
        )}

        {turns.map((turn, i) => (
          <AgentTurnCard
            key={`${turn.source}-${turn.timestamp}-${i}`}
            source={turn.source}
            content={turn.content}
            timestamp={turn.timestamp}
            messageType={turn.messageType}
            tokensIn={turn.tokensIn}
            tokensOut={turn.tokensOut}
          />
        ))}

        {/* Streaming chunk display (think tags stripped) */}
        {streamingSource && streamingChunks && (
          <AgentTurnCard
            source={streamingSource}
            content={stripThinkTags(streamingChunks)}
            timestamp=""
            messageType="agent"
            isStreaming
          />
        )}

        {/* Thinking indicator with elapsed timer */}
        {isThinking && thinkingStartRef.current && (
          <ThinkingIndicator startedAt={thinkingStartRef.current} />
        )}

        {/* Tool approval card */}
        {pendingApproval && (
          <ToolApprovalCard
            approval={pendingApproval}
            queueLength={approvalQueueLength}
            onApprove={handleApprove}
            onApproveAlways={handleApproveAlways}
            onReject={handleReject}
          />
        )}

        {/* Input request indicator */}
        {isInputMode && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-(--color-accent-primary-light)">
            <MessageSquare className="w-4 h-4 text-(--color-accent-primary) shrink-0" />
            <span className="text-body-small text-(--color-text-secondary)">
              {t('playground.requestingInput', { source: inputRequest.source, prompt: inputRequest.prompt })}
            </span>
          </div>
        )}

        {/* Error display */}
        {status === 'error' && error && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-(--color-semantic-error)/10">
            <AlertCircle className="w-4 h-4 text-(--color-semantic-error) shrink-0 mt-0.5" />
            <span className="text-body-small text-(--color-semantic-error)">{error}</span>
          </div>
        )}

        {/* Run Summary (shown after completion) */}
        {runSummary && !isRunning && (
          <RunSummaryCard summary={runSummary} />
        )}
      </div>

      {/* Input bar */}
      <div className="p-4 border-t border-(--color-border-default) bg-(--color-surface-card)">
        {/* File attachments list */}
        {files.length > 0 && (
          <div className="mb-2">
            <FileUpload
              files={files}
              onFilesChange={handleFilesChange}
              disabled={isRunning && !isInputMode}
            />
          </div>
        )}
        <div className="flex items-center gap-2">
          {/* Attach button (only show when no files displayed above) */}
          {files.length === 0 && (
            <FileUpload
              files={files}
              onFilesChange={handleFilesChange}
              disabled={isRunning && !isInputMode}
            />
          )}
          <Input
            value={task}
            onChange={(e) => setTask(e.target.value)}
            onPaste={handlePaste}
            placeholder={
              isInputMode
                ? t('playground.inputPlaceholder', { source: inputRequest.source })
                : currentSessionId
                  ? t('playground.continueSession')
                  : t('playground.enterTask')
            }
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                if (isInputMode) handleSendInput()
                else handleRun()
              }
            }}
            disabled={isRunning && !isInputMode}
          />
          {isRunning && !isInputMode ? (
            <Button variant="danger" onClick={handleStop} aria-label="Stop execution">
              <Square className="w-4 h-4" />
            </Button>
          ) : isInputMode ? (
            <Button onClick={handleSendInput} disabled={!task.trim()} aria-label="Send input">
              <Send className="w-4 h-4" />
            </Button>
          ) : (
            <Button onClick={handleRun} disabled={!task.trim() || !selectedTeamId} aria-label="Send task">
              <Send className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Schedule Panel (drawer) */}
      {scheduleOpen && (
        <SchedulePanel
          teamId={selectedTeamId}
          teamName={selectedTeam ? getTeamName(selectedTeam) : ''}
          onClose={closeSchedule}
        />
      )}
    </div>
  )
}
