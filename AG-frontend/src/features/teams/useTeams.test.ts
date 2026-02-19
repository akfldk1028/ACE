import { describe, it, expect } from 'vitest'
import { getTeamName, getTeamPattern } from './useTeams'
import type { TeamResponse } from '@/shared/api'

function makeTeam(overrides: Partial<TeamResponse> = {}): TeamResponse {
  return {
    id: 1,
    component: null,
    ...overrides,
  }
}

describe('getTeamName', () => {
  it('returns label when component has label', () => {
    const team = makeTeam({
      component: { label: 'My Team', provider: 'test', component_type: 'team', config: {} as never },
    })
    expect(getTeamName(team)).toBe('My Team')
  })

  it('returns fallback Team #id when component is null', () => {
    expect(getTeamName(makeTeam({ id: 42 }))).toBe('Team #42')
  })

  it('returns fallback when component has no label', () => {
    const team = makeTeam({
      id: 7,
      component: { provider: 'test', component_type: 'team', config: {} as never },
    })
    expect(getTeamName(team)).toBe('Team #7')
  })
})

describe('getTeamPattern', () => {
  it('detects RoundRobin as sequential', () => {
    const team = makeTeam({
      component: {
        provider: 'autogen_agentchat.teams.RoundRobinGroupChat',
        component_type: 'team',
        config: {} as never,
      },
    })
    expect(getTeamPattern(team)).toBe('sequential')
  })

  it('detects Selector as selector', () => {
    const team = makeTeam({
      component: {
        provider: 'autogen_agentchat.teams.SelectorGroupChat',
        component_type: 'team',
        config: {} as never,
      },
    })
    expect(getTeamPattern(team)).toBe('selector')
  })

  it('detects Swarm as handoff', () => {
    const team = makeTeam({
      component: {
        provider: 'autogen_agentchat.teams.Swarm',
        component_type: 'team',
        config: {} as never,
      },
    })
    expect(getTeamPattern(team)).toBe('handoff')
  })

  it('detects MagenticOne as custom', () => {
    const team = makeTeam({
      component: {
        provider: 'autogen_agentchat.teams.MagenticOneGroupChat',
        component_type: 'team',
        config: {} as never,
      },
    })
    expect(getTeamPattern(team)).toBe('custom')
  })

  it('falls back to label-based detection for debate', () => {
    const team = makeTeam({
      component: {
        label: 'Debate Team',
        provider: 'some.unknown.provider',
        component_type: 'team',
        config: {} as never,
      },
    })
    expect(getTeamPattern(team)).toBe('selector')
  })

  it('falls back to label-based detection for reflection', () => {
    const team = makeTeam({
      component: {
        label: 'Reflection Team',
        provider: 'some.unknown.provider',
        component_type: 'team',
        config: {} as never,
      },
    })
    expect(getTeamPattern(team)).toBe('sequential')
  })

  it('falls back to label-based detection for handoff', () => {
    const team = makeTeam({
      component: {
        label: 'Handoff Pipeline',
        provider: 'some.unknown.provider',
        component_type: 'team',
        config: {} as never,
      },
    })
    expect(getTeamPattern(team)).toBe('handoff')
  })

  it('returns custom when no pattern matches', () => {
    const team = makeTeam({
      component: {
        label: 'My Cool Team',
        provider: 'some.unknown.provider',
        component_type: 'team',
        config: {} as never,
      },
    })
    expect(getTeamPattern(team)).toBe('custom')
  })

  it('returns custom when component is null', () => {
    expect(getTeamPattern(makeTeam())).toBe('custom')
  })
})
