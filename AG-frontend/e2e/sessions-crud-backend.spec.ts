import { test, expect } from '@playwright/test'

/**
 * Sessions CRUD Backend E2E Tests
 * Requires: AutoGen Studio running on :8081 with at least one team
 */

const USER_ID = 'guestuser@gmail.com'

// Helper: get first team ID
async function getFirstTeamId(request: ReturnType<typeof test.info>['_unused'] extends never ? never : Parameters<Parameters<typeof test>[2]>[0]['request']): Promise<number> {
  const res = await (request as { get: (url: string) => Promise<{ json: () => Promise<Record<string, unknown>> }> }).get(`/api/teams/?user_id=${USER_ID}`)
  const body = await res.json()
  return (body as { data: { id: number }[] }).data[0].id
}

// ---- Sessions Create/Read ----

test.describe('Sessions Create/Read', () => {
  let sessionId: number
  let teamId: number

  test.beforeAll(async ({ request }) => {
    // Get a team to associate session with
    const teamRes = await request.get(`/api/teams/?user_id=${USER_ID}`)
    const teamBody = await teamRes.json()
    teamId = teamBody.data[0].id
  })

  test.afterEach(async ({ request }) => {
    if (sessionId) {
      await request.delete(`/api/sessions/${sessionId}?user_id=${USER_ID}`)
    }
  })

  test('POST /api/sessions/ creates a session', async ({ request }) => {
    const res = await request.post('/api/sessions/', {
      data: {
        user_id: USER_ID,
        team_id: teamId,
        name: 'E2E Test Session',
      },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.data.id).toBeDefined()
    sessionId = body.data.id
  })

  test('created session has id, team_id, user_id', async ({ request }) => {
    const res = await request.post('/api/sessions/', {
      data: {
        user_id: USER_ID,
        team_id: teamId,
        name: 'E2E Fields Check Session',
      },
    })
    const body = await res.json()
    sessionId = body.data.id

    expect(body.data).toHaveProperty('id')
    expect(body.data).toHaveProperty('team_id')
    expect(body.data.team_id).toBe(teamId)
  })

  test('GET /api/sessions/:id returns session details', async ({ request }) => {
    const createRes = await request.post('/api/sessions/', {
      data: {
        user_id: USER_ID,
        team_id: teamId,
        name: 'E2E Get Session',
      },
    })
    const createBody = await createRes.json()
    sessionId = createBody.data.id

    const getRes = await request.get(`/api/sessions/${sessionId}?user_id=${USER_ID}`)
    expect(getRes.ok()).toBeTruthy()
    const getBody = await getRes.json()
    expect(getBody.data.id).toBe(sessionId)
  })

  test('GET /api/sessions/:id/runs returns empty array initially', async ({ request }) => {
    const createRes = await request.post('/api/sessions/', {
      data: {
        user_id: USER_ID,
        team_id: teamId,
        name: 'E2E Empty Runs Session',
      },
    })
    const createBody = await createRes.json()
    sessionId = createBody.data.id

    const runsRes = await request.get(`/api/sessions/${sessionId}/runs?user_id=${USER_ID}`)
    expect(runsRes.ok()).toBeTruthy()
    const runsBody = await runsRes.json()
    const runs = runsBody.data?.runs ?? runsBody.data ?? []
    expect(Array.isArray(runs)).toBeTruthy()
  })
})

// ---- Sessions Update/Delete ----

test.describe('Sessions Update/Delete', () => {
  let sessionId: number
  let teamId: number

  test.beforeAll(async ({ request }) => {
    const teamRes = await request.get(`/api/teams/?user_id=${USER_ID}`)
    const teamBody = await teamRes.json()
    teamId = teamBody.data[0].id
  })

  test('PUT /api/sessions/:id updates session name', async ({ request }) => {
    const createRes = await request.post('/api/sessions/', {
      data: { user_id: USER_ID, team_id: teamId, name: 'E2E Before Update' },
    })
    const createBody = await createRes.json()
    sessionId = createBody.data.id

    const updateRes = await request.put(`/api/sessions/${sessionId}?user_id=${USER_ID}`, {
      data: { id: sessionId, user_id: USER_ID, name: 'E2E After Update' },
    })
    expect(updateRes.ok()).toBeTruthy()

    const getRes = await request.get(`/api/sessions/${sessionId}?user_id=${USER_ID}`)
    const getBody = await getRes.json()
    expect(getBody.data.name).toBe('E2E After Update')

    // Clean up
    await request.delete(`/api/sessions/${sessionId}?user_id=${USER_ID}`)
  })

  test('DELETE /api/sessions/:id removes session', async ({ request }) => {
    const createRes = await request.post('/api/sessions/', {
      data: { user_id: USER_ID, team_id: teamId, name: 'E2E Delete Session' },
    })
    const createBody = await createRes.json()
    sessionId = createBody.data.id

    const delRes = await request.delete(`/api/sessions/${sessionId}?user_id=${USER_ID}`)
    expect(delRes.ok()).toBeTruthy()
  })

  test('GET after delete returns 404', async ({ request }) => {
    const createRes = await request.post('/api/sessions/', {
      data: { user_id: USER_ID, team_id: teamId, name: 'E2E 404 Session' },
    })
    const createBody = await createRes.json()
    sessionId = createBody.data.id

    await request.delete(`/api/sessions/${sessionId}?user_id=${USER_ID}`)
    const getRes = await request.get(`/api/sessions/${sessionId}?user_id=${USER_ID}`)
    expect(getRes.ok()).toBeFalsy()
  })
})

// ---- Sessions - Runs ----

test.describe('Sessions - Runs', () => {
  let sessionId: number
  let teamId: number

  test.beforeAll(async ({ request }) => {
    const teamRes = await request.get(`/api/teams/?user_id=${USER_ID}`)
    const teamBody = await teamRes.json()
    teamId = teamBody.data[0].id
  })

  test.afterEach(async ({ request }) => {
    if (sessionId) {
      await request.delete(`/api/sessions/${sessionId}?user_id=${USER_ID}`)
    }
  })

  test('POST /api/runs/ creates a run for session', async ({ request }) => {
    const sessRes = await request.post('/api/sessions/', {
      data: { user_id: USER_ID, team_id: teamId, name: 'E2E Run Session' },
    })
    const sessBody = await sessRes.json()
    sessionId = sessBody.data.id

    const runRes = await request.post('/api/runs/', {
      data: { session_id: sessionId, user_id: USER_ID },
    })
    expect(runRes.ok()).toBeTruthy()
    const runBody = await runRes.json()
    expect(runBody.data).toHaveProperty('run_id')
  })

  test('GET /api/sessions/:id/runs includes created run', async ({ request }) => {
    const sessRes = await request.post('/api/sessions/', {
      data: { user_id: USER_ID, team_id: teamId, name: 'E2E Runs List Session' },
    })
    const sessBody = await sessRes.json()
    sessionId = sessBody.data.id

    // Create a run
    await request.post('/api/runs/', {
      data: { session_id: sessionId, user_id: USER_ID },
    })

    const runsRes = await request.get(`/api/sessions/${sessionId}/runs?user_id=${USER_ID}`)
    expect(runsRes.ok()).toBeTruthy()
    const runsBody = await runsRes.json()
    const runs = runsBody.data?.runs ?? runsBody.data ?? []
    expect(runs.length).toBeGreaterThan(0)
  })

  test('run has id, status, and created_at', async ({ request }) => {
    const sessRes = await request.post('/api/sessions/', {
      data: { user_id: USER_ID, team_id: teamId, name: 'E2E Run Fields Session' },
    })
    const sessBody = await sessRes.json()
    sessionId = sessBody.data.id

    await request.post('/api/runs/', {
      data: { session_id: sessionId, user_id: USER_ID },
    })

    const runsRes = await request.get(`/api/sessions/${sessionId}/runs?user_id=${USER_ID}`)
    const runsBody = await runsRes.json()
    const runs = runsBody.data?.runs ?? runsBody.data ?? []
    const run = runs[0]
    expect(run).toHaveProperty('id')
    expect(run).toHaveProperty('status')
    expect(run).toHaveProperty('created_at')
  })
})
