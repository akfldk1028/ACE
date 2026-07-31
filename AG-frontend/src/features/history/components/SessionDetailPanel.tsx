/**
 * SessionDetailPanel - Shows session runs and agent messages
 */

import { useState, useCallback } from 'react'
import { Card, Badge, Button } from '@/shared/ui'
import { X, ChevronDown, ChevronUp, Trash2, Clock } from 'lucide-react'
import { useSessionRuns } from '@/features/playground/useExecution'
import { useDeleteSession } from '../useHistory'
import { MessageBubble } from './MessageBubble'
import type { Run, AgentMessageConfig, Message } from '@/shared/types/datamodel'
import { truncateError } from '@/shared/utils'

interface SessionDetailPanelProps {
  sessionId: number
  sessionName: string
  onClose: () => void
}

const STATUS_COLORS: Record<string, 'primary' | 'success' | 'error' | 'warning' | 'default'> = {
  created: 'default',
  active: 'primary',
  awaiting_input: 'warning',
  complete: 'success',
  error: 'error',
  timeout: 'warning',
  stopped: 'default',
}

export function SessionDetailPanel({ sessionId, sessionName, onClose }: SessionDetailPanelProps) {
  const { data: sessionRuns, isLoading } = useSessionRuns(sessionId)
  const deleteMutation = useDeleteSession()
  const [expandedRun, setExpandedRun] = useState<number | null>(null)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const runs = sessionRuns?.runs ?? []

  const handleToggleRun = useCallback((runId: number) => {
    setExpandedRun(prev => prev === runId ? null : runId)
  }, [])

  const handleDelete = useCallback(async () => {
    if (!confirmDelete) {
      setConfirmDelete(true)
      return
    }
    try {
      await deleteMutation.mutateAsync(sessionId)
      onClose()
    } catch (e) {
      setError(truncateError(e instanceof Error ? e.message : 'Delete failed'))
      setConfirmDelete(false)
    }
  }, [confirmDelete, sessionId, deleteMutation, onClose])

  return (
    <Card className="relative" role="complementary" aria-label="Session detail">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 min-w-0">
          <h2 className="text-heading-small truncate">{sessionName}</h2>
          <Badge variant="default">#{sessionId}</Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
            className="text-(--color-semantic-error) hover:bg-(--color-semantic-error)/10"
            aria-label="Delete session"
          >
            <Trash2 className="w-3.5 h-3.5 mr-1" />
            {confirmDelete ? 'Confirm?' : ''}
          </Button>
          <button
            onClick={onClose}
            aria-label="Close session detail"
            className="p-1 rounded hover:bg-(--color-background-secondary) text-(--color-text-tertiary) focus:outline-none focus:ring-2 focus:ring-(--color-accent-primary)"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {error && (
        <p className="text-sm text-(--color-semantic-error) mb-3">{error}</p>
      )}

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2].map(i => (
            <div key={i} className="h-12 bg-(--color-background-secondary) rounded animate-pulse" />
          ))}
        </div>
      ) : runs.length === 0 ? (
        <p className="text-body-medium text-(--color-text-secondary) py-4 text-center">
          No runs in this session yet.
        </p>
      ) : (
        <div className="space-y-2">
          {runs.map((run: Run) => {
            const isExpanded = expandedRun === run.id
            const messages = run.team_result?.task_result?.messages ?? []
            const runMessages = (run.messages ?? []) as Message[]
            const allMessages = messages.length > 0
              ? messages
              : runMessages.map(m => m.config)

            return (
              <div key={run.id} className="border border-(--color-border-default) rounded-lg">
                <button
                  onClick={() => handleToggleRun(run.id)}
                  className="w-full flex items-center justify-between p-3 hover:bg-(--color-background-secondary) transition-colors rounded-lg"
                  aria-expanded={isExpanded}
                >
                  <div className="flex items-center gap-2">
                    <Badge variant={STATUS_COLORS[run.status] ?? 'default'}>{run.status}</Badge>
                    <span className="text-sm text-(--color-text-secondary)">
                      Run #{run.id}
                    </span>
                    {allMessages.length > 0 && (
                      <span className="text-xs text-(--color-text-tertiary)">
                        ({allMessages.length} messages)
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {run.team_result?.duration != null && (
                      <span className="text-xs text-(--color-text-tertiary) flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {(run.team_result.duration / 1000).toFixed(1)}s
                      </span>
                    )}
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>
                </button>

                {isExpanded && (
                  <div className="px-3 pb-3 border-t border-(--color-border-default)">
                    {run.error_message && (
                      <p className="text-sm text-(--color-semantic-error) mt-2 p-2 rounded bg-(--color-semantic-error)/10">
                        {run.error_message}
                      </p>
                    )}
                    {allMessages.length === 0 ? (
                      <p className="text-sm text-(--color-text-tertiary) py-2 text-center">
                        No messages recorded.
                      </p>
                    ) : (
                      <div className="divide-y divide-(--color-border-default) mt-2">
                        {allMessages.map((msg: AgentMessageConfig, i: number) => (
                          <MessageBubble key={i} message={msg} />
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </Card>
  )
}
