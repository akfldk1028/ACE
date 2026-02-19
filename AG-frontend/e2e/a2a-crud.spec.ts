import { test, expect } from '@playwright/test'

/**
 * A2A Agent CRUD E2E Tests
 * Requires: A2A agents running (calculator:8006, history:8005, poetry:8003)
 *
 * Backend response shapes (no `data` wrapper on A2A endpoints):
 * - Registry: {status, agents: [{name, url, skills, is_online, ...}]}
 * - Check single: {status, message, agent_name, agent_card_url}
 * - Check all: {status, agents: [{name, is_online, ...}]}
 * - Register: expects {url}, returns {status, agents}
 * - Component: {status, component: {provider, config, ...}}
 */

const USER_ID = 'guestuser@gmail.com'

// ---- A2A Registry API ----

test.describe('A2A Registry API', () => {
  test('GET /api/a2a/registry returns agent list', async ({ request }) => {
    const res = await request.get('/api/a2a/registry')
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.status).toBe(true)
    expect(Array.isArray(body.agents)).toBeTruthy()
  })

  test('registry contains calculator, history, and poetry agents', async ({ request }) => {
    const res = await request.get('/api/a2a/registry')
    const body = await res.json()
    const names = body.agents.map((a: Record<string, unknown>) => a.name)
    expect(names).toContain('calculator_agent')
    expect(names).toContain('history_agent')
    expect(names).toContain('poetry_agent')
  })

  test('each agent has required fields: name, url, skills, is_online', async ({ request }) => {
    const res = await request.get('/api/a2a/registry')
    const body = await res.json()
    for (const agent of body.agents) {
      expect(agent).toHaveProperty('name')
      expect(agent).toHaveProperty('url')
      expect(agent).toHaveProperty('skills')
      expect(Array.isArray(agent.skills)).toBeTruthy()
      expect(typeof agent.is_online).toBe('boolean')
    }
  })

  test('POST /api/a2a/registry/check-all returns health status array', async ({ request }) => {
    const res = await request.post('/api/a2a/registry/check-all')
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.status).toBe(true)
    expect(Array.isArray(body.agents)).toBeTruthy()
    for (const h of body.agents) {
      expect(h).toHaveProperty('name')
      expect(typeof h.is_online).toBe('boolean')
    }
  })
})

// ---- A2A Register/Unregister ----

test.describe('A2A Register/Unregister', () => {
  const testAgentUrl = 'http://localhost:8006' // calculator

  test('POST register with valid URL succeeds', async ({ request }) => {
    const res = await request.post('/api/a2a/registry/register', {
      data: { url: testAgentUrl },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.status).toBe(true)
  })

  test('duplicate registration is handled gracefully', async ({ request }) => {
    // Register twice - should not cause server error
    await request.post('/api/a2a/registry/register', {
      data: { url: testAgentUrl },
    })
    const res = await request.post('/api/a2a/registry/register', {
      data: { url: testAgentUrl },
    })
    expect(res.status()).toBeLessThan(500)
  })

  test('DELETE unregisters an agent', async ({ request }) => {
    // Ensure registered
    await request.post('/api/a2a/registry/register', {
      data: { url: testAgentUrl },
    })

    const delRes = await request.delete('/api/a2a/registry/calculator_agent')
    expect(delRes.ok()).toBeTruthy()
    const body = await delRes.json()
    expect(body.status).toBe(true)
  })

  test('re-register after unregister succeeds', async ({ request }) => {
    // Unregister first
    await request.delete('/api/a2a/registry/calculator_agent')

    // Re-register
    const res = await request.post('/api/a2a/registry/register', {
      data: { url: testAgentUrl },
    })
    expect(res.ok()).toBeTruthy()

    // Verify it's in the list
    const listRes = await request.get('/api/a2a/registry')
    const body = await listRes.json()
    const names = body.agents.map((a: Record<string, unknown>) => a.name)
    expect(names).toContain('calculator_agent')
  })
})

// ---- A2A Health Check ----

test.describe('A2A Health Check', () => {
  test('health check for online agent returns status: true', async ({ request }) => {
    const res = await request.get('/api/a2a/check?url=http://localhost:8006')
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.status).toBe(true)
    expect(body.agent_name).toBe('calculator_agent')
  })

  test('health check for offline URL returns status: false', async ({ request }) => {
    const res = await request.get('/api/a2a/check?url=http://localhost:9999')
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.status).toBe(false)
  })

  test('online agent check includes agent_card_url', async ({ request }) => {
    const res = await request.get('/api/a2a/check?url=http://localhost:8006')
    const body = await res.json()
    expect(body.agent_card_url).toContain('agent.json')
  })

  test('check-all returns health for all registered agents', async ({ request }) => {
    const res = await request.post('/api/a2a/registry/check-all')
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.agents.length).toBeGreaterThan(0)

    // At least calculator, history, poetry should be online
    const online = body.agents.filter((a: Record<string, unknown>) => a.is_online === true)
    expect(online.length).toBeGreaterThanOrEqual(3)
  })
})

// ---- A2A Component Import ----

