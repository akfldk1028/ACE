const fs = require("fs");
const path = require("path");
const { chromium } = require("D:/Data/25_ACE/ARR/frontend/node_modules/playwright");

const DEFAULT_CASES = [
  { pnu: "1168011800104170004", name: "gangnam-small-piloti", buildingType: "공동주택", algorithm: "maas_legal_envelope", maxGenerations: 5, populationSize: 10, requireParkingStalls: true },
  { pnu: "1168011800104670003", name: "gangnam-dogok-ground", buildingType: "공동주택", algorithm: "maas_legal_envelope", maxGenerations: 5, populationSize: 10, requireParkingStalls: true },
  { pnu: "1168010600110280000", name: "gangnam-daechi-large", buildingType: "공동주택", algorithm: "maas_legal_envelope", maxGenerations: 5, populationSize: 10, requireParkingStalls: true },
  { pnu: "1168011800100910005", name: "gangnam-large-basement", buildingType: "공동주택", algorithm: "maas_legal_envelope", maxGenerations: 5, populationSize: 10, requireParkingStalls: true },
];

function loadCases() {
  const casesFile = process.argv.find(arg => arg.startsWith("--cases="))?.slice("--cases=".length);
  if (!casesFile) return DEFAULT_CASES;
  const raw = JSON.parse(fs.readFileSync(casesFile, "utf8"));
  return raw.map((item, index) => ({
    pnu: item.pnu || item.input,
    name: String(item.name || `case-${index + 1}`).toLowerCase().replace(/[^a-z0-9가-힣]+/gi, "-").replace(/^-|-$/g, ""),
    buildingType: item.buildingType,
    algorithm: item.algorithm,
    maxGenerations: item.maxGenerations,
    populationSize: item.populationSize,
    requireParkingStalls: item.requireParkingStalls === true,
  })).filter(item => /^\d{19}$/.test(item.pnu));
}

function baseUrl() {
  return process.argv.find(arg => arg.startsWith("--base-url="))?.slice("--base-url=".length)
    || "http://127.0.0.1:5174";
}

