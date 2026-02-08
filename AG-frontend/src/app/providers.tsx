import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
// Theme store auto-initializes on import (Zustand)
import '@/shared/theme/useTheme'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
})

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
