import { describe, expect, it } from 'vitest'

import {
  adaptCreativePortfolio,
  creativeMassSelectionKey,
  creativePortfolioPage,
} from '../../../src/design/components/book-language-flow/creative-portfolio-adapter'
import type { CreativePortfolioManifest } from '../../../src/design/lib/language-system-types'


function manifest(count = 100): CreativePortfolioManifest {
  const candidates = Array.from({ length: count }, (_, offset) => {
    const index = offset + 1
    return {
      run_id: 'creative-100',
      candidate_id: `creative-${String(index).padStart(3, '0')}`,
      program_hash: `program-${index}`,
      geometry_hash: `geometry-${index}`,
      render_png: `renders/creative-${String(index).padStart(3, '0')}.png`,
      candidate_json: `candidates/creative-${String(index).padStart(3, '0')}.json`,
      render_url: `/design/maas/creative-portfolios/creative-100/candidates/creative-${String(index).padStart(3, '0')}/render/`,
      family: index === 100 ? 'interlocking_tilted_discs' : `family-${index % 15}`,
      form_class: 'composed',
      capacity_band: index % 4 === 0 ? 'maximum_target' : 'balanced',
      storeys: 3 + (index % 4),
      legal_status: 'not_evaluated' as const,
      morphology_distance: index / 1000,
    }
  })
  return {
    schema_version: 'arr.maas.creative_portfolio_catalog.v1',
    run_type: 'creative_portfolio',
    run_id: 'creative-100',
    pnu: '1168011800104170004',
    created_at: '2026-07-30T00:00:00Z',
    status: 'materialized',
    choice_pool: true,
    candidate_count: count,
    legal_review_status: 'not_evaluated',
    paid_vlm_request_count: 0,
    board: {},
    board_png: 'maas-creative-board.png',
    filter_facets: {},
    morphology_evidence: {},
    candidates,
    graph: {
      schema_version: 'arr.maas.creative_frontend_graph.v1',
      root_node_ids: ['creative:portfolio:creative-100'],
      nodes: [
        {
          id: 'creative:portfolio:creative-100',
          kind: 'geometry_portfolio',
          identity: 'creative-100',
          attributes: {},
        },
        ...candidates.map((candidate) => ({
          id: `creative:candidate:${candidate.candidate_id}`,
          kind: 'creative_mass_candidate',
          identity: candidate.geometry_hash,
          attributes: candidate,
        })),
      ],
      edges: candidates.map((candidate) => ({
        id: `creative:member:${candidate.candidate_id}`,
        source: `creative:candidate:${candidate.candidate_id}`,
        target: 'creative:portfolio:creative-100',
        kind: 'member_of',
      })),
    },
    runs: [],
    contracts: {
      executed_mass_manifest_coercion: false,
      law_evidence_fabricated: false,
      parking_evidence_fabricated: false,
      elevation_evidence_fabricated: false,
      certified_capacity_fabricated: false,
      asset_root: 'configured_docs_mass_root',
    },
  }
}

describe('creative portfolio adapter', () => {
  it('keeps all 100 members and exposes page navigation to 1, 25, and 100', () => {
    const adapted = adaptCreativePortfolio(manifest())

    expect(adapted.cards).toHaveLength(100)
    expect(creativePortfolioPage(adapted.cards, 1, 25).items.map((item) => item.candidateId))
      .toEqual(expect.arrayContaining(['creative-001', 'creative-025']))
    expect(creativePortfolioPage(adapted.cards, 4, 25).items.at(-1)?.candidateId)
      .toBe('creative-100')
    expect(adapted.nodes).toHaveLength(101)
    expect(adapted.edges).toHaveLength(100)
  })

  it('uses the complete immutable tuple as selection identity', () => {
    const card = adaptCreativePortfolio(manifest(1)).cards[0]

    expect(creativeMassSelectionKey(card)).toBe(
      'creative-100/creative-001/program-1/geometry-1',
    )
    expect(card).toMatchObject({
      portfolioRunId: 'creative-100',
      family: 'family-1',
      formClass: 'composed',
      capacityBand: 'balanced',
      storeys: 4,
      legalStatus: 'not_evaluated',
      morphologyDistance: 0.001,
    })
  })
})
