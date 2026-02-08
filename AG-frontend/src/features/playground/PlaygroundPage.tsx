import { useState, useRef, useEffect } from 'react'
import { Button, Input, Badge } from '@/shared/ui'
import { useTeams, getTeamName } from '@/features/teams/useTeams'
import { useTeamStore } from '@/features/teams/teamStore'
import { useExecutionStore } from './executionStore'
import { ExecutionWebSocket } from '@/shared/api/ws'
import { api } from '@/shared/api'
import { Send, Square, Bot, User } from 'lucide-react'
import { cn } from '@/shared/lib/utils'

function AgentTurnCard({ source, content, timestamp }: { source: string; content: string; timestamp: string }) {
  const isUser = source === 'user'
  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      <div className={cn(
        'w-8 h-8 rounded-full flex items-center justify-center shrink-0',
        isUser ? 'bg-(--color-accent-primary-light)' : 'bg-(--color-background-secondary)'
      )}>
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>
      <div className={cn('max-w-[80%] rounded-xl p-4', isUser ? 'bg-(--color-accent-primary-light)' : 'bg-(--color-surface-card) shadow-sm')}>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-label-small font-semibold">{source}</span>
          <span className="text-body-small text-(--color-text-tertiary)">
            {new Date(timestamp).toLocaleTimeString()}
          </span>
        </div>
        <p className="text-body-medium whitespace-pre-wrap">{content}</p>
      </div>
    </div>
  )
}

export function PlaygroundPage() {
  const [task, setTask] = useState('')
  const { data: teams } = useTeams()
  const { selectedTeamId, selectTeam } = useTeamStore()
  const { turns, status, isRunning, startExecution, addWSMessage, reset } = useExecutionStore()
  const wsRef = useRef<ExecutionWebSocket | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  const selectedTeam = teams?.find((t) => t.id === selectedTeamId)

  useEffect(() => {
    return () => { wsRef.current?.disconnect() }
  }, [])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [turns])

  const handleRun = async () => {
    if (!task.trim() || !selectedTeamId) return

    reset()

    try {
      const session = await api.createSession(selectedTeamId)
      const run = await api.createRun(session.id!)

      startExecution(String(run.run_id))

      const ws = new ExecutionWebSocket({
        runId: run.run_id,
        onMessage: addWSMessage,
        onClose: () => useExecutionStore.getState().completeExecution(),
        onError: () => useExecutionStore.getState().setError('WebSocket connection lost'),
      })

      await ws.connect()
      wsRef.current = ws
      ws.startExecution(task, selectedTeam?.component)
    } catch (err) {
      useExecutionStore.getState().setError(String(err))
    }
  }

  const handleStop = () => {
    wsRef.current?.stop()
    wsRef.current?.disconnect()
  }

  return (
    <div className="flex flex-col h-full -m-6">
      {/* Team selector bar */}
      <div className="flex items-center gap-3 p-4 border-b border-(--color-border-default) bg-(--color-surface-card)">
        <span className="text-label text-(--color-text-secondary)">Team:</span>
        <select
          aria-label="Select a team"
          className="h-9 px-3 rounded-md border border-(--color-border-default) bg-(--color-surface-card) text-sm text-(--color-text-primary)"
          value={selectedTeamId ?? ''}
          onChange={(e) => selectTeam(e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">Select a team...</option>
          {teams?.map((t) => (
            <option key={t.id} value={t.id}>
              {getTeamName(t)}
            </option>
          ))}
        </select>
        {status !== 'idle' && (
          <Badge variant={status === 'running' ? 'success' : status === 'error' ? 'error' : 'default'}>
            {status}
          </Badge>
        )}
      </div>

      {/* Chat area */}
      <div ref={scrollRef} className="flex-1 overflow-auto p-6 space-y-4 bg-(--color-background-primary)">
        {turns.length === 0 && !isRunning && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Bot className="w-16 h-16 mx-auto text-(--color-text-tertiary) mb-4" />
              <h2 className="text-heading-medium text-(--color-text-secondary)">
                Ready to execute
              </h2>
              <p className="text-body-medium text-(--color-text-tertiary) mt-2">
                Select a team and enter a task to start
              </p>
            </div>
          </div>
        )}

        {turns.map((turn, i) => (
          <AgentTurnCard key={i} {...turn} />
        ))}

        {isRunning && turns.length > 0 && (
          <div className="flex items-center gap-2 text-(--color-text-tertiary)">
            <div className="w-2 h-2 rounded-full bg-(--color-accent-primary) animate-pulse" />
            <span className="text-body-small">Agent thinking...</span>
          </div>
        )}
      </div>

      {/* Input bar */}
      <div className="p-4 border-t border-(--color-border-default) bg-(--color-surface-card)">
        <div className="flex gap-2">
          <Input
            value={task}
            onChange={(e) => setTask(e.target.value)}
            placeholder="Enter a task for the team..."
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleRun()}
            disabled={isRunning}
          />
          {isRunning ? (
            <Button variant="danger" onClick={handleStop}>
              <Square className="w-4 h-4" />
            </Button>
          ) : (
            <Button onClick={handleRun} disabled={!task.trim() || !selectedTeamId}>
              <Send className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
