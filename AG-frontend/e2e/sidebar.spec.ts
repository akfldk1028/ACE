import { test, expect } from '@playwright/test'

test.describe('Sidebar navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('sidebar is visible with all nav links', async ({ page }) => {
    const sidebar = page.locator('aside')
    await expect(sidebar).toBeVisible()

    // The sidebar shows the app title
    await expect(sidebar.locator('h1')).toHaveText('AG Frontend')

    // All nav labels should be present (matching AutoGen Studio)
    const labels = ['Team Builder', 'Playground', 'MCP', 'A2A Agents', 'Gallery', 'Deploy', 'Settings']
    for (const label of labels) {
      await expect(sidebar.getByRole('link', { name: label })).toBeVisible()
    }
  })

  test('clicking Team Builder link navigates to /build', async ({ page }) => {
    await page.locator('aside').getByRole('link', { name: 'Team Builder' }).click()
    await expect(page).toHaveURL(/\/build$/)
    await expect(page.locator('main h1')).toHaveText('Team Builder')
  })

  test('clicking Gallery link navigates to /gallery', async ({ page }) => {
    await page.locator('aside').getByRole('link', { name: 'Gallery' }).click()
    await expect(page).toHaveURL(/\/gallery$/)
    await expect(page.locator('main h1')).toHaveText('Gallery')
  })

  test('clicking MCP link navigates to /mcp', async ({ page }) => {
    await page.locator('aside').getByRole('link', { name: 'MCP' }).click()
    await expect(page).toHaveURL(/\/mcp$/)
    await expect(page.locator('main h1')).toHaveText('MCP')
  })

  test('clicking Deploy link navigates to /deploy', async ({ page }) => {
    await page.locator('aside').getByRole('link', { name: 'Deploy' }).click()
    await expect(page).toHaveURL(/\/deploy$/)
    await expect(page.locator('main h1')).toHaveText('Deploy')
  })

  test('clicking Settings link navigates to /settings', async ({ page }) => {
    await page.locator('aside').getByRole('link', { name: 'Settings' }).click()
    await expect(page).toHaveURL(/\/settings$/)
    await expect(page.locator('main h1')).toHaveText('Settings')
  })

  test('active nav link has distinct styling on Playground (home)', async ({ page }) => {
    const playgroundLink = page.locator('aside').getByRole('link', { name: 'Playground' })
    await expect(playgroundLink).toHaveClass(/accent-primary/)
  })

  test('active styling follows navigation', async ({ page }) => {
    const buildLink = page.locator('aside').getByRole('link', { name: 'Team Builder' })
    await buildLink.click()
    await expect(page).toHaveURL(/\/build$/)
    await expect(buildLink).toHaveClass(/accent-primary/)

    const playgroundLink = page.locator('aside').getByRole('link', { name: 'Playground' })
    await expect(playgroundLink).not.toHaveClass(/accent-primary/)
  })
})
