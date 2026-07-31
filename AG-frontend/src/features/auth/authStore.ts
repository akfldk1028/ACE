import { create } from 'zustand'
import type { User } from './auth'
import { getStoredUser, setStoredUser, clearStoredUser, GUEST_USER } from './auth'

const TOKEN_KEY = 'auth_token'

interface AuthState {
  user: User | null
  authType: string | null  // 'none' | 'github' | 'msal' | 'firebase'
  token: string | null
  isAuthenticated: boolean
  initialized: boolean
  setAuthType: (type: string) => void
  loginSuccess: (token: string, user: User) => void
  logout: () => void
  setUser: (user: User) => void
  setInitialized: () => void
}

function loadToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export const useAuthStore = create<AuthState>((set) => {
  const token = loadToken()
  const storedUser = getStoredUser()
  return {
    user: storedUser ?? GUEST_USER,
    authType: null,
    token,
    isAuthenticated: token != null || storedUser != null,
    initialized: false,

    setAuthType: (type: string) => {
      set((prev) => {
        // If auth is disabled, ensure guest user is set
        if (type === 'none' && !prev.user) {
          setStoredUser(GUEST_USER)
          return { authType: type, user: GUEST_USER, isAuthenticated: true }
        }
        return { authType: type }
      })
    },

    loginSuccess: (token: string, user: User) => {
      localStorage.setItem(TOKEN_KEY, token)
      setStoredUser(user)
      set({ token, user, isAuthenticated: true })
    },

    logout: () => {
      localStorage.removeItem(TOKEN_KEY)
      clearStoredUser()
      set((prev) => {
        if (prev.authType === 'none') {
          setStoredUser(GUEST_USER)
          return { token: null, user: GUEST_USER, isAuthenticated: true }
        }
        return { token: null, user: null, isAuthenticated: false }
      })
    },

    setUser: (user: User) => {
      setStoredUser(user)
      set({ user, isAuthenticated: true })
    },

    setInitialized: () => set({ initialized: true }),
  }
})
