import { test, expect } from '@playwright/test'

/**
 * Teams Page E2E Tests
 * Verify team listing, team cards, patterns, agent counts, and navigation to playground
 */

test.describe('Team Builder page - team listing and display', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/build')
  })

  test('shows Team Builder heading and description', async ({ page }) => {
    await expect(page.locator('main h1')).toHaveText('Team Builder')
    await expect(page.getByText('Build and manage agent teams')).toBeVisible()
  })

  test('shows "New Team" button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /New Team/i })).toBeVisible()
  })

  test('displays team cards loaded from AutoGen Studio API', async ({ page }) => {
    // Wait for team cards to appear (API data via TanStack Query)
    const cards = page.locator('[class*="hover:shadow-lg"]')
    await expect(cards.first()).toBeVisible({ timeout: 10_000 })

    // Should have at least 5 teams (we imported 5 + existing)
    const count = await cards.count()
    expect(count).toBeGreaterThanOrEqual(5)
  })

  test('team cards show name and agent count', async ({ page }) => {
    // Wait for cards to load
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })

    // Should show "agents" text (each card shows "N agents")
    const agentLabels = page.getByText(/\d+ agents/)
    await expect(agentLabels.first()).toBeVisible()
  })

  test('team card has Run and Edit buttons', async ({ page }) => {
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })

    const runButtons = page.getByRole('button', { name: /Run/i })
    await expect(runButtons.first()).toBeVisible()

    const editButtons = page.getByRole('button', { name: /Edit/i })
    await expect(editButtons.first()).toBeVisible()
  })

  test('clicking Run navigates to playground', async ({ page }) => {
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })

    await page.getByRole('button', { name: /Run/i }).first().click()
    await expect(page).toHaveURL(/^\/$|\/$/)
  })

  test('no teams found message is hidden when teams exist', async ({ page }) => {
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })
    const emptyState = page.getByText('No teams found')
    await expect(emptyState).not.toBeVisible()
  })
})
