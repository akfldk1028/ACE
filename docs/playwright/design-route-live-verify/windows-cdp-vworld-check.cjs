const fs = require("fs");
const path = require("path");
const { chromium } = require("D:/Data/25_ACE/ARR/frontend/node_modules/playwright");

(async () => {
  const outDir = "D:/Data/25_ACE/docs/playwright/design-route-live-verify";
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  const context = browser.contexts()[0] || await browser.newContext();
  const page = await context.newPage();
  page.setDefaultTimeout(30000);
  const cdp = await context.newCDPSession(page);
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

  await page.goto("http://127.0.0.1:5174/design", { waitUntil: "domcontentloaded", timeout: 45000 });
  await page.waitForTimeout(3000);
  const before = await page.evaluate(() => {
    const canvas = document.createElement("canvas");
    let webgl = false;
    let renderer = null;
    try {
      const gl = canvas.getContext("webgl2") || canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
      webgl = Boolean(gl);
      if (gl) {
        const debugInfo = gl.getExtension("WEBGL_debug_renderer_info");
        renderer = debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
      }
    } catch {}
    return {
      webdriver: navigator.webdriver,
      userAgent: navigator.userAgent,
      webgl,
      renderer,
      inputCount: document.querySelectorAll("input").length,
      body: (document.body.innerText || "").slice(0, 1500),
    };
  });

  if (before.inputCount > 0) {
    await page.fill('input[placeholder="PNU 코드 (19자리) 또는 주소"]', "1168011800104170004");
    await page.getByRole("button", { name: "조회" }).click({ force: true });
    await page.waitForTimeout(25000);
  }

  const state = await page.evaluate(() => {
    const text = document.body.innerText || "";
    return {
      hasDisabledText: text.includes("WebGL을 사용할 수 없어"),
      hasFallback: text.includes("2D MASS PREVIEW") || text.includes("WebGL fallback"),
      body: text.slice(0, 4000),
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
      scripts: [...document.scripts].map(s => s.src).filter(src => src.includes("vworld") || src.includes("Cesium")),
      vwKeys: Object.keys(window).filter(k => /vw|vworld|Cesium|ws3d/i.test(k)).slice(0, 100),
    };
  });

  let screenshot = null;
  try {
    const shotPath = path.join(outDir, "windows_chrome_vworld_check.png");
    await page.screenshot({ path: shotPath, fullPage: false, timeout: 15000 });
    screenshot = shotPath;
  } catch (err) {
    screenshot = { error: err.message };
  }

  const out = { before, state, screenshot, logs, errors, responses };
  const outPath = path.join(outDir, "windows-chrome-vworld-check.json");
  fs.writeFileSync(outPath, JSON.stringify(out, null, 2), "utf8");
  console.log(JSON.stringify({
    before,
    state,
    screenshot,
    errorCount: errors.length,
    consoleProblems: logs.filter(l => ["error", "warning"].includes(l.type)).slice(0, 30),
    vworldResponses: responses.filter(r => r.url.includes("vworld") || r.url.includes("/land/map-config")).slice(0, 50),
    responseErrors: responses.filter(r => r.status >= 400).slice(0, 20),
  }, null, 2));
  await page.close();
  await browser.close();
})().catch(err => {
  console.error(err);
  process.exit(1);
});
