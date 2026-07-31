const { chromium } = require("D:/Data/25_ACE/ARR/frontend/node_modules/playwright");

(async () => {
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222", { timeout: 90000 });
  const pages = browser.contexts().flatMap(context => context.pages());
  const page = pages.find(item => item.url().includes("/design")) || pages[0];
  if (!page) {
    console.log("[]");
    return;
  }
  const data = await page.evaluate(() => (window.__arrDesignLastMassFeatures || []).map(feature => {
    const props = feature.properties || {};
    const precheck = props.parking_precheck || {};
    const layout = precheck.layout_candidate || {};
    return {
      id: props.design_id,
      variant: props.variant_id,
      score: props.maas_score,
      shape: props.mass_shape,
      strategy: precheck.selected_strategy,
      status: layout.status,
      provided: layout.provided_spaces,
      required: layout.required_spaces,
      reason: layout.reason,
      adjacency: layout.adjacency,
    };
  }));
  console.log(JSON.stringify(data, null, 2));
})();
