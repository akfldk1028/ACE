import { Card, Button, Input, Badge, Toggle } from '@/shared/ui'
import { useTheme } from '@/shared/theme'
import { useHealth, useVersion } from '@/shared/hooks/useUsage'
import { Key, Palette, Server } from 'lucide-react'

export function SettingsPage() {
  const { colorTheme, setColorTheme, mode, toggleMode, themes } = useTheme()
  const { data: health } = useHealth()
  const { data: version } = useVersion()

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-display-medium">Settings</h1>
        <p className="text-body-medium text-(--color-text-secondary) mt-1">
          Platform configuration
        </p>
      </div>

      {/* Engine Connection */}
      <Card>
        <div className="flex items-center gap-3 mb-4">
          <Server className="w-5 h-5 text-(--color-text-secondary)" />
          <h2 className="text-heading-small">Engine Connection</h2>
        </div>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-label">AutoGen Studio</span>
            <div className="flex items-center gap-2">
              <Badge variant={health?.status ? 'success' : 'error'}>
                {health?.status ? 'Connected' : 'Disconnected'}
              </Badge>
              <span className="text-body-small text-(--color-text-tertiary)">:8081</span>
            </div>
          </div>
          {version && (
            <div className="flex items-center justify-between">
              <span className="text-label">Version</span>
              <span className="text-body-small text-(--color-text-tertiary)">{version.version}</span>
            </div>
          )}
        </div>
      </Card>

      {/* Theme */}
      <Card>
        <div className="flex items-center gap-3 mb-4">
          <Palette className="w-5 h-5 text-(--color-text-secondary)" />
          <h2 className="text-heading-small">Appearance</h2>
        </div>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-label">Dark Mode</span>
            <Toggle checked={mode === 'dark'} onChange={toggleMode} />
          </div>
          <div>
            <span className="text-label block mb-2">Color Theme</span>
            <div className="grid grid-cols-4 gap-2">
              {themes.map((theme) => (
                <button
                  key={theme.id}
                  onClick={() => setColorTheme(theme.id)}
                  className={`p-3 rounded-lg border-2 transition-all ${
                    colorTheme === theme.id
                      ? 'border-(--color-accent-primary) shadow-md'
                      : 'border-(--color-border-default) hover:border-(--color-text-tertiary)'
                  }`}
                >
                  <div className="flex gap-1 mb-2">
                    <div
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: mode === 'dark' ? theme.previewColors.darkBg : theme.previewColors.bg }}
                    />
                    <div
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: theme.previewColors.accent }}
                    />
                  </div>
                  <span className="text-body-small">{theme.name}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* API Keys (placeholder) */}
      <Card>
        <div className="flex items-center gap-3 mb-4">
          <Key className="w-5 h-5 text-(--color-text-secondary)" />
          <h2 className="text-heading-small">API Keys</h2>
        </div>
        <p className="text-body-medium text-(--color-text-secondary) mb-4">
          API keys for programmatic access. Available in Phase 3.
        </p>
        <div className="flex gap-2">
          <Input placeholder="API key name" disabled />
          <Button variant="secondary" disabled>Generate</Button>
        </div>
      </Card>
    </div>
  )
}
