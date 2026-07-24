import { describe, expect, it } from 'vitest';

import { extractElevationProposal } from './elevation-proposal';

const proposal = {
  status: 'complete',
  identity: {
    execution_id: 'mass-one',
    program_hash: 'program-one',
    geometry_hash: 'geometry-one',
  },
  strategy: {
    strategy_id: 'vertical-fins-glass',
    primary_system: 'high-performance glass with vertical metal fins',
  },
  provider: 'gpt-image',
  provider_metadata: {
    model: 'gpt-image-test',
    roof_semantic_guard: {
      status: 'applied',
      changed_pixel_count: 42,
    },
  },
  presentation: {
    kind: 'architectural_render_sheet',
    authority: 'generated_design_proposal',
  },
  request_count: 1,
  retry_count: 0,
  artifact: {
    preview_url: '/design/maas/single-executions/mass-one/elevation-proposals/alt-01/',
    sha256: 'abc123',
  },
};

describe('extractElevationProposal', () => {
  it('accepts only the proposal bound to the selected MASS identity', () => {
    const passport = {
      program_hash: 'program-one',
      geometry_hash: 'geometry-one',
      elevation_evidence: { image_proposal: proposal },
    };

    expect(extractElevationProposal(passport, {
      executionId: 'mass-one',
      programHash: 'program-one',
      geometryHash: 'geometry-one',
    })).toMatchObject({
      status: 'complete',
      previewUrl: proposal.artifact.preview_url,
      model: 'gpt-image-test',
      strategyId: 'vertical-fins-glass',
      presentationKind: 'architectural_render_sheet',
      authority: 'generated_design_proposal',
      requestCount: 1,
      retryCount: 0,
      roofGuardStatus: 'applied',
      roofGuardChangedPixels: 42,
    });
  });

  it('rejects a proposal copied from a different geometry', () => {
    const passport = {
      program_hash: 'program-one',
      geometry_hash: 'geometry-one',
      elevation_evidence: {
        image_proposal: {
          ...proposal,
          identity: { ...proposal.identity, geometry_hash: 'geometry-two' },
        },
      },
    };

    expect(extractElevationProposal(passport, {
      executionId: 'mass-one',
      programHash: 'program-one',
      geometryHash: 'geometry-one',
    })).toBeNull();
  });
});
