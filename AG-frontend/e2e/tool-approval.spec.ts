import { test, expect, type Page } from '@playwright/test'

/**
 * Tool Approval UI E2E Tests
 * Tests the tool approval card rendering, approval/reject actions,
 * and "allow always" auto-approve behavior.
 *
 * Uses store injection since tool approval requires WS input_request messages
 * that can't be triggered without a real execution.
 */

/** Inject tool-approval store state via page.evaluate */
async function enqueueApproval(page: Page, overrides: Record<string, unknown> = {}) {
  await page.evaluate((opts) => {
    // Access the Zustand store directly
    const mod = window as unknown as Record<string, unknown>
    const store = mod.__toolApprovalStore as { getState: () => Record<string, unknown>; setState: (s: unknown) => void } | undefined
    if (!store) return
    const id = `test-${Date.now()}`
    const approval = {
      id,
      toolName: opts.toolName ?? 'read_file',
      args: opts.args ?? '{"path": "/src/index.ts"}',
      icon: opts.icon ?? 'read',
      source: opts.source ?? 'coding_agent',
      timestamp: new Date().toISOString(),
      status: 'pending',
      ...opts,
    }
    const state = store.getState() as { queue: unknown[] }
    store.setState({ queue: [...state.queue, approval] })
  }, overrides)
}

/** Expose the tool-approval store on window before tests */
async function exposeStores(page: Page) {
  await page.evaluate(() => {
    // Dynamic import to get the store reference
    import('/src/features/tool-approval/tool-approval.store.ts').then((mod) => {
      ;(window as unknown as Record<string, unknown>).__toolApprovalStore = mod.useToolApprovalStore
    }).catch(() => {})
  })
  // Give Vite a moment to resolve the dynamic import
  await page.waitForTimeout(500)
}

test.describe('Tool Approval UI', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await exposeStores(page)
  })

  test('tool approval card renders with tool name and source', async ({ page }) => {
    await enqueueApproval(page, { toolName: 'edit_file', source: 'code_agent' })

    const card = page.getByRole('alert')
    await expect(card).toBeVisible({ timeout: 3000 })
    await expect(card.getByText('Tool Approval Required')).toBeVisible()
    await expect(card.getByText('edit_file')).toBeVisible()
    await expect(card.getByText('from code_agent')).toBeVisible()
  })

  test('shows tool arguments in code block', async ({ page }) => {
    await enqueueApproval(page, { args: '{"file": "test.ts", "content": "hello"}' })

    const card = page.getByRole('alert')
    await expect(card).toBeVisible({ timeout: 3000 })
    await expect(card.locator('pre')).toContainText('test.ts')
  })

  test('has Allow Once, Allow Always, and Reject buttons', async ({ page }) => {
    await enqueueApproval(page)

    const card = page.getByRole('alert')
    await expect(card).toBeVisible({ timeout: 3000 })
    await expect(page.getByRole('button', { name: 'Allow once' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Allow always' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Reject' })).toBeVisible()
  })

  test('Allow Once removes the card from queue', async ({ page }) => {
    await enqueueApproval(page)
    await expect(page.getByRole('alert')).toBeVisible({ timeout: 3000 })

    await page.getByRole('button', { name: 'Allow once' }).click()
    await expect(page.getByRole('alert')).not.toBeVisible({ timeout: 3000 })
  })

  test('Reject removes the card from queue', async ({ page }) => {
    await enqueueApproval(page)
    await expect(page.getByRole('alert')).toBeVisible({ timeout: 3000 })

    await page.getByRole('button', { name: 'Reject' }).click()
    await expect(page.getByRole('alert')).not.toBeVisible({ timeout: 3000 })
  })

  test('queue badge shows count when multiple approvals pending', async ({ page }) => {
    await enqueueApproval(page, { toolName: 'tool_a' })
    await enqueueApproval(page, { toolName: 'tool_b' })

    const card = page.getByRole('alert')
    await expect(card).toBeVisible({ timeout: 3000 })
    // Should show "+1 more" since there are 2 items in queue
    await expect(card.getByText('+1 more')).toBeVisible()
  })
})
