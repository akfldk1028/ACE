import { test, expect } from '@playwright/test'

/**
 * API Integration Tests
 * Verify that the platform correctly communicates with AutoGen Studio :8081
 * via Vite proxy (/api/* -> localhost:8081)
 */

test.describe('AutoGen Studio API Integration via Vite proxy', () => {
  test('GET /api/health returns healthy', async ({ request }) => {
    const res = await request.get('/api/health')
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    // Health endpoint: {"status":true,"message":"Service is healthy"} (no data field)
    expect(body.status).toBe(true)
    expect(body.message).toContain('healthy')
  })

  test('GET /api/version returns version string', async ({ request }) => {
    const res = await request.get('/api/version')
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.data.version).toMatch(/\d+\.\d+/)
  })

  test('GET /api/teams/ returns team list with data', async ({ request }) => {
    const res = await request.get('/api/teams/?user_id=guestuser@gmail.com')
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.status).toBe(true)
    expect(Array.isArray(body.data)).toBeTruthy()
    expect(body.data.length).toBeGreaterThan(0)

    // Each team has id + component
    const first = body.data[0]
    expect(first).toHaveProperty('id')
    expect(first).toHaveProperty('component')
    expect(first.component).toHaveProperty('label')
  })

  test('GET /api/sessions/ returns session list', async ({ request }) => {
    const res = await request.get('/api/sessions/?user_id=guestuser@gmail.com')
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.status).toBe(true)
    expect(Array.isArray(body.data)).toBeTruthy()
  })

  test('GET /api/gallery/ returns gallery entries', async ({ request }) => {
    const res = await request.get('/api/gallery/?user_id=guestuser@gmail.com')
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.status).toBe(true)
    expect(Array.isArray(body.data)).toBeTruthy()
    expect(body.data.length).toBeGreaterThan(0)
  })

  test('POST /api/teams/ creates a new team', async ({ request }) => {
    const teamComponent = {
      label: 'E2E Test Team',
      team_type: 'RoundRobinGroupChat',
      config: {
        participants: [
          {
            agent_type: 'AssistantAgent',
            config: {
              name: 'e2e_test_agent',
              model_client: {
                model: 'gpt-4o-mini',
                model_type: 'OpenAIChatCompletionClient',
              },
            },
          },
        ],
        termination_condition: {
          termination_type: 'MaxMessageTermination',
          max_messages: 3,
        },
      },
    }

    const res = await request.post('/api/teams/', {
      data: {
        user_id: 'guestuser@gmail.com',
        component: teamComponent,
      },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.status).toBe(true)
    expect(body.data.id).toBeDefined()
    expect(body.data.component.label).toBe('E2E Test Team')

    // Clean up: delete the team
    const deleteRes = await request.delete(
      `/api/teams/${body.data.id}?user_id=guestuser@gmail.com`,
    )
    expect(deleteRes.ok()).toBeTruthy()
  })

  test('GET /api/sessions/ returns session list (sessions exist)', async ({ request }) => {
    // We created sessions via Python earlier, verify they're accessible via Vite proxy
    const res = await request.get('/api/sessions/?user_id=guestuser@gmail.com')
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.status).toBe(true)
    expect(Array.isArray(body.data)).toBeTruthy()
    expect(body.data.length).toBeGreaterThan(0)

    // Each session has id + team_id
    const first = body.data[0]
    expect(first).toHaveProperty('id')
    expect(first).toHaveProperty('team_id')
  })

  test('GET /api/settings/ returns settings', async ({ request }) => {
    const res = await request.get('/api/settings/?user_id=guestuser@gmail.com')
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.status).toBe(true)
  })
})
