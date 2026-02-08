import { test, expect } from '@playwright/test'

/**
 * Playground Page E2E Tests
 * Verify team selector, task input, send button, and real team loading
 */

test.describe('Playground page - UI elements and team integration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  // --- Basic UI ---
  test('team selector dropdown exists with placeholder option', async ({ page }) => {
    const select = page.locator('select')
    await expect(select).toBeVisible()
    await expect(select.locator('option').first()).toHaveText('Select a team...')
  })

  test('task input field exists with correct placeholder', async ({ page }) => {
    const input = page.getByPlaceholder('Enter a task for the team...')
    await expect(input).toBeVisible()
    await expect(input).toBeEnabled()
  })

  test('send button exists and is disabled when no team and no input', async ({ page }) => {
    const sendButton = page.locator('button').filter({ has: page.locator('svg.lucide-send') })
    await expect(sendButton).toBeVisible()
    await expect(sendButton).toBeDisabled()
  })

  test('send button stays disabled when only input is provided (no team)', async ({ page }) => {
    const input = page.getByPlaceholder('Enter a task for the team...')
    await input.fill('Calculate 2 + 2')
    const sendButton = page.locator('button').filter({ has: page.locator('svg.lucide-send') })
    await expect(sendButton).toBeDisabled()
  })

  test('idle state shows "Ready to execute" message', async ({ page }) => {
    await expect(page.getByText('Ready to execute')).toBeVisible()
    await expect(page.getByText('Select a team and enter a task to start')).toBeVisible()
  })

  test('team label is visible next to selector', async ({ page }) => {
    await expect(page.getByText('Team:', { exact: true })).toBeVisible()
  })

  // --- Real team data from API ---
  test('team selector populates with teams from AutoGen Studio API', async ({ page }) => {
    const select = page.locator('select')
    // Wait for TanStack Query to populate options
    await page.waitForFunction(
      () => document.querySelectorAll('select option').length > 1,
      { timeout: 10_000 },
    )

    const optionCount = await select.locator('option').count()
    // At least placeholder + some teams
    expect(optionCount).toBeGreaterThan(1)
  })

  test('selecting a team and entering text enables the send button', async ({ page }) => {
    // Wait for teams to load
    await page.waitForFunction(
      () => document.querySelectorAll('select option').length > 1,
      { timeout: 10_000 },
    )

    // Select the second option (first real team)
    const select = page.locator('select')
    const options = select.locator('option')
    const secondOption = await options.nth(1).getAttribute('value')
    await select.selectOption(secondOption!)

    // Enter a task
    const input = page.getByPlaceholder('Enter a task for the team...')
    await input.fill('What is 2 + 2?')

    // Send button should now be enabled
    const sendButton = page.locator('button').filter({ has: page.locator('svg.lucide-send') })
    await expect(sendButton).toBeEnabled()
  })

  test('navigating from Teams page Run button pre-selects the team', async ({ page }) => {
    // Go to Team Builder page first
    await page.goto('/build')
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })

    // Click the first Run button
    await page.getByRole('button', { name: /Run/i }).first().click()
    await expect(page).toHaveURL(/^\/$|\/$/)

    // The team selector should now have a value (not empty)
    const select = page.locator('select')
    const value = await select.inputValue()
    expect(value).not.toBe('')
  })
})
