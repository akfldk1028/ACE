import { test, expect } from '@playwright/test'

/**
 * Phase 3b: Team Builder Edit Mode E2E Tests
 * Tests for edit mode toggle, agent editing, pattern switching, and save/discard
 */

test.describe('Edit Mode - Toggle', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/build')
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })
    // Click first team card to open graph panel
    await page.locator('[class*="hover:shadow-lg"]').first().click()
    await expect(page.getByRole('button', { name: /Close graph panel/i })).toBeVisible()
  })

  test('Edit button toggles edit mode', async ({ page }) => {
    const editBtn = page.getByRole('button', { name: /Enter edit mode/i })
    await expect(editBtn).toBeVisible()
    await editBtn.click()
    await expect(page.getByText('Editing')).toBeVisible()
  })

  test('edit mode shows Save and Discard buttons', async ({ page }) => {
    await page.getByRole('button', { name: /Enter edit mode/i }).click()
    await expect(page.getByRole('button', { name: /Save team changes/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /Discard changes/i })).toBeVisible()
  })

  test('edit mode shows Add Agent button', async ({ page }) => {
    await page.getByRole('button', { name: /Enter edit mode/i }).click()
    await expect(page.getByRole('button', { name: /Add agent to team/i })).toBeVisible()
  })

  test('Discard exits edit mode', async ({ page }) => {
    await page.getByRole('button', { name: /Enter edit mode/i }).click()
    await expect(page.getByText('Editing')).toBeVisible()
    await page.getByRole('button', { name: /Discard changes/i }).click()
    await expect(page.getByText('Editing')).not.toBeVisible()
  })

  test('Save is disabled when no changes made', async ({ page }) => {
    await page.getByRole('button', { name: /Enter edit mode/i }).click()
    const saveBtn = page.getByRole('button', { name: /Save team changes/i })
    await expect(saveBtn).toBeDisabled()
  })
})

test.describe('Edit Mode - Add Agent Dialog', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/build')
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })
    await page.locator('[class*="hover:shadow-lg"]').first().click()
    await expect(page.getByRole('button', { name: /Close graph panel/i })).toBeVisible()
    await page.getByRole('button', { name: /Enter edit mode/i }).click()
    await expect(page.getByText('Editing')).toBeVisible({ timeout: 5_000 })
  })

  test('Add Agent opens dialog with 3 agent presets', async ({ page }) => {
    await page.getByRole('button', { name: /Add agent to team/i }).click()
    await expect(page.getByRole('dialog', { name: /Add agent to team/i })).toBeVisible()
    const radios = page.getByRole('radio')
    await expect(radios).toHaveCount(3)
  })

  test('Add Agent dialog requires name', async ({ page }) => {
    await page.getByRole('button', { name: /Add agent to team/i }).click()
    const addBtn = page.getByRole('dialog').getByRole('button', { name: /^Add Agent$/i })
    await expect(addBtn).toBeDisabled()
  })

  test('Add Agent dialog closes on Escape', async ({ page }) => {
    await page.getByRole('button', { name: /Add agent to team/i }).click()
    await page.keyboard.press('Escape')
    await expect(page.getByRole('dialog')).not.toBeVisible()
  })

  test('Add Agent dialog closes on Cancel', async ({ page }) => {
    await page.getByRole('button', { name: /Add agent to team/i }).click()
    await page.getByRole('button', { name: /Cancel/i }).click()
    await expect(page.getByRole('dialog')).not.toBeVisible()
  })
})

test.describe('Edit Mode - Pattern & Termination', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/build')
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })
    await page.locator('[class*="hover:shadow-lg"]').first().click()
    await expect(page.getByRole('button', { name: /Close graph panel/i })).toBeVisible()
    await page.getByRole('button', { name: /Enter edit mode/i }).click()
    await expect(page.getByText('Editing')).toBeVisible({ timeout: 5_000 })
  })

  test('Termination Editor is visible in edit mode', async ({ page }) => {
    await expect(page.getByText('Termination Conditions')).toBeVisible()
  })

  test('Termination Editor expands on click', async ({ page }) => {
    await page.getByText('Termination Conditions').click()
    await expect(page.getByLabel('Condition type to add')).toBeVisible()
  })

  test('Patterns button opens interactive selector in edit mode', async ({ page }) => {
    await page.getByRole('button', { name: /Toggle pattern selector/i }).click()
    const radios = page.getByRole('radio')
    await expect(radios).toHaveCount(5)
    // In edit mode, clicking should be possible (cursor-pointer class)
    const firstRadio = radios.first()
    await expect(firstRadio).toBeVisible()
  })
})

