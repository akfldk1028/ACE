import { lazy, Suspense, memo, useState, useMemo, useCallback, useEffect, useRef } from 'react'
import { Card, Badge, Button } from '@/shared/ui'
import { useTeams, getTeamName, getTeamPattern, useValidateComponent } from './useTeams'
import { useTeamStore } from './teamStore'
import { useNavigate, useBlocker } from 'react-router'
import { Plus, Play, Settings, X, Code, Eye, Target, Trash2, Pencil, Save, Undo2, Redo2, UserPlus, CheckCircle2, AlertTriangle, Download, AlertCircle } from 'lucide-react'
import {
  PATTERN_LABELS, AgentConfigPanel, PatternSelector, JsonView,
  useTeamEditor, EditableAgentPanel, TerminationEditor, AgentAddDialog,
} from '@/features/team-builder'
import type { PatternType } from '@/features/team-builder'

// Lazy-load AgentFlow (pulls in @xyflow/react + d3 + dagre ~270KB)
const AgentFlow = lazy(() =>
  import('@/features/team-builder/agentflow').then(m => ({ default: m.AgentFlow }))
)
import type { TeamResponse } from '@/shared/api'
import { validationAPI } from '@/shared/api'
import type { Component, ComponentConfig, TeamConfig, AgentConfig, TerminationConfig } from '@/shared/types/datamodel'
import { truncateError } from '@/shared/utils'
import { TeamCreateDialog, TeamDeleteDialog } from './components'
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors, type DragEndEvent } from '@dnd-kit/core'
import { SortableContext, useSortable, rectSortingStrategy } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

function downloadJSON(data: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function ValidationBadge({ component }: { component: Component<TeamConfig> | null | undefined }) {
  const { data: validation, isLoading } = useValidateComponent(component as Component<ComponentConfig> | null | undefined)
  if (isLoading || !validation) return null
  if (validation.is_valid) {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-(--color-semantic-success)" title="Component is valid">
        <CheckCircle2 className="w-3.5 h-3.5" />
        Valid
      </span>
    )
  }
  return (
    <span
      className="inline-flex items-center gap-1 text-xs text-(--color-semantic-error)"
      title={validation.errors.map(e => `${e.field}: ${e.error}`).join('\n')}
    >
      <AlertTriangle className="w-3.5 h-3.5" />
      {validation.errors.length} error{validation.errors.length !== 1 ? 's' : ''}
    </span>
  )
}

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

function getTermination(team: TeamResponse): Component<TerminationConfig> | undefined {
  const config = team.component?.config as Record<string, unknown> | undefined
  return config?.termination_condition as Component<TerminationConfig> | undefined
}

const TeamCard = memo(function TeamCard({
  team,
  isSelected,
  onSelect,
  onDelete,
}: {
  team: TeamResponse
  isSelected: boolean
  onSelect: () => void
  onDelete: () => void
}) {
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
        <Button
          size="sm"
          variant="ghost"
          onClick={(e) => {
            e.stopPropagation()
            onSelect()
          }}
        >
          <Settings className="w-3.5 h-3.5 mr-1.5" />
          Edit
        </Button>
        <Button
          size="sm"
          variant="ghost"
          onClick={(e) => {
            e.stopPropagation()
            onDelete()
          }}
          aria-label={`Delete team ${name}`}
          className="text-(--color-semantic-error) hover:bg-(--color-semantic-error)/10"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </Button>
      </div>
    </Card>
  )
})

const SortableChip = memo(function SortableChip({
  id,
  name,
  isSelected,
  onClick,
}: {
  id: string
  name: string
  isSelected: boolean
  onClick: () => void
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id })
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }
  return (
    <span
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      aria-pressed={isSelected}
      className={`text-xs px-2 py-1 rounded-full cursor-grab active:cursor-grabbing transition-colors focus:outline-none focus:ring-2 focus:ring-(--color-accent-primary) ${
        isSelected
          ? 'bg-(--color-accent-primary) text-white'
          : 'bg-(--color-background-secondary) text-(--color-text-secondary)'
      }`}
      onClick={onClick}
    >
      {name}
    </span>
  )
})

