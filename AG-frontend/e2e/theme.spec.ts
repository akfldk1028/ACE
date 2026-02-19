import { test, expect } from '@playwright/test'

test.describe('Theme toggle (light/dark mode)', () => {
  test.beforeEach(async ({ page }) => {
    // Clear persisted theme so we start from a clean state
    await page.goto('/')
    await page.evaluate(() => localStorage.removeItem('platform-theme-config'))
    await page.reload()
  })

  test('theme toggle button is visible in sidebar', async ({ page }) => {
    const sidebar = page.locator('aside')
    // In light mode the button reads "Dark Mode"
    const toggleButton = sidebar.getByRole('button', { name: /Mode/i })
    await expect(toggleButton).toBeVisible()
  })

  test('clicking toggle switches to dark mode and adds .dark class', async ({ page }) => {
    const html = page.locator('html')

    // Starting state: should NOT have "dark" class (default is light or system)
    // First, force light by toggling if needed
    const hasDark = await html.evaluate((el) => el.classList.contains('dark'))
    if (hasDark) {
      // Already dark; click to go to light first
      await page.locator('aside').getByRole('button', { name: /Mode/i }).click()
    }
    await expect(html).not.toHaveClass(/dark/)

    // The button should say "Dark Mode" in light mode
    const toggleButton = page.locator('aside').getByRole('button', { name: /Dark Mode/i })
    await expect(toggleButton).toBeVisible()

    // Click to enable dark mode
    await toggleButton.click()

    // Now the html element should have the "dark" class
    await expect(html).toHaveClass(/dark/)

    // The button text should now say "Light Mode"
    await expect(page.locator('aside').getByRole('button', { name: /Light Mode/i })).toBeVisible()
  })

  test('toggling back to light mode removes .dark class', async ({ page }) => {
    const html = page.locator('html')

    // Force dark mode first
    const hasDark = await html.evaluate((el) => el.classList.contains('dark'))
    if (!hasDark) {
      await page.locator('aside').getByRole('button', { name: /Dark Mode/i }).click()
      await expect(html).toHaveClass(/dark/)
    }

    // Now toggle back to light
    await page.locator('aside').getByRole('button', { name: /Light Mode/i }).click()
    await expect(html).not.toHaveClass(/dark/)
  })

  test('theme persists across page reload', async ({ page }) => {
    const html = page.locator('html')

    // Ensure we start in light mode
    const hasDark = await html.evaluate((el) => el.classList.contains('dark'))
    if (hasDark) {
      await page.locator('aside').getByRole('button', { name: /Mode/i }).click()
    }
    await expect(html).not.toHaveClass(/dark/)

    // Switch to dark
    await page.locator('aside').getByRole('button', { name: /Dark Mode/i }).click()
    await expect(html).toHaveClass(/dark/)

    // Reload the page
    await page.reload()

    // Dark mode should be preserved
    await expect(page.locator('html')).toHaveClass(/dark/)
  })
})

test.describe('Color theme selection (Settings page)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings')
    await page.evaluate(() => localStorage.removeItem('platform-theme-config'))
    await page.reload()
    await page.goto('/settings')
  })

  test('settings page shows color theme buttons', async ({ page }) => {
    // 7 themes: Default, Dusk, Lime, Ocean, Retro, Neo, Forest
    // Theme buttons have role="radio" with aria-label="${name} theme"
    const themeNames = ['Default', 'Dusk', 'Lime', 'Ocean', 'Retro', 'Neo', 'Forest']
    for (const name of themeNames) {
      await expect(page.getByRole('radio', { name: `${name} theme` })).toBeVisible()
    }
  })

  test('selecting a color theme sets data-theme attribute on html', async ({ page }) => {
    const html = page.locator('html')

    // Click the "Ocean" theme radio
    await page.getByRole('radio', { name: 'Ocean theme' }).click()

    // The html element should now have data-theme="ocean"
    await expect(html).toHaveAttribute('data-theme', 'ocean')
  })

  test('selecting Default theme removes data-theme attribute', async ({ page }) => {
    const html = page.locator('html')

    // First set a non-default theme
    await page.getByRole('radio', { name: 'Retro theme' }).click()
    await expect(html).toHaveAttribute('data-theme', 'retro')

    // Switch back to Default
    await page.getByRole('radio', { name: 'Default theme' }).click()

    // data-theme should be removed (not present)
    await expect(html).not.toHaveAttribute('data-theme')
  })
})
