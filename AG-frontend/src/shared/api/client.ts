// ============================================================
// API Client - Matches AutoGen Studio API 1:1
// Proxied via Vite: /api/* -> localhost:8081
// ============================================================

import type {
  Component,
  ComponentConfig,
  TeamConfig,
  Session,
  SessionRuns,
  Gallery,
  Settings,
} from '@/shared/types/datamodel'

// --------------- Config ---------------

const BASE_URL = '/api'
const FALLBACK_USER_ID = 'guestuser@gmail.com'

function getDefaultUserId(): string {
  try {
    const stored = localStorage.getItem('platform-user')
    if (stored) {
      const user = JSON.parse(stored)
      if (typeof user?.email === 'string' && user.email) return user.email
    }
  } catch { /* fall through */ }
  return FALLBACK_USER_ID
}

function getHeaders(): HeadersInit {
  const token = localStorage.getItem('auth_token')
  const headers: HeadersInit = { 'Content-Type': 'application/json' }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

// --------------- Error ---------------

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// --------------- Fetch Helper ---------------

export async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const { headers: extraHeaders, ...rest } = init ?? {}
  const res = await fetch(`${BASE_URL}${path}`, {
    ...rest,
    headers: { ...getHeaders(), ...(extraHeaders as Record<string, string>) },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new ApiError(
      body?.message ?? `${res.status} ${res.statusText}`,
      res.status,
    )
  }
  const json = await res.json()
  // AutoGen Studio wraps responses: { status: boolean, data: T, message?: string }
  if (json && typeof json === 'object' && 'status' in json && 'data' in json) {
    if (!json.status) {
      throw new ApiError(json.message ?? 'API error', res.status)
    }
    return json.data as T
  }
  return json as T
}

// --------------- Response Types ---------------

// DB model shape returned by AutoGen Studio (Team with id + component)
export interface TeamResponse {
  id: number
  user_id?: string
  created_at?: string
  updated_at?: string
  version?: number
  component: Component<TeamConfig> | null
}

export interface SessionResponse extends Session {}

export interface RunResponse {
  run_id: number
}

export interface HealthResponse {
  status: boolean
}

export interface VersionResponse {
  version: string
}

// --------------- Validation Types ---------------

export interface ValidationError {
  field: string
  error: string
  suggestion?: string
}

export interface ValidationResponse {
  is_valid: boolean
  errors: ValidationError[]
  warnings: ValidationError[]
}

export interface ComponentTestResult {
  status: boolean
  message: string
  data?: unknown
  logs: string[]
}

// --------------- Team API ---------------

export const teamAPI = {
  list: (userId: string = getDefaultUserId()) =>
    fetchJSON<TeamResponse[]>(`/teams/?user_id=${encodeURIComponent(userId)}`),

  get: (id: number, userId: string = getDefaultUserId()) =>
    fetchJSON<TeamResponse>(`/teams/${id}?user_id=${encodeURIComponent(userId)}`),

  create: (teamData: Record<string, unknown>, userId: string = getDefaultUserId()) =>
    fetchJSON<TeamResponse>('/teams/', {
      method: 'POST',
      body: JSON.stringify({ ...teamData, user_id: userId }),
    }),

  delete: (id: number, userId: string = getDefaultUserId()) =>
    fetchJSON<void>(`/teams/${id}?user_id=${encodeURIComponent(userId)}`, { method: 'DELETE' }),

  update: (id: number, component: unknown, userId: string = getDefaultUserId()) =>
    fetchJSON<TeamResponse>('/teams/', {
      method: 'POST',
      body: JSON.stringify({ id, user_id: userId, component }),
    }),
}

// --------------- Session API ---------------

export const sessionAPI = {
  list: (userId: string = getDefaultUserId()) =>
    fetchJSON<SessionResponse[]>(`/sessions/?user_id=${encodeURIComponent(userId)}`),

  get: (id: number, userId: string = getDefaultUserId()) =>
    fetchJSON<SessionResponse>(`/sessions/${id}?user_id=${encodeURIComponent(userId)}`),

  create: (sessionData: Partial<Session>, userId: string = getDefaultUserId()) =>
    fetchJSON<SessionResponse>('/sessions/', {
      method: 'POST',
      body: JSON.stringify({ ...sessionData, user_id: userId }),
    }),

  update: (id: number, sessionData: Partial<Session>, userId: string = getDefaultUserId()) =>
    fetchJSON<SessionResponse>(`/sessions/${id}?user_id=${encodeURIComponent(userId)}`, {
      method: 'PUT',
      body: JSON.stringify({ ...sessionData, id, user_id: userId }),
    }),

  getRuns: (sessionId: number, userId: string = getDefaultUserId()) =>
    fetchJSON<SessionRuns>(`/sessions/${sessionId}/runs?user_id=${encodeURIComponent(userId)}`),

  delete: (id: number, userId: string = getDefaultUserId()) =>
    fetchJSON<void>(`/sessions/${id}?user_id=${encodeURIComponent(userId)}`, { method: 'DELETE' }),
}

// --------------- Run API ---------------

export const runAPI = {
  create: (sessionId: number, userId: string = getDefaultUserId()) =>
    fetchJSON<RunResponse>('/runs/', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, user_id: userId }),
    }),
}

