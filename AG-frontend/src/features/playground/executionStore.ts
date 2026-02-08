import { create } from 'zustand'
import type { WSMessage } from '@/shared/api/ws'
import type { BaseMessageConfig } from '@/shared/types/datamodel'

export interface AgentTurn {
  source: string
  content: string
  timestamp: string
  tokensIn?: number
  tokensOut?: number
}

interface ExecutionState {
  isRunning: boolean
  currentRunId: string | null
  turns: AgentTurn[]
  status: 'idle' | 'connecting' | 'running' | 'completed' | 'error'
  error: string | null

  startExecution: (runId: string) => void
  addTurn: (turn: AgentTurn) => void
  addWSMessage: (msg: WSMessage) => void
  completeExecution: () => void
  setError: (error: string) => void
  reset: () => void
}

export const useExecutionStore = create<ExecutionState>((set) => ({
  isRunning: false,
  currentRunId: null,
  turns: [],
  status: 'idle',
  error: null,

  startExecution: (runId) =>
    set({
      isRunning: true,
      currentRunId: runId,
      turns: [],
      status: 'connecting',
      error: null,
    }),

  addTurn: (turn) =>
    set((state) => ({ turns: [...state.turns, turn] })),

  addWSMessage: (msg) =>
    set((state) => {
      if (msg.type === 'message' && msg.data) {
        const data = msg.data as BaseMessageConfig & { content?: string }
        if (data.source && data.content) {
          const usage = data.models_usage
          const turn: AgentTurn = {
            source: data.source,
            content: data.content,
            timestamp: msg.timestamp ?? new Date().toISOString(),
            tokensIn: usage?.prompt_tokens,
            tokensOut: usage?.completion_tokens,
          }
          return { turns: [...state.turns, turn], status: 'running' as const }
        }
        return state
      }
      if (msg.type === 'completion' || msg.type === 'result') {
        return { status: 'completed' as const, isRunning: false }
      }
      if (msg.type === 'error') {
        return { status: 'error' as const, error: msg.error ?? 'Unknown error', isRunning: false }
      }
      return state
    }),

  completeExecution: () =>
    set({ isRunning: false, status: 'completed' }),

  setError: (error) =>
    set({ isRunning: false, status: 'error', error }),

  reset: () =>
    set({
      isRunning: false,
      currentRunId: null,
      turns: [],
      status: 'idle',
      error: null,
    }),
}))
