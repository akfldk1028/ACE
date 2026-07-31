// Auth helpers - supports guest mode + OAuth (GitHub/MSAL/Firebase)
export interface User {
  id: string
  email: string | null
  name: string
  avatar_url?: string
  provider?: string
  roles?: string[]
  orgId?: string
  role: 'owner' | 'admin' | 'member'
}

const STORAGE_KEY = 'platform-user'

export function getStoredUser(): User | null {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored) {
    try {
      return JSON.parse(stored)
    } catch {
      return null
    }
  }
  return null
}

export function setStoredUser(user: User) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
}

export function clearStoredUser() {
  localStorage.removeItem(STORAGE_KEY)
}

// Default guest user (used when auth type is "none")
export const GUEST_USER: User = {
  id: 'guest',
  email: 'guestuser@gmail.com',
  name: 'Guest User',
  role: 'owner',
}