// --------------- Gallery API ---------------

export const galleryAPI = {
  list: (userId: string = getDefaultUserId()) =>
    fetchJSON<Gallery[]>(`/gallery/?user_id=${encodeURIComponent(userId)}`),

  get: (id: number, userId: string = getDefaultUserId()) =>
    fetchJSON<Gallery>(`/gallery/${id}?user_id=${encodeURIComponent(userId)}`),

  create: (galleryData: Partial<Gallery>, userId: string = getDefaultUserId()) =>
    fetchJSON<Gallery>('/gallery/', {
      method: 'POST',
      body: JSON.stringify({ ...galleryData, user_id: userId }),
    }),

  update: (id: number, galleryData: Partial<Gallery>, userId: string = getDefaultUserId()) =>
    fetchJSON<Gallery>(`/gallery/${id}?user_id=${encodeURIComponent(userId)}`, {
      method: 'PUT',
      body: JSON.stringify({ ...galleryData, user_id: userId }),
    }),

  delete: (id: number, userId: string = getDefaultUserId()) =>
    fetchJSON<void>(`/gallery/${id}?user_id=${encodeURIComponent(userId)}`, { method: 'DELETE' }),

  sync: async (url: string): Promise<Gallery> => {
    const res = await fetch(url, { headers: getHeaders() })
    if (!res.ok) throw new ApiError(`Failed to sync gallery from ${url}`, res.status)
    return res.json()
  },
}

// --------------- Validation API ---------------

export const validationAPI = {
  validate: (component: Component<ComponentConfig>) =>
    fetchJSON<ValidationResponse>('/validate/', {
      method: 'POST',
      body: JSON.stringify({ component }),
    }),

  test: (component: Component<ComponentConfig>, timeout: number = 60) =>
    fetchJSON<ComponentTestResult>('/validate/test', {
      method: 'POST',
      body: JSON.stringify({ component, timeout }),
    }),
}

// --------------- Settings API ---------------

export const settingsAPI = {
  get: (userId: string = getDefaultUserId()) =>
    fetchJSON<Settings>(`/settings/?user_id=${encodeURIComponent(userId)}`),

  update: (settings: Settings, userId: string = getDefaultUserId()) =>
    fetchJSON<Settings>('/settings/', {
      method: 'PUT',
      body: JSON.stringify({ ...settings, user_id: settings.user_id ?? userId }),
    }),
}

// --------------- Health / Version ---------------

export const healthAPI = {
  check: () => fetchJSON<HealthResponse>('/health'),
  version: () => fetchJSON<VersionResponse>('/version'),
}

// --------------- Auth API ---------------

export interface AuthUser {
  id: string
  name: string
  email: string | null
  avatar_url?: string
  provider: string
  roles: string[]
}

export const authAPI = {
  getType: () => fetchJSON<{ type: string }>('/auth/type'),
  getLoginUrl: () => fetchJSON<{ login_url: string }>('/auth/login-url'),
  getMe: () => fetchJSON<AuthUser>('/auth/me'),
}

// --------------- Legacy compat: single `api` object ---------------
// Used by existing hooks (TanStack Query). Matches old signatures.

export const api = {
  // Teams
  getTeams: () => teamAPI.list(),
  getTeam: (id: number) => teamAPI.get(id),
  createTeam: (team: Record<string, unknown>) => teamAPI.create(team),
  deleteTeam: (id: number) => teamAPI.delete(id),
  // Sessions
  getSessions: () => sessionAPI.list(),
  getSession: (id: number) => sessionAPI.get(id),
  createSession: (teamId: number) => sessionAPI.create({ team_id: teamId }),
  getSessionRuns: (sessionId: number) => sessionAPI.getRuns(sessionId),
  deleteSession: (id: number) => sessionAPI.delete(id),
  // Runs
  createRun: (sessionId: number) => runAPI.create(sessionId),
  // Gallery
  getGalleries: () => galleryAPI.list(),
  getGallery: (id: number) => galleryAPI.get(id),
  // Settings
  getSettings: () => settingsAPI.get(),
  // Health
  getHealth: () => healthAPI.check(),
  getVersion: () => healthAPI.version(),
}
