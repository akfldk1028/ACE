import { Card, Badge } from '@/shared/ui'
import { useSessions } from '@/features/playground/useExecution'
import { Clock, MessageSquare } from 'lucide-react'

export function HistoryPage() {
  const { data: sessions, isLoading } = useSessions()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-display-medium">History</h1>
        <p className="text-body-medium text-(--color-text-secondary) mt-1">
          Past execution sessions
        </p>
      </div>

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
          {sessions?.map((session) => (
            <Card key={session.id} className="flex items-center justify-between hover:shadow-lg transition-shadow cursor-pointer">
              <div className="flex items-center gap-3">
                <MessageSquare className="w-5 h-5 text-(--color-text-tertiary)" />
                <div>
                  <p className="text-label">{session.name || `Session #${session.id}`}</p>
                  <p className="text-body-small text-(--color-text-tertiary)">
                    Team #{session.team_id}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-(--color-text-tertiary)" />
                <span className="text-body-small text-(--color-text-tertiary)">
                  {session.created_at ? new Date(session.created_at).toLocaleDateString() : 'N/A'}
                </span>
                <Badge>#{session.id}</Badge>
              </div>
            </Card>
          ))}
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