test.describe('Edit Mode - Agent Panel', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/build')
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })
    await page.locator('[class*="hover:shadow-lg"]').first().click()
    await expect(page.getByRole('button', { name: /Close graph panel/i })).toBeVisible()
    await page.getByRole('button', { name: /Enter edit mode/i }).click()
    await expect(page.getByText('Editing')).toBeVisible({ timeout: 5_000 })
  })

  test('clicking agent chip in edit mode shows editable panel', async ({ page }) => {
    const chips = page.locator('[role="button"][aria-pressed]')
    const chipCount = await chips.count()
    if (chipCount === 0) {
      test.skip()
      return
    }
    await chips.first().click()
    // Should see Editing badge in the side panel
    await expect(page.locator('[role="complementary"]').getByText('Editing')).toBeVisible()
  })

  test('editable panel has Remove Agent button', async ({ page }) => {
    const chips = page.locator('[role="button"][aria-pressed]')
    const chipCount = await chips.count()
    if (chipCount === 0) {
      test.skip()
      return
    }
    await chips.first().click()
    await expect(page.getByRole('button', { name: /Remove Agent/i })).toBeVisible()
  })

  test('closing panel from X button works', async ({ page }) => {
    const chips = page.locator('[role="button"][aria-pressed]')
    const chipCount = await chips.count()
    if (chipCount === 0) {
      test.skip()
      return
    }
    await chips.first().click()
    await page.getByRole('button', { name: /Close agent editor/i }).click()
    await expect(page.locator('[role="complementary"]')).not.toBeVisible()
  })

  test('JSON view shows draft in edit mode', async ({ page }) => {
    await page.getByRole('button', { name: /Show JSON view/i }).click()
    // JSON view should be visible
    await expect(page.locator('[aria-label="Team configuration JSON"]')).toBeVisible()
  })
})

test.describe('Edit Mode - Undo/Redo', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/build')
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })
    await page.locator('[class*="hover:shadow-lg"]').first().click()
    await expect(page.getByRole('button', { name: /Close graph panel/i })).toBeVisible()
    await page.getByRole('button', { name: /Enter edit mode/i }).click()
    await expect(page.getByText('Editing')).toBeVisible({ timeout: 5_000 })
  })

  test('undo and redo buttons are visible in edit mode', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Undo' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Redo' })).toBeVisible()
  })

  test('undo and redo are disabled with no history', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Undo' })).toBeDisabled()
    await expect(page.getByRole('button', { name: 'Redo' })).toBeDisabled()
  })

  test('undo and redo buttons have keyboard shortcut tooltips', async ({ page }) => {
    const undo = page.getByRole('button', { name: 'Undo' })
    const redo = page.getByRole('button', { name: 'Redo' })
    await expect(undo).toHaveAttribute('title', 'Undo (Ctrl+Z)')
    await expect(redo).toHaveAttribute('title', 'Redo (Ctrl+Y)')
  })
})

test.describe('Edit Mode - Editable JSON', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/build')
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })
    await page.locator('[class*="hover:shadow-lg"]').first().click()
    await expect(page.getByRole('button', { name: /Close graph panel/i })).toBeVisible()
    await page.getByRole('button', { name: /Enter edit mode/i }).click()
    await page.getByRole('button', { name: /Show JSON view/i }).click()
  })

  test('JSON view shows Edit button in edit mode', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Edit JSON/i })).toBeVisible()
  })

  test('clicking Edit JSON shows textarea with Format/Apply/Cancel', async ({ page }) => {
    await page.getByRole('button', { name: /Edit JSON/i }).click()
    await expect(page.locator('textarea[aria-label="Edit JSON configuration"]')).toBeVisible()
    await expect(page.getByRole('button', { name: /Format JSON/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /Apply JSON changes/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /Cancel editing/i })).toBeVisible()
  })

  test('Cancel returns to read-only JSON view', async ({ page }) => {
    await page.getByRole('button', { name: /Edit JSON/i }).click()
    await expect(page.locator('textarea')).toBeVisible()
    await page.getByRole('button', { name: /Cancel editing/i }).click()
    await expect(page.locator('textarea')).not.toBeVisible()
    await expect(page.locator('pre')).toBeVisible()
  })
})

test.describe('Edit Mode - DnD Agent Chips', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/build')
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })
    await page.locator('[class*="hover:shadow-lg"]').first().click()
    await expect(page.getByRole('button', { name: /Close graph panel/i })).toBeVisible()
    await page.getByRole('button', { name: /Enter edit mode/i }).click()
    await expect(page.getByText('Editing')).toBeVisible({ timeout: 5_000 })
  })

  test('agent chips have drag-and-drop group label in edit mode', async ({ page }) => {
    const chipGroup = page.locator('[role="group"][aria-label="Reorder agents by dragging"]')
    await expect(chipGroup).toBeVisible()
  })

  test('agent chips are clickable in edit mode', async ({ page }) => {
    const chips = page.locator('[role="group"] [role="button"]')
    const count = await chips.count()
    if (count === 0) {
      test.skip()
      return
    }
    await chips.first().click()
    await expect(chips.first()).toHaveAttribute('aria-pressed', 'true')
  })
})
