import { memo, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, Button, Input, Badge, Toggle } from '@/shared/ui'
import { useTheme } from '@/shared/theme'
import { useHealth, useVersion } from '@/shared/hooks/useUsage'
import { useSettings, useUpdateSettings } from './useSettings'
import { useSettingsStore } from './settingsStore'
import { Key, Monitor, Palette, Server, Variable, Eye, EyeOff, Trash2, Plus, Globe } from 'lucide-react'
import type { EnvironmentVariable, EnvironmentVariableType, Settings } from '@/shared/types/datamodel'
import { truncateError } from '@/shared/utils'
import { useLanguage, LOCALES } from '@/shared/i18n'

// ---- UI Settings Section ----

function UISettingsCard() {
  const { data: settings, isLoading, error } = useSettings()
  const updateSettings = useUpdateSettings()
  const store = useSettingsStore()
  const hydrate = useSettingsStore((s) => s.hydrate)

  // Track whether initial hydration happened
  const hydratedRef = useRef(false)

  // Hydrate store from API on first load
  useEffect(() => {
    if (settings?.config?.ui && !hydratedRef.current) {
      hydrate(settings.config.ui)
      hydratedRef.current = true
    }
  }, [settings, hydrate])

  // Dirty check: compare store values to API values
  const isDirty = useMemo(() => {
    if (!settings?.config?.ui) return false
    const ui = settings.config.ui
    return (
      store.showLlmEvents !== ui.show_llm_call_events ||
      store.expandMessages !== (ui.expanded_messages_by_default ?? false) ||
      store.showAgentFlow !== (ui.show_agent_flow_by_default ?? false) ||
      store.humanInputTimeout !== (ui.human_input_timeout_minutes ?? 3)
    )
  }, [settings, store.showLlmEvents, store.expandMessages, store.showAgentFlow, store.humanInputTimeout])

  const handleSave = useCallback(() => {
    if (!settings) return
    const updated: Settings = {
      ...settings,
      config: {
        ...settings.config,
        ui: {
          show_llm_call_events: store.showLlmEvents,
          expanded_messages_by_default: store.expandMessages,
          show_agent_flow_by_default: store.showAgentFlow,
          human_input_timeout_minutes: store.humanInputTimeout,
        },
      },
    }
    updateSettings.mutate(updated)
  }, [settings, store.showLlmEvents, store.expandMessages, store.showAgentFlow, store.humanInputTimeout, updateSettings])

  const handleReset = useCallback(() => {
    if (settings?.config?.ui) {
      hydrate(settings.config.ui)
    }
  }, [settings, hydrate])

  const handleTimeoutChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = parseInt(e.target.value, 10)
      if (!isNaN(val)) {
        store.setHumanInputTimeout(val)
      }
    },
    [store],
  )

  if (isLoading) {
    return (
      <Card>
        <div className="flex items-center gap-3 mb-4">
          <Monitor className="w-5 h-5 text-(--color-text-secondary)" />
          <h2 className="text-heading-small">UI Settings</h2>
        </div>
        <p className="text-body-medium text-(--color-text-tertiary)">Loading settings...</p>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <div className="flex items-center gap-3 mb-4">
          <Monitor className="w-5 h-5 text-(--color-text-secondary)" />
          <h2 className="text-heading-small">UI Settings</h2>
        </div>
        <p className="text-body-medium text-(--color-semantic-error)">
          Failed to load settings: {truncateError(error instanceof Error ? error.message : String(error))}
        </p>
      </Card>
    )
  }

  return (
    <Card>
      <div className="flex items-center gap-3 mb-4">
        <Monitor className="w-5 h-5 text-(--color-text-secondary)" />
        <h2 className="text-heading-small">UI Settings</h2>
      </div>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-label block">Show LLM Events</span>
            <span className="text-body-small text-(--color-text-tertiary)">
              Display detailed LLM call logs in message threads
            </span>
          </div>
          <Toggle
            checked={store.showLlmEvents}
            onChange={store.setShowLlmEvents}
            aria-label="Toggle show LLM events"
          />
        </div>
        <div className="flex items-center justify-between">
          <div>
            <span className="text-label block">Expand Messages by Default</span>
            <span className="text-body-small text-(--color-text-tertiary)">
              Auto-expand message threads when viewing runs
            </span>
          </div>
          <Toggle
            checked={store.expandMessages}
            onChange={store.setExpandMessages}
            aria-label="Toggle expand messages by default"
          />
        </div>
        <div className="flex items-center justify-between">
          <div>
            <span className="text-label block">Show Agent Flow by Default</span>
            <span className="text-body-small text-(--color-text-tertiary)">
              Auto-display the agent flow diagram when opening teams
            </span>
          </div>
          <Toggle
            checked={store.showAgentFlow}
            onChange={store.setShowAgentFlow}
            aria-label="Toggle show agent flow by default"
          />
        </div>
        <div className="flex items-center justify-between">
          <div>
            <label htmlFor="human-input-timeout" className="text-label block">
              Human Input Timeout
            </label>
            <span className="text-body-small text-(--color-text-tertiary)">
              Minutes to wait for human input (1-30)
            </span>
          </div>
          <Input
            id="human-input-timeout"
            type="number"
            min={1}
            max={30}
            value={store.humanInputTimeout}
            onChange={handleTimeoutChange}
            aria-label="Human input timeout in minutes"
            className="w-20 text-center"
          />
        </div>
        {updateSettings.isError && (
          <p className="text-body-small text-(--color-semantic-error)">
            Save failed: {truncateError(updateSettings.error instanceof Error ? updateSettings.error.message : 'Unknown error')}
          </p>
        )}
        <div className="flex gap-2 pt-2">
          <Button
            onClick={handleSave}
            disabled={!isDirty || updateSettings.isPending}
            aria-label="Save UI settings"
          >
            {updateSettings.isPending ? 'Saving...' : 'Save'}
          </Button>
          <Button variant="secondary" onClick={handleReset} disabled={!isDirty} aria-label="Reset UI settings">
            Reset
          </Button>
        </div>
      </div>
    </Card>
  )
}

