import { useState, useMemo, useCallback } from 'react'
import { Card, Badge, Button } from '@/shared/ui'
import { useTeams, getTeamName, getTeamPattern } from './useTeams'
import { useTeamStore } from './teamStore'
import { useNavigate } from 'react-router'
import { Plus, Play, Settings, X, Code, Eye, Target } from 'lucide-react'
import { AgentFlow, PATTERN_LABELS, AgentConfigPanel, PatternSelector, JsonView } from '@/features/team-builder'
import type { PatternType } from '@/features/team-builder'
import type { TeamResponse } from '@/shared/api'
import type { Component, AgentConfig } from '@/shared/types/datamodel'

const PATTERN_COLORS: Record<string, 'primary' | 'success' | 'warning' | 'error' | 'default'> = {
  sequential: 'primary',
  selector: 'success',
  handoff: 'warning',
  debate: 'error',
  reflection: 'success',
  custom: 'default',
}

function getParticipants(team: TeamResponse) {
  const config = team.component?.config as Record<string, unknown> | undefined
  return (config?.participants ?? []) as Component<AgentConfig>[]
}

function TeamCard({ team, isSelected, onSelect }: { team: TeamResponse; isSelected: boolean; onSelect: () => void }) {
  const navigate = useNavigate()
  const { selectTeam } = useTeamStore()
  const name = getTeamName(team)
  const pattern = getTeamPattern(team)
  const participants = getParticipants(team)

  return (
    <Card
      className={`hover:shadow-lg transition-shadow cursor-pointer ${isSelected ? 'ring-2 ring-(--color-accent-primary)' : ''}`}
      onClick={onSelect}
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-heading-small">{name}</h3>
          <p className="text-body-small text-(--color-text-tertiary) mt-1">
            {participants.length} agents
          </p>
        </div>
        <Badge variant={PATTERN_COLORS[pattern] ?? 'default'}>{pattern}</Badge>
      </div>
      <div className="flex gap-2 mt-4">
        <Button
          size="sm"
          variant="primary"
          onClick={(e) => {
            e.stopPropagation()
            selectTeam(team.id)
            navigate('/')
          }}
        >
          <Play className="w-3.5 h-3.5 mr-1.5" />
          Run
        </Button>
        <Button size="sm" variant="ghost" onClick={(e) => e.stopPropagation()}>
          <Settings className="w-3.5 h-3.5 mr-1.5" />
          Edit
        </Button>
      </div>
    </Card>
  )
}

