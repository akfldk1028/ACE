import { useEffect, useCallback, useRef } from 'react'
import { useAuthStore } from './authStore'
import { authAPI } from '@/shared/api/client'
import type { User } from './auth'

/**
 * useAuthInit - call once at app startup (MainLayout).
 * 1. Queries GET /api/auth/type → stores in authStore
 * 2. If token exists: queries GET /api/auth/me → stores user
 * 3. If 401: clears expired token
 */
export function useAuthInit() {
  const setAuthType = useAuthStore((s) => s.setAuthType)
  const setUser = useAuthStore((s) => s.setUser)
  const logout = useAuthStore((s) => s.logout)
  const token = useAuthStore((s) => s.token)
  const initialized = useAuthStore((s) => s.initialized)
  const setInitialized = useAuthStore((s) => s.setInitialized)
  const ran = useRef(false)

  useEffect(() => {
    if (ran.current || initialized) return
    ran.current = true

    async function init() {
      try {
        const { type } = await authAPI.getType()
        setAuthType(type)

        if (token) {
          try {
            const me = await authAPI.getMe()
            setUser({
              id: me.id,
              name: me.name,
              email: me.email,
              avatar_url: me.avatar_url,
              provider: me.provider,
              roles: me.roles,
              role: me.roles?.includes('admin') ? 'admin' : 'member',
            })
          } catch (err: unknown) {
            // 401 = expired token
            if (err && typeof err === 'object' && 'status' in err && (err as { status: number }).status === 401) {
              logout()
            }
          }
        }
      } catch {
        // Auth endpoint not available → default to "none" (guest mode)
        setAuthType('none')
      } finally {
        setInitialized()
      }
    }

    init()
  }, [setAuthType, setUser, logout, token, initialized, setInitialized])
}

/**
 * useLogin - opens OAuth popup flow.
 * 1. GET /api/auth/login-url → popup
 * 2. Listen for postMessage → loginSuccess(token, user)
 */
export function useLogin() {
  const loginSuccess = useAuthStore((s) => s.loginSuccess)

  return useCallback(async () => {
    try {
      const { login_url } = await authAPI.getLoginUrl()
      const popup = window.open(login_url, 'oauth-popup', 'width=600,height=700')
      if (!popup) return

      const handler = (event: MessageEvent) => {
        if (event.origin !== window.location.origin) return
        const data = event.data
        if (data?.type === 'auth_callback' && data.token && data.user) {
          const u = data.user as { id: string; name: string; email: string | null; avatar_url?: string; provider: string; roles: string[] }
          const user: User = {
            id: u.id,
            name: u.name,
            email: u.email,
            avatar_url: u.avatar_url,
            provider: u.provider,
            roles: u.roles,
            role: u.roles?.includes('admin') ? 'admin' : 'member',
          }
          loginSuccess(data.token, user)
          window.removeEventListener('message', handler)
          popup.close()
        }
      }
      window.addEventListener('message', handler)
    } catch {
      // Login URL not available
    }
  }, [loginSuccess])
}

/**
 * useLogout - clears auth state
 */
export function useLogout() {
  const logout = useAuthStore((s) => s.logout)
  return logout
}
