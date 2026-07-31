import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { ChangeEvent } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, Badge, Button, Input, Toggle } from '@/shared/ui'
import { healthAPI } from '@/shared/api'
import { useDeployStore } from './deployStore'
import type { EnvVar } from './deployStore'
import {
  Rocket,
  Container,
  Terminal,
  Cloud,
  Copy,
  Check,
  Plus,
  Trash2,
  RefreshCw,
  Eye,
  EyeOff,
  RotateCcw,
  Server,
  Globe,
  Key,
} from 'lucide-react'

// ============================================================
// Constants
// ============================================================

const DEPLOY_GUIDES = [
  {
    title: 'Docker Deployment',
    icon: Container,
    description:
      'Deploy AutoGen Studio as a Docker container with all dependencies included.',
    badge: 'Recommended',
    steps: [
      'docker pull autogenstudio:latest',
      'docker run -p 8081:8081 autogenstudio:latest',
      'Open http://localhost:8081 in your browser',
    ],
  },
  {
    title: 'Python Server',
    icon: Terminal,
    description:
      'Run AutoGen Studio directly with Python for development and testing.',
    badge: 'Development',
    steps: [
      'pip install autogenstudio',
      'autogenstudio ui --port 8081',
      'Open http://localhost:8081 in your browser',
    ],
  },
  {
    title: 'Cloud Deployment',
    icon: Cloud,
    description: 'Deploy to cloud platforms like Azure, AWS, or GCP.',
    badge: 'Production',
    steps: [
      'Configure environment variables',
      'Set up database (PostgreSQL recommended)',
      'Deploy with your cloud provider CLI',
    ],
  },
] as const

const ENV_PRESETS: EnvVar[] = [
  { key: 'OPENAI_API_KEY', value: '', isSecret: true },
  { key: 'ANTHROPIC_API_KEY', value: '', isSecret: true },
  { key: 'AZURE_OPENAI_ENDPOINT', value: '', isSecret: false },
]

interface ApiEndpoint {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'WS'
  path: string
  description: string
}

const API_ENDPOINTS: ApiEndpoint[] = [
  { method: 'GET', path: '/api/health', description: 'Health check' },
  { method: 'GET', path: '/api/version', description: 'API version' },
  { method: 'GET', path: '/api/teams/', description: 'List all teams' },
  { method: 'POST', path: '/api/teams/', description: 'Create a new team' },
  { method: 'PUT', path: '/api/teams/{id}', description: 'Update a team' },
  { method: 'DELETE', path: '/api/teams/{id}', description: 'Delete a team' },
  { method: 'GET', path: '/api/sessions/', description: 'List all sessions' },
  {
    method: 'POST',
    path: '/api/sessions/',
    description: 'Create a new session',
  },
  {
    method: 'GET',
    path: '/api/sessions/{id}/runs',
    description: 'Get runs for a session',
  },
  {
    method: 'DELETE',
    path: '/api/sessions/{id}',
    description: 'Delete a session',
  },
  {
    method: 'GET',
    path: '/api/gallery/',
    description: 'List gallery items',
  },
  {
    method: 'WS',
    path: '/api/ws/runs/{run_id}',
    description: 'WebSocket for run streaming',
  },
]

const METHOD_BADGE_VARIANT: Record<
  ApiEndpoint['method'],
  'success' | 'primary' | 'warning' | 'error' | 'default'
> = {
  GET: 'success',
  POST: 'primary',
  PUT: 'warning',
  DELETE: 'error',
  WS: 'default',
}

const HEALTH_REFETCH_INTERVAL = 30_000

// ============================================================
// Helpers
// ============================================================

