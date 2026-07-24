import { describe, expect, it } from 'vitest';

import { executionActionCopy, executionRunCopy } from './execution-mode';

describe('MASS execution mode copy', () => {
  it('never presents an exact AST replay as a new generation', () => {
    expect(executionActionCopy()).toEqual({
      label: 'REPLAY EXACT AST',
      detail: 'SAME GEOMETRY PROGRAM · NEW EXECUTION EVIDENCE',
    });
    expect(executionRunCopy('exact_replay')).toBe('EXACT REPLAY');
  });

  it('identifies a genuinely synthesized run separately', () => {
    expect(executionRunCopy('fresh_synthesis')).toBe('NEW SYNTHESIS');
  });
});
