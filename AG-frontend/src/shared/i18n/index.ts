// Initialize i18n on import
import './i18n.config'

export { useLanguage } from './i18n.hooks'
export { LOCALES, DEFAULT_LOCALE } from './i18n.constants'
export type { SupportedLocale } from './i18n.types'