function escapeDockerEnv(value: string): string {
  return value.replace(/"/g, '\\"')
}

function generateDockerfile(
  host: string,
  port: number,
  workers: number,
  dbUrl: string,
  envVars: EnvVar[],
): string {
  const lines = [
    'FROM python:3.11-slim',
    '',
    'RUN pip install autogenstudio',
    '',
    `EXPOSE ${port}`,
    '',
    `ENV AUTOGENSTUDIO_HOST=${host}`,
    `ENV AUTOGENSTUDIO_PORT=${port}`,
    `ENV AUTOGENSTUDIO_WORKERS=${workers}`,
  ]

  if (dbUrl) {
    lines.push(`ENV AUTOGENSTUDIO_DATABASE_URI=${dbUrl}`)
  }

  for (const ev of envVars) {
    if (ev.key.trim()) {
      lines.push(`ENV ${ev.key}=${escapeDockerEnv(ev.value)}`)
    }
  }

  lines.push('')
  lines.push(
    `CMD ["autogenstudio", "ui", "--host", "${host}", "--port", "${port}", "--workers", "${workers}"]`,
  )

  return lines.join('\n')
}

function generateDockerRun(
  port: number,
  envVars: EnvVar[],
): string {
  const envFlags = envVars
    .filter((ev) => ev.key.trim())
    .map((ev) => `-e ${ev.key}="${escapeDockerEnv(ev.value)}"`)
    .join(' ')

  const envPart = envFlags ? ` ${envFlags}` : ''
  return `docker run -p ${port}:${port}${envPart} autogenstudio:latest`
}

// ============================================================
// Sub-components
// ============================================================

function CopyButton({
  text,
  label,
}: {
  text: string
  label: string
}) {
  const [copied, setCopied] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [])

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      if (timerRef.current) clearTimeout(timerRef.current)
      timerRef.current = setTimeout(() => setCopied(false), 2000)
    } catch {
      // clipboard API may fail in insecure contexts
    }
  }, [text])

  return (
    <Button
      variant="secondary"
      size="sm"
      onClick={handleCopy}
      aria-label={label}
    >
      {copied ? (
        <Check className="w-4 h-4 mr-1.5" />
      ) : (
        <Copy className="w-4 h-4 mr-1.5" />
      )}
      {copied ? 'Copied!' : label}
    </Button>
  )
}

function EnvVarPresetButtons({
  existingKeys,
  onAdd,
}: {
  existingKeys: Set<string>
  onAdd: (v: EnvVar) => void
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {ENV_PRESETS.map((preset) => {
        const exists = existingKeys.has(preset.key)
        return (
          <Button
            key={preset.key}
            variant="ghost"
            size="sm"
            disabled={exists}
            title={exists ? 'Already added' : `Add ${preset.key}`}
            onClick={() => onAdd({ ...preset })}
          >
            <Key className="w-3.5 h-3.5 mr-1" />
            {preset.key}
          </Button>
        )
      })}
    </div>
  )
}

// ============================================================
// Main Page
// ============================================================

