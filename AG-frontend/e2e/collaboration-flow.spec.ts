import { test, expect } from '@playwright/test'

/**
 * Collaboration Flow E2E Tests
 * Matches AutoGen Studio navigation: Team Builder -> Playground -> Gallery -> MCP -> Deploy -> Settings
 */

test.describe('Full collaboration flow: Build -> Run -> Browse', () => {
  test('browse teams in Team Builder, navigate to playground, run', async ({ page }) => {
    // Step 1: Start at Team Builder - verify teams loaded
    await page.goto('/build')
    await expect(page.locator('main h1')).toHaveText('Team Builder')

    // Wait for teams to load from API
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })

    // Step 2: Click Run on a team -> goes to Playground (home)
    await page.getByRole('button', { name: /Run/i }).first().click()
    await expect(page).toHaveURL('/')

    // Step 3: Verify playground is ready with team pre-selected
    const select = page.locator('select')
    const value = await select.inputValue()
    expect(value).not.toBe('')

    // Step 4: Enter a task
    const input = page.getByPlaceholder('Enter a task for the team...')
    await input.fill('Hello, test task')

    // Send button should be enabled
    const sendButton = page.locator('button').filter({ has: page.locator('svg.lucide-send') })
    await expect(sendButton).toBeEnabled()
  })

  test('settings shows connected AutoGen Studio with version', async ({ page }) => {
    await page.goto('/settings')

    await expect(page.locator('main').getByText('Connected')).toBeVisible({ timeout: 10_000 })
    await expect(page.locator('main').getByText(':8081')).toBeVisible()
    await expect(page.getByText(/\d+\.\d+\.\d+/)).toBeVisible({ timeout: 10_000 })
  })

  test('full navigation cycle: Playground -> Team Builder -> Gallery -> MCP -> Deploy -> Settings', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('Ready to execute')).toBeVisible()

    await page.locator('aside').getByRole('link', { name: 'Team Builder' }).click()
    await expect(page.locator('main h1')).toHaveText('Team Builder')

    await page.locator('aside').getByRole('link', { name: 'A2A Agents' }).click()
    await expect(page.locator('main h1')).toHaveText('A2A Agents')

    await page.locator('aside').getByRole('link', { name: 'Gallery' }).click()
    await expect(page.locator('main h1')).toHaveText('Gallery')

    await page.locator('aside').getByRole('link', { name: 'MCP' }).click()
    await expect(page.locator('main h1')).toHaveText('MCP')

    await page.locator('aside').getByRole('link', { name: 'Deploy' }).click()
    await expect(page.locator('main h1')).toHaveText('Deploy')

    await page.locator('aside').getByRole('link', { name: 'Settings' }).click()
    await expect(page.locator('main h1')).toHaveText('Settings')
  })
})

test.describe('Team CRUD via API', () => {
  test('create and delete a team via API round-trip', async ({ request }) => {
    const res = await request.post('/api/teams/', {
      data: {
        user_id: 'guestuser@gmail.com',
        component: {
          label: 'Playwright E2E Team',
          team_type: 'RoundRobinGroupChat',
          config: {
            participants: [
              {
                agent_type: 'AssistantAgent',
                config: {
                  name: 'pw_test_agent',
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
        },
      },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    const newTeamId = body.data.id
    expect(body.data.component.label).toBe('Playwright E2E Team')

    // Delete
    const deleteRes = await request.delete(`/api/teams/${newTeamId}?user_id=guestuser@gmail.com`)
    expect(deleteRes.ok()).toBeTruthy()
  })

  test('teams page shows real team labels from API', async ({ page }) => {
    await page.goto('/build')
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })

    const mainContent = await page.locator('main').textContent()
    const hasRealLabel = mainContent?.includes('Sequential') ||
      mainContent?.includes('Selector') ||
      mainContent?.includes('Handoff') ||
      mainContent?.includes('Debate') ||
      mainContent?.includes('Reflection') ||
      mainContent?.includes('Auto-Claude')
    expect(hasRealLabel).toBeTruthy()
  })
})

test.describe('Gallery and API connectivity', () => {
  test('gallery page loads from API', async ({ page }) => {
    await page.goto('/gallery')
    await expect(page.locator('main h1')).toHaveText('Gallery')
  })

  test('gallery items exist via API', async ({ request }) => {
    const res = await request.get('/api/gallery/?user_id=guestuser@gmail.com')
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.data.length).toBeGreaterThan(0)
  })

  test('health endpoint confirms engine is running', async ({ request }) => {
    const res = await request.get('/api/health')
    const body = await res.json()
    expect(body.status).toBe(true)
    expect(body.message).toContain('healthy')
  })

  test('version endpoint returns valid version', async ({ request }) => {
    const res = await request.get('/api/version')
    const body = await res.json()
    expect(body.data.version).toMatch(/^\d+\.\d+/)
  })
})
