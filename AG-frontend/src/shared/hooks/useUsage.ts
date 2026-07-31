import { useQuery } from '@tanstack/react-query'
import { api } from '@/shared/api'

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: api.getHealth,
    refetchInterval: 30000,
  })
}

export function useVersion() {
  return useQuery({
    queryKey: ['version'],
    queryFn: api.getVersion,
  })
}
