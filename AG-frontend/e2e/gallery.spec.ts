import { test, expect } from '@playwright/test'

/**
 * Gallery Page E2E Tests
 * Tests for gallery listing, import dialog, and sync dialog
 */

test.describe('Gallery page - UI elements', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/gallery')
  })

  test('displays Gallery heading and description', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Gallery', exact: true })).toBeVisible({ timeout: 10_000 })
    await expect(page.getByText('Reusable agent team templates')).toBeVisible()
  })

  test('Sync Gallery button is visible', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Sync Gallery/i })).toBeVisible()
  })

  test('New Gallery button is disabled (future feature)', async ({ page }) => {
    const btn = page.getByRole('button', { name: /New Gallery/i })
    await expect(btn).toBeVisible()
    await expect(btn).toBeDisabled()
  })

  test('shows gallery cards or empty state after loading', async ({ page }) => {
    // Wait for loading to finish (API may or may not be available)
    await page.waitForTimeout(2000)
    const emptyMsg = page.getByText('No gallery items yet')
    const loadingCards = page.locator('[class*="animate-pulse"]')
    const galleryCards = page.locator('[class*="hover:shadow-lg"]')
    const hasEmpty = await emptyMsg.isVisible().catch(() => false)
    const hasLoading = (await loadingCards.count()) > 0
    const hasCards = (await galleryCards.count()) > 0
    expect(hasEmpty || hasLoading || hasCards).toBe(true)
  })

  test('Sync Gallery button opens sync dialog', async ({ page }) => {
    await page.getByRole('button', { name: /Sync Gallery/i }).click()
    // Dialog should appear with URL input
    await expect(page.getByRole('dialog')).toBeVisible()
  })
})

test.describe('Gallery page - with backend data', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/gallery')
  })

  test('gallery cards load from API and show import button', async ({ page }) => {
    // Wait for galleries to load from backend
    await page.waitForFunction(
      () => document.querySelectorAll('[class*="hover:shadow-lg"]').length > 0,
      { timeout: 10_000 },
    )

    // Each gallery card should have an Import button
    const importButtons = page.getByRole('button', { name: /Import/i })
    const count = await importButtons.count()
    expect(count).toBeGreaterThan(0)
  })

  test('clicking Import opens import dialog', async ({ page }) => {
    await page.waitForFunction(
      () => document.querySelectorAll('[class*="hover:shadow-lg"]').length > 0,
      { timeout: 10_000 },
    )

    await page.getByRole('button', { name: /Import/i }).first().click()
    await expect(page.getByRole('dialog')).toBeVisible()
  })
})
