const fs = require("fs");
const path = require("path");
const { chromium } = require("D:/Data/25_ACE/ARR/frontend/node_modules/playwright");

(async () => {
  const outDir = "D:/Data/25_ACE/docs/playwright/design-route-live-verify";
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  const context = browser.contexts()[0] || await browser.newContext();
  const page = await context.newPage();
  page.setDefaultTimeout(45000);
  const cdp = await context.newCDPSession(page);
  try {
    await cdp.send("Network.enable");
    await cdp.send("Network.setCacheDisabled", { cacheDisabled: true });
  } catch (err) {
    console.warn("cache disable failed", err);
  }
  try {
    const { windowId } = await cdp.send("Browser.getWindowForTarget");
    await cdp.send("Browser.setWindowBounds", {
      windowId,
      bounds: { left: 0, top: 0, width: 1800, height: 1100, windowState: "normal" },
    });
    await page.setViewportSize({ width: 1800, height: 1000 });
  } catch (err) {
    console.warn("window resize failed", err);
  }

  const logs = [];
  const errors = [];
  const responses = [];
  page.on("console", msg => logs.push({ type: msg.type(), text: msg.text() }));
  page.on("pageerror", err => errors.push({ name: err.name, message: err.message, stack: err.stack }));
  page.on("response", res => {
    const url = res.url();
    if (url.includes("vworld") || url.includes("/land/map-config") || url.includes("/design") || res.status() >= 400) {
      responses.push({ status: res.status(), url });
    }
  });

  await page.goto(`http://127.0.0.1:5174/design?verifyTs=${Date.now()}`, { waitUntil: "domcontentloaded", timeout: 45000 });
  await page.fill('input[placeholder="PNU 코드 (19자리) 또는 주소"]', "1168011800104170004");
  await page.getByRole("button", { name: "조회" }).click({ force: true });
  await page.waitForTimeout(12000);
  await page.getByRole("button", { name: /OPTIMIZE/i }).click({ force: true });
  let waitError = null;
  try {
    await page.waitForFunction(
      () => {
        const text = document.body.innerText || "";
        const entities = window.ws3d?.viewer?.entities?.values || [];
        return text.includes("DESIGN LIST")
          && text.includes("BUILDING MASS")
          && entities.some(e => String(e.id || "").startsWith("design-mass-"));
      },
      null,
      { timeout: 70000 },
    );
  } catch (err) {
    waitError = { name: err.name, message: err.message };
  }
  await page.waitForTimeout(6000);

  const state = await page.evaluate(() => {
    const text = document.body.innerText || "";
    const entityIds = (() => {
      try {
        return window.ws3d?.viewer?.entities?.values?.map(e => e.id).filter(Boolean).slice(0, 220) || [];
      } catch {
        return [];
      }
    })();
    return {
      hasDisabledText: text.includes("WebGL을 사용할 수 없어"),
      hasFallback: text.includes("2D MASS PREVIEW") || text.includes("WebGL fallback"),
      hasComplete: text.includes("COMPLETE"),
      hasDesignList: text.includes("DESIGN LIST"),
      hasMassText: text.includes("BUILDING MASS") && text.includes("maas_legal_envelope"),
      body: text.slice(0, 5000),
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
      entityIds,
      designMassEntities: entityIds.filter(id => String(id).startsWith("design-mass-")),
      massDebug: window.__arrLastMassRender || null,
      vwKeys: Object.keys(window).filter(k => /vw|vworld|Cesium|ws3d/i.test(k)).slice(0, 100),
    };
  });

  const shotPath = path.join(outDir, "windows_chrome_vworld_optimize.png");
  let screenshot = null;
  try {
    await page.screenshot({ path: shotPath, fullPage: false, timeout: 20000 });
    screenshot = shotPath;
  } catch (err) {
    screenshot = { error: err.message };
  }

  const out = { waitError, state, screenshot, logs, errors, responses };
  const outPath = path.join(outDir, "windows-chrome-vworld-optimize.json");
  fs.writeFileSync(outPath, JSON.stringify(out, null, 2), "utf8");
  console.log(JSON.stringify({
    waitError,
    state,
    screenshot,
    errorCount: errors.length,
    consoleProblems: logs.filter(l => ["error", "warning"].includes(l.type)).slice(0, 30),
    responseErrors: responses.filter(r => r.status >= 400).slice(0, 20),
  }, null, 2));
  await page.close();
  await browser.close();
})().catch(err => {
  console.error(err);
  process.exit(1);
});
