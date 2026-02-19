import { useState, useEffect } from 'react'
import { Button, Input, Card } from '@/shared/ui'
import { X, Search, Plus } from 'lucide-react'
import { AgentHealthBadge } from './AgentHealthBadge'
import { agentAPI } from '../api'
import { useRegisterAgent } from '../useAgents'
import type { A2AHealthStatus } from '../types'
import { truncateError } from '@/shared/utils'

interface AgentRegisterDialogProps {
  open: boolean
  onClose: () => void
}

export function AgentRegisterDialog({ open, onClose }: AgentRegisterDialogProps) {
  const [url, setUrl] = useState('')
  const [preview, setPreview] = useState<A2AHealthStatus | null>(null)
  const [discovering, setDiscovering] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const registerMutation = useRegisterAgent()

  // H3: Reset state when dialog opens
  useEffect(() => {
    if (open) {
      setUrl('')
      setPreview(null)
      setError(null)
    }
  }, [open])

  if (!open) return null

  async function handleDiscover() {
    if (!url.trim()) return
    setDiscovering(true)
    setError(null)
    setPreview(null)
    try {
      const result = await agentAPI.healthOne(url.trim())
      setPreview(result)
    } catch (e) {
      setError(truncateError(e instanceof Error ? e.message : 'Failed to reach agent'))
    } finally {
      setDiscovering(false)
    }
  }

  async function handleRegister() {
    try {
      await registerMutation.mutateAsync(url.trim())
      onClose()
    } catch (e) {
      setError(truncateError(e instanceof Error ? e.message : 'Registration failed'))
    }
  }

  // C2: Escape key handler
  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Escape') onClose()
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      role="dialog"
      aria-modal="true"
      aria-label="Register A2A Agent"
      onClick={onClose}
      onKeyDown={handleKeyDown}
    >
      <Card className="w-full max-w-md mx-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-heading-small">Register A2A Agent</h2>
          <button
            onClick={onClose}
            aria-label="Close register dialog"
            className="p-1 rounded hover:bg-(--color-background-secondary) text-(--color-text-tertiary) focus:outline-none focus:ring-2 focus:ring-(--color-accent-primary)"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex gap-2">
          <Input
            autoFocus
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="http://localhost:8006"
            onKeyDown={(e) => e.key === 'Enter' && handleDiscover()}
          />
          <Button
            variant="ghost"
            onClick={handleDiscover}
            disabled={!url.trim() || discovering}
          >
            <Search className="w-4 h-4 mr-1.5" />
            {discovering ? 'Checking...' : 'Discover'}
          </Button>
        </div>

        {error && (
          <p className="text-sm text-(--color-semantic-error) mt-3">{error}</p>
        )}

        {preview && (
          <div className="mt-4 p-3 rounded-md bg-(--color-background-secondary)">
            <div className="flex items-center justify-between">
              <span className="font-medium text-sm">{preview.name || 'Agent'}</span>
              <AgentHealthBadge health={preview} />
            </div>
            <p className="text-xs font-mono text-(--color-text-tertiary) mt-1">{preview.url}</p>
          </div>
        )}

        <div className="flex justify-end gap-2 mt-4">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button
            variant="primary"
            onClick={handleRegister}
            disabled={!preview?.healthy || registerMutation.isPending}
          >
            <Plus className="w-4 h-4 mr-1.5" />
            {registerMutation.isPending ? 'Registering...' : 'Register'}
          </Button>
        </div>
      </Card>
    </div>
  )
}