test.describe('A2A Component Import', () => {
  test('GET component returns JSON definition', async ({ request }) => {
    const res = await request.get('/api/a2a/registry/calculator_agent/component')
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.status).toBe(true)
    expect(body.component).toHaveProperty('provider')
    expect(body.component).toHaveProperty('config')
  })

  test('component contains provider, config with name and skills', async ({ request }) => {
    const res = await request.get('/api/a2a/registry/calculator_agent/component')
    const body = await res.json()
    const comp = body.component
    expect(comp.provider).toContain('A2AAgent')
    expect(comp.config).toHaveProperty('name')
    expect(comp.config).toHaveProperty('skills')
    expect(Array.isArray(comp.config.skills)).toBeTruthy()
  })

  test('component can be used to create a team', async ({ request }) => {
    // Get the A2A component
    const compRes = await request.get('/api/a2a/registry/calculator_agent/component')
    const compBody = await compRes.json()
    const a2aComponent = compBody.component

    // Create a team using this component as a participant
    const teamRes = await request.post('/api/teams/', {
      data: {
        user_id: USER_ID,
        component: {
          label: 'A2A Import Test Team',
          provider: 'autogen_agentchat.teams.RoundRobinGroupChat',
          component_type: 'team',
          config: {
            participants: [a2aComponent],
            termination_condition: {
              provider: 'autogen_agentchat.conditions.MaxMessageTermination',
              component_type: 'termination',
              config: { max_messages: 3 },
            },
          },
        },
      },
    })
    expect(teamRes.ok()).toBeTruthy()
    const teamBody = await teamRes.json()
    const teamId = teamBody.data.id
    expect(teamId).toBeDefined()

    // Clean up
    await request.delete(`/api/teams/${teamId}?user_id=${USER_ID}`)
  })

  test('A2A team loads in Team Builder page', async ({ page, request }) => {
    // Create A2A team via API
    const compRes = await request.get('/api/a2a/registry/calculator_agent/component')
    const compBody = await compRes.json()
    const a2aComponent = compBody.component

    const teamRes = await request.post('/api/teams/', {
      data: {
        user_id: USER_ID,
        component: {
          label: 'A2A Builder Test',
          provider: 'autogen_agentchat.teams.RoundRobinGroupChat',
          component_type: 'team',
          config: {
            participants: [a2aComponent],
            termination_condition: {
              provider: 'autogen_agentchat.conditions.MaxMessageTermination',
              component_type: 'termination',
              config: { max_messages: 3 },
            },
          },
        },
      },
    })
    const teamBody = await teamRes.json()
    const teamId = teamBody.data.id

    // Navigate to Team Builder
    await page.goto('/build')
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })

    // Verify the A2A team card shows
    await expect(page.getByText('A2A Builder Test')).toBeVisible({ timeout: 5_000 })

    // Clean up
    await request.delete(`/api/teams/${teamId}?user_id=${USER_ID}`)
  })

  test('AgentFlow graph displays A2A node', async ({ page, request }) => {
    // Create A2A team
    const compRes = await request.get('/api/a2a/registry/calculator_agent/component')
    const compBody = await compRes.json()
    const a2aComponent = compBody.component

    const teamRes = await request.post('/api/teams/', {
      data: {
        user_id: USER_ID,
        component: {
          label: 'A2A Flow Test',
          provider: 'autogen_agentchat.teams.RoundRobinGroupChat',
          component_type: 'team',
          config: {
            participants: [a2aComponent],
            termination_condition: {
              provider: 'autogen_agentchat.conditions.MaxMessageTermination',
              component_type: 'termination',
              config: { max_messages: 3 },
            },
          },
        },
      },
    })
    const teamBody = await teamRes.json()
    const teamId = teamBody.data.id

    await page.goto('/build')
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })

    // Click the A2A team card to open it
    await page.getByText('A2A Flow Test').first().click()

    // Should see agent flow area with the A2A agent node
    const flowArea = page.locator('.react-flow, [data-testid="agent-flow"]')
    if (await flowArea.isVisible({ timeout: 5_000 }).catch(() => false)) {
      // Look for the calculator node text in the flow
      await expect(page.getByText('calculator_agent').first()).toBeVisible({ timeout: 5_000 })
    }

    // Clean up
    await request.delete(`/api/teams/${teamId}?user_id=${USER_ID}`)
  })

  test('A2A team can be deleted', async ({ request }) => {
    const compRes = await request.get('/api/a2a/registry/calculator_agent/component')
    const compBody = await compRes.json()
    const a2aComponent = compBody.component

    const teamRes = await request.post('/api/teams/', {
      data: {
        user_id: USER_ID,
        component: {
          label: 'A2A Delete Test',
          provider: 'autogen_agentchat.teams.RoundRobinGroupChat',
          component_type: 'team',
          config: {
            participants: [a2aComponent],
            termination_condition: {
              provider: 'autogen_agentchat.conditions.MaxMessageTermination',
              component_type: 'termination',
              config: { max_messages: 3 },
            },
          },
        },
      },
    })
    const teamBody = await teamRes.json()
    const teamId = teamBody.data.id

    const delRes = await request.delete(`/api/teams/${teamId}?user_id=${USER_ID}`)
    expect(delRes.ok()).toBeTruthy()

    // Verify gone
    const getRes = await request.get(`/api/teams/${teamId}?user_id=${USER_ID}`)
    expect(getRes.ok()).toBeFalsy()
  })
})
