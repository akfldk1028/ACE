import { test, expect } from '@playwright/test'

/**
 * Teams CRUD Backend E2E Tests
 * Requires: AutoGen Studio running on :8081
 * Tests full Create/Read/Update/Delete lifecycle via API
 */

const USER_ID = 'guestuser@gmail.com'

function makeTeamComponent(label: string, teamType: string, extras?: Record<string, unknown>) {
  const providerMap: Record<string, string> = {
    RoundRobinGroupChat: 'autogen_agentchat.teams.RoundRobinGroupChat',
    SelectorGroupChat: 'autogen_agentchat.teams.SelectorGroupChat',
    Swarm: 'autogen_agentchat.teams.Swarm',
  }
  const base = {
    label,
    provider: providerMap[teamType] ?? providerMap.RoundRobinGroupChat,
    component_type: 'team' as const,
    config: {
      participants: [
        {
          provider: 'autogen_agentchat.agents.AssistantAgent',
          component_type: 'agent',
          config: {
            name: 'test_agent',
            model_client: {
              provider: 'autogen_ext.models.openai.OpenAIChatCompletionClient',
              component_type: 'model',
              config: { model: 'gpt-4o-mini' },
            },
            description: 'E2E test agent',
            reflect_on_tool_use: false,
            tool_call_summary_format: '{result}',
            model_client_stream: false,
          },
        },
      ],
      termination_condition: {
        provider: 'autogen_agentchat.conditions.MaxMessageTermination',
        component_type: 'termination',
        config: { max_messages: 3 },
      },
      ...extras,
    },
  }
  return base
}

// ---- Teams Create ----

