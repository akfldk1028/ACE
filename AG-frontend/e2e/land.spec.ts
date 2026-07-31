import { test, expect, type Page, type Route } from '@playwright/test'

/**
 * Land Regulation Analysis Page E2E Tests
 *
 * All API calls are route-mocked so no backend is needed.
 * Routes: GET /arr/land/zones/, GET /arr/land/stats/, POST /arr/land/analyze/
 */

// --------------- Mock Data ---------------

const MOCK_ZONES = {
  zones: [
    { zone_name: '제1종전용주거지역', bcr_default: 50, far_default: 100, category: '주거' },
    { zone_name: '일반상업지역', bcr_default: 80, far_default: 1300, category: '상업' },
    { zone_name: '제2종일반주거지역', bcr_default: 60, far_default: 200, category: '주거' },
  ],
  count: 3,
}

const MOCK_STATS = {
  total_queries: 42,
  avg_response_time_ms: 385,
  by_input_type: [
    { input_type: 'address', count: 30 },
    { input_type: 'pnu', count: 12 },
  ],
  error_count: 2,
}

const MOCK_ANALYZE_RESULT = {
  pnu: {
    pnu: '1168010100100770000',
    sido: '서울특별시',
    sigungu: '강남구',
    eupmyeondong: '역삼동',
    ri: '',
    land_type: '1',
    main_number: '0077',
    sub_number: '0000',
    address: '서울시 강남구 역삼동 677',
  },
  zone_info: {
    matched: 1,
    zones: [{ name: '일반상업지역', bcr: 80, far: 1300, category: '상업' }],
    unmatched: [],
  },
  land_info: {
    success: true,
    pnu: '1168010100100770000',
    land_area_m2: 497.2,
    official_land_price: 28620000,
    land_use_situation: '대',
    zones: ['일반상업지역'],
    source: 'vworld',
  },
  regulations: {
    bcr: { limit_pct: 80, article: '건축법 시행령 제84조' },
    far: { limit_pct: 1300, article: '국토계획법 시행령 제85조' },
    height: { limit_m: null, article: '건축법 제60조' },
    sunlight_setback: { applies: false, direction: null, article: '건축법 제61조' },
    corner_cutoff: { required: true, article: '건축법 제46조' },
    road_diagonal: { multiplier: 1.5, article: '건축법 제60조' },
    building_line: { setback_m: 0, article: '건축법 제47조' },
    adjacent_setback: { min_m: 0.5, article: '건축법 시행령 제80조의2' },
    parking: { rule: '시설면적 150m2당 1대', article: '주차장법 시행령 별표1' },
    landscaping: { min_pct: 5, article: '건축법 제42조' },
  },
  law_articles: {
    articles: [
      {
        query: '건폐율',
        results: [
          {
            hang_id: 'HANG_001',
            content: '건폐율은 80퍼센트 이하',
            law_name: '건축법 시행령',
            law_type: '시행령',
            article: '제84조',
            similarity: 0.92,
          },
        ],
      },
    ],
    total_count: 1,
    errors: [],
  },
  restrictions: ['상업지역 내 주거용도 제한'],
  errors: [],
  warning: null,
}

// --------------- Helpers ---------------

/** Scope selectors to the main content area (avoids matching sidebar elements). */
const mainH1 = (page: Page) => page.locator('main h1')

/** Install route mocks for all three Land API endpoints. */
async function mockLandAPIs(page: Page) {
  await page.route('**/arr/land/zones/', async (route: Route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_ZONES) })
  })
  await page.route('**/arr/land/stats/', async (route: Route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_STATS) })
  })
  await page.route('**/arr/land/analyze/', async (route: Route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_ANALYZE_RESULT) })
  })
}

/** Fill the search input and click Analyze. */
async function submitAnalyze(page: Page, address: string) {
  const input = page.locator('main input')
  await input.fill(address)
  await page.getByRole('button', { name: /Analyze|분석/i }).click()
}

// --------------- Tests ---------------

