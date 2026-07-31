import { test, expect } from '@playwright/test'

/**
 * Gallery CRUD Backend E2E Tests
 * Requires: AutoGen Studio running on :8081
 */

const USER_ID = 'guestuser@gmail.com'

function makeGalleryConfig(name: string) {
  return {
    id: `e2e-gallery-${Date.now()}`,
    name,
    metadata: {
      author: 'e2e-test',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      version: '1.0.0',
      description: 'E2E test gallery',
    },
    components: {
      teams: [
        {
          provider: 'autogen_agentchat.teams.RoundRobinGroupChat',
          component_type: 'team',
          label: 'Gallery Team Template',
          config: {
            participants: [
              {
                provider: 'autogen_agentchat.agents.AssistantAgent',
                component_type: 'agent',
                config: {
                  name: 'gallery_agent',
                  model_client: {
                    provider: 'autogen_ext.models.openai.OpenAIChatCompletionClient',
                    component_type: 'model',
                    config: { model: 'gpt-4o-mini' },
                  },
                  description: 'Gallery template agent',
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
      ],
      agents: [],
      models: [],
      tools: [],
      workbenches: [],
      terminations: [],
    },
  }
}

// ---- Gallery Create/Read ----

test.describe('Gallery Create/Read', () => {
  let galleryId: number

  test.afterEach(async ({ request }) => {
    if (galleryId) {
      await request.delete(`/api/gallery/${galleryId}?user_id=${USER_ID}`)
    }
  })

  test('POST /api/gallery/ creates a gallery', async ({ request }) => {
    const res = await request.post('/api/gallery/', {
      data: {
        user_id: USER_ID,
        config: makeGalleryConfig('E2E Test Gallery'),
      },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.data.id).toBeDefined()
    galleryId = body.data.id
  })

  test('created gallery has name and components', async ({ request }) => {
    const res = await request.post('/api/gallery/', {
      data: {
        user_id: USER_ID,
        config: makeGalleryConfig('E2E Fields Gallery'),
      },
    })
    const body = await res.json()
    galleryId = body.data.id
    expect(body.data.config.name).toBe('E2E Fields Gallery')
    expect(body.data.config.components).toHaveProperty('teams')
  })

  test('GET /api/gallery/ list includes created gallery', async ({ request }) => {
    const createRes = await request.post('/api/gallery/', {
      data: {
        user_id: USER_ID,
        config: makeGalleryConfig('E2E List Gallery'),
      },
    })
    const createBody = await createRes.json()
    galleryId = createBody.data.id

    const listRes = await request.get(`/api/gallery/?user_id=${USER_ID}`)
    expect(listRes.ok()).toBeTruthy()
    const listBody = await listRes.json()
    const ids = listBody.data.map((g: Record<string, unknown>) => g.id)
    expect(ids).toContain(galleryId)
  })
})

// ---- Gallery Update/Delete ----

test.describe('Gallery Update/Delete', () => {
  test('PUT /api/gallery/:id updates metadata', async ({ request }) => {
    const createRes = await request.post('/api/gallery/', {
      data: {
        user_id: USER_ID,
        config: makeGalleryConfig('E2E Update Gallery'),
      },
    })
    const createBody = await createRes.json()
    const gId = createBody.data.id

    const updatedConfig = makeGalleryConfig('E2E Updated Gallery')
    updatedConfig.metadata.description = 'Updated description'

    const updateRes = await request.put(`/api/gallery/${gId}?user_id=${USER_ID}`, {
      data: { user_id: USER_ID, config: updatedConfig },
    })
    expect(updateRes.ok()).toBeTruthy()

    // Clean up
    await request.delete(`/api/gallery/${gId}?user_id=${USER_ID}`)
  })

  test('DELETE /api/gallery/:id removes gallery', async ({ request }) => {
    const createRes = await request.post('/api/gallery/', {
      data: {
        user_id: USER_ID,
        config: makeGalleryConfig('E2E Delete Gallery'),
      },
    })
    const createBody = await createRes.json()
    const gId = createBody.data.id

    const delRes = await request.delete(`/api/gallery/${gId}?user_id=${USER_ID}`)
    expect(delRes.ok()).toBeTruthy()
  })

  test('deleted gallery removed from list', async ({ request }) => {
    const createRes = await request.post('/api/gallery/', {
      data: {
        user_id: USER_ID,
        config: makeGalleryConfig('E2E Remove Gallery'),
      },
    })
    const createBody = await createRes.json()
    const gId = createBody.data.id

    await request.delete(`/api/gallery/${gId}?user_id=${USER_ID}`)

    const listRes = await request.get(`/api/gallery/?user_id=${USER_ID}`)
    const listBody = await listRes.json()
    const ids = listBody.data.map((g: Record<string, unknown>) => g.id)
    expect(ids).not.toContain(gId)
  })
})

// ---- Gallery Import -> Teams ----

test.describe('Gallery Import to Teams', () => {
  let teamIds: number[] = []

  test.afterEach(async ({ request }) => {
    for (const id of teamIds) {
      await request.delete(`/api/teams/${id}?user_id=${USER_ID}`)
    }
    teamIds = []
  })

  test('gallery component can be imported as team', async ({ request }) => {
    // Get first gallery
    const listRes = await request.get(`/api/gallery/?user_id=${USER_ID}`)
    const listBody = await listRes.json()
    expect(listBody.data.length).toBeGreaterThan(0)

    const gallery = listBody.data[0]
    const teams = gallery.config?.components?.teams ?? []
    if (teams.length === 0) {
      test.skip()
      return
    }

    const teamComponent = teams[0]
    const res = await request.post('/api/teams/', {
      data: { user_id: USER_ID, component: teamComponent },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    teamIds.push(body.data.id)
  })

  test('imported team config matches gallery template', async ({ request }) => {
    // Create a gallery with known config
    const galleryConfig = makeGalleryConfig('E2E Import Match')
    const createGRes = await request.post('/api/gallery/', {
      data: { user_id: USER_ID, config: galleryConfig },
    })
    const gBody = await createGRes.json()
    const gId = gBody.data.id

    // Import the team from gallery
    const teamTemplate = galleryConfig.components.teams[0]
    const teamRes = await request.post('/api/teams/', {
      data: { user_id: USER_ID, component: teamTemplate },
    })
    const teamBody = await teamRes.json()
    teamIds.push(teamBody.data.id)

    expect(teamBody.data.component.label).toBe('Gallery Team Template')

    // Clean up gallery
    await request.delete(`/api/gallery/${gId}?user_id=${USER_ID}`)
  })

  test('multiple imports create separate teams', async ({ request }) => {
    const listRes = await request.get(`/api/gallery/?user_id=${USER_ID}`)
    const listBody = await listRes.json()
    const gallery = listBody.data[0]
    const teams = gallery.config?.components?.teams ?? []
    if (teams.length === 0) {
      test.skip()
      return
    }

    const teamComponent = teams[0]

    // Import twice
    const res1 = await request.post('/api/teams/', {
      data: { user_id: USER_ID, component: { ...teamComponent, label: 'Import 1' } },
    })
    const res2 = await request.post('/api/teams/', {
      data: { user_id: USER_ID, component: { ...teamComponent, label: 'Import 2' } },
    })

    const body1 = await res1.json()
    const body2 = await res2.json()
    teamIds.push(body1.data.id, body2.data.id)

    expect(body1.data.id).not.toBe(body2.data.id)
  })

  test('deleting gallery does not remove imported teams', async ({ request }) => {
    const galleryConfig = makeGalleryConfig('E2E Persist Import')
    const createGRes = await request.post('/api/gallery/', {
      data: { user_id: USER_ID, config: galleryConfig },
    })
    const gBody = await createGRes.json()
    const gId = gBody.data.id

    // Import team
    const teamRes = await request.post('/api/teams/', {
      data: { user_id: USER_ID, component: galleryConfig.components.teams[0] },
    })
    const teamBody = await teamRes.json()
    const tId = teamBody.data.id
    teamIds.push(tId)

    // Delete gallery
    await request.delete(`/api/gallery/${gId}?user_id=${USER_ID}`)

    // Team should still exist
    const getRes = await request.get(`/api/teams/${tId}?user_id=${USER_ID}`)
    expect(getRes.ok()).toBeTruthy()
  })
})
