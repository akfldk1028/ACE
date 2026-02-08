import { memo } from 'react'
import { Card, Badge, Button } from '@/shared/ui'
import { Trash2, PlusCircle } from 'lucide-react'
import { AgentHealthBadge } from './AgentHealthBadge'
import type { A2AAgent, A2AHealthStatus } from '../types'

interface AgentCardProps {
  agent: A2AAgent
  health?: A2AHealthStatus | null
  isSelected: boolean
  onSelect: () => void
  onUnregister: () => void
}

export const AgentCard = memo(function AgentCard({ agent, health, isSelected, onSelect, onUnregister }: AgentCardProps) {
  const { config } = agent

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onSelect()
    }
  }

  return (
    <Card
      className={`hover:shadow-lg transition-shadow cursor-pointer ${isSelected ? 'ring-2 ring-(--color-accent-primary)' : ''}`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      aria-pressed={isSelected}
      onKeyDown={handleKeyDown}
    >
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <h3 className="text-heading-small truncate">{agent.label}</h3>
          <p className="text-body-small text-(--color-text-tertiary) mt-1 truncate">
            {config.description}
          </p>
        </div>
        <AgentHealthBadge health={health} />
      </div>

      {config.skills.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {config.skills.map((skill) => (
            <Badge key={skill.name} variant="outline">{skill.name}</Badge>
          ))}
        </div>
      )}

      <p className="text-xs font-mono text-(--color-text-tertiary) mt-3 truncate">
        {config.a2a_server_url}
      </p>

      <div className="flex gap-2 mt-3">
        <Button size="sm" variant="primary" disabled title="Coming in Phase 3" onClick={(e) => e.stopPropagation()}>
          <PlusCircle className="w-3.5 h-3.5 mr-1.5" />
          Add to Team
        </Button>
        <Button
          size="sm"
          variant="ghost"
          onClick={(e) => {
            e.stopPropagation()
            onUnregister()
          }}
        >
          <Trash2 className="w-3.5 h-3.5 mr-1.5" />
          Remove
        </Button>
      </div>
    </Card>
  )
})
