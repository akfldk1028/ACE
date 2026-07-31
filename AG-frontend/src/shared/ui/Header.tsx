import { useState, useRef, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/features/auth/authStore'
import { useLogin, useLogout } from '@/features/auth/useAuth'
import { Avatar } from '@/shared/ui'
import { Badge } from '@/shared/ui'
import { LogIn, LogOut, ChevronDown } from 'lucide-react'

export function Header() {
  const user = useAuthStore((s) => s.user)
  const authType = useAuthStore((s) => s.authType)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const login = useLogin()
  const logout = useLogout()
  const { t } = useTranslation()

  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown on outside click
  useEffect(() => {
    if (!dropdownOpen) return
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [dropdownOpen])

  const handleLogout = useCallback(() => {
    setDropdownOpen(false)
    logout()
  }, [logout])

  const showLoginButton = authType != null && authType !== 'none' && !isAuthenticated

  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-(--color-border-default) bg-(--color-surface-card)">
      <div className="flex items-center gap-2">
        <Badge variant="primary">{t('app.engine')}</Badge>
      </div>

      <div className="flex items-center gap-3">
        {showLoginButton ? (
          <button
            onClick={login}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md bg-(--color-accent-primary) text-white hover:opacity-90 transition-opacity focus:outline-none focus:ring-2 focus:ring-(--color-accent-primary)"
          >
            <LogIn className="w-4 h-4" />
            {t('auth.login')}
          </button>
        ) : user ? (
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen((p) => !p)}
              className="flex items-center gap-2 rounded-md px-2 py-1 hover:bg-(--color-background-secondary) transition-colors focus:outline-none focus:ring-2 focus:ring-(--color-accent-primary)"
              aria-expanded={dropdownOpen}
              aria-haspopup="true"
            >
              <span className="text-body-small text-(--color-text-secondary)">
                {user.name}
              </span>
              <Avatar name={user.name} src={user.avatar_url} size="sm" />
              {authType !== 'none' && (
                <ChevronDown className="w-3.5 h-3.5 text-(--color-text-tertiary)" />
              )}
            </button>
            {dropdownOpen && authType !== 'none' && (
              <div className="absolute right-0 mt-1 w-48 rounded-md border border-(--color-border-default) bg-(--color-surface-card) shadow-lg z-50">
                <div className="px-3 py-2 border-b border-(--color-border-default)">
                  <p className="text-sm font-medium truncate">{user.name}</p>
                  {user.email && (
                    <p className="text-xs text-(--color-text-tertiary) truncate">{user.email}</p>
                  )}
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-(--color-text-secondary) hover:bg-(--color-background-secondary) transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  {t('auth.logout')}
                </button>
              </div>
            )}
          </div>
        ) : null}
      </div>
    </header>
  )
}