export function DeployPage() {
  const { config, updateConfig, addEnvVar, removeEnvVar, updateEnvVar, resetConfig } =
    useDeployStore()

  const [newEnvKey, setNewEnvKey] = useState('')
  const [newEnvValue, setNewEnvValue] = useState('')
  const [newEnvSecret, setNewEnvSecret] = useState(false)
  const [revealedKeys, setRevealedKeys] = useState<Set<string>>(new Set())

  // ---- Health / Version queries ----
  const healthQuery = useQuery({
    queryKey: ['health'],
    queryFn: () => healthAPI.check(),
    refetchInterval: HEALTH_REFETCH_INTERVAL,
    retry: false,
  })

  const versionQuery = useQuery({
    queryKey: ['version'],
    queryFn: () => healthAPI.version(),
    retry: false,
  })

  // ---- Derived values ----
  const dockerfile = useMemo(
    () => generateDockerfile(config.host, config.port, config.workers, config.dbUrl, config.envVars),
    [config.host, config.port, config.workers, config.dbUrl, config.envVars],
  )

  const dockerRunCmd = useMemo(
    () => generateDockerRun(config.port, config.envVars),
    [config.port, config.envVars],
  )

  const existingEnvKeys = useMemo(
    () => new Set(config.envVars.map((ev) => ev.key)),
    [config.envVars],
  )

  // ---- Handlers ----
  const handleAddEnvVar = useCallback(() => {
    const trimmedKey = newEnvKey.trim()
    if (!trimmedKey) return
    if (existingEnvKeys.has(trimmedKey)) return

    addEnvVar({ key: trimmedKey, value: newEnvValue, isSecret: newEnvSecret })
    setNewEnvKey('')
    setNewEnvValue('')
    setNewEnvSecret(false)
  }, [newEnvKey, newEnvValue, newEnvSecret, existingEnvKeys, addEnvVar])

  const handleAddPreset = useCallback(
    (v: EnvVar) => {
      addEnvVar(v)
    },
    [addEnvVar],
  )

  const handleToggleReveal = useCallback((key: string) => {
    setRevealedKeys((prev) => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }, [])

  const handleHostChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      updateConfig({ host: e.target.value })
    },
    [updateConfig],
  )

  const handleDbUrlChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      updateConfig({ dbUrl: e.target.value })
    },
    [updateConfig],
  )

  const handlePortChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const val = parseInt(e.target.value, 10)
      if (!isNaN(val) && val > 0 && val <= 65535) {
        updateConfig({ port: val })
      }
    },
    [updateConfig],
  )

  const handleWorkersChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const val = parseInt(e.target.value, 10)
      if (!isNaN(val) && val > 0 && val <= 32) {
        updateConfig({ workers: val })
      }
    },
    [updateConfig],
  )

  return (
    <div className="space-y-6">
      {/* ---- Page Header ---- */}
      <div>
        <h1 className="text-display-medium">Deploy</h1>
        <p className="text-body-medium text-(--color-text-secondary) mt-1">
          Deployment guides, Docker config generator, and API reference
        </p>
      </div>

      {/* ---- Deployment Guides ---- */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {DEPLOY_GUIDES.map((guide) => (
          <Card key={guide.title} className="hover:shadow-lg transition-shadow">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-(--color-background-secondary) flex items-center justify-center">
                <guide.icon className="w-5 h-5 text-(--color-text-secondary)" />
              </div>
              <div>
                <h2 className="text-heading-small">{guide.title}</h2>
                <Badge variant="outline">{guide.badge}</Badge>
              </div>
            </div>
            <p className="text-body-medium text-(--color-text-tertiary) mb-4">
              {guide.description}
            </p>
            <div className="space-y-2">
              {guide.steps.map((step, i) => (
                <div key={step} className="flex items-start gap-2">
                  <span className="text-label-small text-(--color-accent-primary) shrink-0 mt-0.5">
                    {i + 1}.
                  </span>
                  <code className="text-body-small font-mono bg-(--color-background-secondary) px-2 py-1 rounded text-(--color-text-primary) break-all">
                    {step}
                  </code>
                </div>
              ))}
            </div>
          </Card>
        ))}
      </div>

      {/* ============================================================ */}
      {/* Section A: Docker Config Generator */}
      {/* ============================================================ */}
      <Card>
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Container className="w-5 h-5 text-(--color-text-secondary)" />
            <h2 className="text-heading-small">Docker Config Generator</h2>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={resetConfig}
            aria-label="Reset configuration to defaults"
          >
            <RotateCcw className="w-4 h-4 mr-1.5" />
            Reset
          </Button>
        </div>

        {/* Form fields */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div>
            <label
              htmlFor="deploy-host"
              className="block text-label-small text-(--color-text-secondary) mb-1.5"
            >
              Host
            </label>
            <Input
              id="deploy-host"
              value={config.host}
              onChange={handleHostChange}
              placeholder="localhost"
            />
          </div>
          <div>
            <label
              htmlFor="deploy-port"
              className="block text-label-small text-(--color-text-secondary) mb-1.5"
            >
              Port
            </label>
            <Input
              id="deploy-port"
              type="number"
              value={config.port}
              onChange={handlePortChange}
              min={1}
              max={65535}
            />
          </div>
          <div>
            <label
              htmlFor="deploy-workers"
              className="block text-label-small text-(--color-text-secondary) mb-1.5"
            >
              Workers
            </label>
            <Input
              id="deploy-workers"
              type="number"
              value={config.workers}
              onChange={handleWorkersChange}
              min={1}
              max={32}
            />
          </div>
          <div>
            <label
              htmlFor="deploy-dburl"
              className="block text-label-small text-(--color-text-secondary) mb-1.5"
            >
              Database URL
            </label>
            <Input
              id="deploy-dburl"
              value={config.dbUrl}
              onChange={handleDbUrlChange}
              placeholder="postgresql://... (blank = SQLite)"
            />
          </div>
        </div>

        {/* Generated Dockerfile */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-label-small text-(--color-text-secondary)">
              Generated Dockerfile
            </span>
            <div className="flex gap-2">
              <CopyButton text={dockerfile} label="Copy Dockerfile" />
              <CopyButton text={dockerRunCmd} label="Copy docker run" />
            </div>
          </div>
          <pre className="bg-(--color-background-secondary) text-(--color-text-primary) text-body-small font-mono p-4 rounded-lg overflow-x-auto whitespace-pre leading-relaxed border border-(--color-border-default)">
            {dockerfile}
          </pre>
        </div>

        {/* docker run preview */}
        <div>
          <span className="text-label-small text-(--color-text-secondary) block mb-2">
            Docker Run Command
          </span>
          <pre className="bg-(--color-background-secondary) text-(--color-text-primary) text-body-small font-mono p-4 rounded-lg overflow-x-auto whitespace-pre border border-(--color-border-default)">
            {dockerRunCmd}
          </pre>
        </div>
      </Card>

      {/* ============================================================ */}
      {/* Section B: Environment Variables */}
      {/* ============================================================ */}
      <Card>
        <div className="flex items-center gap-3 mb-4">
          <Key className="w-5 h-5 text-(--color-text-secondary)" />
          <h2 className="text-heading-small">Environment Variables</h2>
        </div>

        {/* Presets */}
        <div className="mb-4">
          <span className="text-label-small text-(--color-text-tertiary) block mb-2">
            Common Presets
          </span>
          <EnvVarPresetButtons
            existingKeys={existingEnvKeys}
            onAdd={handleAddPreset}
          />
        </div>

        {/* Env var table */}
        {config.envVars.length > 0 && (
          <div className="border border-(--color-border-default) rounded-lg overflow-hidden mb-4">
            <table className="w-full text-body-small" role="table">
              <thead>
                <tr className="bg-(--color-background-secondary)">
                  <th className="text-left px-4 py-2.5 text-label-small text-(--color-text-secondary) font-medium">
                    Key
                  </th>
                  <th className="text-left px-4 py-2.5 text-label-small text-(--color-text-secondary) font-medium">
                    Value
                  </th>
                  <th className="text-center px-4 py-2.5 text-label-small text-(--color-text-secondary) font-medium w-20">
                    Secret
                  </th>
                  <th className="w-20" />
                </tr>
              </thead>
              <tbody>
                {config.envVars.map((ev) => (
                  <tr
                    key={ev.key}
                    className="border-t border-(--color-border-default)"
                  >
                    <td className="px-4 py-2.5 font-mono text-(--color-text-primary)">
                      {ev.key}
                    </td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2">
                        <Input
                          type={
                            ev.isSecret && !revealedKeys.has(ev.key)
                              ? 'password'
                              : 'text'
                          }
                          value={ev.value}
                          onChange={(e) =>
                            updateEnvVar(ev.key, { value: e.target.value })
                          }
                          className="flex-1"
                          aria-label={`Value for ${ev.key}`}
                        />
                        {ev.isSecret && (
                          <button
                            type="button"
                            onClick={() => handleToggleReveal(ev.key)}
                            className="p-1.5 rounded text-(--color-text-tertiary) hover:text-(--color-text-primary) hover:bg-(--color-background-secondary) transition-colors focus:outline-none focus:ring-2 focus:ring-(--color-accent-primary)"
                            aria-label={
                              revealedKeys.has(ev.key)
                                ? `Hide value for ${ev.key}`
                                : `Show value for ${ev.key}`
                            }
                          >
                            {revealedKeys.has(ev.key) ? (
                              <EyeOff className="w-4 h-4" />
                            ) : (
                              <Eye className="w-4 h-4" />
                            )}
                          </button>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-2.5 text-center">
                      <Toggle
                        checked={ev.isSecret}
                        onChange={(checked) =>
                          updateEnvVar(ev.key, { isSecret: checked })
                        }
                      />
                    </td>
                    <td className="px-4 py-2.5 text-center">
                      <button
                        type="button"
                        onClick={() => removeEnvVar(ev.key)}
                        className="p-1.5 rounded text-(--color-text-tertiary) hover:text-(--color-semantic-error) hover:bg-(--color-semantic-error-light) transition-colors focus:outline-none focus:ring-2 focus:ring-(--color-semantic-error)"
                        aria-label={`Remove ${ev.key}`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Add new row */}
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <label
              htmlFor="new-env-key"
              className="block text-label-small text-(--color-text-secondary) mb-1.5"
            >
              Key
            </label>
            <Input
              id="new-env-key"
              value={newEnvKey}
              onChange={(e) => setNewEnvKey(e.target.value)}
              placeholder="MY_VARIABLE"
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleAddEnvVar()
              }}
            />
          </div>
          <div className="flex-1">
            <label
              htmlFor="new-env-value"
              className="block text-label-small text-(--color-text-secondary) mb-1.5"
            >
              Value
            </label>
            <Input
              id="new-env-value"
              value={newEnvValue}
              onChange={(e) => setNewEnvValue(e.target.value)}
              placeholder="value"
              type={newEnvSecret ? 'password' : 'text'}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleAddEnvVar()
              }}
            />
          </div>
          <div className="flex items-center gap-2 pb-0.5">
            <span className="text-label-small text-(--color-text-tertiary)">
              Secret
            </span>
            <Toggle checked={newEnvSecret} onChange={setNewEnvSecret} />
          </div>
          <Button
            variant="secondary"
            size="md"
            onClick={handleAddEnvVar}
            disabled={!newEnvKey.trim() || existingEnvKeys.has(newEnvKey.trim())}
            aria-label="Add environment variable"
          >
            <Plus className="w-4 h-4 mr-1" />
            Add
          </Button>
        </div>
      </Card>

      {/* ============================================================ */}
      {/* Section C: API Endpoints Reference */}
      {/* ============================================================ */}
      <Card>
        <div className="flex items-center gap-3 mb-4">
          <Globe className="w-5 h-5 text-(--color-text-secondary)" />
          <h2 className="text-heading-small">API Endpoints Reference</h2>
        </div>
        <div className="border border-(--color-border-default) rounded-lg overflow-hidden">
          <table className="w-full text-body-small" role="table">
            <thead>
              <tr className="bg-(--color-background-secondary)">
                <th className="text-left px-4 py-2.5 text-label-small text-(--color-text-secondary) font-medium w-24">
                  Method
                </th>
                <th className="text-left px-4 py-2.5 text-label-small text-(--color-text-secondary) font-medium">
                  Endpoint
                </th>
                <th className="text-left px-4 py-2.5 text-label-small text-(--color-text-secondary) font-medium">
                  Description
                </th>
              </tr>
            </thead>
            <tbody>
              {API_ENDPOINTS.map((ep) => (
                <tr
                  key={`${ep.method}-${ep.path}`}
                  className="border-t border-(--color-border-default)"
                >
                  <td className="px-4 py-2.5">
                    <Badge variant={METHOD_BADGE_VARIANT[ep.method]}>
                      {ep.method}
                    </Badge>
                  </td>
                  <td className="px-4 py-2.5 font-mono text-(--color-text-primary)">
                    {ep.path}
                  </td>
                  <td className="px-4 py-2.5 text-(--color-text-tertiary)">
                    {ep.description}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* ============================================================ */}
      {/* Section D: Deployment Status */}
      {/* ============================================================ */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Server className="w-5 h-5 text-(--color-text-secondary)" />
            <h2 className="text-heading-small">Deployment Status</h2>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              healthQuery.refetch()
              versionQuery.refetch()
            }}
            disabled={healthQuery.isFetching}
            aria-label="Refresh deployment status"
          >
            <RefreshCw
              className={`w-4 h-4 mr-1.5 ${healthQuery.isFetching ? 'animate-spin' : ''}`}
            />
            Refresh
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Connection Status */}
          <div className="p-4 rounded-lg bg-(--color-background-secondary) border border-(--color-border-default)">
            <span className="text-label-small text-(--color-text-tertiary) block mb-2">
              Connection
            </span>
            <div className="flex items-center gap-2">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  healthQuery.isSuccess
                    ? 'bg-(--color-semantic-success)'
                    : healthQuery.isError
                      ? 'bg-(--color-semantic-error)'
                      : 'bg-(--color-border-default)'
                }`}
                aria-hidden="true"
              />
              <span className="text-body-medium text-(--color-text-primary)">
                {healthQuery.isSuccess
                  ? 'Connected'
                  : healthQuery.isError
                    ? 'Disconnected'
                    : 'Checking...'}
              </span>
            </div>
            <p className="text-body-small text-(--color-text-tertiary) mt-1">
              AutoGen Studio at{' '}
              <code className="bg-(--color-surface-card) px-1 py-0.5 rounded text-body-small">
                localhost:8081
              </code>
            </p>
          </div>

          {/* Version */}
          <div className="p-4 rounded-lg bg-(--color-background-secondary) border border-(--color-border-default)">
            <span className="text-label-small text-(--color-text-tertiary) block mb-2">
              Version
            </span>
            <span className="text-body-medium text-(--color-text-primary)">
              {versionQuery.isSuccess
                ? versionQuery.data.version
                : versionQuery.isError
                  ? 'Unavailable'
                  : 'Loading...'}
            </span>
          </div>

          {/* Auto-refresh indicator */}
          <div className="p-4 rounded-lg bg-(--color-background-secondary) border border-(--color-border-default)">
            <span className="text-label-small text-(--color-text-tertiary) block mb-2">
              Auto-Refresh
            </span>
            <span className="text-body-medium text-(--color-text-primary)">
              Every 30s
            </span>
            <p className="text-body-small text-(--color-text-tertiary) mt-1">
              {healthQuery.dataUpdatedAt
                ? `Last checked: ${new Date(healthQuery.dataUpdatedAt).toLocaleTimeString()}`
                : 'Not yet checked'}
            </p>
          </div>
        </div>

        {/* Current Instance */}
        <div className="mt-4 p-4 rounded-lg border border-(--color-border-default)">
          <div className="flex items-center gap-2 mb-2">
            <Rocket className="w-4 h-4 text-(--color-text-secondary)" />
            <span className="text-label-small text-(--color-text-secondary)">
              Current Instance
            </span>
          </div>
          <p className="text-body-medium text-(--color-text-tertiary)">
            AutoGen Studio is running at{' '}
            <code className="bg-(--color-background-secondary) px-1.5 py-0.5 rounded">
              localhost:8081
            </code>
            . The AG Frontend connects via Vite proxy at{' '}
            <code className="bg-(--color-background-secondary) px-1.5 py-0.5 rounded">
              localhost:5173
            </code>
            .
          </p>
        </div>
      </Card>
    </div>
  )
}
