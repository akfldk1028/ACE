import { memo, useState, useCallback, useMemo } from 'react'
import { Card, Badge, Button } from '@/shared/ui'
import { useSessions } from '@/features/playground/useExecution'
import { Clock, MessageSquare, GitCompareArrows, X } from 'lucide-react'
import { SessionDetailPanel } from './components'

const SessionCard = memo(function SessionCard({
  sessionId,
  sessionName,
  teamId,
  createdAt,
  isSelected,
  compareSlot,
  onSelect,
}: {
  sessionId: number
  sessionName: string
  teamId: number | undefined
  createdAt: string | undefined
  isSelected: boolean
  compareSlot: string | null
  onSelect: (id: number) => void
}) {
  const handleClick = useCallback(() => onSelect(sessionId), [onSelect, sessionId])
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(sessionId) }
  }, [onSelect, sessionId])

  return (
    <Card
      className={`flex items-center justify-between hover:shadow-lg transition-shadow cursor-pointer ${
        isSelected ? 'ring-2 ring-(--color-accent-primary)' : ''
      }`}
      role="button"
      tabIndex={0}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
    >
      <div className="flex items-center gap-3">
        <MessageSquare className="w-5 h-5 text-(--color-text-tertiary)" aria-hidden="true" />
        <div>
          <p className="text-label">{sessionName}</p>
          <p className="text-body-small text-(--color-text-tertiary)">
            Team #{teamId}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {compareSlot && (
          <Badge variant="primary">{compareSlot}</Badge>
        )}
        <Clock className="w-4 h-4 text-(--color-text-tertiary)" aria-hidden="true" />
        <span className="text-body-small text-(--color-text-tertiary)">
          {createdAt ? new Date(createdAt).toLocaleDateString() : 'N/A'}
        </span>
        <Badge>#{sessionId}</Badge>
      </div>
    </Card>
  )
})

export function HistoryPage() {
  const { data: sessions, isLoading } = useSessions()
  const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null)

  // Compare mode state
  const [compareMode, setCompareMode] = useState(false)
  const [compareIds, setCompareIds] = useState<[number | null, number | null]>([null, null])

  const selectedSession = sessions?.find(s => s.id === selectedSessionId)

  const handleSelectSession = useCallback((id: number) => {
    if (compareMode) {
      setCompareIds(prev => {
        if (prev[0] === id) return [prev[1], null]
        if (prev[1] === id) return [prev[0], null]
        if (prev[0] === null) return [id, prev[1]]
        if (prev[1] === null) return [prev[0], id]
        return [prev[0], id]
      })
    } else {
      setSelectedSessionId(prev => prev === id ? null : id)
    }
  }, [compareMode])

  const handleCloseDetail = useCallback(() => {
    setSelectedSessionId(null)
  }, [])

  const handleToggleCompare = useCallback(() => {
    setCompareMode(prev => !prev)
    setSelectedSessionId(null)
    setCompareIds([null, null])
  }, [])

  const handleCloseCompare0 = useCallback(() => {
    setCompareIds(prev => [null, prev[1]])
  }, [])

  const handleCloseCompare1 = useCallback(() => {
    setCompareIds(prev => [prev[0], null])
  }, [])

  const compareSession0 = useMemo(
    () => sessions?.find(s => s.id === compareIds[0]),
    [sessions, compareIds],
  )
  const compareSession1 = useMemo(
    () => sessions?.find(s => s.id === compareIds[1]),
    [sessions, compareIds],
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-display-medium">History</h1>
          <p className="text-body-medium text-(--color-text-secondary) mt-1">
            Past execution sessions
          </p>
        </div>
        <Button
          variant={compareMode ? 'primary' : 'ghost'}
          onClick={handleToggleCompare}
          aria-pressed={compareMode}
          aria-label={compareMode ? 'Exit compare mode' : 'Compare sessions'}
        >
          {compareMode ? (
            <><X className="w-4 h-4 mr-2" />Exit Compare</>
          ) : (
            <><GitCompareArrows className="w-4 h-4 mr-2" />Compare</>
          )}
        </Button>
      </div>

      {/* Compare mode hint */}
      {compareMode && compareIds[0] === null && compareIds[1] === null && (
        <Card className="text-center py-4 border-dashed border-2 border-(--color-accent-primary)/30">
          <p className="text-body-medium text-(--color-text-secondary)">
            Select up to 2 sessions to compare side-by-side
          </p>
        </Card>
      )}

      {/* Compare panels (side-by-side) */}
      {compareMode && (compareSession0 || compareSession1) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {compareSession0 ? (
            <SessionDetailPanel
              sessionId={compareSession0.id ?? 0}
              sessionName={compareSession0.name || `Session #${compareSession0.id}`}
              onClose={handleCloseCompare0}
            />
          ) : (
            <Card className="flex items-center justify-center py-12 border-dashed border-2 border-(--color-border-default)">
              <p className="text-body-medium text-(--color-text-tertiary)">
                Select a session to compare
              </p>
            </Card>
          )}
          {compareSession1 ? (
            <SessionDetailPanel
              sessionId={compareSession1.id ?? 0}
              sessionName={compareSession1.name || `Session #${compareSession1.id}`}
              onClose={handleCloseCompare1}
            />
          ) : (
            <Card className="flex items-center justify-center py-12 border-dashed border-2 border-(--color-border-default)">
              <p className="text-body-medium text-(--color-text-tertiary)">
                Select a session to compare
              </p>
            </Card>
          )}
        </div>
      )}

      {/* Single session detail */}
      {!compareMode && selectedSession && (
        <SessionDetailPanel
          sessionId={selectedSession.id ?? 0}
          sessionName={selectedSession.name || `Session #${selectedSession.id}`}
          onClose={handleCloseDetail}
        />
      )}

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <div className="h-4 bg-(--color-background-secondary) rounded w-1/3" />
              <div className="h-3 bg-(--color-background-secondary) rounded w-1/4 mt-2" />
            </Card>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {sessions?.map((session) => {
            const id = session.id ?? 0
            const isSelected = compareMode
              ? compareIds[0] === session.id || compareIds[1] === session.id
              : session.id === selectedSessionId
            const compareSlot = compareMode
              ? compareIds[0] === session.id ? 'A' : compareIds[1] === session.id ? 'B' : null
              : null
            return (
              <SessionCard
                key={id}
                sessionId={id}
                sessionName={session.name || `Session #${session.id}`}
                teamId={session.team_id}
                createdAt={session.created_at}
                isSelected={isSelected}
                compareSlot={compareSlot}
                onSelect={handleSelectSession}
              />
            )
          })}
          {(!sessions || sessions.length === 0) && (
            <Card className="text-center py-12">
              <p className="text-body-large text-(--color-text-secondary)">
                No sessions yet. Run a team in the Playground to see history.
              </p>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
