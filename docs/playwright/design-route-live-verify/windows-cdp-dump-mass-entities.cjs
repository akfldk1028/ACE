const { chromium } = require("D:/Data/25_ACE/ARR/frontend/node_modules/playwright");

(async () => {
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  const context = browser.contexts()[0];
  const page = context.pages().find(p => p.url().includes("/design")) || context.pages()[0];
  const state = await page.evaluate(() => {
    const values = window.ws3d?.viewer?.entities?.values || [];
    const ids = values.map(e => String(e.id || ""));
    return {
      url: location.href,
      count: values.length,
      massIds: ids.filter(id => id.startsWith("design-mass-")).slice(0, 200),
      facadeLike: ids.filter(id => id.includes("facade")),
      aestheticLike: ids.filter(id => id.includes("aesthetic")),
      selectedText: (document.body.innerText || "").match(/DESIGN\\n#[\\s\\S]{0,80}/)?.[0] || null,
    };
  });
  console.log(JSON.stringify(state, null, 2));
  await browser.close();
})().catch(err => {
  console.error(err);
  process.exit(1);
});
