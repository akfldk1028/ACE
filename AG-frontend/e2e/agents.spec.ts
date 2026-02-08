import { test, expect } from '@playwright/test'

/**
 * A2A Agents Page E2E Tests
 * Comprehensive tests: page load, dialog, keyboard, search, detail panel, sidebar nav
 */

test.describe('A2A Agents page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/agents')
  })

  test('shows A2A Agents heading and description', async ({ page }) => {
    await expect(page.locator('main h1')).toHaveText('A2A Agents')
    await expect(page.getByText('Discover and manage A2A protocol agents')).toBeVisible()
  })

  test('shows "Register Agent" button in header', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Register Agent/i }).first()).toBeVisible()
  })

  test('shows "Health Check All" button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Health Check All/i })).toBeVisible()
  })

  test('renders agent cards or empty state after loading', async ({ page }) => {
    // Wait for loading skeletons to disappear
    await page.waitForFunction(() => {
      return document.querySelectorAll('.animate-pulse').length === 0
    }, { timeout: 15_000 })

    const cards = page.locator('[class*="hover:shadow-lg"]')
    const emptyState = page.getByText(/No agents registered/)
    const searchEmpty = page.getByText(/No agents match/)

    await expect(
      cards.first().or(emptyState).or(searchEmpty)
    ).toBeVisible({ timeout: 5_000 })
  })

  test('sidebar has A2A Agents navigation link', async ({ page }) => {
    const navLink = page.getByRole('link', { name: /A2A Agents/i })
    await expect(navLink).toBeVisible()
  })
})

test.describe('A2A Agents - Register dialog', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/agents')
  })

  test('opens dialog and shows all controls', async ({ page }) => {
    await page.getByRole('button', { name: /Register Agent/i }).first().click()
    await expect(page.getByText('Register A2A Agent')).toBeVisible()
    await expect(page.getByPlaceholder('http://localhost:8006')).toBeVisible()
    await expect(page.getByRole('button', { name: /Discover/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /Cancel/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /Register$/i })).toBeVisible()
  })

  test('closes dialog via Cancel button', async ({ page }) => {
    await page.getByRole('button', { name: /Register Agent/i }).first().click()
    await expect(page.getByText('Register A2A Agent')).toBeVisible()

    await page.getByRole('button', { name: /Cancel/i }).click()
    await expect(page.getByText('Register A2A Agent')).not.toBeVisible()
  })

  test('closes dialog via Escape key', async ({ page }) => {
    await page.getByRole('button', { name: /Register Agent/i }).first().click()
    await expect(page.getByText('Register A2A Agent')).toBeVisible()

    await page.keyboard.press('Escape')
    await expect(page.getByText('Register A2A Agent')).not.toBeVisible()
  })

  test('closes dialog via backdrop click', async ({ page }) => {
    await page.getByRole('button', { name: /Register Agent/i }).first().click()
    await expect(page.getByText('Register A2A Agent')).toBeVisible()

    // Click top-left corner (backdrop area)
    await page.mouse.click(10, 10)
    await expect(page.getByText('Register A2A Agent')).not.toBeVisible()
  })

  test('dialog resets state on reopen', async ({ page }) => {
    // Open, type URL, close
    await page.getByRole('button', { name: /Register Agent/i }).first().click()
    const input = page.getByPlaceholder('http://localhost:8006')
    await input.fill('http://localhost:9999')
    await expect(input).toHaveValue('http://localhost:9999')
    await page.getByRole('button', { name: /Cancel/i }).click()

    // Reopen - should be empty
    await page.getByRole('button', { name: /Register Agent/i }).first().click()
    await expect(input).toHaveValue('')
  })

  test('Discover button disabled when URL is empty', async ({ page }) => {
    await page.getByRole('button', { name: /Register Agent/i }).first().click()
    const discoverBtn = page.getByRole('button', { name: /Discover/i })
    await expect(discoverBtn).toBeDisabled()
  })

  test('Register button disabled without successful discovery', async ({ page }) => {
    await page.getByRole('button', { name: /Register Agent/i }).first().click()
    const registerBtn = page.getByRole('button', { name: /Register$/i })
    await expect(registerBtn).toBeDisabled()
  })
})

test.describe('A2A Agents - Navigation integration', () => {
  test('sidebar click navigates to /agents with correct content', async ({ page }) => {
    await page.goto('/')
    await page.locator('aside').getByRole('link', { name: 'A2A Agents' }).click()
    await expect(page).toHaveURL(/\/agents$/)
    await expect(page.locator('main h1')).toHaveText('A2A Agents')
  })

  test('agents page has active sidebar styling', async ({ page }) => {
    await page.goto('/agents')
    const agentsLink = page.locator('aside').getByRole('link', { name: 'A2A Agents' })
    await expect(agentsLink).toHaveClass(/accent-primary/)
  })

  test('navigating away and back preserves page state', async ({ page }) => {
    await page.goto('/agents')
    await expect(page.locator('main h1')).toHaveText('A2A Agents')

    // Navigate to settings and back
    await page.locator('aside').getByRole('link', { name: 'Settings' }).click()
    await expect(page.locator('main h1')).toHaveText('Settings')

    await page.locator('aside').getByRole('link', { name: 'A2A Agents' }).click()
    await expect(page.locator('main h1')).toHaveText('A2A Agents')
  })
})
