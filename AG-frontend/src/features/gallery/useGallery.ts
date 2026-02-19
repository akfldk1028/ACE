import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, galleryAPI, teamAPI } from '@/shared/api'
import type { Component, TeamConfig } from '@/shared/types/datamodel'

export function useGalleries() {
  return useQuery({
    queryKey: ['galleries'],
    queryFn: api.getGalleries,
  })
}

export function useImportGalleryTeam() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (team: Component<TeamConfig>) =>
      teamAPI.create({ component: team }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] })
    },
  })
}

export function useSyncGallery() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (url: string) => galleryAPI.sync(url),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['galleries'] })
    },
  })
}
