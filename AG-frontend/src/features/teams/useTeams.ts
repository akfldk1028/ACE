import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, teamAPI, validationAPI } from '@/shared/api'
import type { TeamResponse } from '@/shared/api'
import type { Component, ComponentConfig } from '@/shared/types/datamodel'

export function useTeams() {
  return useQuery({
    queryKey: ['teams'],
    queryFn: api.getTeams,
  })
}

export function useTeam(id: number | null) {
  return useQuery({
    queryKey: ['teams', id],
    queryFn: () => api.getTeam(id!),
    enabled: id !== null,
  })
}

export function useCreateTeam() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (team: Record<string, unknown>) => api.createTeam(team),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] })
    },
  })
}

export function useUpdateTeam() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, component }: { id: number; component: unknown }) =>
      teamAPI.update(id, component),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['teams'] }),
  })
}

export function useDeleteTeam() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.deleteTeam(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['teams'] }),
  })
}

export function useValidateComponent(component: Component<ComponentConfig> | null | undefined) {
  return useQuery({
    queryKey: ['validation', component ? JSON.stringify(component) : null],
    queryFn: () => validationAPI.validate(component!),
    enabled: !!component,
    retry: false,
    staleTime: 60_000,
  })
}

export function getTeamName(team: TeamResponse) {
  return team.component?.label ?? `Team #${team.id}`
}

export function getTeamPattern(team: TeamResponse) {
  const comp = team.component as Record<string, unknown> | null
  const teamType = String(comp?.team_type ?? comp?.provider ?? '')
  if (teamType.includes('RoundRobin')) return 'sequential'
  if (teamType.includes('Selector')) return 'selector'
  if (teamType.includes('Swarm')) return 'handoff'
  if (teamType.includes('MagenticOne')) return 'custom'
  // Fallback: check label for pattern hints
  const label = (team.component?.label ?? '').toLowerCase()
  if (label.includes('debate')) return 'selector'
  if (label.includes('reflection')) return 'sequential'
  if (label.includes('handoff')) return 'handoff'
  return 'custom'
}
