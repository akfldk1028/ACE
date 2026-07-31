import { test, expect } from '@playwright/test'

/**
 * History Page E2E Tests
 * Tests for session listing, detail panel, and navigation
 */

test.describe('History page - UI elements', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/history')
  })

  test('displays History heading and description', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'History' })).toBeVisible()
    await expect(page.getByText('Past execution sessions')).toBeVisible()
  })

  test('shows session cards or empty state after loading', async ({ page }) => {
    // Wait for loading to finish (API may or may not be available)
    await page.waitForTimeout(2000)
    const emptyMsg = page.getByText('No sessions yet')
    const loadingCards = page.locator('[class*="animate-pulse"]')
    const sessionCards = page.locator('[class*="hover:shadow-lg"]')
    const hasEmpty = await emptyMsg.isVisible().catch(() => false)
    const hasLoading = (await loadingCards.count()) > 0
    const hasCards = (await sessionCards.count()) > 0
    expect(hasEmpty || hasLoading || hasCards).toBe(true)
  })

  test('navigating to /history from sidebar works', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('link', { name: 'History' }).click()
    await expect(page).toHaveURL('/history')
    await expect(page.getByRole('heading', { name: 'History' })).toBeVisible()
  })
})

test.describe('History page - with backend data', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/history')
  })

  test('session cards load from API', async ({ page }) => {
    await page.waitForFunction(
      () => document.querySelectorAll('[class*="hover:shadow-lg"]').length > 0,
      { timeout: 10_000 },
    )

    const cards = page.locator('[class*="hover:shadow-lg"]')
    const count = await cards.count()
    expect(count).toBeGreaterThan(0)
  })

  test('clicking a session card shows detail panel', async ({ page }) => {
    await page.waitForFunction(
      () => document.querySelectorAll('[role="button"][tabindex="0"]').length > 0,
      { timeout: 10_000 },
    )

    await page.locator('[role="button"][tabindex="0"]').first().click()

    // Detail panel should appear (SessionDetailPanel has role="complementary")
    await expect(page.locator('[aria-label="Session detail"]')).toBeVisible({ timeout: 5_000 })
  })

  test('clicking same session card twice deselects it', async ({ page }) => {
    await page.waitForFunction(
      () => document.querySelectorAll('[role="button"][tabindex="0"]').length > 0,
      { timeout: 10_000 },
    )

    const firstCard = page.locator('[role="button"][tabindex="0"]').first()
    await firstCard.click()
    // Detail panel should appear
    await expect(page.locator('[aria-label="Session detail"]')).toBeVisible({ timeout: 5_000 })

    await firstCard.click()
    // Detail panel should be gone
    await expect(page.locator('[aria-label="Session detail"]')).not.toBeVisible()
  })
})