test.describe('Teams Create', () => {
  let createdIds: number[] = []

  test.afterEach(async ({ request }) => {
    for (const id of createdIds) {
      await request.delete(`/api/teams/${id}?user_id=${USER_ID}`)
    }
    createdIds = []
  })

  test('create Sequential pattern team (RoundRobinGroupChat)', async ({ request }) => {
    const res = await request.post('/api/teams/', {
      data: {
        user_id: USER_ID,
        component: makeTeamComponent('E2E Sequential Team', 'RoundRobinGroupChat'),
      },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.data.id).toBeDefined()
    expect(body.data.component.label).toBe('E2E Sequential Team')
    createdIds.push(body.data.id)
  })

  test('create Selector pattern team (SelectorGroupChat)', async ({ request }) => {
    const component = makeTeamComponent('E2E Selector Team', 'SelectorGroupChat', {
      model_client: {
        provider: 'autogen_ext.models.openai.OpenAIChatCompletionClient',
        component_type: 'model',
        config: { model: 'gpt-4o-mini' },
      },
      selector_prompt: 'Select the best agent.',
      allow_repeated_speaker: false,
    })
    const res = await request.post('/api/teams/', {
      data: { user_id: USER_ID, component },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.data.id).toBeDefined()
    createdIds.push(body.data.id)
  })

  test('create Handoff pattern team (Swarm)', async ({ request }) => {
    const res = await request.post('/api/teams/', {
      data: {
        user_id: USER_ID,
        component: makeTeamComponent('E2E Swarm Team', 'Swarm'),
      },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.data.id).toBeDefined()
    createdIds.push(body.data.id)
  })

  test('created team appears in GET /api/teams/ list', async ({ request }) => {
    const createRes = await request.post('/api/teams/', {
      data: {
        user_id: USER_ID,
        component: makeTeamComponent('E2E List Check Team', 'RoundRobinGroupChat'),
      },
    })
    const createBody = await createRes.json()
    const newId = createBody.data.id
    createdIds.push(newId)

    const listRes = await request.get(`/api/teams/?user_id=${USER_ID}`)
    const listBody = await listRes.json()
    const ids = listBody.data.map((t: Record<string, unknown>) => t.id)
    expect(ids).toContain(newId)
  })
})

// ---- Teams Update (POST upsert) ----

test.describe('Teams Update', () => {
  let teamId: number

  test.beforeEach(async ({ request }) => {
    const res = await request.post('/api/teams/', {
      data: {
        user_id: USER_ID,
        component: makeTeamComponent('E2E Update Base', 'RoundRobinGroupChat'),
      },
    })
    const body = await res.json()
    teamId = body.data.id
  })

  test.afterEach(async ({ request }) => {
    await request.delete(`/api/teams/${teamId}?user_id=${USER_ID}`)
  })

  test('POST upsert changes team label', async ({ request }) => {
    const updated = makeTeamComponent('E2E Updated Label', 'RoundRobinGroupChat')
    const res = await request.post('/api/teams/', {
      data: { id: teamId, user_id: USER_ID, component: updated },
    })
    expect(res.ok()).toBeTruthy()

    const getRes = await request.get(`/api/teams/${teamId}?user_id=${USER_ID}`)
    const getBody = await getRes.json()
    expect(getBody.data.component.label).toBe('E2E Updated Label')
  })

  test('update termination condition (MaxMessage to TextMention)', async ({ request }) => {
    const updated = makeTeamComponent('E2E Update Base', 'RoundRobinGroupChat')
    updated.config.termination_condition = {
      provider: 'autogen_agentchat.conditions.TextMentionTermination',
      component_type: 'termination',
      config: { text: 'TERMINATE' },
    }
    const res = await request.post('/api/teams/', {
      data: { id: teamId, user_id: USER_ID, component: updated },
    })
    expect(res.ok()).toBeTruthy()

    const getRes = await request.get(`/api/teams/${teamId}?user_id=${USER_ID}`)
    const getBody = await getRes.json()
    expect(getBody.data.component.config.termination_condition.provider).toContain(
      'TextMention',
    )
  })

  test('add agent to participants array', async ({ request }) => {
    const updated = makeTeamComponent('E2E Update Base', 'RoundRobinGroupChat')
    updated.config.participants.push({
      provider: 'autogen_agentchat.agents.AssistantAgent',
      component_type: 'agent',
      config: {
        name: 'second_agent',
        model_client: {
          provider: 'autogen_ext.models.openai.OpenAIChatCompletionClient',
          component_type: 'model',
          config: { model: 'gpt-4o-mini' },
        },
        description: 'Second test agent',
        reflect_on_tool_use: false,
        tool_call_summary_format: '{result}',
        model_client_stream: false,
      },
    })
    const res = await request.post('/api/teams/', {
      data: { id: teamId, user_id: USER_ID, component: updated },
    })
    expect(res.ok()).toBeTruthy()

    const getRes = await request.get(`/api/teams/${teamId}?user_id=${USER_ID}`)
    const getBody = await getRes.json()
    expect(getBody.data.component.config.participants.length).toBe(2)
  })

  test('GET /api/teams/:id reflects all changes', async ({ request }) => {
    const updated = makeTeamComponent('E2E Verify Changes', 'RoundRobinGroupChat')
    await request.post('/api/teams/', {
      data: { id: teamId, user_id: USER_ID, component: updated },
    })

    const getRes = await request.get(`/api/teams/${teamId}?user_id=${USER_ID}`)
    expect(getRes.ok()).toBeTruthy()
    const getBody = await getRes.json()
    expect(getBody.data.component.label).toBe('E2E Verify Changes')
    expect(getBody.data.id).toBe(teamId)
  })
})

// ---- Teams Delete ----

test.describe('Teams Delete', () => {
  test('DELETE /api/teams/:id removes team', async ({ request }) => {
    const createRes = await request.post('/api/teams/', {
      data: {
        user_id: USER_ID,
        component: makeTeamComponent('E2E Delete Test', 'RoundRobinGroupChat'),
      },
    })
    const createBody = await createRes.json()
    const id = createBody.data.id

    const delRes = await request.delete(`/api/teams/${id}?user_id=${USER_ID}`)
    expect(delRes.ok()).toBeTruthy()
  })

  test('GET after delete returns 404', async ({ request }) => {
    const createRes = await request.post('/api/teams/', {
      data: {
        user_id: USER_ID,
        component: makeTeamComponent('E2E 404 Test', 'RoundRobinGroupChat'),
      },
    })
    const createBody = await createRes.json()
    const id = createBody.data.id

    await request.delete(`/api/teams/${id}?user_id=${USER_ID}`)
    const getRes = await request.get(`/api/teams/${id}?user_id=${USER_ID}`)
    expect(getRes.ok()).toBeFalsy()
  })

  test('deleted team removed from list', async ({ request }) => {
    const createRes = await request.post('/api/teams/', {
      data: {
        user_id: USER_ID,
        component: makeTeamComponent('E2E Remove From List', 'RoundRobinGroupChat'),
      },
    })
    const createBody = await createRes.json()
    const id = createBody.data.id

    await request.delete(`/api/teams/${id}?user_id=${USER_ID}`)

    const listRes = await request.get(`/api/teams/?user_id=${USER_ID}`)
    const listBody = await listRes.json()
    const ids = listBody.data.map((t: Record<string, unknown>) => t.id)
    expect(ids).not.toContain(id)
  })
})

// ---- Teams Read ----

test.describe('Teams Read', () => {
  let ownTeamId: number

  test.beforeAll(async ({ request }) => {
    const res = await request.post('/api/teams/', {
      data: {
        user_id: USER_ID,
        component: makeTeamComponent('E2E Read Test Team', 'RoundRobinGroupChat'),
      },
    })
    const body = await res.json()
    ownTeamId = body.data.id
  })

  test.afterAll(async ({ request }) => {
    if (ownTeamId) {
      await request.delete(`/api/teams/${ownTeamId}?user_id=${USER_ID}`)
    }
  })

  test('GET /api/teams/:id returns full component', async ({ request }) => {
    const getRes = await request.get(`/api/teams/${ownTeamId}?user_id=${USER_ID}`)
    expect(getRes.ok()).toBeTruthy()
    const getBody = await getRes.json()
    expect(getBody.data).toHaveProperty('id')
    expect(getBody.data).toHaveProperty('component')
    expect(getBody.data.component).toHaveProperty('config')
  })

  test('GET /api/teams/ supports user_id filter', async ({ request }) => {
    const res = await request.get(`/api/teams/?user_id=${USER_ID}`)
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(Array.isArray(body.data)).toBeTruthy()
  })

  test('GET non-existent team returns 404', async ({ request }) => {
    const res = await request.get(`/api/teams/999999?user_id=${USER_ID}`)
    expect(res.ok()).toBeFalsy()
  })
})
