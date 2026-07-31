const fs = require("fs");
const path = require("path");
const { chromium } = require("D:/Data/25_ACE/ARR/frontend/node_modules/playwright");

(async () => {
  const outDir = "D:/Data/25_ACE/docs/playwright/design-route-live-verify/live-captures";
  fs.mkdirSync(outDir, { recursive: true });
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  const context = browser.contexts()[0] || await browser.newContext();
  let page = context.pages().find((p) => p.url().includes("/design")) || context.pages()[0];
  if (!page) page = await context.newPage();
  page.setDefaultTimeout(30000);

  try {
    const cdp = await context.newCDPSession(page);
    const { windowId } = await cdp.send("Browser.getWindowForTarget");
    await cdp.send("Browser.setWindowBounds", {
      windowId,
      bounds: { left: 0, top: 0, width: 1800, height: 1100, windowState: "normal" },
    });
    await page.setViewportSize({ width: 1800, height: 1000 });
  } catch {}

  if (!page.url().includes("/design")) {
    await page.goto("http://127.0.0.1:5174/design", {
      waitUntil: "domcontentloaded",
      timeout: 45000,
    });
    await page.waitForTimeout(5000);
  }

  const state = await page.evaluate(() => {
    const text = document.body.innerText || "";
    const entityIds = (() => {
      try {
        return window.ws3d?.viewer?.entities?.values?.map((e) => e.id).filter(Boolean) || [];
      } catch {
        return [];
      }
    })();
    return {
      url: location.href,
      hasComplete: text.includes("OPTIMIZATION") && text.includes("COMPLETE"),
      hasDesignList: text.includes("DESIGN LIST"),
      hasMassText: text.includes("BUILDING MASS"),
      hasFallback: text.includes("2D MASS PREVIEW") || text.includes("WebGL fallback"),
      hasDisabledText: text.includes("WebGL을 사용할 수 없어"),
      bodyHead: text.slice(0, 1200),
      canvases: [...document.querySelectorAll("canvas")].map((c, i) => ({
        i,
        width: c.width,
        height: c.height,
        rect: {
          width: c.getBoundingClientRect().width,
          height: c.getBoundingClientRect().height,
        },
        className: String(c.className || ""),
      })),
      designMassEntities: entityIds.filter((id) => String(id).startsWith("design-mass-")),
      entityCount: entityIds.length,
      vwKeys: Object.keys(window).filter((k) => /vw|vworld|Cesium|ws3d/i.test(k)).slice(0, 80),
    };
  });

  const pngPath = path.join(outDir, `vworld-live-${stamp}.png`);
  await page.screenshot({ path: pngPath, fullPage: false, timeout: 30000 });
  const jsonPath = path.join(outDir, `vworld-live-${stamp}.json`);
  fs.writeFileSync(jsonPath, JSON.stringify({ stamp, pngPath, state }, null, 2), "utf8");

  console.log(JSON.stringify({
    pngPath,
    jsonPath,
    state: {
      hasComplete: state.hasComplete,
      hasDesignList: state.hasDesignList,
      hasMassText: state.hasMassText,
      hasFallback: state.hasFallback,
      hasDisabledText: state.hasDisabledText,
      designMassEntities: state.designMassEntities.length,
      canvases: state.canvases.slice(0, 3),
    },
  }, null, 2));
  await browser.close();
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
