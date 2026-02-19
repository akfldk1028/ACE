import { memo } from 'react'
import { X } from 'lucide-react'
import { SHORTCUT_GROUPS } from '../shortcuts.constants'

interface ShortcutsDialogProps {
  isOpen: boolean
  onClose: () => void
}

const KeyBadge = memo(function KeyBadge({ children }: { children: string }) {
  return (
    <kbd className="inline-flex items-center justify-center min-w-[24px] h-6 px-1.5 rounded border border-(--color-border-default) bg-(--color-background-secondary) text-xs font-mono text-(--color-text-secondary) shadow-sm">
      {children}
    </kbd>
  )
})

export const ShortcutsDialog = memo(function ShortcutsDialog({
  isOpen,
  onClose,
}: ShortcutsDialogProps) {
  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-label="Keyboard Shortcuts"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="relative w-full max-w-lg mx-4 rounded-xl border border-(--color-border-default) bg-(--color-surface-card) shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-(--color-border-default)">
          <h2 className="text-heading-small text-(--color-text-primary)">Keyboard Shortcuts</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-md text-(--color-text-tertiary) hover:text-(--color-text-primary) hover:bg-(--color-background-secondary) transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-4 max-h-[60vh] overflow-y-auto space-y-5">
          {SHORTCUT_GROUPS.map((group) => (
            <div key={group.label}>
              <h3 className="text-label text-(--color-text-tertiary) mb-2">{group.label}</h3>
              <div className="space-y-2">
                {group.shortcuts.map((shortcut) => (
                  <div
                    key={shortcut.description}
                    className="flex items-center justify-between py-1"
                  >
                    <span className="text-sm text-(--color-text-primary)">{shortcut.description}</span>
                    <div className="flex items-center gap-1">
                      {shortcut.keys.map((key, i) => (
                        <span key={i} className="flex items-center gap-1">
                          {i > 0 && <span className="text-xs text-(--color-text-tertiary)">+</span>}
                          <KeyBadge>{key}</KeyBadge>
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-(--color-border-default) bg-(--color-background-secondary)">
          <p className="text-xs text-(--color-text-tertiary) text-center">
            Press <KeyBadge>?</KeyBadge> to toggle this dialog
          </p>
        </div>
      </div>
    </div>
  )
})
