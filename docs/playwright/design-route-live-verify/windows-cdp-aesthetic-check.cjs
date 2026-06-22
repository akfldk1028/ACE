const fs = require("fs");
const path = require("path");
let chromium;
try {
  chromium = require("D:/Data/25_ACE/ARR/frontend/node_modules/playwright").chromium;
} catch {
  chromium = require("/mnt/d/Data/25_ACE/ARR/frontend/node_modules/playwright").chromium;
}

(async () => {
  const outDir = "D:/Data/25_ACE/docs/playwright/design-route-live-verify";
  fs.mkdirSync(outDir, { recursive: true });
  const provider = process.env.AESTHETIC_PROVIDER || "placeholder";
  const textureProbe = process.env.TEXTURE_PROBE === "reference";
  const providerLabel = {
    "placeholder": "Reference only",
    "gpt-image": "GPT Image",
    "nano-banana": "Nano Banana",
  }[provider] || "Reference only";
  const providerSlug = provider.replace(/[^a-z0-9-]/gi, "_");

  let browser;
  let context;
  try {
    browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
    context = browser.contexts()[0] || await browser.newContext();
  } catch (err) {
    console.warn("CDP attach failed; launching Playwright Chromium", err.message);
    browser = await chromium.launch({
      headless: true,
      args: [
        "--enable-webgl",
        "--ignore-gpu-blocklist",
        "--use-gl=swiftshader",
        "--disable-software-rasterizer=false",
      ],
    });
    context = await browser.newContext({ viewport: { width: 1800, height: 1000 } });
  }
  const page = await context.newPage();
  page.setDefaultTimeout(60000);

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
    if (url.includes("/design/jobs/") || url.includes("/design/maas/aesthetic-assets/") || res.status() >= 400) {
      responses.push({ status: res.status(), url });
    }
  });

  const designUrl = `http://127.0.0.1:5174/design${textureProbe ? "?textureProbe=reference" : ""}`;
  await page.goto(designUrl, { waitUntil: "domcontentloaded", timeout: 45000 });
  await page.fill('input[placeholder="PNU 코드 (19자리) 또는 주소"]', "1168011800104170004");
  await page.getByRole("button", { name: "조회" }).click({ force: true });
  await page.waitForTimeout(12000);
  await page.getByRole("button", { name: /OPTIMIZE/i }).click({ force: true });

  let optimizeWaitError = null;
  try {
    await page.waitForFunction(
      () => {
        const text = document.body.innerText || "";
        return text.includes("OPTIMIZATION") &&
          text.includes("COMPLETE") &&
          text.includes("DESIGN LIST") &&
          text.includes("BUILDING MASS");
      },
      null,
      { timeout: 80000 },
    );
  } catch (err) {
    optimizeWaitError = { name: err.name, message: err.message };
  }

  let aestheticWaitError = null;
  try {
    await page.getByTestId("design-row-0").click({ force: true });
    await page.waitForTimeout(500);
    await page.getByText("외관 이미지 생성").scrollIntoViewIfNeeded();
    await page.locator("select").last().selectOption({ label: providerLabel }).catch(async () => {
      await page.getByText(providerLabel).click({ force: true });
    });
    await page.getByRole("button", { name: "매스 기반 외관 생성" }).click({ force: true });
    await page.waitForFunction(
      (expectedProvider) => {
        const text = document.body.innerText || "";
        const imgs = [...document.querySelectorAll("img")].map(img => img.currentSrc || img.src);
        const entities = window.ws3d?.viewer?.entities?.values || [];
        const last = window.__arrLastMassRender || {};
        const providerDone = expectedProvider === "placeholder"
          ? text.includes("needs_provider")
          : (text.includes("complete") || text.includes("not_configured") || text.includes("fail"));
        const providerFailed = expectedProvider !== "placeholder" &&
          (text.includes("not_configured") || text.includes("fail"));
        const hasFacadeEntity = entities.some(e => String(e.id || "").startsWith("design-mass-facade-"));
        const hasGltfAttempt = last.gltfAttempts > 0 || last.gltfStatus === "added";
        const meshSkipped = text.includes("mesh skipped");
        return text.includes("외관 이미지 생성") &&
          providerDone &&
          imgs.some(src => src.includes("/design/maas/aesthetic-assets/references/")) &&
          (
            (meshSkipped && !hasFacadeEntity && !hasGltfAttempt && last.hasFacadeTextureUrl !== true) ||
            ((hasFacadeEntity || hasGltfAttempt) &&
              (expectedProvider === "placeholder" || providerFailed || last.hasFacadeTextureUrl === true))
          );
      },
      provider,
      { timeout: provider === "placeholder" ? 45000 : 240000 },
    );
  } catch (err) {
    aestheticWaitError = { name: err.name, message: err.message };
  }

  await page.waitForTimeout(1500);

  const state = await page.evaluate(() => {
    const text = document.body.innerText || "";
    const images = [...document.querySelectorAll("img")].map(img => ({
      src: img.currentSrc || img.src,
      alt: img.alt,
      naturalWidth: img.naturalWidth,
      naturalHeight: img.naturalHeight,
      rect: {
        width: img.getBoundingClientRect().width,
        height: img.getBoundingClientRect().height,
      },
    }));
    return {
      hasAestheticSection: text.includes("외관 이미지 생성"),
      providerUnderTest: window.__arrAestheticProviderUnderTest || null,
      hasReferenceImage: images.some(img => img.src.includes("/design/maas/aesthetic-assets/references/")),
      hasNeedsProvider: text.includes("needs_provider"),
      hasLegalEffectNone: text.includes("legal_status_effect: none"),
      lastMassRender: window.__arrLastMassRender || null,
      aestheticOverlayEntities: (() => {
        try {
          return window.ws3d?.viewer?.entities?.values
            ?.map(e => String(e.id || ""))
            ?.filter(id => id.startsWith("design-mass-aesthetic-overlay-")) || [];
        } catch {
          return [];
        }
      })(),
      aestheticFacadeEntities: (() => {
        try {
          return window.ws3d?.viewer?.entities?.values
            ?.map(e => String(e.id || ""))
            ?.filter(id => id.startsWith("design-mass-facade-")) || [];
        } catch {
          return [];
        }
      })(),
      aestheticFacadeMaterialTypes: (() => {
        try {
          return window.ws3d?.viewer?.entities?.values
            ?.filter(e => String(e.id || "").startsWith("design-mass-facade-"))
            ?.slice(0, 8)
            ?.map(e => ({
              id: String(e.id || ""),
              materialType: e.wall?.material?.constructor?.name || typeof e.wall?.material,
              atlasView: e.properties?.facadeAtlasView?.getValue?.() || e.properties?.facadeAtlasView || null,
            })) || [];
        } catch {
          return [];
        }
      })(),
      aestheticGltfPrimitives: (() => {
        try {
          const primitives = window.ws3d?.viewer?.scene?.primitives;
          if (!primitives) return [];
          const ids = [];
          for (let i = 0; i < primitives.length; i++) {
            const primitive = primitives.get(i);
            if (primitive?.__arrEntityPrefix === "design-mass-") {
              ids.push({ designId: primitive.__arrDesignId || null, ready: primitive.ready || false });
            }
          }
          return ids;
        } catch {
          return [];
        }
      })(),
      hasProviderSelect: [...document.querySelectorAll("select option")].map(o => o.textContent),
      body: text.slice(0, 7000),
      images,
    };
  });

  const shotPath = path.join(outDir, `windows_chrome_aesthetic_check_${providerSlug}.png`);
  let screenshot = null;
  try {
    await page.screenshot({ path: shotPath, fullPage: false, timeout: 20000 });
    screenshot = shotPath;
  } catch (err) {
    screenshot = { error: err.message };
  }

  const closeupPath = path.join(outDir, `windows_chrome_aesthetic_closeup_${providerSlug}.png`);
  let closeupScreenshot = null;
  try {
    await page.evaluate(async () => {
      const viewer = window.ws3d?.viewer;
      if (!viewer) return false;
      const entities = viewer.entities?.values || [];
      const targets = entities.filter(e => {
        const id = String(e.id || "");
        return id.startsWith("design-mass-facade-") || id.startsWith("design-mass-floor-group-");
      });
      if (targets.length) await viewer.zoomTo(targets);
      else {
        const primitives = viewer.scene?.primitives;
        const hasGltf = primitives && Array.from({ length: primitives.length }).some((_, i) => primitives.get(i)?.__arrEntityPrefix === "design-mass-");
        if (!hasGltf) return false;
      }
      viewer.scene?.requestRender?.();
      return true;
    });
    await page.waitForTimeout(1200);
    await page.screenshot({ path: closeupPath, fullPage: false, timeout: 20000 });
    closeupScreenshot = closeupPath;
  } catch (err) {
    closeupScreenshot = { error: err.message };
  }

  const out = { optimizeWaitError, aestheticWaitError, state, screenshot, closeupScreenshot, logs, errors, responses };
  const outPath = path.join(outDir, `windows-chrome-aesthetic-check-${providerSlug}.json`);
  fs.writeFileSync(outPath, JSON.stringify(out, null, 2), "utf8");
  console.log(JSON.stringify({
    optimizeWaitError,
    aestheticWaitError,
    state,
    screenshot,
    closeupScreenshot,
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
