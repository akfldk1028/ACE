import { test, expect } from '@playwright/test'

/**
 * i18n E2E Tests
 * Tests default English locale, language switching to Korean,
 * and persistence of language preference.
 */

test.describe('i18n - Default English', () => {
  test.beforeEach(async ({ page }) => {
    // Clear language preference to test default
    await page.addInitScript(() => {
      localStorage.removeItem('ag-frontend-locale')
    })
    await page.goto('/')
  })

  test('sidebar shows English navigation labels', async ({ page }) => {
    const sidebar = page.locator('aside')
    await expect(sidebar).toBeVisible()

    const labels = ['Team Builder', 'Playground', 'MCP', 'A2A Agents', 'Gallery', 'Deploy', 'Settings']
    for (const label of labels) {
      await expect(sidebar.getByRole('link', { name: label })).toBeVisible()
    }
  })

  test('playground shows English empty state', async ({ page }) => {
    await expect(page.getByText('Ready to execute')).toBeVisible()
    await expect(page.getByText('Select a team and enter a task to start')).toBeVisible()
  })

  test('playground shows English team label', async ({ page }) => {
    await expect(page.getByText('Team:', { exact: true })).toBeVisible()
  })

  test('playground shows English input placeholder', async ({ page }) => {
    const input = page.getByPlaceholder('Enter a task for the team...')
    await expect(input).toBeVisible()
  })
})

test.describe('i18n - Language Switching', () => {
  test('settings page has language selector', async ({ page }) => {
    await page.goto('/settings')
    await expect(page.getByText('Language', { exact: true })).toBeVisible()
    await expect(page.getByText('Interface language', { exact: true })).toBeVisible()
  })

  test('switching to Korean updates sidebar labels', async ({ page }) => {
    await page.goto('/settings')

    // Find and change language to Korean
    const langSelect = page.locator('select').filter({ has: page.locator('option[value="ko-KR"]') })
    await langSelect.selectOption('ko-KR')

    // Wait for re-render
    await page.waitForTimeout(500)

    // Sidebar should show Korean labels
    const sidebar = page.locator('aside')
    await expect(sidebar.getByRole('link', { name: '팀 빌더' })).toBeVisible()
    await expect(sidebar.getByRole('link', { name: '플레이그라운드' })).toBeVisible()
    await expect(sidebar.getByRole('link', { name: '갤러리' })).toBeVisible()
    await expect(sidebar.getByRole('link', { name: '설정' })).toBeVisible()
  })

  test('language preference persists across navigation', async ({ page }) => {
    // Set Korean locale
    await page.addInitScript(() => {
      localStorage.setItem('ag-frontend-locale', 'ko-KR')
    })
    await page.goto('/')

    // Sidebar should show Korean
    const sidebar = page.locator('aside')
    await expect(sidebar.getByRole('link', { name: '플레이그라운드' })).toBeVisible()

    // Navigate to settings
    await sidebar.getByRole('link', { name: '설정' }).click()
    await expect(page.locator('main h1')).toHaveText('설정')
  })

  test('switching back to English restores labels', async ({ page }) => {
    // Start with Korean
    await page.addInitScript(() => {
      localStorage.setItem('ag-frontend-locale', 'ko-KR')
    })
    await page.goto('/settings')

    // Switch to English
    const langSelect = page.locator('select').filter({ has: page.locator('option[value="en-US"]') })
    await langSelect.selectOption('en-US')
    await page.waitForTimeout(500)

    // Sidebar should show English
    const sidebar = page.locator('aside')
    await expect(sidebar.getByRole('link', { name: 'Settings' })).toBeVisible()
    await expect(sidebar.getByRole('link', { name: 'Playground' })).toBeVisible()
  })
})
