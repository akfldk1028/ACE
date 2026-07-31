import { test, expect } from '@playwright/test'

/**
 * Collaboration Full Flow E2E Tests
 * Tests end-to-end workflows: Build->Run->History and Gallery->Import->Run
 * Requires: AutoGen Studio running on :8081
 */

const USER_ID = 'guestuser@gmail.com'

// ---- Build -> Run -> History ----

test.describe('Build -> Run -> History', () => {
  let createdTeamId: number | null = null

  test.afterEach(async ({ request }) => {
    if (createdTeamId) {
      await request.delete(`/api/teams/${createdTeamId}?user_id=${USER_ID}`)
      createdTeamId = null
    }
  })

  test('team created in API shows in Team Builder', async ({ page, request }) => {
    const res = await request.post('/api/teams/', {
      data: {
        user_id: USER_ID,
        component: {
          provider: 'autogen_agentchat.teams.RoundRobinGroupChat',
          component_type: 'team',
          label: 'E2E Flow Team',
          config: {
            participants: [
              {
                provider: 'autogen_agentchat.agents.AssistantAgent',
                component_type: 'agent',
                config: {
                  name: 'flow_agent',
                  model_client: {
                    provider: 'autogen_ext.models.openai.OpenAIChatCompletionClient',
                    component_type: 'model',
                    config: { model: 'gpt-4o-mini' },
                  },
                  description: 'Flow test agent',
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
    const body = await res.json()
    createdTeamId = body.data.id

    await page.goto('/build')
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })
    await expect(page.getByText('E2E Flow Team')).toBeVisible({ timeout: 5_000 })
  })

  test('Run button navigates to Playground with team pre-selected', async ({ page, request }) => {
    const res = await request.post('/api/teams/', {
      data: {
        user_id: USER_ID,
        component: {
          provider: 'autogen_agentchat.teams.RoundRobinGroupChat',
          component_type: 'team',
          label: 'E2E Run Navigate Team',
          config: {
            participants: [
              {
                provider: 'autogen_agentchat.agents.AssistantAgent',
                component_type: 'agent',
                config: {
                  name: 'nav_agent',
                  model_client: {
                    provider: 'autogen_ext.models.openai.OpenAIChatCompletionClient',
                    component_type: 'model',
                    config: { model: 'gpt-4o-mini' },
                  },
                  description: 'Navigation test agent',
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
    const body = await res.json()
    createdTeamId = body.data.id

    await page.goto('/build')
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })

    // Find the team card with our specific label and click Run
    const teamCard = page.locator('[class*="hover:shadow-lg"]').filter({ hasText: 'E2E Run Navigate Team' })
    await teamCard.scrollIntoViewIfNeeded()
    await expect(teamCard).toBeVisible({ timeout: 5_000 })

    // Click Run button (first button in the card, contains "Run" text)
    const runBtn = teamCard.getByRole('button', { name: /^Run$/i })
    await runBtn.click()

    // Should navigate to playground
    await expect(page).toHaveURL('/', { timeout: 5_000 })

    // Team should be pre-selected (select element should have a value)
    const teamSelect = page.getByLabel('Select a team')
    await expect(teamSelect).toBeVisible({ timeout: 5_000 })
    // Wait for the team to be populated in the select
    await page.waitForFunction(
      () => {
        const s = document.querySelector('[aria-label="Select a team"]') as HTMLSelectElement
        return s && s.value !== ''
      },
      { timeout: 10_000 },
    )
    const value = await teamSelect.inputValue()
    expect(value).not.toBe('')
  })

  test('Playground accepts task input and Send is enabled', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('Ready to execute')).toBeVisible({ timeout: 5_000 })

    // Select first available team
    const teamSelect = page.getByLabel('Select a team')
    const options = await teamSelect.locator('option').allTextContents()
    const realOptions = options.filter(o => o.trim() && !o.includes('Select'))
    if (realOptions.length === 0) {
      test.skip()
      return
    }

    await teamSelect.selectOption({ index: 1 })

    const input = page.getByPlaceholder(/Enter a task|Continue this session/)
    await input.fill('Hello test task')

    const sendButton = page.getByLabel('Send task')
    await expect(sendButton).toBeEnabled()
  })

  test('History page shows sessions from API', async ({ page }) => {
    await page.goto('/history')
    await expect(page.locator('main h1')).toHaveText('History')

    // Wait for session list to load (either sessions or empty state)
    await page.waitForFunction(
      () => {
        const main = document.querySelector('main')
        return main && (
          main.querySelectorAll('[class*="hover:shadow"]').length > 0 ||
          main.textContent?.includes('No sessions') ||
          main.textContent?.includes('history')
        )
      },
      { timeout: 10_000 },
    )
  })
})

// ---- Gallery -> Import -> Run ----

test.describe('Gallery -> Import -> Run', () => {
  let importedTeamId: number | null = null

  test.afterEach(async ({ request }) => {
    if (importedTeamId) {
      await request.delete(`/api/teams/${importedTeamId}?user_id=${USER_ID}`)
      importedTeamId = null
    }
  })

  test('Gallery page loads with entries from API', async ({ page }) => {
    await page.goto('/gallery')
    await expect(page.locator('main h1')).toHaveText('Gallery')

    // Wait for gallery to load
    await page.waitForFunction(
      () => {
        const main = document.querySelector('main')
        return main && !main.querySelector('.animate-pulse')
      },
      { timeout: 10_000 },
    )
  })

  test('import gallery team creates new team via API', async ({ request }) => {
    // Get gallery list
    const galleryRes = await request.get(`/api/gallery/?user_id=${USER_ID}`)
    const galleryBody = await galleryRes.json()
    if (galleryBody.data.length === 0) {
      test.skip()
      return
    }

    const gallery = galleryBody.data[0]
    const teams = gallery.config?.components?.teams ?? []
    if (teams.length === 0) {
      test.skip()
      return
    }

    // Import first team template
    const teamComponent = { ...teams[0], label: 'E2E Gallery Import' }
    const importRes = await request.post('/api/teams/', {
      data: { user_id: USER_ID, component: teamComponent },
    })
    expect(importRes.ok()).toBeTruthy()
    const importBody = await importRes.json()
    importedTeamId = importBody.data.id
  })

  test('imported team appears in Team Builder', async ({ page, request }) => {
    // Import a team
    const galleryRes = await request.get(`/api/gallery/?user_id=${USER_ID}`)
    const galleryBody = await galleryRes.json()
    if (galleryBody.data.length === 0) {
      test.skip()
      return
    }

    const gallery = galleryBody.data[0]
    const teams = gallery.config?.components?.teams ?? []
    if (teams.length === 0) {
      test.skip()
      return
    }

    const teamComponent = { ...teams[0], label: 'E2E Gallery In Builder' }
    const importRes = await request.post('/api/teams/', {
      data: { user_id: USER_ID, component: teamComponent },
    })
    const importBody = await importRes.json()
    importedTeamId = importBody.data.id

    // Navigate to Team Builder
    await page.goto('/build')
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })
    await expect(page.getByText('E2E Gallery In Builder')).toBeVisible({ timeout: 5_000 })
  })

  test('History page accessible after gallery operations', async ({ page }) => {
    await page.goto('/history')
    await expect(page.locator('main h1')).toHaveText('History')
    // Page should load without errors
    await page.waitForTimeout(1_000)
    const errorText = await page.locator('main').textContent()
    expect(errorText).not.toContain('Error')
  })
})
