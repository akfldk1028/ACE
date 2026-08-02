import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { LanguageNetworkCanvas } from '../../../src/design/components/book-language-flow/LanguageNetworkCanvas'
import {
  adaptCreativePortfolio,
} from '../../../src/design/components/book-language-flow/creative-portfolio-adapter'


describe('LanguageNetworkCanvas UnitBox matrix authority', () => {
  it('renders one UnitBox root, a 4x4 matrix, and derived volume separately', () => {
    const matrix4 = [
      [1, 0, 0, 0],
      [0, 1, 0, 0],
      [0, 0, 1, 0],
      [0, 0, 0, 1],
    ]
    const { container } = render(
      <LanguageNetworkCanvas
        nodes={[
          {
            id: 'book:base-model:1-1',
            kind: 'base_model',
            stage: 'base_model',
            label: '1/1 UnitBox',
            authority: 'book',
            attributes: { matrix4, cells: [{ minimum: [0, 0, 0], maximum: [1, 1, 1] }] },
          },
          {
            id: 'book:derived-volume:3-8',
            kind: 'derived_volume',
            stage: 'derived_volume',
            label: '3/8 Derived Volume',
            authority: 'book',
            attributes: { cells: [] },
          },
        ]}
        edges={[{
          id: 'edge:derive',
          source: 'book:base-model:1-1',
          target: 'book:derived-volume:3-8',
          kind: 'derives_volume',
          scope: 'execution',
        }]}
        stageOrder={['base_model', 'derived_volume']}
        selectedNodeId={null}
        onSelectNode={vi.fn()}
      />,
    )

    expect(screen.getByRole('button', { name: /1\/1 unitbox/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /3\/8 derived volume/i })).toBeInTheDocument()
    expect(container.querySelectorAll('[data-node-kind="base_model"]')).toHaveLength(1)
    expect(container.querySelectorAll('.book-network__matrix4 code')).toHaveLength(16)
    expect(container.querySelector('[data-edge-relation="derives_volume"]')).toBeInTheDocument()
  })

  it('renders the 101-node creative graph without dropping candidate 100', () => {
    const candidates = Array.from({ length: 100 }, (_, index) => ({
      run_id: 'creative-100',
      candidate_id: `creative-${String(index + 1).padStart(3, '0')}`,
      program_hash: `p-${index}`,
      geometry_hash: `g-${index}`,
      render_png: `renders/${index}.png`,
      candidate_json: `candidates/${index}.json`,
      render_url: `/render/${index}`,
      family: `family-${index % 15}`,
      form_class: 'composed',
      capacity_band: 'balanced',
      storeys: 4,
      legal_status: 'not_evaluated' as const,
      morphology_distance: 0.1,
    }))
    const adapted = adaptCreativePortfolio({
      schema_version: 'v1',
      run_type: 'creative_portfolio',
      run_id: 'creative-100',
      pnu: '',
      created_at: '',
      status: 'materialized',
      choice_pool: true,
      candidate_count: 100,
      legal_review_status: 'not_evaluated',
      paid_vlm_request_count: 0,
      board: {},
      board_png: 'board.png',
      filter_facets: {},
      morphology_evidence: {},
      candidates,
      graph: {
        schema_version: 'v1',
        root_node_ids: ['portfolio'],
        nodes: [
          { id: 'portfolio', kind: 'geometry_portfolio', identity: 'creative-100', attributes: {} },
          ...candidates.map((candidate) => ({
            id: `node:${candidate.candidate_id}`,
            kind: 'creative_mass_candidate',
            identity: candidate.geometry_hash,
            attributes: candidate,
          })),
        ],
        edges: candidates.map((candidate) => ({
          id: `edge:${candidate.candidate_id}`,
          source: `node:${candidate.candidate_id}`,
          target: 'portfolio',
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
        asset_root: 'root',
      },
    })

    const { container } = render(
      <LanguageNetworkCanvas
        nodes={adapted.nodes}
        edges={adapted.edges}
        stageOrder={adapted.stageOrder}
        selectedNodeId="node:creative-100"
        onSelectNode={vi.fn()}
        includeDescendants
      />,
    )

    expect(container.querySelector('[data-node-id="portfolio"]')).toBeInTheDocument()
    expect(container.querySelector('[data-node-id="node:creative-100"]')).toBeInTheDocument()
    expect(container.querySelector('[data-edge-id="edge:creative-100"]')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /creative-100.*not evaluated/i })).toBeInTheDocument()
  })
})
