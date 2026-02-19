import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface EnvVar {
  key: string
  value: string
  isSecret: boolean
}

export interface DeployConfig {
  host: string
  port: number
  workers: number
  dbUrl: string
  envVars: EnvVar[]
}

const DEFAULT_CONFIG: DeployConfig = {
  host: 'localhost',
  port: 8081,
  workers: 1,
  dbUrl: '',
  envVars: [],
}

interface DeployState {
  config: DeployConfig
  updateConfig: (patch: Partial<DeployConfig>) => void
  addEnvVar: (v: EnvVar) => void
  removeEnvVar: (key: string) => void
  updateEnvVar: (key: string, patch: Partial<EnvVar>) => void
  resetConfig: () => void
}

export const useDeployStore = create<DeployState>()(
  persist(
    (set) => ({
      config: { ...DEFAULT_CONFIG },

      updateConfig: (patch) =>
        set((state) => ({
          config: { ...state.config, ...patch },
        })),

      addEnvVar: (v) =>
        set((state) => ({
          config: {
            ...state.config,
            envVars: [...state.config.envVars, v],
          },
        })),

      removeEnvVar: (key) =>
        set((state) => ({
          config: {
            ...state.config,
            envVars: state.config.envVars.filter((ev) => ev.key !== key),
          },
        })),

      updateEnvVar: (key, patch) =>
        set((state) => ({
          config: {
            ...state.config,
            envVars: state.config.envVars.map((ev) =>
              ev.key === key ? { ...ev, ...patch } : ev,
            ),
          },
        })),

      resetConfig: () =>
        set({ config: { ...DEFAULT_CONFIG, envVars: [] } }),
    }),
    {
      name: 'ag-deploy-config',
    },
  ),
)
