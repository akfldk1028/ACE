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
  await page.getByRole("button", { name: /OPTIMIZE/i }).click({ force: true });

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
    await page.getByRole("button", { name: /AG-light 검토 시작/ }).click({ force: true, timeout: 15000 });
    await page.waitForTimeout(6000);
  } catch (err) {
    agClickError = { name: err.name, message: err.message };
  }

  let fullscreenError = null;
  try {
    const flow = page.locator('[data-testid="ag-light-react-flow"]');
    await flow.getByRole("button", { name: "전체화면" }).click({ force: true });
    await page.waitForTimeout(800);
  } catch (err) {
    fullscreenError = { name: err.name, message: err.message };
  }

  const state = await page.evaluate(() => {
    const text = document.body.innerText || "";
    const flow = document.querySelector('[data-testid="ag-light-react-flow"]');
    const box = flow?.getBoundingClientRect();
    return {
      hasComplete: text.includes("COMPLETE"),
      hasBuildingMass: text.includes("BUILDING MASS"),
      hasAgLightBlock: text.includes("AG-light 협업모드"),
      hasReactFlow: Boolean(flow),
      reactFlowNodes: flow ? flow.querySelectorAll(".react-flow__node").length : 0,
      reactFlowEdges: flow ? flow.querySelectorAll(".react-flow__edge").length : 0,
      hasSelectorHandoff: text.includes("Selector/Handoff"),
      hasDesignOrchestrator: text.includes("design_orchestrator"),
      hasDatumAgent: text.includes("ngii_local_dem 기준면"),
      flowBox: box ? { width: Math.round(box.width), height: Math.round(box.height) } : null,
    };
  });

  const screenshotPath = path.join(OUT_DIR, `ag-light-current-fullscreen-${Date.now()}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: false, timeout: 30000 });

  const result = {
    url: FRONTEND_URL,
    pnu: PNU,
    optimizeWaitError,
    agClickError,
    fullscreenError,
    state,
    screenshotPath,
    pageErrors,
    consoleProblems: logs.filter((log) => ["error", "warning"].includes(log.type)).slice(0, 80),
    responseErrors: responses.filter((res) => res.status >= 400).slice(0, 80),
    agLightResponses: responses.filter((res) => res.url.includes(":8200")).slice(-40),
  };

  const jsonPath = path.join(OUT_DIR, "ag-light-current-fullscreen-result.json");
  fs.writeFileSync(jsonPath, JSON.stringify(result, null, 2), "utf8");
  console.log(JSON.stringify(result, null, 2));

  await browser.close();

  if (
    optimizeWaitError ||
    agClickError ||
    fullscreenError ||
    pageErrors.length ||
    result.responseErrors.length ||
    !state.hasAgLightBlock ||
    !state.hasReactFlow ||
    !state.hasSelectorHandoff ||
    state.reactFlowNodes < 5 ||
    state.reactFlowEdges < 5
  ) {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
