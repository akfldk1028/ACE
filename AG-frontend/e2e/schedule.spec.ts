import { test, expect, type Page } from '@playwright/test'

/**
 * Cron/Scheduling UI E2E Tests
 * Tests the schedule panel, job CRUD, indicator badge,
 * and persistence via localStorage.
 */

/** Clear schedule localStorage and select a team */
async function setupWithTeam(page: Page) {
  await page.addInitScript(() => {
    localStorage.removeItem('ag-schedule-jobs')
  })
  await page.goto('/')

  // Wait for teams to load
  await page.waitForFunction(
    () => {
      const teamSelect = document.querySelector('[aria-label="Select a team"]')
      return teamSelect && teamSelect.querySelectorAll('option').length > 1
    },
    { timeout: 10_000 },
  )

  // Select the first available team
  const select = page.getByLabel('Select a team')
  const options = select.locator('option')
  const secondOption = await options.nth(1).getAttribute('value')
  await select.selectOption(secondOption!)
}

/** Seed a schedule job in localStorage before page load */
async function seedJob(page: Page, overrides: Record<string, unknown> = {}) {
  await page.addInitScript((opts) => {
    const job = {
      id: `sched-test-${Date.now()}`,
      teamId: 1,
      teamName: 'Test Team',
      task: 'Run daily report',
      schedule: { frequency: 'daily', hour: 9, minute: 0 },
      description: 'Daily at 09:00',
      enabled: true,
      status: 'active',
      lastRunAt: null,
      lastRunStatus: null,
      nextRunAt: new Date(Date.now() + 3600000).toISOString(),
      createdAt: new Date().toISOString(),
      ...opts,
    }
    localStorage.setItem('ag-schedule-jobs', JSON.stringify([job]))
  }, overrides)
}

test.describe('Schedule - Indicator', () => {
  test('indicator is hidden when no jobs exist', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.removeItem('ag-schedule-jobs')
    })
    await page.goto('/')

    // ScheduleIndicator returns null when jobs.length === 0
    const indicator = page.getByRole('button', { name: /Schedule/ })
    await expect(indicator).not.toBeVisible()
  })

  test('indicator shows active job count when jobs exist', async ({ page }) => {
    await seedJob(page)
    await page.goto('/')

    const indicator = page.getByRole('button', { name: /Schedule: 1 active/ })
    await expect(indicator).toBeVisible({ timeout: 3000 })
  })

  test('clicking indicator opens schedule panel', async ({ page }) => {
    await seedJob(page)
    await page.goto('/')

    await page.getByRole('button', { name: /Schedule/ }).click()
    const panel = page.getByRole('dialog', { name: 'Schedule Panel' })
    await expect(panel).toBeVisible()
  })
})

test.describe('Schedule - Panel', () => {
  test('panel shows empty state with no jobs', async ({ page }) => {
    await seedJob(page) // Need at least one job for indicator to show
    await page.goto('/')
    // We'll open via indicator then clear
    await page.getByRole('button', { name: /Schedule/ }).click()
    const panel = page.getByRole('dialog', { name: 'Schedule Panel' })
    await expect(panel).toBeVisible()

    // Header
    await expect(panel.getByText('Scheduled Jobs')).toBeVisible()
    // Warning banner
    await expect(panel.getByText('Only runs while this tab is open')).toBeVisible()
  })

  test('close button dismisses the panel', async ({ page }) => {
    await seedJob(page)
    await page.goto('/')

    await page.getByRole('button', { name: /Schedule/ }).click()
    const panel = page.getByRole('dialog', { name: 'Schedule Panel' })
    await expect(panel).toBeVisible()

    await panel.getByRole('button', { name: 'Close schedule panel' }).click()
    await expect(panel).not.toBeVisible()
  })

  test('existing job displays in the panel', async ({ page }) => {
    await seedJob(page, { teamName: 'My Team', task: 'Daily standup check' })
    await page.goto('/')

    await page.getByRole('button', { name: /Schedule/ }).click()
    const panel = page.getByRole('dialog', { name: 'Schedule Panel' })

    await expect(panel.getByText('My Team')).toBeVisible()
    await expect(panel.getByText('Daily standup check')).toBeVisible()
    await expect(panel.getByText('Daily at 09:00')).toBeVisible()
  })
})

test.describe('Schedule - Add Job', () => {
  test('add button opens form and form creates job', async ({ page }) => {
    await setupWithTeam(page)

    // Seed a job so indicator shows
    await page.evaluate(() => {
      const dummyJob = {
        id: 'sched-dummy',
        teamId: 1,
        teamName: 'Dummy',
        task: 'dummy',
        schedule: { frequency: 'daily', hour: 9, minute: 0 },
        description: 'Daily at 09:00',
        enabled: true,
        status: 'active',
        lastRunAt: null,
        lastRunStatus: null,
        nextRunAt: new Date(Date.now() + 3600000).toISOString(),
        createdAt: new Date().toISOString(),
      }
      localStorage.setItem('ag-schedule-jobs', JSON.stringify([dummyJob]))
    })

    // Reload to pick up localStorage
    await page.reload()
    await page.waitForFunction(
      () => {
        const teamSelect = document.querySelector('[aria-label="Select a team"]')
        return teamSelect && teamSelect.querySelectorAll('option').length > 1
      },
      { timeout: 10_000 },
    )
    const select = page.getByLabel('Select a team')
    const options = select.locator('option')
    const secondOption = await options.nth(1).getAttribute('value')
    await select.selectOption(secondOption!)

    // Open panel
    await page.getByRole('button', { name: /Schedule/ }).click()
    const panel = page.getByRole('dialog', { name: 'Schedule Panel' })

    // Click "Add Scheduled Job"
    await panel.getByRole('button', { name: 'Add Scheduled Job' }).click()

    // Fill task
    await panel.getByLabel('Scheduled task').fill('Generate weekly summary')

    // Select frequency
    await panel.getByLabel('Schedule frequency').selectOption('weekly')

    // Click "Add Job"
    await panel.getByRole('button', { name: 'Add Job' }).click()

    // Job should now appear in the list
    await expect(panel.getByText('Generate weekly summary')).toBeVisible()
  })
})

test.describe('Schedule - Job Actions', () => {
  test('pause button toggles job enabled state', async ({ page }) => {
    await seedJob(page)
    await page.goto('/')

    await page.getByRole('button', { name: /Schedule/ }).click()
    const panel = page.getByRole('dialog', { name: 'Schedule Panel' })

    // Click pause
    await panel.getByRole('button', { name: 'Pause job' }).click()

    // After pausing, button should change to "Resume job"
    await expect(panel.getByRole('button', { name: 'Resume job' })).toBeVisible()
  })

  test('delete button removes the job', async ({ page }) => {
    await seedJob(page, { task: 'Task to delete' })
    await page.goto('/')

    await page.getByRole('button', { name: /Schedule/ }).click()
    const panel = page.getByRole('dialog', { name: 'Schedule Panel' })

    await expect(panel.getByText('Task to delete')).toBeVisible()
    await panel.getByRole('button', { name: 'Delete job' }).click()

    // Job should be gone
    await expect(panel.getByText('Task to delete')).not.toBeVisible()
    // Empty state
    await expect(panel.getByText('No scheduled jobs')).toBeVisible()
  })
})
