import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { ExecutedMassEvidence } from '../../../src/design/components/book-language-flow/ExecutedMassEvidence'
import type {
  ExecutedMassManifest,
  ExecutedMassRecord,
  MassExecutionPassport,
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
  it('offers one explicit exact-AST replay action in the existing sidebar', () => {
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

    const button = screen.getByRole('button', { name: /replay exact selected mass ast/i })
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

  it('shows the hash-bound specialist collaboration for the selected MASS', () => {
    const passport = {
      status: 'needs_evidence',
      stages: [],
      agent_collaboration: {
        final_status: 'needs_evidence',
        identity: {
          execution_id: 'mass-fast',
          program_hash: mass.program_hash,
          geometry_hash: mass.geometry_hash,
          pnu: archive.pnu,
        },
        evidence: [
          { evidence_id: 'geometry', agent: 'maas_geometry_agent', status: 'passed', summary: 'compiled', evidence: {} },
          { evidence_id: 'law', agent: 'law_graph_agent', status: 'needs_evidence', summary: 'Neo4j unavailable', evidence: {} },
          { evidence_id: 'parking', agent: 'parking_agent', status: 'passed', summary: 'layout pass', evidence: {} },
          { evidence_id: 'review', agent: 'review_agent', status: 'needs_evidence', summary: 'blocked', evidence: {} },
          { evidence_id: 'selector', agent: 'selector', status: 'needs_evidence', summary: 'blocked', evidence: {} },
        ],
        handoffs: [],
      },
    } as unknown as MassExecutionPassport

    render(
      <ExecutedMassEvidence
        archive={archive}
        mass={mass}
        passport={passport}
        passportError=""
        onExecute={vi.fn()}
        executionState="complete"
        executionError=""
        onVlmReview={vi.fn()}
        vlmReviewState="idle"
        vlmReviewError=""
      />,
    )

    expect(screen.getByText('SPECIALIST COLLABORATION')).toBeInTheDocument()
    expect(screen.getByText('LAW GRAPH AGENT')).toBeInTheDocument()
    expect(screen.getAllByText('NEEDS EVIDENCE').length).toBeGreaterThan(0)
  })

  it('keeps a legacy passport with an empty collaboration object renderable', () => {
    const legacyPassport = {
      status: 'in_progress',
      stages: [],
      agent_collaboration: {},
    } as unknown as MassExecutionPassport

    expect(() => render(
      <ExecutedMassEvidence
        archive={{ ...archive, selected_run_id: 'book-program-portfolios-r182-seven-page-closure-pass' }}
        mass={mass}
        passport={legacyPassport}
        passportError=""
        onExecute={vi.fn()}
        executionState="idle"
        executionError=""
        onVlmReview={vi.fn()}
        vlmReviewState="idle"
        vlmReviewError=""
      />,
    )).not.toThrow()

    expect(screen.getByText('MASS 01')).toBeInTheDocument()
  })

  it('shows plan-aware floor product evidence without calling an incomplete passport complete', () => {
    const planAwareMass = {
      ...mass,
      num_floors: 5,
      floor_height_m: 3,
      total_floor_area_m2: 294.2,
      bcr_pct: 55.4,
      floor_contract_hash: 'floor-contract-123',
      floor_capacity_plan_hash: 'capacity-plan-123',
      parking_required: 2,
      parking_provided: 2,
      elevation_status: 'blocked',
    } as ExecutedMassRecord
    const passport = {
      status: 'in_progress',
      full_flow_complete: false,
      stages: [
        { id: 'vlm', status: 'not_evaluated', evidence: {} },
        { id: 'selector', status: 'passed', evidence: {} },
      ],
    } as unknown as MassExecutionPassport

    render(
      <ExecutedMassEvidence
        archive={archive}
        mass={planAwareMass}
        passport={passport}
        passportError=""
        onExecute={vi.fn()}
        executionState="idle"
        executionError=""
        onVlmReview={vi.fn()}
        vlmReviewState="idle"
        vlmReviewError=""
      />,
    )

    expect(screen.getByText('IN PROGRESS')).toBeInTheDocument()
    expect(screen.queryByText(/COMPLETE · VLM NOT EVALUATED/)).not.toBeInTheDocument()
    expect(screen.getByText('5 FLOORS · 3.000m')).toBeInTheDocument()
    expect(screen.getByText('294.200m²')).toBeInTheDocument()
    expect(screen.getByText('55.400%')).toBeInTheDocument()
    expect(screen.getByText('2 / 2')).toBeInTheDocument()
    expect(screen.getByText('BLOCKED')).toBeInTheDocument()
    expect(screen.getByText('capacity-plan-123')).toBeInTheDocument()
  })

  it('shows the six generated geometry-verification views for the selected MASS', () => {
    const views = ['front', 'right', 'back', 'left', 'top', 'axon'].map((view) => ({
      view,
      preview_url: `/design/maas/single-executions/mass-fast/elevation/${view}/`,
      sha256: view.repeat(8),
    }))
    const passport = {
      status: 'needs_evidence',
      stages: [],
      activation_graph: {
        nodes: [{
          id: 'elevation:result',
          kind: 'elevation_result',
          status: 'generated',
          evidence: {
            artifact_exists: true,
            view_count: 6,
            views,
          },
        }],
        edges: [],
      },
    } as unknown as MassExecutionPassport

    render(
      <ExecutedMassEvidence
        archive={archive}
        mass={mass}
        passport={passport}
        passportError=""
        onExecute={vi.fn()}
        executionState="complete"
        executionError=""
        onVlmReview={vi.fn()}
        vlmReviewState="idle"
        vlmReviewError=""
      />,
    )

    expect(screen.getByText('6-VIEW GEOMETRY VERIFICATION · 6 VIEWS')).toBeInTheDocument()
    expect(screen.getByAltText('MASS 01 front elevation')).toHaveAttribute(
      'src',
      '/design/maas/single-executions/mass-fast/elevation/front/',
    )
    expect(screen.getAllByRole('img')).toHaveLength(7)
  })

  it('marks an incomplete or duplicated geometry view set without a six-view claim', () => {
    const views = ['front', 'right', 'back', 'left', 'front'].map((view, index) => ({
      view,
      preview_url: `/design/maas/single-executions/mass-fast/elevation/${view}-${index}/`,
      sha256: `${view}-${index}`.repeat(8),
    }))
    const passport = {
      status: 'needs_evidence',
      stages: [],
      activation_graph: {
        nodes: [{
          id: 'elevation:result',
          kind: 'elevation_result',
          status: 'generated',
          evidence: {
            artifact_exists: true,
            view_count: 5,
            views,
          },
        }],
        edges: [],
      },
    } as unknown as MassExecutionPassport

    render(
      <ExecutedMassEvidence
        archive={archive}
        mass={mass}
        passport={passport}
        passportError=""
        onExecute={vi.fn()}
        executionState="complete"
        executionError=""
        onVlmReview={vi.fn()}
        vlmReviewState="idle"
        vlmReviewError=""
      />,
    )

    expect(screen.getByText('GEOMETRY VIEW EVIDENCE INCOMPLETE · 5 / 6 VIEWS')).toBeInTheDocument()
    expect(screen.queryByText(/6-VIEW GEOMETRY VERIFICATION/)).not.toBeInTheDocument()
  })
})
