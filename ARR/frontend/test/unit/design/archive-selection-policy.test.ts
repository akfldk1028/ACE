import { describe, expect, it } from 'vitest'

import {
  buildRecentMassCards,
  reconcileExecutedMassArchive,
  latestReplayableRunId,
  resolveSelectedMassIndex,
} from '../../../src/design/components/book-language-flow/archive-selection-policy'
import type { ExecutedMassManifest } from '../../../src/design/lib/language-system-types'


function manifest(
  selectedRunId: string,
  knownRunIds: string[],
  archiveRevision: string,
): ExecutedMassManifest {
  return {
    selected_run_id: selectedRunId,
    run_id: selectedRunId,
    archive_revision: archiveRevision,
    run_count: knownRunIds.length,
    runs: knownRunIds.map((runId) => ({
      run_id: runId,
      label: runId,
      mass_count: 1,
      created_at: '2026-07-24T00:00:00Z',
      source_archive: runId,
      selected: runId === selectedRunId,
      replayable: true,
    })),
    masses: [{
      index: 1,
      archive_key: `${selectedRunId}:1`,
      run_id: selectedRunId,
      label: selectedRunId,
    }],
  } as ExecutedMassManifest
}

describe('executed MASS archive selection policy', () => {
  it('follows a newly arrived replayable run into the graph body', () => {
    const current = manifest('single-execution:r207', ['single-execution:r207'], 'rev-207')
    const incoming = manifest(
      'single-execution:r208',
      ['single-execution:r208', 'single-execution:r207'],
      'rev-208',
    )

    const resolved = reconcileExecutedMassArchive(current, incoming)

    expect(resolved.selected_run_id).toBe('single-execution:r208')
    expect(resolved.masses[0].run_id).toBe('single-execution:r208')
  })

  it('preserves a manual historical selection once the latest run is already known', () => {
    const current = manifest(
      'single-execution:r207',
      ['single-execution:r208', 'single-execution:r207'],
      'rev-208',
    )
    const incoming = manifest(
      'single-execution:r208',
      ['single-execution:r208', 'single-execution:r207'],
      'rev-209',
    )

    const resolved = reconcileExecutedMassArchive(current, incoming)

    expect(resolved.selected_run_id).toBe('single-execution:r207')
    expect(resolved.archive_revision).toBe('rev-209')
  })

  it('resets a stale MASS_04 index to the first MASS in a new single execution', () => {
    const incoming = manifest('single-execution:r208', ['single-execution:r208'], 'rev-208')

    expect(resolveSelectedMassIndex(incoming, 4)).toBe(1)
  })

  it('selects the chronologically latest replayable MASS when the page opens', () => {
    const archive = manifest(
      'book-program-portfolios:r196',
      ['book-program-portfolios:r196', 'single-execution:r210'],
      'rev-210',
    )
    archive.runs[0].created_at = '2026-07-23T00:00:00Z'
    archive.runs[1].created_at = '2026-07-24T02:04:02Z'

    expect(latestReplayableRunId(archive)).toBe('single-execution:r210')
  })

  it('builds a newest-first MASS-only rail from replayable single executions', () => {
    const archive = manifest(
      'single-execution:r212-diagonal-slice',
      [
        'book-program-portfolios:r196',
        'single-execution:r211-radial-fan',
        'single-execution:r212-diagonal-slice',
      ],
      'rev-212',
    )
    archive.runs[0].run_type = 'portfolio'
    archive.runs[0].created_at = '2026-07-23T00:00:00Z'
    archive.runs[1].run_type = 'single_execution'
    archive.runs[1].created_at = '2026-07-24T02:11:00Z'
    archive.runs[2].run_type = 'single_execution'
    archive.runs[2].created_at = '2026-07-24T02:12:00Z'

    const cards = buildRecentMassCards(archive)

    expect(cards.map((card) => card.runId)).toEqual([
      'single-execution:r212-diagonal-slice',
      'single-execution:r211-radial-fan',
    ])
    expect(cards[0]).toMatchObject({
      executionId: 'r212-diagonal-slice',
      selected: true,
      previewUrl: '/design/maas/single-executions/r212-diagonal-slice/thumbnail/',
    })
  })

  it('shows one newest representative card for repeated geometry hashes', () => {
    const archive = manifest(
      'single-execution:r209-render-proof',
      [
        'single-execution:r211-unique-mass',
        'single-execution:r209-render-proof',
        'single-execution:r210-render-proof',
      ],
      'rev-211',
    )
    archive.runs.forEach((run) => { run.run_type = 'single_execution' })
    archive.runs[0].created_at = '2026-07-24T02:11:00Z'
    archive.runs[0].geometry_hash = 'unique-geometry'
    archive.runs[1].created_at = '2026-07-24T02:09:00Z'
    archive.runs[1].geometry_hash = 'repeated-geometry'
    archive.runs[2].created_at = '2026-07-24T02:10:00Z'
    archive.runs[2].geometry_hash = 'repeated-geometry'
    archive.masses[0].geometry_hash = 'repeated-geometry'

    const cards = buildRecentMassCards(archive)

    expect(cards).toHaveLength(2)
    expect(cards.map((card) => card.runId)).toEqual([
      'single-execution:r211-unique-mass',
      'single-execution:r210-render-proof',
    ])
    expect(cards[1]).toMatchObject({
      selected: true,
      previewUrl: '/design/maas/single-executions/r210-render-proof/thumbnail/',
    })
  })

  it('keeps the selected portfolio MASS candidates without mixing non-MASS evidence', () => {
    const archive = manifest(
      'book-program-portfolios:r196',
      ['book-program-portfolios:r196'],
      'rev-196',
    )
    archive.runs[0].run_type = 'portfolio'
    archive.masses[0].preview_url = '/design/maas/executed-masses/1/preview/'
    archive.masses[0].variant_id = 'courtyard-01'
    archive.masses[0].operation_label = 'Courtyard'

    const cards = buildRecentMassCards(archive)

    expect(cards).toHaveLength(1)
    expect(cards[0]).toMatchObject({
      runId: 'book-program-portfolios:r196',
      massIndex: 1,
      previewUrl: '/design/maas/executed-masses/1/preview/',
      selected: true,
    })
  })
})
