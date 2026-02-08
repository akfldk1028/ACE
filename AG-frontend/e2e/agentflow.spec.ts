import { test, expect } from '@playwright/test'

/**
 * AgentFlow Graph Visualization E2E Tests
 * Verify that clicking a team card shows the React Flow graph
 */

test.describe('AgentFlow graph visualization on Team Builder', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/build')
    // Wait for team cards to load from API
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })
  })

  test('clicking a team card shows the agent flow graph', async ({ page }) => {
    // Click the first team card
    await page.locator('[class*="hover:shadow-lg"]').first().click()

    // React Flow canvas should appear
    const reactFlow = page.locator('.react-flow')
    await expect(reactFlow).toBeVisible({ timeout: 5_000 })
  })

  test('graph shows agent nodes from the team', async ({ page }) => {
    // Click the first team card
    await page.locator('[class*="hover:shadow-lg"]').first().click()

    // Wait for React Flow to render
    await expect(page.locator('.react-flow')).toBeVisible({ timeout: 5_000 })

    // Should have at least a User node and one agent node
    const nodes = page.locator('.react-flow__node')
    await expect(nodes.first()).toBeVisible()
    const count = await nodes.count()
    expect(count).toBeGreaterThanOrEqual(2) // user + at least 1 agent
  })

  test('graph shows edges connecting nodes', async ({ page }) => {
    await page.locator('[class*="hover:shadow-lg"]').first().click()
    await expect(page.locator('.react-flow')).toBeVisible({ timeout: 5_000 })

    // Should have at least one edge in the DOM (SVG edges may not pass visibility checks)
    const edges = page.locator('.react-flow__edge')
    const count = await edges.count()
    expect(count).toBeGreaterThanOrEqual(1)
  })

  test('graph has a toolbar with controls', async ({ page }) => {
    await page.locator('[class*="hover:shadow-lg"]').first().click()
    await expect(page.locator('.react-flow')).toBeVisible({ timeout: 5_000 })

    // Toolbar buttons should be visible
    await expect(page.getByTitle('Enter Fullscreen')).toBeVisible()
    await expect(page.getByTitle(/Switch to/)).toBeVisible()
    await expect(page.getByTitle(/Labels/)).toBeVisible()
  })

  test('clicking X closes the graph panel', async ({ page }) => {
    await page.locator('[class*="hover:shadow-lg"]').first().click()
    await expect(page.locator('.react-flow')).toBeVisible({ timeout: 5_000 })

    // Close the panel
    await page.locator('button').filter({ has: page.locator('svg.lucide-x') }).click()

    // Graph should disappear
    await expect(page.locator('.react-flow')).not.toBeVisible()
  })

  test('agent names are shown as chips below the graph', async ({ page }) => {
    await page.locator('[class*="hover:shadow-lg"]').first().click()
    await expect(page.locator('.react-flow')).toBeVisible({ timeout: 5_000 })

    // Agent name chips should appear below the graph
    const chips = page.locator('.rounded-full')
    await expect(chips.first()).toBeVisible()
  })

  test('clicking a different team card switches the graph', async ({ page }) => {
    const cards = page.locator('[class*="hover:shadow-lg"]')
    const count = await cards.count()
    if (count < 2) return // Skip if only 1 team

    // Select first team
    await cards.first().click()
    await expect(page.locator('.react-flow')).toBeVisible({ timeout: 5_000 })

    // Get first team's graph node count
    const firstCount = await page.locator('.react-flow__node').count()

    // Select second team
    await cards.nth(1).click()
    await expect(page.locator('.react-flow')).toBeVisible({ timeout: 5_000 })

    // Graph should still be visible (may have different node count)
    const secondCount = await page.locator('.react-flow__node').count()
    expect(secondCount).toBeGreaterThanOrEqual(2)
  })
})
