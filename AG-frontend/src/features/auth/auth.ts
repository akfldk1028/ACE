// Auth helpers - MVP: simple local user, expandable to Supabase/Clerk
export interface User {
  id: string
  email: string
  name: string
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

// Default guest user for MVP (no auth backend yet)
export const GUEST_USER: User = {
  id: 'guest',
  email: 'guestuser@gmail.com',
  name: 'Guest User',
  role: 'owner',
}
