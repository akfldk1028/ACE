import type { ExecutedMassManifest } from '../../lib/language-system-types'

export interface RecentMassCard {
  key: string
  runId: string
  executionId: string
  massIndex: number
  label: string
  operationLabel: string
  previewUrl: string
  selected: boolean
}


export function reconcileExecutedMassArchive(
  current: ExecutedMassManifest | null,
  incoming: ExecutedMassManifest,
): ExecutedMassManifest {
  if (!current || current.archive_revision === incoming.archive_revision) {
    return current ?? incoming
  }
  const knownRunIds = new Set(current.runs.map((run) => run.run_id))
  const incomingSelectionIsNew = !knownRunIds.has(incoming.selected_run_id)
  const incomingSelectionIsReplayable = incoming.runs.some(
    (run) => run.run_id === incoming.selected_run_id && run.replayable,
  )
  if (incomingSelectionIsNew && incomingSelectionIsReplayable) {
    return incoming
  }
  if (current.selected_run_id !== incoming.selected_run_id) {
    return {
      ...current,
      runs: incoming.runs,
      run_count: incoming.run_count,
      archive_revision: incoming.archive_revision,
    }
  }
  return incoming
}

export function resolveSelectedMassIndex(
  archive: ExecutedMassManifest,
  selectedMassIndex: number,
): number {
  return archive.masses.some((mass) => mass.index === selectedMassIndex)
    ? selectedMassIndex
    : (archive.masses[0]?.index ?? 1)
}

export function latestReplayableRunId(
  archive: ExecutedMassManifest,
): string {
  return archive.runs
    .filter((run) => run.replayable)
    .reduce((latest, run) => (
      !latest || run.created_at > latest.created_at ? run : latest
    ), null as ExecutedMassManifest['runs'][number] | null)
    ?.run_id ?? archive.selected_run_id
}

function isSingleExecution(runId: string, runType?: string): boolean {
  return runType === 'single_execution' || runId.startsWith('single-execution:')
}

export function buildRecentMassCards(
  archive: ExecutedMassManifest,
  selectedMassIndex = archive.masses[0]?.index ?? 1,
  limit = 24,
): RecentMassCard[] {
  const selectedMass = archive.masses[0]
  const singleExecutionCards = archive.runs
    .filter((run) => run.replayable && isSingleExecution(run.run_id, run.run_type))
    .sort((left, right) => right.created_at.localeCompare(left.created_at))
    .slice(0, limit)
    .map((run): RecentMassCard => {
      const executionId = run.run_id.slice('single-execution:'.length)
      const currentMass = run.run_id === archive.selected_run_id ? selectedMass : undefined
      return {
        key: `${run.run_id}:1`,
        runId: run.run_id,
        executionId,
        massIndex: currentMass?.index ?? 1,
        label: currentMass?.label || executionId,
        operationLabel: currentMass?.operation_label || 'EXECUTED MASS',
        previewUrl: currentMass?.preview_url
          || `/design/maas/single-executions/${executionId}/preview/`,
        selected: run.run_id === archive.selected_run_id,
      }
    })

  if (singleExecutionCards.length > 0 || isSingleExecution(archive.selected_run_id)) {
    return singleExecutionCards
  }

  return archive.masses.slice(0, limit).map((mass): RecentMassCard => ({
    key: mass.archive_key,
    runId: mass.run_id,
    executionId: mass.variant_id,
    massIndex: mass.index,
    label: mass.label,
    operationLabel: mass.operation_label,
    previewUrl: mass.preview_url,
    selected: mass.run_id === archive.selected_run_id && mass.index === selectedMassIndex,
  }))
}
