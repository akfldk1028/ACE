import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/shared/api'

export function useDeleteSession() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.deleteSession(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sessions'] }),
  })
}
