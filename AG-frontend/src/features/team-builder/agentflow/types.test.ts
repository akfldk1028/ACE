import { describe, it, expect } from 'vitest'
import { patternToProvider } from './types'
import type { PatternType } from './types'

describe('patternToProvider', () => {
  it('maps sequential to RoundRobinGroupChat', () => {
    expect(patternToProvider('sequential')).toBe('autogen_agentchat.teams.RoundRobinGroupChat')
  })

  it('maps selector to SelectorGroupChat', () => {
    expect(patternToProvider('selector')).toBe('autogen_agentchat.teams.SelectorGroupChat')
  })

  it('maps handoff to Swarm', () => {
    expect(patternToProvider('handoff')).toBe('autogen_agentchat.teams.Swarm')
  })

  it('maps debate to SelectorGroupChat', () => {
    expect(patternToProvider('debate')).toBe('autogen_agentchat.teams.SelectorGroupChat')
  })

  it('maps reflection to RoundRobinGroupChat', () => {
    expect(patternToProvider('reflection')).toBe('autogen_agentchat.teams.RoundRobinGroupChat')
  })

  it('maps unknown to RoundRobinGroupChat (default)', () => {
    expect(patternToProvider('unknown')).toBe('autogen_agentchat.teams.RoundRobinGroupChat')
  })

  it('roundtrips: patternToProvider(sequential) contains RoundRobin', () => {
    const provider = patternToProvider('sequential')
    expect(provider).toContain('RoundRobin')
  })

  it('roundtrips: patternToProvider(handoff) contains Swarm', () => {
    const provider = patternToProvider('handoff')
    expect(provider).toContain('Swarm')
  })

  it('all known patterns return valid provider strings', () => {
    const patterns: PatternType[] = ['sequential', 'selector', 'handoff', 'debate', 'reflection', 'unknown']
    for (const p of patterns) {
      const provider = patternToProvider(p)
      expect(provider).toContain('autogen_agentchat.teams.')
    }
  })
})
