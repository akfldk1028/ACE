import { test, expect } from '@playwright/test'

/**
 * Tests for the unsaved changes warning dialog on the Team Builder page.
 * Requires AutoGen Studio running on port 8081 to load team data.
 */

test.describe('Unsaved Changes Warning', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/build')
    // Wait for team cards to load (requires backend)
    await page.waitForSelector('[class*="cursor-pointer"]', { timeout: 5000 })
  })

  test('no blocker dialog when not in edit mode', async ({ page }) => {
    // Navigate away without editing - should not show dialog
    await page.getByRole('link', { name: /History/i }).click()
    await expect(page.getByRole('alertdialog')).not.toBeVisible()
    await expect(page).toHaveURL(/\/history/)
  })

  test('blocker dialog appears when navigating with unsaved edits', async ({ page }) => {
    // Click first team card to select it
    const firstCard = page.locator('[class*="cursor-pointer"]').first()
    await firstCard.click()

    // Enter edit mode
    await page.getByRole('button', { name: 'Enter edit mode' }).click()
    await expect(page.getByText('Editing')).toBeVisible()

    // Make a change (add an agent)
    await page.getByRole('button', { name: 'Add agent to team' }).click()
    await page.getByLabel('Agent name').fill('test_agent')
    await page.getByRole('dialog').getByRole('button', { name: /^Add Agent$/i }).click()

    // Try to navigate away
    await page.getByRole('link', { name: /History/i }).click()

    // Should show the blocker dialog
    await expect(page.getByRole('alertdialog', { name: 'Unsaved changes' })).toBeVisible()
    await expect(page.getByText('You have unsaved changes')).toBeVisible()
  })

  test('Stay button keeps user on page', async ({ page }) => {
    const firstCard = page.locator('[class*="cursor-pointer"]').first()
    await firstCard.click()
    await page.getByRole('button', { name: 'Enter edit mode' }).click()
    await page.getByRole('button', { name: 'Add agent to team' }).click()
    await page.getByLabel('Agent name').fill('test_agent')
    await page.getByRole('dialog').getByRole('button', { name: /^Add Agent$/i }).click()

    await page.getByRole('link', { name: /History/i }).click()
    await expect(page.getByRole('alertdialog')).toBeVisible()

    // Click Stay
    await page.getByRole('button', { name: 'Stay' }).click()
    await expect(page.getByRole('alertdialog')).not.toBeVisible()
    await expect(page).toHaveURL(/\/build/)
  })

  test('Leave button navigates away', async ({ page }) => {
    const firstCard = page.locator('[class*="cursor-pointer"]').first()
    await firstCard.click()
    await page.getByRole('button', { name: 'Enter edit mode' }).click()
    await page.getByRole('button', { name: 'Add agent to team' }).click()
    await page.getByLabel('Agent name').fill('test_agent')
    await page.getByRole('dialog').getByRole('button', { name: /^Add Agent$/i }).click()

    await page.getByRole('link', { name: /History/i }).click()
    await expect(page.getByRole('alertdialog')).toBeVisible()

    // Click Leave
    await page.getByRole('button', { name: 'Leave' }).click()
    await expect(page).toHaveURL(/\/history/)
  })
})
