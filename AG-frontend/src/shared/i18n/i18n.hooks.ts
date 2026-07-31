import { useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import type { SupportedLocale } from './i18n.types'
import { LOCALE_STORAGE_KEY } from './i18n.constants'

/**
 * Hook to get and switch the current language.
 * Persists to localStorage.
 */
export function useLanguage() {
  const { i18n } = useTranslation()

  const currentLocale = i18n.language as SupportedLocale

  const setLocale = useCallback(
    (locale: SupportedLocale) => {
      i18n.changeLanguage(locale)
      localStorage.setItem(LOCALE_STORAGE_KEY, locale)
    },
    [i18n],
  )

  return { currentLocale, setLocale }
}
