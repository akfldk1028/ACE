const fs = require('fs');
const path = require('path');
const { chromium } = require(path.resolve(__dirname, '../../../../ARR/frontend/node_modules/playwright'));

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  const consoleErrors = [];
  const pageErrors = [];
  page.on('console', (message) => { if (message.type() === 'error') consoleErrors.push(message.text()); });
  page.on('pageerror', (error) => pageErrors.push(error.message));

  const response = await page.goto('http://127.0.0.1:5175/design/language', {
    waitUntil: 'domcontentloaded', timeout: 60000,
  });
  await page.locator('[data-testid="maas-book-language-flow"]').waitFor({ state: 'visible', timeout: 30000 });
  const timeline = page.locator('.execution-run-timeline');
  await timeline.waitFor({ state: 'visible', timeout: 30000 });
  const runButtons = timeline.locator('button');
  await runButtons.first().waitFor({ state: 'visible', timeout: 30000 });
  const runCount = await runButtons.count();
  const newestRunTitle = await runButtons.first().getAttribute('title');

  const failedRun = timeline.locator('button[title="book-program-portfolios-r185-program-controller-archive-preflight"]');
  await failedRun.click();
  await page.getByText('실행 상태: aborted_memory_pressure.').waitFor({ state: 'visible', timeout: 30000 });
  const failedRunSelected = await failedRun.getAttribute('data-selected');
  const failedRunMassCards = await page.locator('.geometry-result-gallery button').count();

  const replayRun = timeline.locator('button[title="book-program-portfolios-r182-seven-page-closure-pass"]');
  await replayRun.click();
  await page.locator('.geometry-result-gallery button').first().waitFor({ state: 'visible', timeout: 30000 });
  const replayRunSelected = await replayRun.getAttribute('data-selected');
  const replayMassCards = await page.locator('.geometry-result-gallery button').count();
  const firstMassCard = page.locator('.geometry-result-gallery button').first();
  await firstMassCard.click();
  const selectedMassNode = page.locator('[data-node-kind="executed_mass_result"][data-selected="true"]');
  await selectedMassNode.waitFor({ state: 'visible', timeout: 30000 });
  const selectedMassNodeId = await selectedMassNode.getAttribute('data-node-id');
  const activeEdgeCount = await page.locator('.book-network__edge.is-active').count();
  const runNodeCount = await page.locator('[data-node-kind="execution_run_archive"]').count();
  const bookRasterDomCount = await page.locator('img[src*="book-assets"], a[href*="book-assets"]').count();
  const fullGraphCount = await page.locator('.maas-language-flow__viewport .book-network').count();

  await page.getByRole('tab', { name: 'MASS ARCHIVE' }).click();
  const massOnlyArchive = page.locator('.mass-only-archive');
  await massOnlyArchive.waitFor({ state: 'visible', timeout: 30000 });
  const massOnlyCardCount = await massOnlyArchive.locator('button').count();

  await page.screenshot({
    path: path.join(__dirname, 'chronological-mass-archive.png'),
    fullPage: true,
  });
  const result = {
    http_status: response?.status() ?? null,
    run_count: runCount,
    newest_run_title: newestRunTitle,
    run_node_count: runNodeCount,
    failed_run_selected: failedRunSelected === 'true',
    failed_run_mass_card_count: failedRunMassCards,
    replay_run_selected: replayRunSelected === 'true',
    replay_mass_card_count: replayMassCards,
    selected_mass_node_id: selectedMassNodeId,
    active_edge_count: activeEdgeCount,
    full_graph_count: fullGraphCount,
    mass_only_card_count: massOnlyCardCount,
    book_raster_dom_count: bookRasterDomCount,
    console_errors: consoleErrors,
    page_errors: pageErrors,
  };
  result.pass = result.http_status === 200
    && result.run_count >= 2
    && String(result.newest_run_title || '').includes('r185-program-controller-archive-preflight')
    && result.run_node_count === result.run_count
    && result.failed_run_selected
    && result.failed_run_mass_card_count === 0
    && result.replay_run_selected
    && result.replay_mass_card_count === 20
    && String(result.selected_mass_node_id || '').includes('r182-seven-page-closure-pass')
    && result.active_edge_count > 0
    && result.full_graph_count === 1
    && result.mass_only_card_count === 20
    && result.book_raster_dom_count === 0
    && result.console_errors.length === 0
    && result.page_errors.length === 0;
  fs.writeFileSync(path.join(__dirname, 'verify-chronological-archive.json'), `${JSON.stringify(result, null, 2)}\n`);
  await browser.close();
  if (!result.pass) {
    console.error(JSON.stringify(result, null, 2));
    process.exit(1);
  }
  console.log(JSON.stringify(result, null, 2));
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
