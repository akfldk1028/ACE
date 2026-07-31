import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { LanguageNetworkCanvas } from '../../../src/design/components/book-language-flow/LanguageNetworkCanvas'


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
})
