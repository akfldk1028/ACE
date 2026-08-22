import { describe, expect, it } from 'vitest'

import {
  adaptMassPortfolio,
  filterMassPortfolioCards,
} from '../../../src/design/components/book-language-flow/mass-portfolio-adapter'
import type { MassPortfolioManifest } from '../../../src/design/lib/mass-portfolio-types'

const stage = (name: string, status = 'pass') => ({
  stage: name,
  status,
  reasons: status === 'failed' ? [`${name}_failed`] : [],
  evidence: {},
})

function manifest(count = 20): MassPortfolioManifest {
  return {
    schema_version: 'arr.maas.portfolio_evaluation_manifest.v1',
    run_id: 'run-20',
    pnu: '1168011800104170004',
    candidate_count: count,
    status_counts: { legal_pass: count - 1, failed: 1 },
    candidates: Array.from({ length: count }, (_, index) => ({
      schema_version: 'arr.maas.candidate_evaluation.v1',
      run_id: 'run-20',
      program_slug: index % 2 ? 'library' : 'neighborhood',
      candidate_id: `book:operative:${index}`,
      program_hash: String(index).padStart(64, 'a').slice(-64),
      geometry_hash: String(index).padStart(64, 'b').slice(-64),
      overall_status: index === 19 ? 'failed' : 'legal_pass',
      selected: index === 0,
      integrity_failures: [],
      terminal_reasons: index === 19 ? ['law_failed'] : [],
      preview_path: index === 18 ? '' : `renders/${index}.png`,
      preview_url: index === 18 ? '' : `/render/${index}.png`,
      lineage: { book_principle_id: `book:operative:${index}`, book_scope: '3/8' },
      finalized: true,
      stages: {
        geometry: stage('geometry'),
        law: stage('law', index === 19 ? 'failed' : 'pass'),
        capacity: stage('capacity'),
        parking: stage('parking'),
        program: stage('program'),
        vlm: stage('vlm', 'not_evaluated'),
        selection: stage('selection', index === 0 ? 'pass' : 'not_evaluated'),
      },
    })),
  }
}

describe('mass portfolio adapter', () => {
  it('keeps all twenty candidates and builds the shared language lineage', () => {
    const adapted = adaptMassPortfolio(manifest())

    expect(adapted.cards).toHaveLength(20)
    expect(adapted.stageOrder).toEqual([
      'unitbox', 'matrix4', 'book', 'compile', 'geometry', 'law',
      'capacity', 'parking', 'program', 'vlm', 'selection', 'mass_result',
    ])
    expect(adapted.nodes.some((node) => node.id === 'mass-stage:matrix4')).toBe(true)
    expect(adapted.nodes.filter((node) => node.kind === 'mass_candidate')).toHaveLength(20)
  })

  it('preserves failed and missing-preview candidates without inventing evidence', () => {
    const adapted = adaptMassPortfolio(manifest())

    expect(adapted.cards[18].previewUrl).toBe('')
    expect(adapted.cards[19].overallStatus).toBe('failed')
    expect(adapted.cards[19].stages.law.status).toBe('failed')
  })

  it('filters by overall and individual gate status', () => {
    const cards = adaptMassPortfolio(manifest()).cards

    expect(filterMassPortfolioCards(cards, {
      program: '', overallStatus: 'failed', gate: '', gateStatus: '',
    })).toHaveLength(1)
    expect(filterMassPortfolioCards(cards, {
      program: 'library', overallStatus: '', gate: 'law', gateStatus: 'pass',
    })).toHaveLength(9)
  })
})
