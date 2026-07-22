import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { ExecutedMassEvidence } from '../../../src/design/components/book-language-flow/ExecutedMassEvidence'
import type {
  ExecutedMassManifest,
  ExecutedMassRecord,
} from '../../../src/design/lib/language-system-types'


const mass = {
  archive_key: 'run:1',
  index: 1,
  variant_id: 'mass-01',
  label: 'MASS 01',
  operation_label: 'box -> taper',
  source_sequence: '1',
  run_id: 'source-run',
  program_type: 'neighborhood',
  program_label: 'Neighborhood',
  program_hash: 'a'.repeat(64),
  geometry_hash: 'b'.repeat(64),
  dsl: 'mass base = box(1, 1, 1)',
  node_count: 2,
  operator_path: ['box', 'taper'],
  book_principle_id: 'taper',
  book_scope: '1/1',
  book_orientation: 'vertical',
  capacity_alternative_id: 'alt-1',
  capacity_target_utilization: 0.9,
  capacity_achieved_utilization: 0.88,
  far_pct: 220,
  score: 0.8,
  hard_pass: true,
  geometry_ready: true,
  vlm_evaluated: false,
  preview_url: '/preview.png',
  passport_url: '/passport.json',
  image_role: 'actual_run_candidate_render',
} as ExecutedMassRecord

const archive = {
  schema_version: 'arr.maas.executed_mass_archive.v1',
  run_id: 'source-run',
  pnu: 'test-pnu',
  run_status: 'selected_mass_ready',
  numeric_status: 'pass',
  source_archive: 'archive.json',
  mass_count: 1,
  selected_run_id: 'source-run',
  run_count: 1,
  archive_revision: 'rev-1',
  runs: [],
  book_images_included: false,
  image_authority: 'actual render',
  portfolio_vlm_audit: {},
  masses: [mass],
} as ExecutedMassManifest

describe('ExecutedMassEvidence', () => {
  it('offers one explicit selected-MASS execution action in the existing sidebar', () => {
    const onExecute = vi.fn()
    const onVlmReview = vi.fn()
    render(
      <ExecutedMassEvidence
        archive={archive}
        mass={mass}
        passport={null}
        passportError=""
        onExecute={onExecute}
        executionState="idle"
        executionError=""
        onVlmReview={onVlmReview}
        vlmReviewState="idle"
        vlmReviewError=""
      />,
    )

    const button = screen.getByRole('button', { name: /execute selected mass/i })
    fireEvent.click(button)
    expect(onExecute).toHaveBeenCalledOnce()
  })

  it('offers a bounded paid VLM action only after a single-MASS run exists', () => {
    const onVlmReview = vi.fn()
    render(
      <ExecutedMassEvidence
        archive={{ ...archive, selected_run_id: 'single-execution:mass-fast' }}
        mass={{ ...mass, variant_id: 'mass-fast', run_id: 'single-execution:mass-fast' }}
        passport={null}
        passportError=""
        onExecute={vi.fn()}
        executionState="idle"
        executionError=""
        onVlmReview={onVlmReview}
        vlmReviewState="idle"
        vlmReviewError=""
      />,
    )

    const button = screen.getByRole('button', { name: /run bounded paid vlm/i })
    fireEvent.click(button)
    expect(onVlmReview).toHaveBeenCalledOnce()
  })
})
