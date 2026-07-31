import { useState } from 'react'
import { Card, Badge, Button } from '@/shared/ui'
import { X, Code, Trash2 } from 'lucide-react'
import { AgentHealthBadge } from './AgentHealthBadge'
import { useAgentComponent } from '../useAgents'
import type { A2AAgent, A2AHealthStatus } from '../types'

interface AgentDetailPanelProps {
  agent: A2AAgent
  health?: A2AHealthStatus | null
  onClose: () => void
  onUnregister: () => void
}

export function AgentDetailPanel({ agent, health, onClose, onUnregister }: AgentDetailPanelProps) {
  const [showJson, setShowJson] = useState(false)
  const { data: componentData } = useAgentComponent(showJson ? agent.config.name : null)
  const { config } = agent

  return (
    <Card className="relative">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h2 className="text-heading-small">{agent.label}</h2>
          <AgentHealthBadge health={health} />
        </div>
        <button
          onClick={onClose}
          aria-label="Close detail panel"
          className="p-1 rounded hover:bg-(--color-background-secondary) text-(--color-text-tertiary) focus:outline-none focus:ring-2 focus:ring-(--color-accent-primary)"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
        <div>
          <span className="text-(--color-text-tertiary)">Name</span>
          <p className="font-medium">{config.name}</p>
        </div>
        <div>
          <span className="text-(--color-text-tertiary)">Provider</span>
          <p className="font-medium font-mono text-xs">{agent.provider}</p>
        </div>
        <div>
          <span className="text-(--color-text-tertiary)">URL</span>
          <p className="font-medium font-mono text-xs">{config.a2a_server_url}</p>
        </div>
        <div>
          <span className="text-(--color-text-tertiary)">Timeout</span>
          <p className="font-medium">{config.timeout}s</p>
        </div>
        <div>
          <span className="text-(--color-text-tertiary)">Version</span>
          <p className="font-medium">{agent.version}</p>
        </div>
        {health?.latency_ms != null && (
          <div>
            <span className="text-(--color-text-tertiary)">Latency</span>
            <p className="font-medium">{health.latency_ms}ms</p>
          </div>
        )}
      </div>

      <div className="mt-4">
        <h3 className="text-sm font-medium text-(--color-text-secondary) mb-2">Skills</h3>
        {config.skills.length > 0 ? (
          <div className="space-y-1.5">
            {config.skills.map((skill) => (
              <div key={skill.name} className="flex items-start gap-2">
                <Badge variant="outline">{skill.name}</Badge>
                <span className="text-sm text-(--color-text-tertiary)">{skill.description}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-(--color-text-tertiary)">No skills defined</p>
        )}
      </div>

      {agent.description && (
        <p className="text-sm text-(--color-text-tertiary) mt-4">{agent.description}</p>
      )}

      <div className="flex gap-2 mt-4">
        <Button
          size="sm"
          variant="ghost"
          onClick={() => setShowJson(!showJson)}
        >
          <Code className="w-3.5 h-3.5 mr-1.5" />
          {showJson ? 'Hide JSON' : 'Show JSON'}
        </Button>
        <Button
          size="sm"
          variant="ghost"
          onClick={onUnregister}
        >
          <Trash2 className="w-3.5 h-3.5 mr-1.5" />
          Unregister
        </Button>
      </div>

      {showJson && (
        <pre className="mt-3 p-3 rounded-md bg-(--color-background-secondary) text-xs font-mono overflow-x-auto max-h-64 overflow-y-auto">
          {componentData ? JSON.stringify(componentData, null, 2) : 'Loading...'}
        </pre>
      )}
    </Card>
  )
}
