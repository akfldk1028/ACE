import { describe, it, expect, beforeEach, vi } from 'vitest'

// Mock localStorage and document before importing store
const mockStorage = new Map<string, string>()
vi.stubGlobal('localStorage', {
  getItem: (k: string) => mockStorage.get(k) ?? null,
  setItem: (k: string, v: string) => mockStorage.set(k, v),
  removeItem: (k: string) => mockStorage.delete(k),
})

// Mock document.documentElement.style
const mockStyle = { fontSize: '' }
vi.stubGlobal('document', {
  documentElement: { style: mockStyle },
})

describe('FontScale store', () => {
  beforeEach(() => {
    mockStorage.clear()
    mockStyle.fontSize = ''
  })

  it('defaults to scale 1', async () => {
    // Dynamic import to reset module state
    const { useFontScaleStore } = await import('./font-scale.store')
    expect(useFontScaleStore.getState().scale).toBe(1)
  })

  it('clamps values to min/max', async () => {
    const { useFontScaleStore } = await import('./font-scale.store')
    useFontScaleStore.getState().setScale(0.5) // Below min 0.8
    expect(useFontScaleStore.getState().scale).toBe(0.8)

    useFontScaleStore.getState().setScale(2.0) // Above max 1.5
    expect(useFontScaleStore.getState().scale).toBe(1.5)
  })

  it('persists to localStorage', async () => {
    const { useFontScaleStore } = await import('./font-scale.store')
    useFontScaleStore.getState().setScale(1.2)
    expect(mockStorage.get('ag-frontend-font-scale')).toBe('1.2')
  })

  it('applies scale to document root', async () => {
    const { useFontScaleStore } = await import('./font-scale.store')
    useFontScaleStore.getState().setScale(1.2)
    expect(mockStyle.fontSize).toBe('120%')
  })

  it('reset restores default', async () => {
    const { useFontScaleStore } = await import('./font-scale.store')
    useFontScaleStore.getState().setScale(1.3)
    useFontScaleStore.getState().reset()
    expect(useFontScaleStore.getState().scale).toBe(1)
    expect(mockStyle.fontSize).toBe('100%')
  })
})
