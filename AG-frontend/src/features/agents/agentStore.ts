import { create } from 'zustand'

interface AgentState {
  selectedAgentName: string | null
  selectAgent: (name: string | null) => void
}

export const useAgentStore = create<AgentState>((set) => ({
  selectedAgentName: null,
  selectAgent: (name) => set({ selectedAgentName: name }),
}))
