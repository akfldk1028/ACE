import { describe, expect, it } from 'vitest';

import { extractElevationProposal } from './elevation-proposal';

const proposal = {
  status: 'complete',
  identity: {
    execution_id: 'mass-one',
    program_hash: 'program-one',
    geometry_hash: 'geometry-one',
    final_geometry_hash: 'final-one',
    final_legal_geometry_hash: 'final-one',
    visual_hash: 'visual-one',
    floor_capacity_plan_hash: 'floor-plan-one',
    legal_floor_field_hash: 'legal-field-one',
    candidate_actual_gfa_stop_hash: 'actual-stop-one',
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
      final_legal_geometry_hash: 'final-one',
      visual_hash: 'visual-one',
      floor_capacity_plan_hash: 'floor-plan-one',
      legal_floor_field_hash: 'legal-field-one',
      candidate_actual_gfa_stop_hash: 'actual-stop-one',
      elevation_evidence: { image_proposal: proposal },
    };

    expect(extractElevationProposal(passport, {
      executionId: 'mass-one',
      programHash: 'program-one',
      geometryHash: 'geometry-one',
      finalGeometryHash: 'final-one',
      visualHash: 'visual-one',
      floorCapacityPlanHash: 'floor-plan-one',
      legalFloorFieldHash: 'legal-field-one',
      actualGfaStopHash: 'actual-stop-one',
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
      final_legal_geometry_hash: 'final-one',
      visual_hash: 'visual-one',
      floor_capacity_plan_hash: 'floor-plan-one',
      legal_floor_field_hash: 'legal-field-one',
      candidate_actual_gfa_stop_hash: 'actual-stop-one',
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
      finalGeometryHash: 'final-one',
      visualHash: 'visual-one',
      floorCapacityPlanHash: 'floor-plan-one',
      legalFloorFieldHash: 'legal-field-one',
      actualGfaStopHash: 'actual-stop-one',
    })).toBeNull();
  });

  it('rejects a proposal copied from a different floor capacity plan', () => {
    const passport = {
      program_hash: 'program-one',
      geometry_hash: 'geometry-one',
      final_legal_geometry_hash: 'final-one',
      visual_hash: 'visual-one',
      floor_capacity_plan_hash: 'floor-plan-one',
      legal_floor_field_hash: 'legal-field-one',
      candidate_actual_gfa_stop_hash: 'actual-stop-one',
      elevation_evidence: {
        image_proposal: {
          ...proposal,
          identity: {
            ...proposal.identity,
            floor_capacity_plan_hash: 'floor-plan-two',
          },
        },
      },
    };

    expect(extractElevationProposal(passport, {
      executionId: 'mass-one',
      programHash: 'program-one',
      geometryHash: 'geometry-one',
      finalGeometryHash: 'final-one',
      visualHash: 'visual-one',
      floorCapacityPlanHash: 'floor-plan-one',
      legalFloorFieldHash: 'legal-field-one',
      actualGfaStopHash: 'actual-stop-one',
    })).toBeNull();
  });

  it('rejects a proposal copied from another legal field', () => {
    const passport = {
      program_hash: 'program-one',
      geometry_hash: 'geometry-one',
      final_legal_geometry_hash: 'final-one',
      visual_hash: 'visual-one',
      floor_capacity_plan_hash: 'floor-plan-one',
      legal_floor_field_hash: 'legal-field-one',
      candidate_actual_gfa_stop_hash: 'actual-stop-one',
      elevation_evidence: {
        image_proposal: {
          ...proposal,
          identity: {
            ...proposal.identity,
            legal_floor_field_hash: 'legal-field-stale',
          },
        },
      },
    };

    expect(extractElevationProposal(passport, {
      executionId: 'mass-one',
      programHash: 'program-one',
      geometryHash: 'geometry-one',
      finalGeometryHash: 'final-one',
      visualHash: 'visual-one',
      floorCapacityPlanHash: 'floor-plan-one',
      legalFloorFieldHash: 'legal-field-one',
      actualGfaStopHash: 'actual-stop-one',
    })).toBeNull();
  });

  it('rejects a proposal copied from another actual GFA stop', () => {
    const passport = {
      program_hash: 'program-one',
      geometry_hash: 'geometry-one',
      final_legal_geometry_hash: 'final-one',
      visual_hash: 'visual-one',
      floor_capacity_plan_hash: 'floor-plan-one',
      legal_floor_field_hash: 'legal-field-one',
      candidate_actual_gfa_stop_hash: 'actual-stop-one',
      elevation_evidence: {
        image_proposal: {
          ...proposal,
          identity: {
            ...proposal.identity,
            candidate_actual_gfa_stop_hash: 'actual-stop-stale',
          },
        },
      },
    };

    expect(extractElevationProposal(passport, {
      executionId: 'mass-one',
      programHash: 'program-one',
      geometryHash: 'geometry-one',
      finalGeometryHash: 'final-one',
      visualHash: 'visual-one',
      floorCapacityPlanHash: 'floor-plan-one',
      legalFloorFieldHash: 'legal-field-one',
      actualGfaStopHash: 'actual-stop-one',
    })).toBeNull();
  });
});
