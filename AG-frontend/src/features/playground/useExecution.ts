import { useQuery } from '@tanstack/react-query'
import { api } from '@/shared/api'

export function useSessions() {
  return useQuery({
    queryKey: ['sessions'],
    queryFn: api.getSessions,
  })
}

export function useSessionRuns(sessionId: number | null) {
  return useQuery({
    queryKey: ['sessions', sessionId, 'runs'],
    queryFn: () => api.getSessionRuns(sessionId!),
    enabled: sessionId !== null,
  })
}
