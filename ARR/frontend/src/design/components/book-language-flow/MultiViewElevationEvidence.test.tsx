import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import type { MultiViewElevationEvidence as Evidence } from './multi-view-elevation';
import { MultiViewElevationEvidence } from './MultiViewElevationEvidence';

describe('MultiViewElevationEvidence', () => {
  it('renders four creative facades and the joint consistency result', () => {
    const proposal = {
      status: 'accepted',
      strategyId: 'stone-grid',
      primarySystem: 'stone and glass',
      views: ['front', 'right', 'back', 'left'].map((view) => ({
        view,
        previewUrl: `/creative-${view}.png`,
        sha256: `${view}-hash`,
        provider: 'gpt-image',
        model: 'gpt-image-2',
      })),
      deterministicStatus: 'passed',
      criticStatus: 'passed',
      criticResponseId: 'response-one',
      issues: [],
      paidRequestAttemptCount: 7,
      retryCount: 0,
    } as Evidence;

    render(
      <MultiViewElevationEvidence
        massLabel="MASS 03"
        proposal={proposal}
      />,
    );

    expect(screen.getAllByRole('img')).toHaveLength(4);
    expect(screen.getByText('4 / 4 CREATIVE FACADES')).toBeTruthy();
    expect(screen.getByText('JOINT CONSISTENCY PASS')).toBeTruthy();
    expect(screen.getByText('7 PAID ATTEMPTS · 0 TRANSPORT RETRIES')).toBeTruthy();
    expect(screen.getByText(/NOT GEOMETRY \/ LEGAL AUTHORITY/)).toBeTruthy();
  });
});
