import type { SupportedLocale } from './i18n.types'

export const LOCALES: { code: SupportedLocale; label: string }[] = [
  { code: 'en-US', label: 'English' },
  { code: 'ko-KR', label: '한국어' },
]

export const DEFAULT_LOCALE: SupportedLocale = 'en-US'
export const LOCALE_STORAGE_KEY = 'ag-frontend-locale'
