import { NavLink } from 'react-router'
import { cn } from '@/shared/lib/utils'
import {
  Bot,
  MessagesSquare,
  Wrench,
  Users,
  GalleryHorizontalEnd,
  Rocket,
  Settings,
  Sun,
  Moon,
} from 'lucide-react'
import { useTheme } from '@/shared/theme'

// Match AutoGen Studio navigation structure exactly
const navItems = [
  { path: '/build', icon: Bot, label: 'Team Builder' },
  { path: '/', icon: MessagesSquare, label: 'Playground' },
  { path: '/mcp', icon: Wrench, label: 'MCP' },
  { path: '/agents', icon: Users, label: 'A2A Agents' },
  { path: '/gallery', icon: GalleryHorizontalEnd, label: 'Gallery' },
  { path: '/deploy', icon: Rocket, label: 'Deploy' },
]

export function Sidebar() {
  const { mode, toggleMode } = useTheme()

  return (
    <aside aria-label="Main navigation" className="w-60 h-screen flex flex-col bg-(--color-surface-card) border-r border-(--color-border-default)">
      <div className="p-5 border-b border-(--color-border-default)">
        <h1 className="text-heading-medium text-(--color-text-primary) font-bold tracking-tight">
          AG Frontend
        </h1>
        <p className="text-body-small text-(--color-text-tertiary) mt-1">
          Agent Orchestration
        </p>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {navItems.map(({ path, icon: Icon, label }) => (
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
            {label}
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
          Settings
        </NavLink>
        <button
          onClick={toggleMode}
          className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm text-(--color-text-secondary) hover:bg-(--color-background-secondary) transition-colors"
        >
          {mode === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          {mode === 'dark' ? 'Light Mode' : 'Dark Mode'}
        </button>
      </div>
    </aside>
  )
}
