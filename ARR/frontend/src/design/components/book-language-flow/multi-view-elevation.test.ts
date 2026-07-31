import { describe, expect, it } from 'vitest';

import { extractMultiViewElevation } from './multi-view-elevation';

const identity = {
  execution_id: 'mass-one',
  program_hash: 'program-one',
  geometry_hash: 'geometry-one',
};

function proposal() {
  return {
    status: 'accepted',
    identity,
    strategy: {
      strategy_id: 'stone-grid',
      primary_system: 'stone and glass',
    },
    artifacts: Object.fromEntries(
      ['front', 'right', 'back', 'left'].map((view) => [
        view,
        {
          view,
          identity: { ...identity, view },
          artifact: {
            preview_url: `/creative-${view}.png`,
            sha256: `${view}-hash`,
          },
          provider: 'gpt-image',
          provider_metadata: { model: 'gpt-image-2' },
        },
      ]),
    ),
    deterministic_gate: {
      status: 'passed',
      failed_views: [],
      issues: [],
    },
    critic: {
      status: 'passed',
      failed_views: [],
      issues: [],
      response_id: 'response-one',
    },
    paid_request_attempt_count: 7,
    retry_count: 0,
  };
}

describe('extractMultiViewElevation', () => {
  it('extracts exactly four identity-bound creative facade views', () => {
    const result = extractMultiViewElevation({
      program_hash: 'program-one',
      geometry_hash: 'geometry-one',
      elevation_evidence: { multi_view_proposal: proposal() },
    }, {
      executionId: 'mass-one',
      programHash: 'program-one',
      geometryHash: 'geometry-one',
    });

    expect(result?.status).toBe('accepted');
    expect(result?.views.map((view) => view.view)).toEqual([
      'front', 'right', 'back', 'left',
    ]);
    expect(result?.paidRequestAttemptCount).toBe(7);
  });

  it('rejects a multi-view proposal from another geometry', () => {
    expect(extractMultiViewElevation({
      program_hash: 'program-one',
      geometry_hash: 'geometry-one',
      elevation_evidence: { multi_view_proposal: proposal() },
    }, {
      executionId: 'mass-one',
      programHash: 'program-one',
      geometryHash: 'geometry-two',
    })).toBeNull();
  });
});