export function TeamsPage() {
  const { data: teams, isLoading } = useTeams()
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null)
  const [selectedNodeLabel, setSelectedNodeLabel] = useState<string | null>(null)
  const [showJson, setShowJson] = useState(false)
  const [showPatterns, setShowPatterns] = useState(false)

  const selectedTeam = teams?.find(t => t.id === selectedTeamId)
  const selectedParticipants = useMemo(
    () => selectedTeam ? getParticipants(selectedTeam) : [],
    [selectedTeam],
  )
  const selectedPattern = selectedTeam ? getTeamPattern(selectedTeam) : 'unknown'
  const selectedName = selectedTeam ? getTeamName(selectedTeam) : ''
  const patternInfo = PATTERN_LABELS[selectedPattern as keyof typeof PATTERN_LABELS] ?? PATTERN_LABELS.unknown

  const flowParticipants = useMemo(
    () => selectedParticipants.map(p => ({
      config: { name: p.config?.name },
      label: p.label ?? '',
      description: p.description ?? '',
    })),
    [selectedParticipants],
  )

  const selectedAgent = useMemo(() => {
    if (!selectedNodeLabel || !selectedParticipants.length) return null
    return selectedParticipants.find(
      p => (p.label ?? p.config?.name ?? '') === selectedNodeLabel
    ) ?? null
  }, [selectedNodeLabel, selectedParticipants])

  const handleNodeClick = useCallback((label: string) => {
    setSelectedNodeLabel(prev => prev === label ? null : label)
    setShowJson(false)
  }, [])

  const handleCloseConfigPanel = useCallback(() => {
    setSelectedNodeLabel(null)
  }, [])

  const handleClosePanel = useCallback(() => {
    setSelectedTeamId(null)
    setSelectedNodeLabel(null)
    setShowJson(false)
    setShowPatterns(false)
  }, [])

  const handleSelectTeam = useCallback((teamId: number) => {
    setSelectedTeamId(prev => prev === teamId ? null : teamId)
    setSelectedNodeLabel(null)
    setShowJson(false)
    setShowPatterns(false)
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-display-medium">Team Builder</h1>
          <p className="text-body-medium text-(--color-text-secondary) mt-1">
            Build and manage agent teams
          </p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          New Team
        </Button>
      </div>

      {/* Agent Flow Graph Panel */}
      {selectedTeam && (
        <Card className="relative">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <h2 className="text-heading-small">{selectedName}</h2>
              <Badge variant={PATTERN_COLORS[selectedPattern] ?? 'default'}>
                {patternInfo.label}
              </Badge>
              <span className="text-body-small text-(--color-text-tertiary)">
                {patternInfo.description}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant={showPatterns ? 'primary' : 'ghost'}
                onClick={() => setShowPatterns(p => !p)}
                aria-label="Toggle pattern selector"
              >
                <Target className="w-3.5 h-3.5 mr-1.5" />
                Patterns
              </Button>
              <Button
                size="sm"
                variant={showJson ? 'primary' : 'ghost'}
                onClick={() => { setShowJson(j => !j); setSelectedNodeLabel(null) }}
                aria-label={showJson ? 'Show graph view' : 'Show JSON view'}
              >
                {showJson
                  ? <><Eye className="w-3.5 h-3.5 mr-1.5" />Graph</>
                  : <><Code className="w-3.5 h-3.5 mr-1.5" />JSON</>
                }
              </Button>
              <button
                onClick={handleClosePanel}
                className="p-1 rounded hover:bg-(--color-background-secondary) text-(--color-text-tertiary) focus:outline-none focus:ring-2 focus:ring-(--color-accent-primary)"
                aria-label="Close graph panel"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Pattern Selector (toggle) */}
          {showPatterns && <PatternSelector currentPattern={selectedPattern as PatternType} />}

          {/* JSON vs Graph toggle */}
          {showJson ? (
            <JsonView data={selectedTeam.component} />
          ) : (
            <div className="flex gap-4">
              <div className={selectedAgent ? 'flex-1 min-w-0' : 'w-full'}>
                <AgentFlow
                  teamProvider={selectedTeam.component?.provider}
                  participants={flowParticipants}
                  height={400}
                  onNodeClick={handleNodeClick}
                />
              </div>
              {selectedAgent && (
                <div className="w-80 flex-shrink-0">
                  <AgentConfigPanel
                    agent={selectedAgent}
                    onClose={handleCloseConfigPanel}
                  />
                </div>
              )}
            </div>
          )}

          {/* Agent chips with highlight */}
          <div className="mt-3 flex flex-wrap gap-2">
            {selectedParticipants.map((p, i) => {
              const chipName = p.label ?? p.config?.name ?? `agent-${i}`
              const isSelected = chipName === selectedNodeLabel
              return (
                <span
                  key={chipName}
                  role="button"
                  tabIndex={0}
                  aria-pressed={isSelected}
                  className={`text-xs px-2 py-1 rounded-full cursor-pointer transition-colors focus:outline-none focus:ring-2 focus:ring-(--color-accent-primary) ${
                    isSelected
                      ? 'bg-(--color-accent-primary) text-white'
                      : 'bg-(--color-background-secondary) text-(--color-text-secondary)'
                  }`}
                  onClick={() => handleNodeClick(chipName)}
                  onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleNodeClick(chipName) } }}
                >
                  {p.config?.name ?? `agent-${i}`}
                </span>
              )
            })}
          </div>
        </Card>
      )}

      {isLoading ? (
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
          {teams?.map((team) => (
            <TeamCard
              key={team.id}
              team={team}
              isSelected={team.id === selectedTeamId}
              onSelect={() => handleSelectTeam(team.id)}
            />
          ))}
          {(!teams || teams.length === 0) && (
            <Card className="col-span-full text-center py-12">
              <p className="text-body-large text-(--color-text-secondary)">
                No teams found. Create your first team or connect to AutoGen Studio.
              </p>
              <Button className="mt-4">
                <Plus className="w-4 h-4 mr-2" />
                Create Team
              </Button>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