test.describe('Land page - basic layout', () => {
  test.beforeEach(async ({ page }) => {
    await mockLandAPIs(page)
    await page.goto('/land')
  })

  test('shows page title', async ({ page }) => {
    // Title is i18n: "Land Regulation Analysis" (en) or "토지 규제 분석" (ko)
    await expect(mainH1(page)).toHaveText(/Land Regulation Analysis|토지 규제 분석/)
  })

  test('shows page description', async ({ page }) => {
    await expect(
      page.locator('main').getByText(/BCR.*FAR.*PNU|PNU.*건폐율.*용적률/i),
    ).toBeVisible()
  })

  test('search form has address/PNU toggle, input, and analyze button', async ({ page }) => {
    // Address / PNU toggle buttons
    await expect(page.getByRole('button', { name: /Address|주소/i })).toBeVisible()
    await expect(page.getByRole('button', { name: 'PNU' })).toBeVisible()

    // Input field
    const input = page.locator('main input')
    await expect(input).toBeVisible()

    // Analyze button (disabled when input is empty)
    const analyzeBtn = page.getByRole('button', { name: /Analyze|분석/i })
    await expect(analyzeBtn).toBeVisible()
    await expect(analyzeBtn).toBeDisabled()
  })

  test('zone selector dropdown exists with auto-detect default', async ({ page }) => {
    const select = page.locator('#zone-select')
    await expect(select).toBeVisible()

    // First option is auto-detect
    const firstOption = select.locator('option').first()
    await expect(firstOption).toHaveText(/Auto-detect|자동 감지/)
  })

  test('zone selector is populated from mocked zones API', async ({ page }) => {
    const select = page.locator('#zone-select')
    // Should have auto-detect + 3 zone options = 4 total
    const options = select.locator('option')
    await expect(options).toHaveCount(4)

    // Verify zone names appear in the options
    await expect(select).toContainText('제1종전용주거지역')
    await expect(select).toContainText('일반상업지역')
    await expect(select).toContainText('제2종일반주거지역')
  })
})

test.describe('Land page - stats panel', () => {
  test.beforeEach(async ({ page }) => {
    await mockLandAPIs(page)
    await page.goto('/land')
  })

  test('stats panel renders with mocked data', async ({ page }) => {
    // The heading "Query Statistics" or "조회 통계"
    await expect(page.getByText(/Query Statistics|조회 통계/)).toBeVisible({ timeout: 5_000 })

    // Total queries value
    await expect(page.getByText('42')).toBeVisible()

    // Avg response time
    await expect(page.getByText('385ms')).toBeVisible()

    // Top input type (exact match to avoid matching the "Address" toggle button)
    await expect(page.getByText('address', { exact: true })).toBeVisible()
  })
})

test.describe('Land page - analyze flow', () => {
  test.beforeEach(async ({ page }) => {
    await mockLandAPIs(page)
    await page.goto('/land')
  })

  test('analyze button enables when input has value', async ({ page }) => {
    const input = page.locator('main input')
    const analyzeBtn = page.getByRole('button', { name: /Analyze|분석/i })

    await expect(analyzeBtn).toBeDisabled()
    await input.fill('서울시 강남구 역삼동 677')
    await expect(analyzeBtn).toBeEnabled()
  })

  test('submitting form shows land info card', async ({ page }) => {
    await submitAnalyze(page, '서울시 강남구 역삼동 677')

    // formatPnu: 11680-101-00-1-0077-0000 (slices: 0-5, 5-8, 8-10, 10-11, 11-15, 15-19)
    await expect(page.getByText('11680-101-00-1-0077-0000')).toBeVisible({ timeout: 5_000 })

    // Address in result
    await expect(page.getByText('서울시 강남구 역삼동 677').first()).toBeVisible()

    // Zone info - use the Land Information card (not the hidden <option> in the zone selector)
    const infoCard = page.getByText(/Land Information|토지 정보/).locator('..').locator('..')
    await expect(infoCard.getByText('일반상업지역')).toBeVisible()
  })

  test('regulation summary shows BCR and FAR values', async ({ page }) => {
    await submitAnalyze(page, '서울시 강남구 역삼동 677')

    // Core Regulations heading
    await expect(page.getByText(/Core Regulations|핵심 규제/)).toBeVisible({ timeout: 5_000 })

    // BCR and FAR values - use exact: true to avoid matching hidden <option> text
    await expect(page.getByText('80%', { exact: true })).toBeVisible()
    await expect(page.getByText('1300%', { exact: true })).toBeVisible()
  })

  test('law articles section is collapsible and shows content when expanded', async ({ page }) => {
    await submitAnalyze(page, '서울시 강남구 역삼동 677')

    // Law articles heading (collapsed by default)
    const lawToggle = page.getByText(/Related Law Articles|관련 법조항/)
    await expect(lawToggle).toBeVisible({ timeout: 5_000 })

    // Content should not be visible before expanding
    await expect(page.getByText(/건폐율은 80퍼센트 이하/)).not.toBeVisible()

    // Click to expand (the entire button row is clickable)
    await lawToggle.click()

    // Article content now visible
    await expect(page.getByText(/건폐율은 80퍼센트 이하/)).toBeVisible()
    await expect(page.getByText('건축법 시행령')).toBeVisible()
    await expect(page.getByText('제84조')).toBeVisible()
  })

  test('restrictions section shows restriction items', async ({ page }) => {
    await submitAnalyze(page, '서울시 강남구 역삼동 677')

    await expect(page.getByText('상업지역 내 주거용도 제한')).toBeVisible({ timeout: 5_000 })
  })
})

