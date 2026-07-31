import { create } from 'zustand'
import type { FontScaleState } from './font-scale.types'
import {
  FONT_SCALE_DEFAULT,
  FONT_SCALE_MIN,
  FONT_SCALE_MAX,
  FONT_SCALE_STORAGE_KEY,
} from './font-scale.constants'

function clamp(value: number): number {
  return Math.min(FONT_SCALE_MAX, Math.max(FONT_SCALE_MIN, value))
}

function loadScale(): number {
  try {
    const stored = localStorage.getItem(FONT_SCALE_STORAGE_KEY)
    if (stored) {
      const parsed = parseFloat(stored)
      if (!isNaN(parsed)) return clamp(parsed)
    }
  } catch { /* ignore */ }
  return FONT_SCALE_DEFAULT
}

function applyScale(scale: number): void {
  document.documentElement.style.fontSize = `${scale * 100}%`
}

export const useFontScaleStore = create<FontScaleState>((set) => {
  const initial = loadScale()
  // Apply immediately on creation
  applyScale(initial)

  return {
    scale: initial,
    setScale: (scale: number) => {
      const clamped = clamp(Number(scale.toFixed(2)))
      localStorage.setItem(FONT_SCALE_STORAGE_KEY, String(clamped))
      applyScale(clamped)
      set({ scale: clamped })
    },
    reset: () => {
      localStorage.removeItem(FONT_SCALE_STORAGE_KEY)
      applyScale(FONT_SCALE_DEFAULT)
      set({ scale: FONT_SCALE_DEFAULT })
    },
  }
})
