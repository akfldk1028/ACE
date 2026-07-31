import { test, expect } from '@playwright/test'

/**
 * Phase 3a: Team CRUD E2E Tests
 * Tests for team creation, deletion, and button wiring
 */

test.describe('Team CRUD - Create Dialog', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/build')
    await page.waitForSelector('h1')
  })

  test('New Team button opens create dialog', async ({ page }) => {
    await page.getByRole('button', { name: /New Team/i }).click()
    await expect(page.getByRole('dialog', { name: /Create new team/i })).toBeVisible()
    await expect(page.getByText('Team Name')).toBeVisible()
    await expect(page.getByText('Team Pattern')).toBeVisible()
  })

  test('create dialog closes on Escape', async ({ page }) => {
    await page.getByRole('button', { name: /New Team/i }).click()
    await expect(page.getByRole('dialog')).toBeVisible()
    await page.keyboard.press('Escape')
    await expect(page.getByRole('dialog')).not.toBeVisible()
  })

  test('create dialog closes on Cancel', async ({ page }) => {
    await page.getByRole('button', { name: /New Team/i }).click()
    await page.getByRole('button', { name: /Cancel/i }).click()
    await expect(page.getByRole('dialog')).not.toBeVisible()
  })

  test('create button is disabled without name', async ({ page }) => {
    await page.getByRole('button', { name: /New Team/i }).click()
    const createBtn = page.getByRole('button', { name: /Create Team/i })
    await expect(createBtn).toBeDisabled()
  })

  test('create dialog has pattern selector with 5 patterns', async ({ page }) => {
    await page.getByRole('button', { name: /New Team/i }).click()
    const radios = page.getByRole('radio')
    await expect(radios).toHaveCount(5)
  })

  test('create dialog closes on backdrop click', async ({ page }) => {
    await page.getByRole('button', { name: /New Team/i }).click()
    await expect(page.getByRole('dialog')).toBeVisible()
    // Click backdrop (the overlay behind the card)
    await page.locator('.fixed.inset-0').click({ position: { x: 10, y: 10 } })
    await expect(page.getByRole('dialog')).not.toBeVisible()
  })
})

test.describe('Team CRUD - Delete Dialog', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/build')
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })
  })

  test('delete button opens confirmation dialog', async ({ page }) => {
    const deleteButtons = page.getByRole('button', { name: /Delete team/i })
    await expect(deleteButtons.first()).toBeVisible({ timeout: 10_000 })
    await deleteButtons.first().click()
    await expect(page.getByRole('alertdialog')).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Delete Team' })).toBeVisible()
  })

  test('delete dialog requires name confirmation', async ({ page }) => {
    const deleteButtons = page.getByRole('button', { name: /Delete team/i })
    await deleteButtons.first().click()
    const deleteBtn = page.getByRole('button', { name: /Delete Team/i }).last()
    await expect(deleteBtn).toBeDisabled()
  })

  test('delete dialog closes on Escape', async ({ page }) => {
    const deleteButtons = page.getByRole('button', { name: /Delete team/i })
    await deleteButtons.first().click()
    await page.keyboard.press('Escape')
    await expect(page.getByRole('alertdialog')).not.toBeVisible()
  })
})

test.describe('Team CRUD - Card Buttons', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/build')
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })
  })

  test('each team card has Run, Edit, and Delete buttons', async ({ page }) => {
    const firstCard = page.locator('[class*="hover:shadow-lg"]').first()
    await expect(firstCard.getByRole('button', { name: /Run/i })).toBeVisible()
    await expect(firstCard.getByRole('button', { name: /Edit/i })).toBeVisible()
    await expect(firstCard.getByRole('button', { name: /Delete team/i })).toBeVisible()
  })

  test('Edit button opens graph panel for team', async ({ page }) => {
    const editButton = page.getByRole('button', { name: /Edit/i }).first()
    await editButton.click()
    // Graph panel should open - look for the close button
    await expect(page.getByRole('button', { name: /Close graph panel/i })).toBeVisible()
  })

  test('empty state Create Team button opens dialog', async ({ page }) => {
    // This test only works when there are no teams. Skip if teams exist.
    const cards = page.locator('[class*="hover:shadow-lg"]')
    const count = await cards.count()
    if (count > 0) {
      test.skip()
      return
    }
    await page.getByRole('button', { name: /Create Team/i }).click()
    await expect(page.getByRole('dialog', { name: /Create new team/i })).toBeVisible()
  })
})
