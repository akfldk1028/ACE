import { describe, expect, it } from 'vitest'

import type { ExecutedMassManifest } from '../../lib/language-system-types'
import { latestReplayableRunId } from './archive-selection-policy'

function manifest(
  runs: ExecutedMassManifest['runs'],
): ExecutedMassManifest {
  return {
    schema_version: 'arr.maas.executed_mass_archive.v1',
    run_id: 'portfolio-old',
    pnu: '1168011800104170004',
    run_status: 'selected_mass_ready',
    numeric_status: 'pass',
    source_archive: '',
    mass_count: 0,
    selected_run_id: 'portfolio-old',
    run_count: runs.length,
    archive_revision: 'test',
    runs,
    book_images_included: false,
    image_authority: 'executed_geometry_only',
    portfolio_vlm_audit: {},
    masses: [],
  }
}

describe('latestReplayableRunId', () => {
  it('opens the latest fresh synthesis even when an older portfolio is site-bound', () => {
    const value = manifest([
      {
        run_id: 'portfolio-old',
        created_at: '2026-07-24T05:00:00.000Z',
        pnu: '1168011800104170004',
        site_context_status: 'site_bound',
        selected_mass_count: 15,
        status: 'selected_mass_ready',
        replayable: true,
        run_type: 'portfolio',
      },
      {
        run_id: 'single-execution:r222-fresh',
        created_at: '2026-07-24T06:00:00.000Z',
        pnu: '',
        site_context_status: 'unresolved',
        selected_mass_count: 1,
        status: 'single_mass_ready',
        replayable: true,
        run_type: 'single_execution',
        execution_mode: 'fresh_synthesis',
      },
    ])

    expect(latestReplayableRunId(value)).toBe('single-execution:r222-fresh')
  })

  it('does not mistake a newer exact replay for a newly synthesized MASS', () => {
    const value = manifest([
      {
        run_id: 'single-execution:fresh',
        created_at: '2026-07-24T06:00:00.000Z',
        pnu: '',
        site_context_status: 'unresolved',
        selected_mass_count: 1,
        status: 'single_mass_ready',
        replayable: true,
        run_type: 'single_execution',
        execution_mode: 'fresh_synthesis',
      },
      {
        run_id: 'single-execution:replay',
        created_at: '2026-07-24T07:00:00.000Z',
        pnu: '1168011800104170004',
        site_context_status: 'source_gate_only',
        selected_mass_count: 1,
        status: 'single_mass_ready',
        replayable: true,
        run_type: 'single_execution',
        execution_mode: 'exact_replay',
      },
    ])

    expect(latestReplayableRunId(value)).toBe('single-execution:fresh')
  })
})
