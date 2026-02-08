import { Card, Badge, ProgressCircle } from '@/shared/ui'
import { useTeams } from '@/features/teams/useTeams'
import { useSessions } from '@/features/playground/useExecution'
import { useHealth } from '@/shared/hooks/useUsage'
import { Activity, Users, Zap, Server } from 'lucide-react'

export function DashboardPage() {
  const { data: teams } = useTeams()
  const { data: sessions } = useSessions()
  const { data: health } = useHealth()

  const stats = [
    {
      label: 'Teams',
      value: teams?.length ?? 0,
      icon: Users,
      color: 'var(--color-accent-primary)',
    },
    {
      label: 'Sessions',
      value: sessions?.length ?? 0,
      icon: Activity,
      color: 'var(--color-semantic-info)',
    },
    {
      label: 'Engine Status',
      value: health?.status ? 'Online' : 'Offline',
      icon: Server,
      color: health?.status ? 'var(--color-semantic-success)' : 'var(--color-semantic-error)',
    },
    {
      label: 'Executions Today',
      value: 0,
      icon: Zap,
      color: 'var(--color-semantic-warning)',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-display-medium text-(--color-text-primary)">Dashboard</h1>
        <p className="text-body-medium text-(--color-text-secondary) mt-1">
          Agent orchestration overview
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-label-small text-(--color-text-tertiary)">{stat.label}</p>
                <p className="text-heading-large mt-1">{stat.value}</p>
              </div>
              <stat.icon className="w-8 h-8" style={{ color: stat.color }} />
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h2 className="text-heading-small mb-4">Team Patterns</h2>
          <div className="space-y-3">
            {['Sequential', 'Selector', 'Handoff', 'Debate', 'Reflection'].map((pattern) => (
              <div key={pattern} className="flex items-center justify-between">
                <span className="text-body-medium">{pattern}</span>
                <Badge variant="outline">{pattern}</Badge>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <h2 className="text-heading-small mb-4">Usage Summary</h2>
          <div className="flex items-center justify-center py-8">
            <ProgressCircle value={0} size="lg" />
          </div>
          <p className="text-center text-body-small text-(--color-text-tertiary)">
            0 / 50 free executions used
          </p>
        </Card>
      </div>
    </div>
  )
}
