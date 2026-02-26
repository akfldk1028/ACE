import { NavLink } from 'react-router'
import { useTranslation } from 'react-i18next'
import { cn } from '@/shared/lib/utils'
import {
  Bot,
  MessagesSquare,
  Wrench,
  Users,
  GalleryHorizontalEnd,
  Clock,
  Rocket,
  MapPin,
  Settings,
  Sun,
  Moon,
} from 'lucide-react'
import { useTheme } from '@/shared/theme'

// Match AutoGen Studio navigation structure exactly
const navItems = [
  { path: '/build', icon: Bot, labelKey: 'nav.teamBuilder' },
  { path: '/', icon: MessagesSquare, labelKey: 'nav.playground' },
  { path: '/mcp', icon: Wrench, labelKey: 'nav.mcp' },
  { path: '/agents', icon: Users, labelKey: 'nav.agents' },
  { path: '/gallery', icon: GalleryHorizontalEnd, labelKey: 'nav.gallery' },
  { path: '/history', icon: Clock, labelKey: 'nav.history' },
  { path: '/deploy', icon: Rocket, labelKey: 'nav.deploy' },
  { path: '/land', icon: MapPin, labelKey: 'nav.land' },
]

export function Sidebar() {
  const { mode, toggleMode } = useTheme()
  const { t } = useTranslation()

  return (
    <aside aria-label="Main navigation" className="w-60 h-screen flex flex-col bg-(--color-surface-card) border-r border-(--color-border-default)">
      <div className="p-5 border-b border-(--color-border-default)">
        <h1 className="text-heading-medium text-(--color-text-primary) font-bold tracking-tight">
          {t('app.title')}
        </h1>
        <p className="text-body-small text-(--color-text-tertiary) mt-1">
          {t('app.subtitle')}
        </p>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {navItems.map(({ path, icon: Icon, labelKey }) => (
          <NavLink
            key={path}
            to={path}
            end={path === '/'}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-(--color-accent-primary-light) text-(--color-accent-primary)'
                  : 'text-(--color-text-secondary) hover:bg-(--color-background-secondary) hover:text-(--color-text-primary)'
              )
            }
          >
            <Icon className="w-5 h-5" />
            {t(labelKey)}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-(--color-border-default) space-y-1">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
              isActive
                ? 'bg-(--color-accent-primary-light) text-(--color-accent-primary)'
                : 'text-(--color-text-secondary) hover:bg-(--color-background-secondary) hover:text-(--color-text-primary)'
            )
          }
        >
          <Settings className="w-5 h-5" />
          {t('nav.settings')}
        </NavLink>
        <button
          onClick={toggleMode}
          className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm text-(--color-text-secondary) hover:bg-(--color-background-secondary) transition-colors"
        >
          {mode === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          {mode === 'dark' ? t('nav.lightMode') : t('nav.darkMode')}
        </button>
      </div>
    </aside>
  )
}