test.describe('Land page - input type toggle', () => {
  test.beforeEach(async ({ page }) => {
    await mockLandAPIs(page)
    await page.goto('/land')
  })

  test('clicking PNU toggle switches input type', async ({ page }) => {
    const pnuBtn = page.getByRole('button', { name: 'PNU' })
    await pnuBtn.click()

    // PNU button should now have the active styling (text-white)
    await expect(pnuBtn).toHaveClass(/text-white/)
  })

  test('typing a 19-digit PNU auto-detects PNU mode', async ({ page }) => {
    const input = page.locator('main input')
    await input.fill('1168010100100770000')

    // PNU button should become active (the component auto-switches)
    const pnuBtn = page.getByRole('button', { name: 'PNU' })
    await expect(pnuBtn).toHaveClass(/text-white/)
  })
})

test.describe('Land page - zone selection', () => {
  test.beforeEach(async ({ page }) => {
    await mockLandAPIs(page)
    await page.goto('/land')
  })

  test('selecting a zone includes it in the analyze request', async ({ page }) => {
    // Select a zone
    const select = page.locator('#zone-select')
    await select.selectOption('일반상업지역')

    // Fill input
    const input = page.locator('main input')
    await input.fill('서울시 강남구 역삼동 677')

    // Intercept the POST to verify the request body includes zones
    const requestPromise = page.waitForRequest(
      (req) =>
        req.url().includes('/arr/land/analyze/') && req.method() === 'POST',
    )

    await page.getByRole('button', { name: /Analyze|분석/i }).click()

    const request = await requestPromise
    const body = request.postDataJSON()
    expect(body.zones).toEqual(['일반상업지역'])
  })
})

test.describe('Land page - error handling', () => {
  test('shows error message when analyze API fails', async ({ page }) => {
    // Mock zones/stats normally but fail analyze
    await page.route('**/arr/land/zones/', async (route: Route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_ZONES) })
    })
    await page.route('**/arr/land/stats/', async (route: Route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_STATS) })
    })
    await page.route('**/arr/land/analyze/', async (route: Route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Vworld API timeout' }),
      })
    })

    await page.goto('/land')

    const input = page.locator('main input')
    await input.fill('잘못된 주소')
    await page.getByRole('button', { name: /Analyze|분석/i }).click()

    // Error message should appear
    await expect(page.getByText('Vworld API timeout')).toBeVisible({ timeout: 5_000 })
  })
})

test.describe('Land page - navigation', () => {
  test('navigating to /land from another page works', async ({ page }) => {
    await mockLandAPIs(page)
    await page.goto('/')
    await page.goto('/land')
    await expect(mainH1(page)).toHaveText(/Land Regulation Analysis|토지 규제 분석/)
  })
})
