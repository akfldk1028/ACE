import { useAuthStore } from '@/features/auth/authStore'
import { Avatar } from '@/shared/ui'
import { Badge } from '@/shared/ui'

export function Header() {
  const { user } = useAuthStore()

  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-(--color-border-default) bg-(--color-surface-card)">
      <div className="flex items-center gap-2">
        <Badge variant="primary">AutoGen Studio :8081</Badge>
      </div>

      <div className="flex items-center gap-3">
        {user && (
          <div className="flex items-center gap-2">
            <span className="text-body-small text-(--color-text-secondary)">
              {user.name}
            </span>
            <Avatar name={user.name} size="sm" />
          </div>
        )}
      </div>
    </header>
  )
}
