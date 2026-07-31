import { fetchJSON } from '@/shared/api/client'
import type { A2AAgent, A2AHealthStatus } from './types'

/** Backend registry flat shape (GET /api/a2a/registry) */
interface RegistryEntry {
  name: string
  display_name?: string
  url: string
  description?: string
  skills?: Array<{ id?: string; name: string; description: string; tags?: string[] }>
  is_online?: boolean
  timeout?: number
  registered_at?: string
}

/** Transform flat registry entry → A2AAgent component shape */
function mapAgent(entry: RegistryEntry): A2AAgent {
  return {
    provider: 'autogenstudio.a2a.A2AAgent',
    component_type: 'agent',
    version: 1,
    label: entry.display_name ?? entry.name,
    description: entry.description ?? '',
    config: {
      name: entry.name,
      a2a_server_url: entry.url,
      description: entry.description ?? '',
      timeout: entry.timeout ?? 300,
      skills: (entry.skills ?? []).map(s => ({ name: s.name, description: s.description })),
    },
  }
}

/** Map backend is_online field to frontend healthy field */
function mapHealth<T extends { is_online?: boolean; healthy?: boolean }>(item: T): T & { healthy: boolean } {
  return { ...item, healthy: item.healthy ?? item.is_online ?? false }
}

export const agentAPI = {
  list: async () => {
    const res = await fetchJSON<{ agents: RegistryEntry[] }>('/a2a/registry')
    return { agents: (res.agents ?? []).map(mapAgent) }
  },

  register: (url: string) =>
    fetchJSON<void>('/a2a/registry/register', {
      method: 'POST',
      body: JSON.stringify({ url }),
    }),

  unregister: (name: string) =>
    fetchJSON<void>(`/a2a/registry/${encodeURIComponent(name)}`, {
      method: 'DELETE',
    }),

  healthAll: async () => {
    const res = await fetchJSON<{ agents: A2AHealthStatus[] }>('/a2a/registry/check-all', {
      method: 'POST',
    })
    return { agents: (res.agents ?? []).map(mapHealth) }
  },

  healthOne: async (url: string) => {
    const res = await fetchJSON<{ status: boolean; agent_name: string | null }>(`/a2a/check?url=${encodeURIComponent(url)}`)
    return { name: res.agent_name ?? '', url, healthy: res.status } as A2AHealthStatus
  },

  component: async (name: string) => {
    const res = await fetchJSON<{ component: Record<string, unknown> }>(`/a2a/registry/${encodeURIComponent(name)}/component`)
    return res.component ?? res
  },
}
