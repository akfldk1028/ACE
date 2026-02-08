import { createBrowserRouter } from 'react-router'
import { lazy, Suspense } from 'react'
import { MainLayout } from '@/shared/ui/MainLayout'

// Match AutoGen Studio page structure: Team Builder, Playground (home), MCP, Gallery, Deploy, Settings
const PlaygroundPage = lazy(() => import('@/features/playground/PlaygroundPage').then(m => ({ default: m.PlaygroundPage })))
const TeamsPage = lazy(() => import('@/features/teams/TeamsPage').then(m => ({ default: m.TeamsPage })))
const McpPage = lazy(() => import('@/features/mcp/McpPage').then(m => ({ default: m.McpPage })))
const GalleryPage = lazy(() => import('@/features/gallery/GalleryPage').then(m => ({ default: m.GalleryPage })))
const DeployPage = lazy(() => import('@/features/deploy/DeployPage').then(m => ({ default: m.DeployPage })))
const AgentsPage = lazy(() => import('@/features/agents/AgentsPage').then(m => ({ default: m.AgentsPage })))
const SettingsPage = lazy(() => import('@/features/settings/SettingsPage').then(m => ({ default: m.SettingsPage })))

function PageLoader() {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="w-8 h-8 border-2 border-(--color-accent-primary) border-t-transparent rounded-full animate-spin" />
    </div>
  )
}

function SuspenseWrapper({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<PageLoader />}>{children}</Suspense>
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      { index: true, element: <SuspenseWrapper><PlaygroundPage /></SuspenseWrapper> },
      { path: 'build', element: <SuspenseWrapper><TeamsPage /></SuspenseWrapper> },
      { path: 'mcp', element: <SuspenseWrapper><McpPage /></SuspenseWrapper> },
      { path: 'agents', element: <SuspenseWrapper><AgentsPage /></SuspenseWrapper> },
      { path: 'gallery', element: <SuspenseWrapper><GalleryPage /></SuspenseWrapper> },
      { path: 'deploy', element: <SuspenseWrapper><DeployPage /></SuspenseWrapper> },
      { path: 'settings', element: <SuspenseWrapper><SettingsPage /></SuspenseWrapper> },
    ],
  },
])
