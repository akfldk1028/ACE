import { fetchJSON } from '@/shared/api/client'
import type { A2AAgent, A2AHealthStatus } from './types'

export const agentAPI = {
  list: () =>
    fetchJSON<{ agents: A2AAgent[] }>('/a2a/registry'),

  register: (url: string) =>
    fetchJSON<void>('/a2a/registry/register', {
      method: 'POST',
      body: JSON.stringify({ agent_url: url }),
    }),

  unregister: (name: string) =>
    fetchJSON<void>(`/a2a/registry/${encodeURIComponent(name)}`, {
      method: 'DELETE',
    }),

  healthAll: () =>
    fetchJSON<{ agents: A2AHealthStatus[] }>('/a2a/registry/check-all', {
      method: 'POST',
    }),

  healthOne: (url: string) =>
    fetchJSON<A2AHealthStatus>(`/a2a/check?url=${encodeURIComponent(url)}`),

  component: (name: string) =>
    fetchJSON<Record<string, unknown>>(`/a2a/registry/${encodeURIComponent(name)}/component`),
}