// ---- Environment Variables Section ----

interface EnvVarRowProps {
  envVar: EnvironmentVariable
  onDelete: (name: string) => void
  onValueChange: (name: string, value: string) => void
}

const EnvVarRow = memo(function EnvVarRow({ envVar, onDelete, onValueChange }: EnvVarRowProps) {
  const [showValue, setShowValue] = useState(false)
  const isSecret = envVar.type === 'secret'

  const handleToggleVisibility = useCallback(() => {
    setShowValue((prev) => !prev)
  }, [])

  const handleDelete = useCallback(() => {
    onDelete(envVar.name)
  }, [onDelete, envVar.name])

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onValueChange(envVar.name, e.target.value)
    },
    [onValueChange, envVar.name],
  )

  const badgeVariant = useMemo(() => {
    switch (envVar.type) {
      case 'secret':
        return 'error' as const
      case 'number':
        return 'primary' as const
      case 'boolean':
        return 'warning' as const
      default:
        return 'default' as const
    }
  }, [envVar.type])

  return (
    <tr className="border-b border-(--color-border-default) last:border-b-0">
      <td className="py-2 pr-3">
        <span className="text-label-small font-mono">{envVar.name}</span>
      </td>
      <td className="py-2 pr-3">
        <div className="flex items-center gap-2">
          <Input
            type={isSecret && !showValue ? 'password' : 'text'}
            value={envVar.value}
            onChange={handleChange}
            aria-label={`Value for ${envVar.name}`}
            className="h-8 text-body-small font-mono"
          />
          {isSecret && (
            <button
              type="button"
              onClick={handleToggleVisibility}
              className="p-1 rounded text-(--color-text-tertiary) hover:text-(--color-text-primary) focus:outline-none focus:ring-2 focus:ring-(--color-accent-primary)"
              aria-label={showValue ? `Hide value for ${envVar.name}` : `Show value for ${envVar.name}`}
            >
              {showValue ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          )}
        </div>
      </td>
      <td className="py-2 pr-3">
        <span className="inline-block">
          <Badge variant={badgeVariant}>{envVar.type}</Badge>
        </span>
      </td>
      <td className="py-2 pr-3">
        <span className="text-body-small text-(--color-text-tertiary)">{envVar.description ?? '-'}</span>
      </td>
      <td className="py-2">
        <button
          type="button"
          onClick={handleDelete}
          className="p-1 rounded text-(--color-text-tertiary) hover:text-(--color-semantic-error) focus:outline-none focus:ring-2 focus:ring-(--color-accent-primary)"
          aria-label={`Delete ${envVar.name}`}
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </td>
    </tr>
  )
})

