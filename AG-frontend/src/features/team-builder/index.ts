export { AgentConfigPanel } from './AgentConfigPanel'
export { PatternSelector } from './PatternSelector'
export { JsonView } from './JsonView'
// Light agentflow exports (types + pattern utilities, no xyflow dependency)
export { patternToProvider, PATTERN_LABELS, PATTERN_DEFINITIONS } from './agentflow'
export type { PatternType, Participant } from './agentflow'
// AgentFlow component should be lazy-loaded: lazy(() => import('@/features/team-builder/agentflow'))

// Phase 3b: Edit mode
export { useTeamEditor } from './useTeamEditor'
export { EditableAgentPanel } from './EditableAgentPanel'
export { ModelSelector } from './ModelSelector'
export { TerminationEditor } from './TerminationEditor'
export { AgentAddDialog } from './AgentAddDialog'