function UnsavedChangesDialog({ onStay, onLeave }: { onStay: () => void; onLeave: () => void }) {
  const dialogRef = useRef<HTMLDivElement>(null)

  // Focus trap + Escape key
  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return

    const focusable = dialog.querySelectorAll<HTMLElement>('button, [tabindex]:not([tabindex="-1"])')
    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    first?.focus()

    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        onStay()
        return
      }
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === first) { e.preventDefault(); last?.focus() }
        } else {
          if (document.activeElement === last) { e.preventDefault(); first?.focus() }
        }
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onStay])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onStay}
    >
      <div
        ref={dialogRef}
        role="alertdialog"
        aria-modal="true"
        aria-label="Unsaved changes"
        className="bg-(--color-background-primary) rounded-xl shadow-xl p-6 max-w-md mx-4"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 mb-4">
          <AlertCircle className="w-6 h-6 text-(--color-semantic-warning) shrink-0" />
          <h2 className="text-heading-small">Unsaved Changes</h2>
        </div>
        <p className="text-body-medium text-(--color-text-secondary) mb-6">
          You have unsaved changes to this team. Leaving will discard them.
        </p>
        <div className="flex justify-end gap-3">
          <Button variant="ghost" onClick={onStay}>
            Stay
          </Button>
          <Button
            variant="primary"
            className="bg-(--color-semantic-error) hover:bg-(--color-semantic-error)/90"
            onClick={onLeave}
          >
            Leave
          </Button>
        </div>
      </div>
    </div>
  )
}