async function runCase(context, outDir, testCase, index) {
  const page = await context.newPage();
  page.setDefaultTimeout(50000);
  const cdp = await context.newCDPSession(page);
  await cdp.send("Network.enable").catch(() => undefined);
  await cdp.send("Network.setCacheDisabled", { cacheDisabled: true }).catch(() => undefined);
  try {
    const { windowId } = await cdp.send("Browser.getWindowForTarget");
    await cdp.send("Browser.setWindowBounds", {
      windowId,
      bounds: { left: 0, top: 0, width: 1800, height: 1100, windowState: "normal" },
    });
    await page.setViewportSize({ width: 1800, height: 1000 });
  } catch {}

  const logs = [];
  const errors = [];
  const responses = [];
  page.on("console", msg => logs.push({ type: msg.type(), text: msg.text() }));
  page.on("pageerror", err => errors.push({ name: err.name, message: err.message, stack: err.stack }));
  page.on("response", res => {
    const url = res.url();
    if (url.includes("vworld") || url.includes("/design") || res.status() >= 400) {
      responses.push({ status: res.status(), url });
    }
  });

  await page.goto(`${baseUrl()}/design?batchPnu=${testCase.pnu}&verifyTs=${Date.now()}`, {
    waitUntil: "domcontentloaded",
    timeout: 50000,
  });
  await page.fill('input[placeholder="PNU 코드 (19자리) 또는 주소"]', testCase.pnu);
  await page.getByRole("button", { name: "조회" }).click({ force: true });
  await page.waitForTimeout(12000);
  if (testCase.buildingType) {
    const selected = await page.locator("select").filter({ has: page.locator(`option[value="${testCase.buildingType}"]`) }).first().selectOption(testCase.buildingType).then(() => true).catch(() => false);
    if (!selected) {
      await page.getByText(testCase.buildingType, { exact: false }).first().click({ force: true });
    }
    await page.waitForTimeout(800);
  }
  if (testCase.algorithm) {
    await page.locator("select").filter({ has: page.locator(`option[value="${testCase.algorithm}"]`) }).first().selectOption(testCase.algorithm);
    await page.waitForTimeout(300);
  }
  const numericInputs = page.locator('input[type="number"]');
  if (testCase.maxGenerations) {
    await numericInputs.nth(0).fill(String(testCase.maxGenerations));
  }
  if (testCase.populationSize) {
    await numericInputs.nth(1).fill(String(testCase.populationSize));
  }
  await page.getByRole("button", { name: /OPTIMIZE/i }).click({ force: true });

  let waitError = null;
  try {
    await page.waitForFunction(
      () => {
        const text = document.body.innerText || "";
        const entities = window.ws3d?.viewer?.entities?.values || [];
        const debug = window.__arrLastMassRender || {};
        const ids = entities.map(e => String(e.id || ""));
        return text.includes("OPTIMIZATION")
          && text.includes("COMPLETE")
          && text.includes("DESIGN LIST")
          && text.includes("BUILDING MASS")
          && debug.selectedId >= 900000
          && ids.some(id => id.startsWith("design-mass-"))
          && ids.some(id => id.includes("parking"));
      },
      null,
      { timeout: 220000 },
    );
  } catch (err) {
    waitError = { name: err.name, message: err.message };
  }
  await page.waitForTimeout(5500);

  const zoomState = await page.evaluate(async () => {
    const viewer = window.ws3d?.viewer;
    if (!viewer?.entities?.values?.length) return { zoomed: false, reason: "missing-viewer" };
    const Cesium = window.Cesium;
    if (!Cesium?.Cartesian3) return { zoomed: false, reason: "missing-cesium-global" };
    const parkingEntities = viewer.entities.values.filter(entity => {
      const id = String(entity?.id || "");
      return id.includes("parking-space-outline") || id.includes("parking-line-shadow");
    });
    const feature = (() => {
      const selectedId = window.__arrLastMassRender?.selectedId;
      return window.__arrDesignLastMassFeatures?.find?.(item => item?.properties?.design_id === selectedId)
        || window.__arrDesignLastMassFeatures?.[0];
    })();
    const stalls = feature?.properties?.parking_precheck?.layout_candidate?.stalls || [];
    const points = stalls
      .flatMap(stall => Array.isArray(stall?.polygon_wgs84) ? stall.polygon_wgs84 : [])
      .filter(point => Array.isArray(point) && point.length >= 2 && isFinite(point[0]) && isFinite(point[1]));
    if (!points.length) return { zoomed: false, reason: "missing-parking-coordinates", parkingLineCount: parkingEntities.length };
    try {
      let lng = 0;
      let lat = 0;
      let minLng = Number.POSITIVE_INFINITY;
      let maxLng = Number.NEGATIVE_INFINITY;
      let minLat = Number.POSITIVE_INFINITY;
      let maxLat = Number.NEGATIVE_INFINITY;
      for (const point of points) {
        lng += point[0];
        lat += point[1];
        minLng = Math.min(minLng, point[0]);
        maxLng = Math.max(maxLng, point[0]);
        minLat = Math.min(minLat, point[1]);
        maxLat = Math.max(maxLat, point[1]);
      }
      lng /= points.length;
      lat /= points.length;
      const beforeHeight = viewer.camera?.positionCartographic?.height;
      viewer.trackedEntity = undefined;
      viewer.camera.setView({
        destination: Cesium.Cartesian3.fromDegrees(lng, lat, 38),
        orientation: {
          heading: 0,
          pitch: Cesium.Math.toRadians(-72),
          roll: 0,
        },
      });
      viewer.scene?.requestRender?.();
      await new Promise(resolve => setTimeout(resolve, 1400));
      return {
        zoomed: true,
        parkingLineCount: parkingEntities.length,
        parkingCoordinateCount: points.length,
        center: { lng, lat },
        bounds: { minLng, maxLng, minLat, maxLat },
        beforeHeight,
        afterHeight: viewer.camera?.positionCartographic?.height,
        ids: parkingEntities.map(entity => String(entity.id || "")),
      };
    } catch (error) {
      return {
        zoomed: false,
        reason: error instanceof Error ? error.message : "zoom-failed",
        parkingLineCount: parkingEntities.length,
      };
    }
  });

  const state = await page.evaluate(async (casePnu) => {
    const ringArea = ring => {
      if (!Array.isArray(ring) || ring.length < 3) return 0;
      let sum = 0;
      for (let i = 0; i < ring.length; i++) {
        const a = ring[i];
        const b = ring[(i + 1) % ring.length];
        sum += Number(a?.[0] || 0) * Number(b?.[1] || 0) - Number(b?.[0] || 0) * Number(a?.[1] || 0);
      }
      return Math.abs(sum) / 2;
    };
    const largestPolygon = polygons => {
      if (!Array.isArray(polygons) || !polygons.length) return null;
      return polygons.reduce((best, polygon) => {
        if (!Array.isArray(polygon) || !polygon[0]) return best;
        if (!best) return polygon;
        return ringArea(polygon[0]) > ringArea(best[0]) ? polygon : best;
      }, null);
    };
    const outerRing = geometry => {
      if (!geometry) return null;
      if (geometry.type === "Feature") return outerRing(geometry.geometry);
      if (geometry.type === "Polygon") return geometry.coordinates?.[0] || null;
      if (geometry.type === "MultiPolygon") return largestPolygon(geometry.coordinates)?.[0] || null;
      return null;
    };
    const onSegment = (a, b, c) => {
      const cross = (b[1] - a[1]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[1] - a[1]);
      if (Math.abs(cross) > 1e-11) return false;
      return b[0] <= Math.max(a[0], c[0]) + 1e-11
        && b[0] + 1e-11 >= Math.min(a[0], c[0])
        && b[1] <= Math.max(a[1], c[1]) + 1e-11
        && b[1] + 1e-11 >= Math.min(a[1], c[1]);
    };
    const pointInOrOnRing = (point, ring) => {
      if (!Array.isArray(point) || !Array.isArray(ring) || ring.length < 3) return false;
      for (let i = 0; i < ring.length - 1; i++) {
        if (onSegment(ring[i], point, ring[i + 1])) return true;
      }
      let inside = false;
      const x = point[0], y = point[1];
      for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
        const xi = ring[i][0], yi = ring[i][1];
        const xj = ring[j][0], yj = ring[j][1];
        const intersects = ((yi > y) !== (yj > y))
          && (x < ((xj - xi) * (y - yi)) / ((yj - yi) || 1e-12) + xi);
        if (intersects) inside = !inside;
      }
      return inside;
    };
    const containment = (siteRing, featureRing) => {
      if (!siteRing || !featureRing) return null;
      const points = featureRing.slice(0, -1);
      const outside = points.filter(point => !pointInOrOnRing(point, siteRing));
      return {
        checked_points: points.length,
        outside_points: outside.length,
        inside: outside.length === 0,
      };
    };
    const text = document.body.innerText || "";
    const entityIds = (() => {
      try {
        return window.ws3d?.viewer?.entities?.values?.map(e => e.id).filter(Boolean) || [];
      } catch {
        return [];
      }
    })();
    const designMassEntities = entityIds.filter(id => String(id).startsWith("design-mass-"));
    const selectedParkingPrecheck = (() => {
      try {
        const debug = window.__arrLastMassRender || {};
        const id = debug.selectedId;
        const feature = window.__arrDesignLastMassFeatures?.find?.(f => f?.properties?.design_id === id)
          || window.__arrDesignLastMassFeatures?.[0];
        return feature?.properties?.parking_precheck || null;
      } catch {
        return null;
      }
    })();
    const selectedMassFeature = (() => {
      try {
        const debug = window.__arrLastMassRender || {};
        const id = debug.selectedId;
        return window.__arrDesignLastMassFeatures?.find?.(f => f?.properties?.design_id === id)
          || window.__arrDesignLastMassFeatures?.[0]
          || null;
      } catch {
        return null;
      }
    })();
    const siteBoundary = await fetch("/design/site-boundary/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pnu: casePnu }),
    }).then(res => res.ok ? res.json() : null).catch(() => null);
    const siteRing = outerRing(siteBoundary?.geometry);
    const massRing = outerRing(selectedMassFeature?.geometry);
    const stallPoints = (() => {
      const stalls = selectedMassFeature?.properties?.parking_precheck?.layout_candidate?.stalls || [];
      return stalls.flatMap(stall => Array.isArray(stall?.polygon_wgs84) ? stall.polygon_wgs84.slice(0, -1) : []);
    })();
    const outsideParkingPoints = siteRing
      ? stallPoints.filter(point => !pointInOrOnRing(point, siteRing)).length
      : null;
    const sunlightContainment = (() => {
      const envelope = window.__arrDesignSetbackGeometries?.sunlight_envelope || null;
      if (!envelope) return { applies: false, status: "not_applicable_or_missing", reason: "missing_sunlight_envelope" };
      const baseHeightM = Number(envelope.base_height_m ?? 10);
      const baseRing = Array.isArray(envelope.slanted_polygons?.[0]?.corners)
        ? envelope.slanted_polygons[0].corners.map(point => [point[0], point[1]])
        : null;
      if (!baseRing || baseRing.length < 4) return { applies: true, status: "fail", inside: false, reason: "missing_base_ring" };
      const closedBaseRing = (() => {
        const first = baseRing[0];
        const last = baseRing[baseRing.length - 1];
        if (first && last && Math.abs(first[0] - last[0]) < 1e-12 && Math.abs(first[1] - last[1]) < 1e-12) {
          return baseRing;
        }
        return [...baseRing, first];
      })();
      const volumes = Array.isArray(selectedMassFeature?.properties?.mass_volumes)
        ? selectedMassFeature.properties.mass_volumes
        : [];
      const checks = (volumes.length ? volumes : [{ top_height: selectedMassFeature?.properties?.height, geometry: selectedMassFeature?.geometry }])
        .map((volume, index) => {
          const ring = outerRing(volume?.geometry);
          const points = Array.isArray(ring) ? ring.slice(0, -1) : [];
          const topHeightM = Number(volume?.top_height ?? selectedMassFeature?.properties?.height ?? 0);
          const outside = points.filter(point => !pointInOrOnRing(point, closedBaseRing));
          return {
            index,
            top_height_m: Number.isFinite(topHeightM) ? topHeightM : null,
            method: Number.isFinite(topHeightM) && topHeightM <= baseHeightM + 1e-6
              ? "base_1_5m_ring"
              : "needs_height_layer_check",
            checked_points: points.length,
            outside_points: outside.length,
            inside: outside.length === 0,
          };
        });
      const needsLayerCheck = checks.some(check => check.method === "needs_height_layer_check");
      return {
        applies: true,
        status: needsLayerCheck ? "needs_height_layer_check" : (checks.every(check => check.inside) ? "pass" : "fail"),
        baseHeightM,
        datumElevationM: envelope.datum_elevation_m ?? null,
        datumCase: envelope.datum_case ?? null,
        baseSetbackM: envelope.base_setback_m ?? null,
        slope: envelope.slope ?? null,
        envelopeLayerCount: Array.isArray(envelope.envelope_layers) ? envelope.envelope_layers.length : 0,
        maxMassTopM: Math.max(...checks.map(check => check.top_height_m || 0)),
        method: needsLayerCheck ? "base_ring_plus_pending_height_layer_check" : "base_1_5m_ring",
        checked_points: checks.reduce((sum, check) => sum + check.checked_points, 0),
        outside_points: checks.reduce((sum, check) => sum + check.outside_points, 0),
        inside: !needsLayerCheck && checks.every(check => check.inside),
        checks,
      };
    })();
    const parkingPrecheckSummaries = (() => {
      try {
        return (window.__arrDesignLastMassFeatures || []).map(feature => {
          const props = feature?.properties || {};
          const precheck = props.parking_precheck || {};
          const layout = precheck.layout_candidate || {};
          return {
            designId: props.design_id,
            variantId: props.variant_id,
            score: props.maas_score,
            shape: props.mass_shape,
            strategy: precheck.selected_strategy,
            status: layout.status,
            required: layout.required_spaces,
            provided: layout.provided_spaces,
            reason: layout.reason,
            adjacency: layout.adjacency,
          };
        });
      } catch {
        return [];
      }
    })();
    const requiredSpaces = selectedParkingPrecheck?.layout_candidate?.required_spaces
      ?? selectedParkingPrecheck?.required_count?.required_spaces
      ?? null;
    const providedSpaces = selectedParkingPrecheck?.layout_candidate?.provided_spaces ?? null;
    return {
      hasDisabledText: text.includes("WebGL을 사용할 수 없어"),
      hasFallback: text.includes("2D MASS PREVIEW") || text.includes("WebGL fallback"),
      hasComplete: text.includes("COMPLETE"),
      hasDesignList: text.includes("DESIGN LIST"),
      hasMassText: text.includes("BUILDING MASS"),
      hasAuthorityReviewText: text.includes("관청검토"),
      hasEvidenceNeededText: text.includes("증빙필요"),
      hasVworldCanvas: [...document.querySelectorAll("canvas")].some(c => c.getBoundingClientRect().width > 800 && c.getBoundingClientRect().height > 700),
      bodyHead: text.slice(0, 5000),
      entityCount: entityIds.length,
      designMassEntities,
      parkingEntities: designMassEntities.filter(id => String(id).includes("parking")),
      parkingStallEntities: designMassEntities.filter(id => String(id).includes("parking-stall") || String(id).includes("parking-space-outline")),
      pilotiEntities: designMassEntities.filter(id => String(id).includes("piloti")),
      parkingRequiredSpaces: requiredSpaces,
      parkingProvidedSpaces: providedSpaces,
      selectedParkingPrecheck,
      selectedMassFeature,
      siteContainment: {
        requestedPnu: casePnu,
        boundaryPnu: siteBoundary?.pnu || null,
        siteAreaM2: siteBoundary?.area_m2 || null,
        hasSiteRing: Boolean(siteRing),
        mass: containment(siteRing, massRing),
        parking: siteRing ? {
          checked_points: stallPoints.length,
          outside_points: outsideParkingPoints,
          inside: outsideParkingPoints === 0,
        } : null,
      },
      sunlightContainment,
      parkingPrecheckSummaries,
      massDebug: window.__arrLastMassRender || null,
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
    };
  }, testCase.pnu);

  const base = `${String(index + 1).padStart(2, "0")}_${testCase.name}_${testCase.pnu}`;
  const pngPath = path.join(outDir, `zoom_${base}.png`);
  const jsonPath = path.join(outDir, `${base}.json`);
  await page.screenshot({ path: pngPath, fullPage: false, timeout: 30000 });
  const result = {
    ...testCase,
    waitError,
    pngPath,
    jsonPath,
    zoomState,
    state,
    errorCount: errors.length,
    consoleProblems: logs.filter(l => ["error", "warning"].includes(l.type)).slice(0, 30),
    responseErrors: responses.filter(r => r.status >= 400).slice(0, 20),
  };
  fs.writeFileSync(jsonPath, JSON.stringify(result, null, 2), "utf8");
  await page.close();
  return result;
}

