import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import {
  CreativeMassFilters,
  filterCreativeMassCards,
  type CreativeMassFilterState,
} from '../../../src/design/components/book-language-flow/CreativeMassFilters'
import type { CreativeMassCard } from '../../../src/design/lib/language-system-types'


const cards = [
  {
    selectionKey: 'run/a/p1/g1',
    portfolioRunId: 'run',
    candidateId: 'a',
    programHash: 'p1',
    geometryHash: 'g1',
    renderUrl: '/a.png',
    family: 'interlocking_tilted_discs',
    formClass: 'disc',
    capacityBand: 'maximum_target',
    storeys: 5,
    legalStatus: 'not_evaluated',
    morphologyDistance: 0.1,
  },
  {
    selectionKey: 'run/b/p2/g2',
    portfolioRunId: 'run',
    candidateId: 'b',
    programHash: 'p2',
    geometryHash: 'g2',
    renderUrl: '/b.png',
    family: 'long_span_bridge',
    formClass: 'span',
    capacityBand: 'balanced',
    storeys: 4,
    legalStatus: 'not_evaluated',
    morphologyDistance: 0.2,
  },
] satisfies CreativeMassCard[]

describe('CreativeMassFilters', () => {
  it('filters all four facets without changing selection identity', () => {
    const filters: CreativeMassFilterState = {
      family: 'interlocking_tilted_discs',
      capacityBand: 'maximum_target',
      storeys: '5',
      legalStatus: 'not_evaluated',
    }

    const filtered = filterCreativeMassCards(cards, filters)

    expect(filtered).toHaveLength(1)
    expect(filtered[0].selectionKey).toBe('run/a/p1/g1')
  })

  it('emits a family filter change using accessible controls', () => {
    const onChange = vi.fn()
    render(
      <CreativeMassFilters
        cards={cards}
        value={{
          family: '',
          capacityBand: '',
          storeys: '',
          legalStatus: '',
        }}
        onChange={onChange}
      />,
    )

    fireEvent.change(screen.getByLabelText(/family/i), {
      target: { value: 'interlocking_tilted_discs' },
    })

    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({
      family: 'interlocking_tilted_discs',
    }))
  })
})
