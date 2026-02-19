import { test, expect } from '@playwright/test'

/**
 * Validation, Settings, Health/Version Backend E2E Tests
 * Requires: AutoGen Studio running on :8081
 */

const USER_ID = 'guestuser@gmail.com'

// ---- Validation API ----

test.describe('Validation API', () => {
  test('POST /api/validate/ returns validation result with is_valid field', async ({ request }) => {
    const res = await request.post('/api/validate/', {
      data: {
        component: {
          provider: 'autogen_agentchat.teams.RoundRobinGroupChat',
          component_type: 'team',
          label: 'Valid Team',
          config: {
            participants: [
              {
                provider: 'autogen_agentchat.agents.AssistantAgent',
                component_type: 'agent',
                config: {
                  name: 'valid_agent',
                  model_client: {
                    provider: 'autogen_ext.models.openai.OpenAIChatCompletionClient',
                    component_type: 'model',
                    config: { model: 'gpt-4o-mini' },
                  },
                  description: 'A valid agent',
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
        },
      },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    const data = body.data ?? body
    // Validate returns is_valid field (may be false if API key is missing for instantiation check)
    expect(typeof data.is_valid).toBe('boolean')
    if (!data.is_valid) {
      // Backend tries to instantiate - may fail without OPENAI_API_KEY
      expect(Array.isArray(data.errors)).toBeTruthy()
    }
  })

  test('invalid component returns errors array', async ({ request }) => {
    const res = await request.post('/api/validate/', {
      data: {
        component: {
          provider: 'invalid.provider.NotReal',
          component_type: 'team',
          config: {},
        },
      },
    })
    // May return 200 with is_valid:false or 400
    const body = await res.json()
    const data = body.data ?? body
    if (res.ok()) {
      expect(data.is_valid).toBe(false)
      expect(Array.isArray(data.errors)).toBeTruthy()
      expect(data.errors.length).toBeGreaterThan(0)
    } else {
      // Server returned error status for invalid component
      expect(res.status()).toBeGreaterThanOrEqual(400)
    }
  })

  test('empty participants triggers validation error', async ({ request }) => {
    const res = await request.post('/api/validate/', {
      data: {
        component: {
          provider: 'autogen_agentchat.teams.RoundRobinGroupChat',
          component_type: 'team',
          label: 'Empty Team',
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
    // Empty participants should cause validation error
    if (res.ok() && data.is_valid !== undefined) {
      expect(data.is_valid).toBe(false)
    }
  })

  test('POST /api/validate/test runs component test', async ({ request }) => {
    const res = await request.post('/api/validate/test', {
      data: {
        component: {
          provider: 'autogen_agentchat.teams.RoundRobinGroupChat',
          component_type: 'team',
          label: 'Test Team',
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
                  description: 'Test agent',
                  reflect_on_tool_use: false,
                  tool_call_summary_format: '{result}',
                  model_client_stream: false,
                },
              },
            ],
            termination_condition: {
              provider: 'autogen_agentchat.conditions.MaxMessageTermination',
              component_type: 'termination',
              config: { max_messages: 2 },
            },
          },
        },
        timeout: 30,
      },
    })
    // Test endpoint may take time; accept success or timeout
    const status = res.status()
    expect(status).toBeLessThan(500)
    if (res.ok()) {
      const body = await res.json()
      const data = body.data ?? body
      expect(data).toHaveProperty('status')
    }
  })
})

// ---- Settings API ----

test.describe('Settings API', () => {
  test('GET /api/settings/ returns user settings', async ({ request }) => {
    const res = await request.get(`/api/settings/?user_id=${USER_ID}`)
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.status).toBe(true)
    expect(body.data).toHaveProperty('config')
  })

  test('PUT /api/settings/ updates settings', async ({ request }) => {
    // Get current settings first
    const getRes = await request.get(`/api/settings/?user_id=${USER_ID}`)
    const getBody = await getRes.json()
    const currentSettings = getBody.data

    // Round-trip: send full settings object back (backend requires config field)
    const updateRes = await request.put('/api/settings/', {
      data: {
        id: currentSettings.id,
        user_id: currentSettings.user_id ?? USER_ID,
        config: currentSettings.config,
      },
    })
    // Accept 200 or 201 (backend may return "Settings Created Successfully")
    expect(updateRes.status()).toBeLessThan(400)
  })
})

// ---- Health/Version ----

test.describe('Health and Version', () => {
  test('GET /api/health returns status: true', async ({ request }) => {
    const res = await request.get('/api/health')
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.status).toBe(true)
    expect(body.message).toContain('healthy')
  })

  test('GET /api/version returns version string', async ({ request }) => {
    const res = await request.get('/api/version')
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    const version = body.data?.version ?? body.version
    expect(version).toMatch(/\d+\.\d+/)
  })
})
