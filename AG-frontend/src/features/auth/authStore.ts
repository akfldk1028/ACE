import { create } from 'zustand'
import type { User } from './auth'
import { getStoredUser, setStoredUser, clearStoredUser, GUEST_USER } from './auth'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  login: (user?: User) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: getStoredUser() ?? GUEST_USER,
  isAuthenticated: true, // MVP: always authenticated as guest

  login: (user?: User) => {
    const u = user ?? GUEST_USER
    setStoredUser(u)
    set({ user: u, isAuthenticated: true })
  },

  logout: () => {
    clearStoredUser()
    set({ user: null, isAuthenticated: false })
  },
}))
