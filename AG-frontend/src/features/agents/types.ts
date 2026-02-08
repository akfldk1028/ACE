// A2A Agent types - 1:1 match with JSON_MODULES/a2a_agents/*.json schema

export interface A2ASkill {
  name: string
  description: string
}

export interface A2AAgentConfig {
  name: string
  a2a_server_url: string
  description: string
  timeout: number
  skills: A2ASkill[]
}

export interface A2AAgent {
  provider: string        // "autogenstudio.a2a.A2AAgent"
  component_type: string  // "agent"
  version: number
  label: string
  description: string
  config: A2AAgentConfig
}

export interface A2AHealthStatus {
  name: string
  url: string
  healthy: boolean
  latency_ms?: number
  error?: string
}
