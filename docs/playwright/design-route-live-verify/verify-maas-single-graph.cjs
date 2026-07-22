const fs = require('fs');
const path = require('path');
const { chromium } = require(path.resolve(
  __dirname,
  '../../../ARR/frontend/node_modules/playwright',
));

async function main() {
  const outputDir = path.resolve(
    process.env.MAAS_VERIFY_OUTPUT_DIR
      || path.join(__dirname, 'maas-single-graph-current'),
  );
  const expectedMassCount = Number(process.env.MAAS_EXPECTED_MASS_COUNT || 20);
  fs.mkdirSync(outputDir, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  const consoleErrors = [];
  const pageErrors = [];
  const bookRasterRequests = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('request', (request) => {
    if (request.url().includes('/book-assets/')) bookRasterRequests.push(request.url());
  });

  const response = await page.goto('http://127.0.0.1:5175/design/language', {
    waitUntil: 'domcontentloaded',
    timeout: 60000,
  });
  await page.locator('[data-testid="maas-book-language-flow"]').waitFor({
    state: 'visible',
    timeout: 30000,
  });
  await page.getByRole('tab', { name: 'FULL GRAPH' }).click();
  await page.locator('[data-node-kind="executed_mass_result"]').first().waitFor({
    state: 'visible',
    timeout: 30000,
  });
  await page.locator('[data-node-kind^="agent_memory_"]').first().waitFor({
    state: 'visible',
    timeout: 30000,
  });
  await page.waitForFunction((expected) => {
    const images = [...document.querySelectorAll('.geometry-result-gallery img')];
    return images.length === expected
      && images.every((image) => image.complete && image.naturalWidth > 0 && image.naturalHeight > 0);
  }, expectedMassCount, { timeout: 30000 });

  const massNodeCount = await page.locator('[data-node-kind="executed_mass_result"]').count();
  const galleryImages = await page.locator('.geometry-result-gallery img').evaluateAll((images) => ({
    count: images.length,
    loaded: images.filter((image) => image.complete && image.naturalWidth > 0 && image.naturalHeight > 0).length,
  }));
  const firstMass = page.locator('[data-node-kind="executed_mass_result"]').first();
  await firstMass.click();
  const result = {
    http_status: response?.status() ?? null,
    graph_count: await page.locator('.maas-language-flow__viewport .book-network').count(),
    base_model_count: await page.locator('[data-node-kind="base_model"]').count(),
    operative_count: await page.locator('[data-node-kind="operation"]').count(),
    executed_mass_node_count: massNodeCount,
    expected_mass_node_count: expectedMassCount,
    executed_mass_gallery_image_count: galleryImages.count,
    loaded_mass_gallery_image_count: galleryImages.loaded,
    retrieved_archdaily_reference_count: await page.locator('[data-node-kind="retrieved_reference_image"]').count(),
    active_vlm_reference_count: await page.locator('[data-node-kind="vlm_reference_image"]').count(),
    exact_agent_memory_node_count: await page.locator('[data-node-kind^="agent_memory_"]').count(),
    related_node_count_after_mass_click: await page.locator('.book-network__node[data-related="true"]').count(),
    active_edge_count_after_mass_click: await page.locator('.book-network__edge.is-active').count(),
    book_raster_requests: bookRasterRequests,
    book_raster_dom_count: await page.locator('img[src*="book-assets"], a[href*="book-assets"]').count(),
    console_errors: consoleErrors,
    page_errors: pageErrors,
  };

  await page.getByRole('tab', { name: 'SELECTED MASS PATH' }).click();
  await page.locator('[data-node-id="result:mass"]').waitFor({ state: 'visible', timeout: 30000 });
  result.selected_path_graph_count = await page.locator('.maas-language-flow__viewport .book-network').count();
  result.selected_path_result_count = await page.locator('[data-node-id="result:mass"]').count();
  await page.getByRole('tab', { name: 'FULL GRAPH' }).click();
  await page.waitForFunction(() => {
    const image = document.querySelector('.executed-mass-evidence .geometry-contract__preview img');
    return image instanceof HTMLImageElement
      && image.complete
      && image.naturalWidth > 0
      && image.naturalHeight > 0;
  }, undefined, { timeout: 30000 });
  result.selected_mass_evidence_image_loaded = await page
    .locator('.executed-mass-evidence .geometry-contract__preview img')
    .evaluate((image) => image.complete && image.naturalWidth > 0 && image.naturalHeight > 0);

  const runCountBeforeSingleExecution = await page.locator('.execution-run-timeline button').count();
  await page.getByRole('button', { name: 'Execute selected MASS' }).click();
  await page.waitForFunction(() => {
    const selected = document.querySelector('.execution-run-timeline button[data-selected="true"]');
    return selected instanceof HTMLButtonElement
      && (selected.title || '').startsWith('single-execution:');
  }, undefined, { timeout: 30000 });
  await page.waitForFunction(() => {
    const images = [...document.querySelectorAll('.geometry-result-gallery img')];
    return images.length === 1
      && images.every((image) => image.complete && image.naturalWidth > 0 && image.naturalHeight > 0);
  }, undefined, { timeout: 30000 });
  result.single_execution_run_id = await page
    .locator('.execution-run-timeline button[data-selected="true"]')
    .getAttribute('title');
  result.single_execution_timeline_count = await page.locator('.execution-run-timeline button').count();
  result.single_execution_mass_node_count = await page.locator('[data-node-kind="executed_mass_result"]').count();
  result.single_execution_gallery_image_count = await page.locator('.geometry-result-gallery img').count();
  result.single_execution_graph_count = await page.locator('.maas-language-flow__viewport .book-network').count();
  result.single_execution_button_complete = await page
    .getByRole('button', { name: 'Execute selected MASS' })
    .textContent();
  result.single_execution_passport_visible = await page
    .locator('.executed-mass-evidence')
    .getByText('PASSPORT', { exact: true })
    .count();
  await page.locator('[data-node-kind="executed_mass_result"]').first().click();
  result.single_execution_related_node_count = await page.locator('.book-network__node[data-related="true"]').count();
  result.single_execution_active_edge_count = await page.locator('.book-network__edge.is-active').count();
  result.single_execution_run_added = result.single_execution_timeline_count > runCountBeforeSingleExecution;
  await page.screenshot({
    path: path.join(outputDir, 'single-execution-full-graph.png'),
    fullPage: true,
  });

  await page.screenshot({
    path: path.join(outputDir, 'full-graph.png'),
    fullPage: true,
  });
  const reference = page.locator('[data-node-kind="retrieved_reference_image"]').first();
  if (await reference.count()) {
    await reference.evaluate((node) => node.scrollIntoView({ block: 'center', inline: 'center' }));
    await page.screenshot({
      path: path.join(outputDir, 'archdaily-vlm-reference-nodes.png'),
      fullPage: false,
    });
  }

  result.pass = result.http_status === 200
    && result.graph_count === 1
    && result.base_model_count === 6
    && result.operative_count === 30
    && result.executed_mass_node_count === expectedMassCount
    && result.executed_mass_gallery_image_count === expectedMassCount
    && result.loaded_mass_gallery_image_count === expectedMassCount
    && result.selected_mass_evidence_image_loaded === true
    && typeof result.single_execution_run_id === 'string'
    && result.single_execution_run_id.startsWith('single-execution:')
    && result.single_execution_run_added === true
    && result.single_execution_mass_node_count === 1
    && result.single_execution_gallery_image_count === 1
    && result.single_execution_graph_count === 1
    && result.single_execution_button_complete.includes('NEW RUN ADDED TO THIS GRAPH')
    && result.single_execution_passport_visible === 1
    && result.single_execution_related_node_count > 1
    && result.single_execution_active_edge_count > 0
    && result.retrieved_archdaily_reference_count > 0
    && result.exact_agent_memory_node_count > 0
    && result.related_node_count_after_mass_click > 1
    && result.active_edge_count_after_mass_click > 0
    && result.selected_path_graph_count === 1
    && result.selected_path_result_count === 1
    && result.book_raster_requests.length === 0
    && result.book_raster_dom_count === 0
    && result.console_errors.length === 0
    && result.page_errors.length === 0;
  fs.writeFileSync(
    path.join(outputDir, 'verify.json'),
    `${JSON.stringify(result, null, 2)}\n`,
  );
  await browser.close();
  if (!result.pass) throw new Error(JSON.stringify(result));
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
