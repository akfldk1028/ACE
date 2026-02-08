import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { agentAPI } from './api'

export function useAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: async () => {
      const res = await agentAPI.list()
      return res.agents ?? []
    },
    retry: false,
  })
}

export function useAgentHealth() {
  return useQuery({
    queryKey: ['agents', 'health'],
    queryFn: async () => {
      const res = await agentAPI.healthAll()
      return res.agents ?? []
    },
    enabled: false, // manual refetch only
    staleTime: 30_000,
  })
}

export function useRegisterAgent() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (url: string) => agentAPI.register(url),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] })
    },
  })
}

export function useUnregisterAgent() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => agentAPI.unregister(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] })
    },
  })
}

export function useAgentComponent(name: string | null) {
  return useQuery({
    queryKey: ['agents', name, 'component'],
    queryFn: () => agentAPI.component(name!),
    enabled: !!name,
  })
}
