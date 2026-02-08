import { useState, useMemo, useCallback } from 'react'
import { Card, Button } from '@/shared/ui'
import { Plus, RefreshCw } from 'lucide-react'
import { useAgents, useAgentHealth, useUnregisterAgent } from './useAgents'
import { useAgentStore } from './agentStore'
import { AgentCard } from './components/AgentCard'
import { AgentDetailPanel } from './components/AgentDetailPanel'
import { AgentRegisterDialog } from './components/AgentRegisterDialog'
import type { A2AHealthStatus } from './types'

export function AgentsPage() {
  const { data: agents, isLoading, isError } = useAgents()
  const { data: healthData, refetch: refetchHealth, isFetching: isHealthFetching } = useAgentHealth()
  const unregisterMutation = useUnregisterAgent()
  const { selectedAgentName, selectAgent } = useAgentStore()
  const [registerOpen, setRegisterOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const healthMap = useMemo(() => {
    const map = new Map<string, A2AHealthStatus>()
    if (healthData) {
      for (const h of healthData) {
        map.set(h.name, h)
      }
    }
    return map
  }, [healthData])

  const filteredAgents = useMemo(() => {
    if (!agents) return []
    const valid = agents.filter(a => a.config?.name)
    if (!searchQuery.trim()) return valid
    const q = searchQuery.toLowerCase()
    return valid.filter(a =>
      a.label?.toLowerCase().includes(q) ||
      a.config.name.toLowerCase().includes(q) ||
      a.config.description?.toLowerCase().includes(q)
    )
  }, [agents, searchQuery])

  const selectedAgent = filteredAgents.find(a => a.config.name === selectedAgentName)

  // H1: Move selectAgent(null) into onSuccess callback
  const handleUnregister = useCallback((name: string) => {
    if (confirm(`Unregister agent "${name}"?`)) {
      unregisterMutation.mutate(name, {
        onSuccess: () => {
          if (selectedAgentName === name) selectAgent(null)
        },
      })
    }
  }, [unregisterMutation, selectedAgentName, selectAgent])

  const handleSelect = useCallback((name: string) => {
    selectAgent(name === selectedAgentName ? null : name)
  }, [selectAgent, selectedAgentName])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-display-medium">A2A Agents</h1>
          <p className="text-body-medium text-(--color-text-secondary) mt-1">
            Discover and manage A2A protocol agents
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            onClick={() => refetchHealth()}
            disabled={isHealthFetching}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isHealthFetching ? 'animate-spin' : ''}`} />
            Health Check All
          </Button>
          <Button onClick={() => setRegisterOpen(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Register Agent
          </Button>
        </div>
      </div>

      {/* Search - M1: aria-label added */}
      {agents && agents.length > 0 && (
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search agents..."
          aria-label="Search agents"
          className="h-10 w-full max-w-sm px-4 rounded-md border border-(--color-border-default) bg-(--color-surface-card) text-(--color-text-primary) text-sm focus:outline-none focus:border-(--color-accent-primary) focus:ring-2 focus:ring-(--color-accent-primary)/20 placeholder:text-(--color-text-tertiary)"
        />
      )}

      {/* Detail Panel */}
      {selectedAgent && (
        <AgentDetailPanel
          agent={selectedAgent}
          health={healthMap.get(selectedAgent.config.name)}
          onClose={() => selectAgent(null)}
          onUnregister={() => handleUnregister(selectedAgent.config.name)}
        />
      )}

      {/* Grid */}
      {isLoading && !isError ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <div className="h-4 bg-(--color-background-secondary) rounded w-3/4" />
              <div className="h-3 bg-(--color-background-secondary) rounded w-1/2 mt-3" />
              <div className="h-8 bg-(--color-background-secondary) rounded w-20 mt-4" />
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAgents.map((agent) => (
            <AgentCard
              key={agent.config.name}
              agent={agent}
              health={healthMap.get(agent.config.name)}
              isSelected={agent.config.name === selectedAgentName}
              onSelect={() => handleSelect(agent.config.name)}
              onUnregister={() => handleUnregister(agent.config.name)}
            />
          ))}
          {filteredAgents.length === 0 && (
            <Card className="col-span-full text-center py-12">
              <p className="text-body-large text-(--color-text-secondary)">
                {searchQuery
                  ? 'No agents match your search.'
                  : 'No agents registered. Add your first A2A agent to get started.'}
              </p>
              {!searchQuery && (
                <Button className="mt-4" onClick={() => setRegisterOpen(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Register Agent
                </Button>
              )}
            </Card>
          )}
        </div>
      )}

      <AgentRegisterDialog
        open={registerOpen}
        onClose={() => setRegisterOpen(false)}
      />
    </div>
  )
}
