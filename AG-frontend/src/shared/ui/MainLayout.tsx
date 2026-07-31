import { Outlet } from 'react-router'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { useAuthInit } from '@/features/auth/useAuth'
import { useShortcutsDialog, ShortcutsDialog } from '@/features/shortcuts'

export function MainLayout() {
  useAuthInit()
  const { isOpen: shortcutsOpen, close: closeShortcuts } = useShortcutsDialog()

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-6 bg-(--color-background-primary)">
          <Outlet />
        </main>
      </div>
      <ShortcutsDialog isOpen={shortcutsOpen} onClose={closeShortcuts} />
    </div>
  )
}