const ENV_PRESETS: { name: string; type: EnvironmentVariableType; description: string }[] = [
  { name: 'OPENAI_API_KEY', type: 'secret', description: 'OpenAI API key for GPT models' },
  { name: 'ANTHROPIC_API_KEY', type: 'secret', description: 'Anthropic API key for Claude models' },
]

const ENV_TYPE_OPTIONS: EnvironmentVariableType[] = ['string', 'number', 'boolean', 'secret']

function EnvironmentVariablesCard() {
  const { data: settings } = useSettings()
  const updateSettings = useUpdateSettings()

  const [envVars, setEnvVars] = useState<EnvironmentVariable[]>([])
  const [newName, setNewName] = useState('')
  const [newValue, setNewValue] = useState('')
  const [newType, setNewType] = useState<EnvironmentVariableType>('string')
  const [nameError, setNameError] = useState<string | null>(null)

  const initializedRef = useRef(false)

  // Hydrate from API
  useEffect(() => {
    if (settings?.config?.environment && !initializedRef.current) {
      setEnvVars(settings.config.environment)
      initializedRef.current = true
    }
  }, [settings])

  // Re-sync after successful save
  useEffect(() => {
    if (updateSettings.isSuccess && settings?.config?.environment) {
      setEnvVars(settings.config.environment)
    }
  }, [updateSettings.isSuccess, settings])

  const isDirty = useMemo(() => {
    if (!settings?.config?.environment) return envVars.length > 0
    return JSON.stringify(envVars) !== JSON.stringify(settings.config.environment)
  }, [envVars, settings])

  const existingNames = useMemo(() => new Set(envVars.map((v) => v.name)), [envVars])

  const handleAdd = useCallback(() => {
    const trimmedName = newName.trim()
    if (!trimmedName) {
      setNameError('Name is required')
      return
    }
    if (existingNames.has(trimmedName)) {
      setNameError('Variable name already exists')
      return
    }
    setNameError(null)
    setEnvVars((prev) => [
      ...prev,
      { name: trimmedName, value: newValue, type: newType, required: false },
    ])
    setNewName('')
    setNewValue('')
    setNewType('string')
  }, [newName, newValue, newType, existingNames])

  const handleAddPreset = useCallback(
    (preset: (typeof ENV_PRESETS)[0]) => {
      if (existingNames.has(preset.name)) return
      setEnvVars((prev) => [
        ...prev,
        { name: preset.name, value: '', type: preset.type, description: preset.description, required: false },
      ])
    },
    [existingNames],
  )

  const handleDelete = useCallback((name: string) => {
    setEnvVars((prev) => prev.filter((v) => v.name !== name))
  }, [])

  const handleValueChange = useCallback((name: string, value: string) => {
    setEnvVars((prev) => prev.map((v) => (v.name === name ? { ...v, value } : v)))
  }, [])

  const handleSave = useCallback(() => {
    if (!settings) return
    const updated: Settings = {
      ...settings,
      config: {
        ...settings.config,
        environment: envVars,
      },
    }
    updateSettings.mutate(updated)
  }, [settings, envVars, updateSettings])

  const handleNewNameChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setNewName(e.target.value)
    setNameError(null)
  }, [])

  const handleNewValueChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setNewValue(e.target.value)
  }, [])

  const handleNewTypeChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setNewType(e.target.value as EnvironmentVariableType)
  }, [])

  return (
    <Card>
      <div className="flex items-center gap-3 mb-4">
        <Variable className="w-5 h-5 text-(--color-text-secondary)" />
        <h2 className="text-heading-small">Environment Variables</h2>
      </div>

      {/* Preset buttons */}
      <div className="flex gap-2 mb-4">
        {ENV_PRESETS.map((preset) => (
          <Button
            key={preset.name}
            variant="secondary"
            size="sm"
            disabled={existingNames.has(preset.name)}
            onClick={() => handleAddPreset(preset)}
            aria-label={`Add preset ${preset.name}`}
          >
            <Plus className="w-3 h-3 mr-1" />
            {preset.name}
          </Button>
        ))}
      </div>

      {/* Env vars table */}
      {envVars.length > 0 && (
        <div className="overflow-x-auto mb-4">
          <table className="w-full text-sm" aria-label="Environment variables">
            <thead>
              <tr className="border-b border-(--color-border-default) text-(--color-text-tertiary)">
                <th className="py-2 pr-3 text-left text-label-small font-medium">Name</th>
                <th className="py-2 pr-3 text-left text-label-small font-medium">Value</th>
                <th className="py-2 pr-3 text-left text-label-small font-medium">Type</th>
                <th className="py-2 pr-3 text-left text-label-small font-medium">Description</th>
                <th className="py-2 text-left text-label-small font-medium w-10" />
              </tr>
            </thead>
            <tbody>
              {envVars.map((envVar) => (
                <EnvVarRow
                  key={envVar.name}
                  envVar={envVar}
                  onDelete={handleDelete}
                  onValueChange={handleValueChange}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {envVars.length === 0 && (
        <p className="text-body-medium text-(--color-text-tertiary) mb-4">
          No environment variables configured. Add presets above or create a custom variable below.
        </p>
      )}

      {/* Add new variable */}
      <div className="flex items-end gap-2 flex-wrap">
        <div className="flex-1 min-w-[140px]">
          <label htmlFor="env-new-name" className="text-label-small block mb-1">
            Name
          </label>
          <Input
            id="env-new-name"
            value={newName}
            onChange={handleNewNameChange}
            placeholder="VARIABLE_NAME"
            aria-label="New variable name"
            className={nameError ? 'border-(--color-semantic-error)' : ''}
          />
          {nameError && <p className="text-body-small text-(--color-semantic-error) mt-1">{nameError}</p>}
        </div>
        <div className="flex-1 min-w-[140px]">
          <label htmlFor="env-new-value" className="text-label-small block mb-1">
            Value
          </label>
          <Input
            id="env-new-value"
            value={newValue}
            onChange={handleNewValueChange}
            placeholder="value"
            type={newType === 'secret' ? 'password' : 'text'}
            aria-label="New variable value"
          />
        </div>
        <div className="min-w-[100px]">
          <label htmlFor="env-new-type" className="text-label-small block mb-1">
            Type
          </label>
          <select
            id="env-new-type"
            value={newType}
            onChange={handleNewTypeChange}
            aria-label="New variable type"
            className="h-10 w-full px-3 rounded-md border border-(--color-border-default) bg-(--color-surface-card) text-(--color-text-primary) text-sm focus:outline-none focus:border-(--color-accent-primary) focus:ring-2 focus:ring-(--color-accent-primary)/20"
          >
            {ENV_TYPE_OPTIONS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        <Button onClick={handleAdd} size="md" aria-label="Add environment variable">
          <Plus className="w-4 h-4 mr-1" />
          Add
        </Button>
      </div>

      {/* Save */}
      {updateSettings.isError && (
        <p className="text-body-small text-(--color-semantic-error) mt-3">
          Save failed: {truncateError(updateSettings.error instanceof Error ? updateSettings.error.message : 'Unknown error')}
        </p>
      )}
      <div className="flex gap-2 pt-4">
        <Button
          onClick={handleSave}
          disabled={!isDirty || updateSettings.isPending}
          aria-label="Save environment variables"
        >
          {updateSettings.isPending ? 'Saving...' : 'Save'}
        </Button>
      </div>
    </Card>
  )
}

// ---- Main SettingsPage ----

export function SettingsPage() {
  const { colorTheme, setColorTheme, mode, toggleMode, themes } = useTheme()
  const { data: health } = useHealth()
  const { data: version } = useVersion()
  const { t } = useTranslation()
  const { currentLocale, setLocale } = useLanguage()

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-display-medium">{t('settings.title')}</h1>
        <p className="text-body-medium text-(--color-text-secondary) mt-1">
          {t('settings.desc')}
        </p>
      </div>

      {/* Engine Connection */}
      <Card>
        <div className="flex items-center gap-3 mb-4">
          <Server className="w-5 h-5 text-(--color-text-secondary)" />
          <h2 className="text-heading-small">{t('settings.engine')}</h2>
        </div>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-label">AutoGen Studio</span>
            <div className="flex items-center gap-2">
              <Badge variant={health?.status ? 'success' : 'error'}>
                {health?.status ? t('settings.connected') : t('settings.disconnected')}
              </Badge>
              <span className="text-body-small text-(--color-text-tertiary)">:8081</span>
            </div>
          </div>
          {version && (
            <div className="flex items-center justify-between">
              <span className="text-label">{t('settings.version')}</span>
              <span className="text-body-small text-(--color-text-tertiary)">{version.version}</span>
            </div>
          )}
        </div>
      </Card>

      {/* Theme + Language */}
      <Card>
        <div className="flex items-center gap-3 mb-4">
          <Palette className="w-5 h-5 text-(--color-text-secondary)" />
          <h2 className="text-heading-small">{t('settings.appearance')}</h2>
        </div>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-label">{t('settings.darkMode')}</span>
            <Toggle checked={mode === 'dark'} onChange={toggleMode} aria-label="Toggle dark mode" />
          </div>
          <div>
            <span className="text-label block mb-2">{t('settings.colorTheme')}</span>
            <div className="grid grid-cols-4 gap-2" role="radiogroup" aria-label="Color theme">
              {themes.map((theme) => (
                <button
                  key={theme.id}
                  role="radio"
                  aria-checked={colorTheme === theme.id}
                  aria-label={`${theme.name} theme`}
                  onClick={() => setColorTheme(theme.id)}
                  className={`p-3 rounded-lg border-2 transition-all focus:outline-none focus:ring-2 focus:ring-(--color-accent-primary) ${
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
          {/* Language selector */}
          <div className="flex items-center justify-between">
            <div>
              <span className="text-label block">{t('settings.language')}</span>
              <span className="text-body-small text-(--color-text-tertiary)">
                {t('settings.languageDesc')}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-(--color-text-tertiary)" />
              <select
                aria-label="Language"
                className="h-9 px-3 rounded-md border border-(--color-border-default) bg-(--color-surface-card) text-sm text-(--color-text-primary)"
                value={currentLocale}
                onChange={(e) => setLocale(e.target.value as 'en-US' | 'ko-KR')}
              >
                {LOCALES.map((l) => (
                  <option key={l.code} value={l.code}>{l.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </Card>

      {/* UI Settings */}
      <UISettingsCard />

      {/* Environment Variables */}
      <EnvironmentVariablesCard />

      {/* API Keys (placeholder) */}
      <Card>
        <div className="flex items-center gap-3 mb-4">
          <Key className="w-5 h-5 text-(--color-text-secondary)" />
          <h2 className="text-heading-small">{t('settings.apiKeys')}</h2>
        </div>
        <p className="text-body-medium text-(--color-text-secondary) mb-4">
          {t('settings.apiKeysDesc')}
        </p>
        <div className="flex gap-2">
          <Input placeholder="API key name" disabled />
          <Button variant="secondary" disabled>{t('settings.generate')}</Button>
        </div>
      </Card>
    </div>
  )
}
