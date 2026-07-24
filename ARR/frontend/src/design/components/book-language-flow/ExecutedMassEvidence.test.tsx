import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type {
  ExecutedMassManifest,
  ExecutedMassRecord,
  MassExecutionPassport,
} from '../../lib/language-system-types';
import { ExecutedMassEvidence } from './ExecutedMassEvidence';

describe('ExecutedMassEvidence', () => {
  it('presents the architectural render before technical elevation evidence', () => {
    const mass = {
      index: 1,
      variant_id: 'mass-one',
      label: 'Radial common hub',
      geometry_hash: 'geometry-one',
      program_hash: 'program-one',
      preview_url: '/mass-one.png',
      execution_mode: 'fresh_synthesis',
      hard_pass: true,
      operation_label: 'radial_array -> union',
      book_principle_id: 'book:operative:merge',
      book_scope: '1/1',
      program_label: 'radial',
      program_type: 'radial',
      capacity_alternative_id: '',
      capacity_target_utilization: null,
      capacity_achieved_utilization: null,
      far_pct: null,
      geometry_ready: true,
      node_count: 7,
      dsl: 'mass result = union(hub, radial_array(wing))',
    } as unknown as ExecutedMassRecord;
    const archive = {
      selected_run_id: 'single-execution:mass-one',
      run_id: 'single-execution:mass-one',
      pnu: '',
    } as unknown as ExecutedMassManifest;
    const passport = {
      program_hash: 'program-one',
      geometry_hash: 'geometry-one',
      status: 'passed',
      stages: [
        { id: 'vlm', status: 'not_evaluated', evidence: {} },
        { id: 'selector', status: 'passed', evidence: {} },
      ],
      activation_graph: {
        nodes: [{
          id: 'elevation:result',
          status: 'generated',
          evidence: {
            artifact_exists: true,
            views: [{
              view: 'front',
              preview_url: '/front.png',
              sha256: 'front-hash',
            }],
          },
        }],
        edges: [],
      },
      elevation_evidence: {
        image_proposal: {
          status: 'complete',
          identity: {
            execution_id: 'mass-one',
            program_hash: 'program-one',
            geometry_hash: 'geometry-one',
          },
          strategy: {
            strategy_id: 'render-strategy',
            primary_system: 'stone and glass',
          },
          presentation: {
            kind: 'architectural_render_sheet',
            authority: 'generated_design_proposal',
          },
          provider: 'gpt-image',
          provider_metadata: {
            model: 'gpt-image-2',
            roof_semantic_guard: {
              status: 'applied',
              changed_pixel_count: 42,
            },
          },
          request_count: 1,
          retry_count: 0,
          artifact: {
            preview_url: '/render.png',
            sha256: 'render-hash',
          },
        },
      },
    } as unknown as MassExecutionPassport;

    const { container } = render(
      <ExecutedMassEvidence
        archive={archive}
        mass={mass}
        passport={passport}
        passportError=""
        onExecute={vi.fn()}
        executionState="idle"
        executionError=""
        onVlmReview={vi.fn()}
        vlmReviewState="idle"
        vlmReviewError=""
      />,
    );

    const renderHeading = screen.getByText(/ARCHITECTURAL RENDER AGENT/);
    const elevationHeading = screen.getByText(/6-VIEW GEOMETRY VERIFICATION/);
    expect(screen.getByText(/ACTUAL COMPILER MASS/)).toBeTruthy();
    expect(screen.getByText(/NOT GEOMETRY \/ LEGAL AUTHORITY/)).toBeTruthy();
    expect(screen.getByText(/1 REQUEST · 0 RETRIES/)).toBeTruthy();
    expect(renderHeading.compareDocumentPosition(elevationHeading)
      & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(
      container
        .querySelector('.executed-mass-evidence__proposal img')
        ?.getAttribute('src'),
    ).toBe('/render.png');
  });
});
