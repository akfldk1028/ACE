const fs = require("fs");
const path = require("path");
const { chromium } = require("../../../../ARR/frontend/node_modules/playwright");

const OUT_DIR = path.resolve(__dirname);
const FRONTEND_URL = process.env.FRONTEND_URL || "http://127.0.0.1:5174/design";
const PNU = process.env.PNU || "1168011800104170004";

async function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const browser = await chromium.launch({
    headless: true,
    args: ["--ignore-gpu-blocklist", "--enable-webgl", "--use-gl=swiftshader"],
  });
  const page = await browser.newPage({ viewport: { width: 1800, height: 1000 } });
  page.setDefaultTimeout(45000);

  const logs = [];
  const pageErrors = [];
  const responses = [];
  page.on("console", (msg) => logs.push({ type: msg.type(), text: msg.text() }));
  page.on("pageerror", (err) => pageErrors.push({ name: err.name, message: err.message, stack: err.stack }));
  page.on("response", (res) => {
    const url = res.url();
    if (url.includes("/design") || url.includes(":8200") || res.status() >= 400) {
      responses.push({ status: res.status(), url });
    }
  });

  await page.goto(`${FRONTEND_URL}?verifyTs=${Date.now()}`, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForSelector('input[placeholder="PNU 코드 (19자리) 또는 주소"]', { timeout: 30000 });
  await page.fill('input[placeholder="PNU 코드 (19자리) 또는 주소"]', PNU);
  await page.getByRole("button", { name: "조회" }).click({ force: true });
  await page.waitForTimeout(12000);

  const optimizeButton = page.getByRole("button", { name: /OPTIMIZE/i });
  await optimizeButton.click({ force: true });

  let optimizeWaitError = null;
  try {
    await page.waitForFunction(
      () => {
        const text = document.body.innerText || "";
        return text.includes("BUILDING MASS") && text.includes("COMPLETE");
      },
      null,
      { timeout: 90000 },
    );
  } catch (err) {
    optimizeWaitError = { name: err.name, message: err.message };
  }
  await page.waitForTimeout(5000);

  let agClickError = null;
  try {
    const agButton = page.getByRole("button", { name: /AG-light 검토 시작/ });
    await agButton.click({ force: true, timeout: 15000 });
    await page.waitForTimeout(6000);
  } catch (err) {
    agClickError = { name: err.name, message: err.message };
  }

  const state = await page.evaluate(() => {
    const text = document.body.innerText || "";
    const flow = document.querySelector('[data-testid="ag-light-react-flow"]');
    const transfer = document.querySelector('[data-testid="ag-light-transfer-status"]');
    const agBlock = flow?.closest("section, aside, div") || flow;
    const features = window.__arrDesignLastMassFeatures || [];
    const selectedFeature = features[0] || null;
    const selectedProps = selectedFeature?.properties || {};
    const designQuality = selectedProps.design_quality || selectedProps.maas_model?.design_quality || null;
    const entityIds = (() => {
      try {
        return window.ws3d?.viewer?.entities?.values?.map((e) => String(e.id || "")).filter(Boolean) || [];
      } catch {
        return [];
      }
    })();
    return {
      hasBody: text.trim().length > 0,
      hasComplete: text.includes("COMPLETE"),
      hasBuildingMass: text.includes("BUILDING MASS"),
      hasAgLightBlock: text.includes("AI 설계 협업") && text.includes("AG-light React Flow"),
      hasAgButton: text.includes("현재 안 AG-light 검토 시작"),
      hasReactFlow: Boolean(flow),
      reactFlowNodes: flow ? flow.querySelectorAll(".react-flow__node").length : 0,
      reactFlowEdges: flow ? flow.querySelectorAll(".react-flow__edge").length : 0,
      overlayEdges: flow ? flow.querySelectorAll('[data-testid="ag-light-edge-path"]').length : 0,
      transferStatusText: transfer ? transfer.textContent || "" : "",
      agBlockText: agBlock ? (agBlock.textContent || "").slice(0, 1600) : "",
      hasWebglFallback: text.includes("WebGL fallback"),
      designFeatureCount: features.length,
      selectedMassShape: selectedProps.mass_shape || null,
      selectedDesignQualityScore: selectedProps.design_quality_score || designQuality?.score || null,
      selectedDesignQualitySource: designQuality?.source || null,
      selectedOptimizerBackend: designQuality?.optimizer_backend || null,
      designMassEntities: entityIds.filter((id) => id.startsWith("design-mass-")).length,
      parkingStallEntities: entityIds.filter((id) => id.includes("parking-stall")).length,
      pilotiEntities: entityIds.filter((id) => id.includes("piloti")).length,
      massDebug: window.__arrLastMassRender || null,
      bodyExcerpt: text.slice(0, 4000),
    };
  });

  const screenshotPath = path.join(OUT_DIR, `ag-light-current-${Date.now()}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: false, timeout: 30000 });

  const result = {
    url: FRONTEND_URL,
    pnu: PNU,
    optimizeWaitError,
    agClickError,
    state,
    screenshotPath,
    pageErrors,
    consoleProblems: logs.filter((log) => ["error", "warning"].includes(log.type)).slice(0, 80),
    responseErrors: responses.filter((res) => res.status >= 400).slice(0, 80),
    agLightResponses: responses.filter((res) => res.url.includes(":8200")).slice(-40),
  };

  const jsonPath = path.join(OUT_DIR, "ag-light-current-result.json");
  fs.writeFileSync(jsonPath, JSON.stringify(result, null, 2), "utf8");
  console.log(JSON.stringify({ ...result, logs: undefined }, null, 2));

  await browser.close();

  if (
    optimizeWaitError ||
    agClickError ||
    pageErrors.length ||
    result.responseErrors.length ||
    !state.hasAgLightBlock ||
    !state.hasReactFlow ||
    state.reactFlowNodes < 6 ||
    state.overlayEdges < 5 ||
    !state.transferStatusText.includes(PNU) ||
    !state.transferStatusText.includes("법규") ||
    !state.transferStatusText.includes("주차") ||
    state.designFeatureCount < 1 ||
    !state.selectedDesignQualitySource
  ) {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
