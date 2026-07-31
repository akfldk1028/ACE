import { memo } from 'react'
import type { A2AHealthStatus } from '../types'

// M3: Use theme tokens instead of hardcoded Tailwind colors
const STATUS_STYLES = {
  healthy: 'bg-(--color-semantic-success)',
  unhealthy: 'bg-(--color-semantic-error)',
  unknown: 'bg-(--color-text-tertiary)',
} as const

export const AgentHealthBadge = memo(function AgentHealthBadge({ health }: { health?: A2AHealthStatus | null }) {
  const status = health == null ? 'unknown' : health.healthy ? 'healthy' : 'unhealthy'
  const latency = health?.latency_ms != null ? `${health.latency_ms}ms` : ''
  const title = status === 'unknown'
    ? 'Status unknown'
    : `${status}${latency ? ` (${latency})` : ''}${health?.error ? ` - ${health.error}` : ''}`

  return (
    <span className="inline-flex items-center gap-1.5" title={title}>
      <span className={`w-2 h-2 rounded-full ${STATUS_STYLES[status]}`} />
      <span className="text-label-small text-(--color-text-tertiary) capitalize">{status}</span>
    </span>
  )
})
