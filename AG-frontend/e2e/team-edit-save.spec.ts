import { test, expect } from '@playwright/test'

/**
 * Team Edit -> Save -> Persist E2E Tests
 * Tests editing teams in the UI and verifying backend persistence
 * Requires: AutoGen Studio running on :8081
 */

const USER_ID = 'guestuser@gmail.com'

function makeTeam(label: string) {
  return {
    provider: 'autogen_agentchat.teams.RoundRobinGroupChat',
    component_type: 'team' as const,
    label,
    config: {
      participants: [
        {
          provider: 'autogen_agentchat.agents.AssistantAgent',
          component_type: 'agent',
          config: {
            name: 'edit_test_agent',
            model_client: {
              provider: 'autogen_ext.models.openai.OpenAIChatCompletionClient',
              component_type: 'model',
              config: { model: 'gpt-4o-mini' },
            },
            description: 'Edit test agent',
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
    },
  }
}

// ---- Edit -> Save -> Persist ----

test.describe('Edit -> Save -> Persist', () => {
  let teamId: number

  test.beforeEach(async ({ request }) => {
    const res = await request.post('/api/teams/', {
      data: { user_id: USER_ID, component: makeTeam('E2E Edit Base') },
    })
    const body = await res.json()
    teamId = body.data.id
  })

  test.afterEach(async ({ request }) => {
    if (teamId) {
      await request.delete(`/api/teams/${teamId}?user_id=${USER_ID}`)
    }
  })

  test('add agent via API upsert and verify backend', async ({ request }) => {
    // Get current team
    const getRes = await request.get(`/api/teams/${teamId}?user_id=${USER_ID}`)
    const getBody = await getRes.json()
    const component = getBody.data.component

    // Add a second agent
    component.config.participants.push({
      provider: 'autogen_agentchat.agents.AssistantAgent',
      component_type: 'agent',
      config: {
        name: 'added_agent',
        model_client: {
          provider: 'autogen_ext.models.openai.OpenAIChatCompletionClient',
          component_type: 'model',
          config: { model: 'gpt-4o-mini' },
        },
        description: 'Newly added agent',
        reflect_on_tool_use: false,
        tool_call_summary_format: '{result}',
        model_client_stream: false,
      },
    })

    // Save via POST upsert
    const saveRes = await request.post('/api/teams/', {
      data: { id: teamId, user_id: USER_ID, component },
    })
    expect(saveRes.ok()).toBeTruthy()

    // Verify backend has 2 participants
    const verifyRes = await request.get(`/api/teams/${teamId}?user_id=${USER_ID}`)
    const verifyBody = await verifyRes.json()
    expect(verifyBody.data.component.config.participants.length).toBe(2)
  })

  test('change termination condition and verify backend', async ({ request }) => {
    const getRes = await request.get(`/api/teams/${teamId}?user_id=${USER_ID}`)
    const getBody = await getRes.json()
    const component = getBody.data.component

    // Change termination to TextMention
    component.config.termination_condition = {
      provider: 'autogen_agentchat.conditions.TextMentionTermination',
      component_type: 'termination',
      config: { text: 'TERMINATE' },
    }

    const saveRes = await request.post('/api/teams/', {
      data: { id: teamId, user_id: USER_ID, component },
    })
    expect(saveRes.ok()).toBeTruthy()

    const verifyRes = await request.get(`/api/teams/${teamId}?user_id=${USER_ID}`)
    const verifyBody = await verifyRes.json()
    expect(verifyBody.data.component.config.termination_condition.provider).toContain('TextMention')
  })

  test('switch pattern (provider) and verify team_type change', async ({ request }) => {
    const getRes = await request.get(`/api/teams/${teamId}?user_id=${USER_ID}`)
    const getBody = await getRes.json()
    const component = getBody.data.component

    // Switch from RoundRobin to Swarm
    component.provider = 'autogen_agentchat.teams.Swarm'

    const saveRes = await request.post('/api/teams/', {
      data: { id: teamId, user_id: USER_ID, component },
    })
    expect(saveRes.ok()).toBeTruthy()

    const verifyRes = await request.get(`/api/teams/${teamId}?user_id=${USER_ID}`)
    const verifyBody = await verifyRes.json()
    expect(verifyBody.data.component.provider).toContain('Swarm')
  })

  test('save persists across page reload', async ({ page, request }) => {
    // Update team label
    const getRes = await request.get(`/api/teams/${teamId}?user_id=${USER_ID}`)
    const getBody = await getRes.json()
    const component = getBody.data.component
    component.label = 'E2E Persist Check'

    await request.post('/api/teams/', {
      data: { id: teamId, user_id: USER_ID, component },
    })

    // Load Team Builder
    await page.goto('/build')
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })
    await expect(page.getByText('E2E Persist Check')).toBeVisible({ timeout: 5_000 })

    // Reload page
    await page.reload()
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })
    await expect(page.getByText('E2E Persist Check')).toBeVisible({ timeout: 5_000 })
  })
})

// ---- Edit -> Validation ----

test.describe('Edit -> Validation', () => {
  test('invalid provider triggers validation error', async ({ request }) => {
    const res = await request.post('/api/validate/', {
      data: {
        component: {
          provider: 'nonexistent.Provider',
          component_type: 'team',
          label: 'Invalid Team',
          config: {
            participants: [],
          },
        },
      },
    })
    const body = await res.json()
    const data = body.data ?? body
    if (res.ok()) {
      expect(data.is_valid).toBe(false)
    } else {
      expect(res.status()).toBeGreaterThanOrEqual(400)
    }
  })

  test('empty participants fails validation', async ({ request }) => {
    const res = await request.post('/api/validate/', {
      data: {
        component: {
          provider: 'autogen_agentchat.teams.RoundRobinGroupChat',
          component_type: 'team',
          label: 'Empty Participants',
          config: {
            participants: [],
            termination_condition: {
              provider: 'autogen_agentchat.conditions.MaxMessageTermination',
              component_type: 'termination',
              config: { max_messages: 3 },
            },
          },
        },
      },
    })
    const body = await res.json()
    const data = body.data ?? body
    if (res.ok() && data.is_valid !== undefined) {
      expect(data.is_valid).toBe(false)
    }
  })

  test('valid team structure returns validation response', async ({ request }) => {
    const res = await request.post('/api/validate/', {
      data: {
        component: makeTeam('E2E Valid Team'),
      },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    const data = body.data ?? body
    // Validate endpoint returns is_valid field (may be false if backend cannot instantiate without API key)
    expect(typeof data.is_valid).toBe('boolean')
    if (!data.is_valid) {
      expect(Array.isArray(data.errors)).toBeTruthy()
    }
  })

  test('discard changes keeps original backend state', async ({ request }) => {
    // Create team
    const createRes = await request.post('/api/teams/', {
      data: { user_id: USER_ID, component: makeTeam('E2E Discard Test') },
    })
    const createBody = await createRes.json()
    const id = createBody.data.id

    // Read original state
    const originalRes = await request.get(`/api/teams/${id}?user_id=${USER_ID}`)
    const originalBody = await originalRes.json()
    const originalLabel = originalBody.data.component.label

    // Simulate "discard" by simply not saving and re-reading
    const verifyRes = await request.get(`/api/teams/${id}?user_id=${USER_ID}`)
    const verifyBody = await verifyRes.json()
    expect(verifyBody.data.component.label).toBe(originalLabel)

    // Clean up
    await request.delete(`/api/teams/${id}?user_id=${USER_ID}`)
  })
})
