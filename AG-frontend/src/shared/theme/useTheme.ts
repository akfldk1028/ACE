import { create } from 'zustand'
import type { ThemeConfig, ColorTheme, Mode } from './types'
import { COLOR_THEMES } from './constants'

function loadStoredConfig(): ThemeConfig {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('platform-theme-config')
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        const themeExists = COLOR_THEMES.some(t => t.id === parsed.colorTheme)
        if (themeExists) return parsed
        return { colorTheme: 'default' as ColorTheme, mode: parsed.mode || 'light' }
      } catch { /* use default */ }
    }
    return {
      colorTheme: 'default' as ColorTheme,
      mode: window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light',
    }
  }
  return { colorTheme: 'default', mode: 'light' }
}

function applyTheme(config: ThemeConfig) {
  const root = document.documentElement
  if (config.colorTheme === 'default') {
    root.removeAttribute('data-theme')
  } else {
    root.setAttribute('data-theme', config.colorTheme)
  }
  if (config.mode === 'dark') {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }
  localStorage.setItem('platform-theme-config', JSON.stringify(config))
}

interface ThemeState {
  colorTheme: ColorTheme
  mode: Mode
  themes: typeof COLOR_THEMES
  setColorTheme: (colorTheme: ColorTheme) => void
  setMode: (mode: Mode) => void
  toggleMode: () => void
}

export const useTheme = create<ThemeState>((set, get) => {
  const initial = loadStoredConfig()
  // Apply theme immediately on store creation
  if (typeof window !== 'undefined') {
    applyTheme(initial)
  }

  return {
    colorTheme: initial.colorTheme,
    mode: initial.mode,
    themes: COLOR_THEMES,

    setColorTheme: (colorTheme) => {
      const config = { colorTheme, mode: get().mode }
      applyTheme(config)
      set({ colorTheme })
    },

    setMode: (mode) => {
      const config = { colorTheme: get().colorTheme, mode }
      applyTheme(config)
      set({ mode })
    },

    toggleMode: () => {
      const newMode: Mode = get().mode === 'light' ? 'dark' : 'light'
      const config: ThemeConfig = { colorTheme: get().colorTheme, mode: newMode }
      applyTheme(config)
      set({ mode: newMode })
    },
  }
})
