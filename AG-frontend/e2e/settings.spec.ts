import { test, expect } from '@playwright/test'

/**
 * Settings Page E2E Tests
 * Verify engine connection status, theme controls, and API key section
 */

test.describe('Settings page - configuration display', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings')
  })

  test('shows Settings heading and description', async ({ page }) => {
    await expect(page.locator('main h1')).toHaveText('Settings')
    await expect(page.getByText('Platform configuration')).toBeVisible()
  })

  // --- Engine Connection ---
  test('shows Engine Connection card with AutoGen Studio label and port', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Engine Connection' })).toBeVisible()
    // "AutoGen Studio" text in settings section
    await expect(page.locator('main').getByText('AutoGen Studio')).toBeVisible()
    await expect(page.locator('main').getByText(':8081')).toBeVisible()
  })

  test('engine shows "Connected" when AutoGen Studio is running', async ({ page }) => {
    // After health fix, status should now show "Connected"
    await expect(page.locator('main').getByText('Connected')).toBeVisible({ timeout: 10_000 })
  })

  test('shows AutoGen Studio version from API', async ({ page }) => {
    await expect(page.getByText('Version')).toBeVisible({ timeout: 10_000 })
    await expect(page.getByText(/\d+\.\d+\.\d+/)).toBeVisible({ timeout: 10_000 })
  })

  // --- Appearance ---
  test('shows Appearance card with Dark Mode toggle and Color Theme', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Appearance' })).toBeVisible()
    await expect(page.locator('main').getByText('Dark Mode')).toBeVisible()
    await expect(page.locator('main').getByText('Color Theme')).toBeVisible()
  })

  test('shows 7 color theme buttons', async ({ page }) => {
    const themeNames = ['Default', 'Dusk', 'Lime', 'Ocean', 'Retro', 'Neo', 'Forest']
    for (const name of themeNames) {
      await expect(page.getByRole('button', { name, exact: true })).toBeVisible()
    }
  })

  // --- API Keys ---
  test('shows API Keys section with disabled Generate button', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'API Keys' })).toBeVisible()
    await expect(page.getByText('Phase 3')).toBeVisible()
    await expect(page.getByRole('button', { name: /Generate/i })).toBeDisabled()
  })
})
