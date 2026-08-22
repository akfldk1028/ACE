import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { MassPortfolioView } from '../../../src/design/components/book-language-flow/MassPortfolioView'
import type { MassPortfolioManifest } from '../../../src/design/lib/mass-portfolio-types'

const stages = Object.fromEntries(['geometry', 'law', 'capacity', 'parking', 'program', 'vlm', 'selection'].map((name) => [name, { stage: name, status: name === 'vlm' ? 'not_evaluated' : 'pass', reasons: [], evidence: {} }]))
const manifest = {
  schema_version: 'arr.maas.portfolio_evaluation_manifest.v1', run_id: 'legal-20', pnu: '1', candidate_count: 2,
  status_counts: { legal_pass: 1, failed: 1 },
  candidates: [0, 1].map((index) => ({ schema_version: 'arr.maas.candidate_evaluation.v1', run_id: 'legal-20', program_slug: 'library', candidate_id: `mass:${index}`, program_hash: 'a'.repeat(64), geometry_hash: `${index}`.repeat(64), overall_status: index ? 'failed' : 'legal_pass', selected: false, integrity_failures: [], terminal_reasons: index ? ['law_failed'] : [], preview_path: index ? '' : '0.png', preview_url: index ? '' : '/0.png', lineage: {}, finalized: true, stages: index ? { ...stages, law: { stage: 'law', status: 'failed', reasons: ['law_failed'], evidence: {} } } : stages })),
} as MassPortfolioManifest

describe('MassPortfolioView', () => {
  it('shows every candidate, the 4x4 lineage, explicit statuses, and missing preview', () => {
    render(<MassPortfolioView manifest={manifest} />)

    expect(screen.getByText('4×4 AFFINE MATRIX')).toBeInTheDocument()
    expect(screen.getByText(/2 TOTAL · 2 VISIBLE · 1 LAW PASS · 1 FINAL PASS · 1 FAILED/)).toBeInTheDocument()
    expect(screen.getAllByRole('listitem')).toHaveLength(2)
    expect(screen.getByText('NO PNG')).toBeInTheDocument()
    expect(screen.getAllByText('NOT EVALUATED').length).toBeGreaterThan(0)
  })
})
