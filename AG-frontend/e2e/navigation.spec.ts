import { test, expect } from '@playwright/test'

// Use main content area to avoid matching sidebar h1 "AG Frontend"
const mainH1 = (page: import('@playwright/test').Page) => page.locator('main h1')

test.describe('Page navigation - all 7 routes load correctly', () => {
  test('/ renders the Playground page (index route)', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('Ready to execute')).toBeVisible()
  })

  test('/build shows Team Builder heading', async ({ page }) => {
    await page.goto('/build')
    await expect(mainH1(page)).toHaveText('Team Builder')
  })

  test('/agents shows A2A Agents heading', async ({ page }) => {
    await page.goto('/agents')
    await expect(mainH1(page)).toHaveText('A2A Agents')
  })

  test('/gallery shows Gallery heading', async ({ page }) => {
    await page.goto('/gallery')
    await expect(mainH1(page)).toHaveText('Gallery')
  })

  test('/mcp shows MCP heading', async ({ page }) => {
    await page.goto('/mcp')
    await expect(mainH1(page)).toHaveText('MCP')
  })

  test('/deploy shows Deploy heading', async ({ page }) => {
    await page.goto('/deploy')
    await expect(mainH1(page)).toHaveText('Deploy')
  })

  test('/settings shows Settings heading', async ({ page }) => {
    await page.goto('/settings')
    await expect(mainH1(page)).toHaveText('Settings')
  })
})
