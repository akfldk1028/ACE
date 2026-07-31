import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsAPI } from '@/shared/api'
import type { Settings } from '@/shared/types/datamodel'

export function useSettings() {
  return useQuery({
    queryKey: ['settings'],
    queryFn: () => settingsAPI.get(),
    retry: false,
  })
}

export function useUpdateSettings() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (settings: Settings) => settingsAPI.update(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
    },
  })
}
