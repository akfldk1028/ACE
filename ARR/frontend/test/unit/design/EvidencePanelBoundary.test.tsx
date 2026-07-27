import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { EvidencePanelBoundary } from '../../../src/design/components/book-language-flow/EvidencePanelBoundary'

function BrokenEvidence(): never {
  throw new Error('malformed historical passport')
}

describe('EvidencePanelBoundary', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('contains an evidence rendering failure without losing the surrounding route', () => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined)

    render(
      <main>
        <h1>MASS LANGUAGE SYSTEM</h1>
        <EvidencePanelBoundary resetKey="legacy-run:1">
          <BrokenEvidence />
        </EvidencePanelBoundary>
      </main>,
    )

    expect(screen.getByRole('heading', { name: 'MASS LANGUAGE SYSTEM' })).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('EVIDENCE PANEL UNAVAILABLE')
    expect(screen.getByText('The selected historical evidence could not be rendered.')).toBeInTheDocument()
  })
})
