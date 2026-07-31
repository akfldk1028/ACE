import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import enUS from './locales/en-US.json'
import koKR from './locales/ko-KR.json'
import { DEFAULT_LOCALE, LOCALE_STORAGE_KEY } from './i18n.constants'

function detectLocale(): string {
  // 1. Check localStorage
  const stored = localStorage.getItem(LOCALE_STORAGE_KEY)
  if (stored) return stored
  // 2. Browser language
  const nav = navigator.language
  if (nav.startsWith('ko')) return 'ko-KR'
  return DEFAULT_LOCALE
}

i18n.use(initReactI18next).init({
  resources: {
    'en-US': { translation: enUS },
    'ko-KR': { translation: koKR },
  },
  lng: detectLocale(),
  fallbackLng: DEFAULT_LOCALE,
  interpolation: {
    escapeValue: false,
  },
})

export default i18n