export function TeamsPage() {
  const { data: teams, isLoading } = useTeams()
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null)
  const [selectedNodeLabel, setSelectedNodeLabel] = useState<string | null>(null)
  const [showJson, setShowJson] = useState(false)
  const [showPatterns, setShowPatterns] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<TeamResponse | null>(null)
  const [addAgentOpen, setAddAgentOpen] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  const editor = useTeamEditor()

  // DnD sensors with distance constraint to distinguish click from drag
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }))

  // Keyboard shortcuts for undo/redo
  const undoRef = useRef(editor.undo)
  const redoRef = useRef(editor.redo)
  undoRef.current = editor.undo
  redoRef.current = editor.redo

  useEffect(() => {
    if (!editor.isEditing) return
    const handler = (e: KeyboardEvent) => {
      // Don't intercept undo/redo inside text inputs (let native behavior work)
      if (e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLInputElement) return
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault()
        undoRef.current()
      }
      if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault()
        redoRef.current()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [editor.isEditing])

  // Block navigation when there are unsaved edits
  const blocker = useBlocker(editor.isEditing && editor.isDirty)

  // Also block browser close/refresh with unsaved edits
  useEffect(() => {
    if (!editor.isEditing || !editor.isDirty) return
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault()
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [editor.isEditing, editor.isDirty])

  const selectedTeam = teams?.find(t => t.id === selectedTeamId)

  // Use draft participants when editing, real participants otherwise
  const selectedParticipants = useMemo(() => {
    if (editor.isEditing && editor.draft?.teamId === selectedTeamId) {
      return editor.participants
    }
    return selectedTeam ? getParticipants(selectedTeam) : []
  }, [editor.isEditing, editor.draft, editor.participants, selectedTeamId, selectedTeam])

  const draftTermination = useMemo(() => {
    if (editor.isEditing && editor.draft?.teamId === selectedTeamId) {
      const config = editor.draft.component.config as unknown as Record<string, unknown>
      return config?.termination_condition as Component<TerminationConfig> | undefined
    }
    return selectedTeam ? getTermination(selectedTeam) : undefined
  }, [editor.isEditing, editor.draft, selectedTeamId, selectedTeam])

  const selectedPattern = useMemo(() => {
    if (editor.isEditing && editor.draft?.teamId === selectedTeamId) {
      return getTeamPattern({ id: editor.draft.teamId, component: editor.draft.component } as TeamResponse)
    }
    return selectedTeam ? getTeamPattern(selectedTeam) : 'unknown'
  }, [editor.isEditing, editor.draft, selectedTeamId, selectedTeam])

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

  const selectedAgentIndex = useMemo(() => {
    if (!selectedNodeLabel || !selectedParticipants.length) return -1
    return selectedParticipants.findIndex(
      p => (p.label ?? p.config?.name ?? '') === selectedNodeLabel
    )
  }, [selectedNodeLabel, selectedParticipants])

  // DnD sortable chip IDs (name-based for stable React keys across reorder)
  const chipIds = useMemo(
    () => selectedParticipants.map((p, i) => p.label ?? p.config?.name ?? `agent-${i}`),
    [selectedParticipants],
  )

  const handleNodeClick = useCallback((label: string) => {
    setSelectedNodeLabel(prev => prev === label ? null : label)
    setShowJson(false)
  }, [])

  const handleCloseConfigPanel = useCallback(() => {
    setSelectedNodeLabel(null)
  }, [])

  const handleClosePanel = useCallback(() => {
    if (editor.isEditing) editor.cancelEditing()
    setSelectedTeamId(null)
    setSelectedNodeLabel(null)
    setShowJson(false)
    setShowPatterns(false)
  }, [editor])

  const handleSelectTeam = useCallback((teamId: number) => {
    if (editor.isEditing) editor.cancelEditing()
    setSelectedTeamId(prev => prev === teamId ? null : teamId)
    setSelectedNodeLabel(null)
    setShowJson(false)
    setShowPatterns(false)
  }, [editor])

  const handleOpenCreate = useCallback(() => setCreateOpen(true), [])
  const handleCloseCreate = useCallback(() => setCreateOpen(false), [])

  const handleDeleteTeam = useCallback((team: TeamResponse) => {
    setDeleteTarget(team)
  }, [])

  const handleCloseDelete = useCallback(() => {
    const deletedId = deleteTarget?.id
    setDeleteTarget(null)
    if (deletedId === selectedTeamId) {
      setSelectedTeamId(null)
      setSelectedNodeLabel(null)
    }
  }, [deleteTarget, selectedTeamId])

  const handleToggleEdit = useCallback(() => {
    if (editor.isEditing) {
      editor.cancelEditing()
    } else if (selectedTeam) {
      editor.startEditing(selectedTeam)
    }
  }, [editor, selectedTeam])

  const handleSave = useCallback(async () => {
    try {
      setSaveError(null)
      // Validate before saving
      if (editor.draft?.component) {
        try {
          const validation = await validationAPI.validate(
            editor.draft.component as unknown as Component<ComponentConfig>
          )
          if (!validation.is_valid) {
            setSaveError(`Validation failed: ${validation.errors.map(e => e.error).join(', ')}`)
            return
          }
        } catch {
          // If validation API is unavailable, proceed with save anyway
        }
      }
      await editor.save()
    } catch (e) {
      setSaveError(truncateError(e instanceof Error ? e.message : 'Failed to save team'))
    }
  }, [editor])

  const handlePatternSelect = useCallback((pattern: PatternType) => {
    if (editor.isEditing) {
      editor.updatePattern(pattern)
    }
  }, [editor])

  const handleAddAgent = useCallback((agent: Component<AgentConfig>) => {
    editor.addParticipant(agent)
  }, [editor])

  const handleOpenAddAgent = useCallback(() => setAddAgentOpen(true), [])
  const handleCloseAddAgent = useCallback(() => setAddAgentOpen(false), [])
  const handleDiscard = useCallback(() => editor.cancelEditing(), [editor])
  const handleTogglePatterns = useCallback(() => setShowPatterns(p => !p), [])
  const handleToggleJson = useCallback(() => { setShowJson(j => !j); setSelectedNodeLabel(null) }, [])

  const handleExport = useCallback(() => {
    downloadJSON(
      editor.isEditing ? editor.draft?.component : selectedTeam?.component,
      `${selectedName.replace(/\s+/g, '_').toLowerCase()}.json`,
    )
  }, [editor.isEditing, editor.draft, selectedTeam, selectedName])

  const handleDragEnd = useCallback((event: DragEndEvent) => {
    const { active, over } = event
    if (over && active.id !== over.id) {
      const fromIndex = chipIds.indexOf(String(active.id))
      const toIndex = chipIds.indexOf(String(over.id))
      if (fromIndex >= 0 && toIndex >= 0) {
        editor.reorderParticipants(fromIndex, toIndex)
      }
    }
  }, [editor, chipIds])

  const handleJsonChange = useCallback((data: unknown) => {
    // Basic schema guard: must have provider (string) and config (object)
    if (
      typeof data !== 'object' || data === null ||
      typeof (data as Record<string, unknown>).provider !== 'string' ||
      typeof (data as Record<string, unknown>).config !== 'object'
    ) {
      setSaveError('Invalid team component: must have "provider" (string) and "config" (object)')
      return
    }
    setSaveError(null)
    editor.updateDraftComponent(data as Component<TeamConfig>)
  }, [editor])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-display-medium">Team Builder</h1>
          <p className="text-body-medium text-(--color-text-secondary) mt-1">
            Build and manage agent teams
          </p>
        </div>
        <Button onClick={handleOpenCreate}>
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
              <ValidationBadge component={editor.isEditing ? editor.draft?.component : selectedTeam.component} />
              {editor.isEditing && (
                <Badge variant="warning">Editing</Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              {/* Edit mode toolbar */}
              {editor.isEditing && (
                <>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={editor.undo}
                    disabled={!editor.canUndo}
                    aria-label="Undo"
                    title="Undo (Ctrl+Z)"
                  >
                    <Undo2 className="w-3.5 h-3.5" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={editor.redo}
                    disabled={!editor.canRedo}
                    aria-label="Redo"
                    title="Redo (Ctrl+Y)"
                  >
                    <Redo2 className="w-3.5 h-3.5" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleOpenAddAgent}
                    aria-label="Add agent to team"
                  >
                    <UserPlus className="w-3.5 h-3.5 mr-1.5" />
                    Add Agent
                  </Button>
                  <Button
                    size="sm"
                    variant="primary"
                    onClick={handleSave}
                    disabled={!editor.isDirty || editor.isSaving}
                    aria-label="Save team changes"
                  >
                    <Save className="w-3.5 h-3.5 mr-1.5" />
                    {editor.isSaving ? 'Saving...' : 'Save'}
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleDiscard}
                    aria-label="Discard changes"
                  >
                    <X className="w-3.5 h-3.5 mr-1.5" />
                    Discard
                  </Button>
                </>
              )}
              <Button
                size="sm"
                variant={editor.isEditing ? 'primary' : 'ghost'}
                onClick={handleToggleEdit}
                aria-label={editor.isEditing ? 'Exit edit mode' : 'Enter edit mode'}
              >
                <Pencil className="w-3.5 h-3.5 mr-1.5" />
                Edit
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={handleExport}
                aria-label="Download team as JSON"
              >
                <Download className="w-3.5 h-3.5 mr-1.5" />
                Export
              </Button>
              <Button
                size="sm"
                variant={showPatterns ? 'primary' : 'ghost'}
                onClick={handleTogglePatterns}
                aria-label="Toggle pattern selector"
              >
                <Target className="w-3.5 h-3.5 mr-1.5" />
                Patterns
              </Button>
              <Button
                size="sm"
                variant={showJson ? 'primary' : 'ghost'}
                onClick={handleToggleJson}
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

          {/* Pattern Selector (toggle) - interactive in edit mode */}
          {showPatterns && (
            <PatternSelector
              currentPattern={selectedPattern as PatternType}
              onSelect={editor.isEditing ? handlePatternSelect : undefined}
            />
          )}

          {/* Save error message */}
          {saveError && (
            <p className="text-sm text-(--color-semantic-error) mb-3">{saveError}</p>
          )}

          {/* Termination Editor (edit mode only) */}
          {editor.isEditing && (
            <div className="mb-3">
              <TerminationEditor
                value={draftTermination}
                onChange={editor.updateTermination}
              />
            </div>
          )}

          {/* JSON vs Graph toggle */}
          {showJson ? (
            <JsonView
              data={editor.isEditing ? editor.draft?.component : selectedTeam.component}
              editable={editor.isEditing}
              onChange={handleJsonChange}
            />
          ) : (
            <div className="flex gap-4">
              <div className={selectedAgent ? 'flex-1 min-w-0' : 'w-full'}>
                <Suspense fallback={
                  <div className="flex items-center justify-center h-[400px]">
                    <div className="w-6 h-6 border-2 border-(--color-accent-primary) border-t-transparent rounded-full animate-spin" />
                  </div>
                }>
                  <AgentFlow
                    teamProvider={editor.isEditing ? editor.draft?.component.provider : selectedTeam.component?.provider}
                    participants={flowParticipants}
                    height={400}
                    onNodeClick={handleNodeClick}
                  />
                </Suspense>
              </div>
              {selectedAgent && (
                <div className="w-80 flex-shrink-0">
                  {editor.isEditing && selectedAgentIndex >= 0 ? (
                    <EditableAgentPanel
                      agent={selectedAgent}
                      index={selectedAgentIndex}
                      onUpdate={editor.updateParticipant}
                      onRemove={editor.removeParticipant}
                      onClose={handleCloseConfigPanel}
                    />
                  ) : (
                    <AgentConfigPanel
                      agent={selectedAgent}
                      onClose={handleCloseConfigPanel}
                    />
                  )}
                </div>
              )}
            </div>
          )}

          {/* Agent chips - sortable via DnD in edit mode */}
          {editor.isEditing ? (
            <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
              <SortableContext items={chipIds} strategy={rectSortingStrategy}>
                <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Reorder agents by dragging">
                  {selectedParticipants.map((p, i) => {
                    const chipName = p.label ?? p.config?.name ?? `agent-${i}`
                    return (
                      <SortableChip
                        key={chipName}
                        id={chipName}
                        name={p.config?.name ?? `agent-${i}`}
                        isSelected={chipName === selectedNodeLabel}
                        onClick={() => handleNodeClick(chipName)}
                      />
                    )
                  })}
                </div>
              </SortableContext>
            </DndContext>
          ) : (
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
          )}
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
              onDelete={() => handleDeleteTeam(team)}
            />
          ))}
          {(!teams || teams.length === 0) && (
            <Card className="col-span-full text-center py-12">
              <p className="text-body-large text-(--color-text-secondary)">
                No teams found. Create your first team or connect to AutoGen Studio.
              </p>
              <Button className="mt-4" onClick={handleOpenCreate}>
                <Plus className="w-4 h-4 mr-2" />
                Create Team
              </Button>
            </Card>
          )}
        </div>
      )}

      {/* Dialogs */}
      <TeamCreateDialog open={createOpen} onClose={handleCloseCreate} />
      <TeamDeleteDialog team={deleteTarget} onClose={handleCloseDelete} />
      <AgentAddDialog
        open={addAgentOpen}
        onClose={handleCloseAddAgent}
        onAdd={handleAddAgent}
      />

      {/* Unsaved changes navigation blocker */}
      {blocker.state === 'blocked' && (
        <UnsavedChangesDialog
          onStay={() => blocker.reset?.()}
          onLeave={() => {
            editor.cancelEditing()
            blocker.proceed?.()
          }}
        />
      )}
    </div>
  )
}
