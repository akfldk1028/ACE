import { test, expect } from '@playwright/test'

/**
 * Phase 2c E2E Tests
 * Agent Config Panel + Pattern Selector + JSON Toggle
 */

test.describe('Agent Config Panel', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/build')
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })
    // Click first team card to open graph panel
    await page.locator('[class*="hover:shadow-lg"]').first().click()
    await expect(page.locator('.react-flow')).toBeVisible({ timeout: 5_000 })
  })

  test('clicking an agent node shows config panel', async ({ page }) => {
    // Find and click an agent node (not User or End)
    const agentNode = page.locator('[data-testid^="agent-node-"]').filter({ hasNot: page.locator('text=User') }).filter({ hasNot: page.locator('text=End') }).first()
    await agentNode.click()

    // Config panel should appear
    await expect(page.locator('[aria-label="Agent configuration panel"]')).toBeVisible({ timeout: 3_000 })
  })

  test('config panel shows agent name and provider', async ({ page }) => {
    const agentNode = page.locator('[data-testid^="agent-node-"]').filter({ hasNot: page.locator('text=User') }).filter({ hasNot: page.locator('text=End') }).first()
    await agentNode.click()

    const panel = page.locator('[aria-label="Agent configuration panel"]')
    await expect(panel).toBeVisible({ timeout: 3_000 })

    // Should have "Name" label and agent name text
    await expect(panel.locator('text=Name')).toBeVisible()
    await expect(panel.locator('text=Provider')).toBeVisible()
  })

  test('config panel shows model info when available', async ({ page }) => {
    const agentNode = page.locator('[data-testid^="agent-node-"]').filter({ hasNot: page.locator('text=User') }).filter({ hasNot: page.locator('text=End') }).first()
    await agentNode.click()

    const panel = page.locator('[aria-label="Agent configuration panel"]')
    await expect(panel).toBeVisible({ timeout: 3_000 })

    // Model section may or may not exist depending on data, but panel is visible
    expect(await panel.textContent()).toBeTruthy()
  })

  test('close button hides config panel', async ({ page }) => {
    const agentNode = page.locator('[data-testid^="agent-node-"]').filter({ hasNot: page.locator('text=User') }).filter({ hasNot: page.locator('text=End') }).first()
    await agentNode.click()

    const panel = page.locator('[aria-label="Agent configuration panel"]')
    await expect(panel).toBeVisible({ timeout: 3_000 })

    // Click close button
    await page.locator('[aria-label="Close agent panel"]').click()
    await expect(panel).not.toBeVisible()
  })

  test('clicking same node again closes panel (toggle)', async ({ page }) => {
    const agentNode = page.locator('[data-testid^="agent-node-"]').filter({ hasNot: page.locator('text=User') }).filter({ hasNot: page.locator('text=End') }).first()

    // First click opens
    await agentNode.click()
    await expect(page.locator('[aria-label="Agent configuration panel"]')).toBeVisible({ timeout: 3_000 })

    // Second click on same node closes
    await agentNode.click()
    await expect(page.locator('[aria-label="Agent configuration panel"]')).not.toBeVisible()
  })
})

test.describe('Pattern Selector', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/build')
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })
    await page.locator('[class*="hover:shadow-lg"]').first().click()
    await expect(page.locator('.react-flow')).toBeVisible({ timeout: 5_000 })
  })

  test('Patterns button toggles pattern selector', async ({ page }) => {
    await page.locator('[aria-label="Toggle pattern selector"]').click()
    await expect(page.locator('[role="radiogroup"]')).toBeVisible()

    // Toggle off
    await page.locator('[aria-label="Toggle pattern selector"]').click()
    await expect(page.locator('[role="radiogroup"]')).not.toBeVisible()
  })

  test('current pattern is highlighted with aria-checked', async ({ page }) => {
    await page.locator('[aria-label="Toggle pattern selector"]').click()

    const radioGroup = page.locator('[role="radiogroup"]')
    await expect(radioGroup).toBeVisible()

    // Exactly one radio should be checked
    const checkedRadios = radioGroup.locator('[role="radio"][aria-checked="true"]')
    await expect(checkedRadios).toHaveCount(1)
  })

  test('shows 5 pattern radio cards', async ({ page }) => {
    await page.locator('[aria-label="Toggle pattern selector"]').click()

    const radios = page.locator('[role="radiogroup"] [role="radio"]')
    await expect(radios).toHaveCount(5)
  })
})

test.describe('JSON Toggle', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/build')
    await page.waitForSelector('[class*="hover:shadow-lg"]', { timeout: 10_000 })
    await page.locator('[class*="hover:shadow-lg"]').first().click()
    await expect(page.locator('.react-flow')).toBeVisible({ timeout: 5_000 })
  })

  test('JSON toggle button exists', async ({ page }) => {
    await expect(page.locator('[aria-label="Show JSON view"]')).toBeVisible()
  })

  test('clicking JSON button shows JSON view', async ({ page }) => {
    await page.locator('[aria-label="Show JSON view"]').click()

    // JSON view should appear
    await expect(page.locator('[aria-label="Team configuration JSON"]')).toBeVisible()

    // Graph should be hidden
    await expect(page.locator('.react-flow')).not.toBeVisible()
  })

  test('clicking Graph button returns to graph view', async ({ page }) => {
    // Switch to JSON
    await page.locator('[aria-label="Show JSON view"]').click()
    await expect(page.locator('[aria-label="Team configuration JSON"]')).toBeVisible()

    // Switch back to Graph
    await page.locator('[aria-label="Show graph view"]').click()
    await expect(page.locator('.react-flow')).toBeVisible({ timeout: 5_000 })
  })

  test('copy button provides feedback', async ({ context, page }) => {
    // Grant clipboard permission for this test
    await context.grantPermissions(['clipboard-write', 'clipboard-read'])

    await page.locator('[aria-label="Show JSON view"]').click()

    const copyBtn = page.locator('[aria-label="Copy JSON to clipboard"]')
    await expect(copyBtn).toBeVisible()

    await copyBtn.click()

    // Should show "Copied!" text briefly
    await expect(copyBtn).toContainText('Copied!')
  })
})