(async () => {
  const outDir = "D:/Data/25_ACE/docs/playwright/design-route-live-verify/pnu-batch";
  fs.mkdirSync(outDir, { recursive: true });
  const cases = loadCases();
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222", { timeout: 90000 });
  const context = await browser.newContext({
    viewport: { width: 1800, height: 1000 },
    ignoreHTTPSErrors: true,
  });
  const results = [];
  for (let i = 0; i < cases.length; i++) {
    const result = await runCase(context, outDir, cases[i], i);
    results.push(result);
    console.log(JSON.stringify({
      pnu: result.pnu,
      name: result.name,
      pass: !result.waitError
        && result.state.hasComplete
        && result.state.hasVworldCanvas
        && result.state.designMassEntities.length > 0
        && result.state.parkingEntities.length > 0
        && result.state.siteContainment?.mass?.inside !== false
        && result.state.siteContainment?.parking?.inside !== false
        && (result.state.sunlightContainment?.applies !== true || result.state.sunlightContainment?.inside === true)
        && (!result.requireParkingStalls || (
          result.state.parkingStallEntities.length >= Math.max(1, Number(result.state.parkingRequiredSpaces || 0))
          && Number(result.state.parkingProvidedSpaces || 0) >= Number(result.state.parkingRequiredSpaces || 0)
        ))
        && result.errorCount === 0,
      massDebug: result.state.massDebug,
      designMassEntities: result.state.designMassEntities.length,
      parkingEntities: result.state.parkingEntities.length,
      parkingStallEntities: result.state.parkingStallEntities.length,
      pilotiEntities: result.state.pilotiEntities.length,
      pngPath: result.pngPath,
    }, null, 2));
  }
  const summary = results.map(result => ({
    pnu: result.pnu,
    name: result.name,
    pass: !result.waitError
      && result.state.hasComplete
      && result.state.hasVworldCanvas
      && result.state.designMassEntities.length > 0
      && result.state.parkingEntities.length > 0
      && result.state.siteContainment?.mass?.inside !== false
      && result.state.siteContainment?.parking?.inside !== false
      && (result.state.sunlightContainment?.applies !== true || result.state.sunlightContainment?.inside === true)
      && (!result.requireParkingStalls || (
        result.state.parkingStallEntities.length >= Math.max(1, Number(result.state.parkingRequiredSpaces || 0))
        && Number(result.state.parkingProvidedSpaces || 0) >= Number(result.state.parkingRequiredSpaces || 0)
      ))
      && result.errorCount === 0,
    strategy: result.state.selectedParkingPrecheck?.layout_candidate?.strategy
      || result.state.selectedParkingPrecheck?.selected_strategy
      || result.state.selectedParkingPrecheck?.strategy
      || result.state.massDebug?.pilotiFeatures?.[0]?.strategy
      || (result.state.parkingEntities.length ? "non_piloti_parking_overlay" : "missing"),
    voidHeight: result.state.massDebug?.pilotiFeatures?.[0]?.voidHeight || 0,
    designMassEntities: result.state.designMassEntities.length,
    parkingEntities: result.state.parkingEntities.length,
    parkingStallEntities: result.state.parkingStallEntities.length,
    pilotiEntities: result.state.pilotiEntities.length,
    sunlightContainment: result.state.sunlightContainment,
    hasFallback: result.state.hasFallback,
    hasDisabledText: result.state.hasDisabledText,
    waitError: result.waitError,
    responseErrors: result.responseErrors.length,
    pngPath: result.pngPath,
    jsonPath: result.jsonPath,
  }));
  const summaryPath = path.join(outDir, "summary.json");
  fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2), "utf8");
  console.log(JSON.stringify({ summaryPath, summary }, null, 2));
  await context.close().catch(() => undefined);
  await browser.close();
})().catch(err => {
  console.error(err);
  process.exit(1);
});
