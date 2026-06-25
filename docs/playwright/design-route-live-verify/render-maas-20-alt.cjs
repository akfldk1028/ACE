const fs = require("fs");
const path = require("path");
const { chromium } = require("../../../ARR/frontend/node_modules/playwright");

const OUT_DIR = path.resolve(__dirname);
const BACKEND = process.env.ARR_BACKEND_URL || "http://127.0.0.1:18000";
const PNU = process.env.PNU || "1168011800104170004";
const BUILDING_TYPE = process.env.BUILDING_TYPE || "공동주택";
const MAX_VARIANTS = Number(process.env.MAX_VARIANTS || 20);

function coordsOf(feature) {
  const geometry = feature.geometry || {};
  if (geometry.type === "Polygon") return geometry.coordinates?.[0] || [];
  if (geometry.type === "MultiPolygon") return geometry.coordinates?.[0]?.[0] || [];
  return [];
}

function geomCoords(geometry) {
  if (!geometry) return [];
  if (geometry.type === "Polygon") return geometry.coordinates?.[0] || [];
  if (geometry.type === "MultiPolygon") return geometry.coordinates?.[0]?.[0] || [];
  return [];
}

function bounds(coords) {
  const xs = coords.map(point => point[0]);
  const ys = coords.map(point => point[1]);
  return {
    minX: Math.min(...xs),
    maxX: Math.max(...xs),
    minY: Math.min(...ys),
    maxY: Math.max(...ys),
  };
}

function allFeatureCoords(feature) {
  const props = feature.properties || {};
  return [
    ...coordsOf(feature),
    ...(props.mass_volumes || []).flatMap(volume => geomCoords(volume.geometry)),
  ];
}

function projectFactory(globalBounds, width, height) {
  const sx = width / Math.max(1e-9, globalBounds.maxX - globalBounds.minX);
  const sy = height / Math.max(1e-9, globalBounds.maxY - globalBounds.minY);
  const scale = Math.min(sx, sy) * 0.64;
  const cx = (globalBounds.minX + globalBounds.maxX) / 2;
  const cy = (globalBounds.minY + globalBounds.maxY) / 2;
  return ([x, y], z = 0) => {
    const px = (x - cx) * scale;
    const py = (y - cy) * scale;
    return [
      width * 0.50 + (px - py) * 0.85,
      height * 0.68 + (px + py) * 0.32 - z * 3.7,
    ];
  };
}

function polyPath(coords, project, z = 0) {
  return coords.map((point, index) => {
    const [x, y] = project(point, z);
    return `${index ? "L" : "M"} ${x.toFixed(1)} ${y.toFixed(1)}`;
  }).join(" ") + " Z";
}

function sidePaths(coords, project, bottom, top) {
  const paths = [];
  for (let index = 0; index < coords.length - 1; index += 1) {
    const a = coords[index];
    const b = coords[index + 1];
    const [ax0, ay0] = project(a, bottom);
    const [bx0, by0] = project(b, bottom);
    const [bx1, by1] = project(b, top);
    const [ax1, ay1] = project(a, top);
    paths.push(`M ${ax0.toFixed(1)} ${ay0.toFixed(1)} L ${bx0.toFixed(1)} ${by0.toFixed(1)} L ${bx1.toFixed(1)} ${by1.toFixed(1)} L ${ax1.toFixed(1)} ${ay1.toFixed(1)} Z`);
  }
  return paths;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>]/g, char => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
  }[char]));
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const text = await response.text();
  if (!response.ok) {
    throw new Error(`${url} failed ${response.status}: ${text.slice(0, 500)}`);
  }
  return JSON.parse(text);
}

async function buildPayload() {
  const boundary = await postJson(`${BACKEND}/design/site-boundary/`, { pnu: PNU });
  const constraints = await postJson(`${BACKEND}/design/auto-constraints/`, {
    pnu: PNU,
    building_type: BUILDING_TYPE,
  });
  const coords = boundary.geometry.coordinates[0];
  const cx = coords.slice(0, -1).reduce((sum, point) => sum + point[0], 0) / (coords.length - 1);
  const cy = coords.slice(0, -1).reduce((sum, point) => sum + point[1], 0) / (coords.length - 1);
  const massCoords = coords.map(([x, y]) => [cx + (x - cx) * 0.72, cy + (y - cy) * 0.72]);
  const massGeojson = {
    type: "Feature",
    geometry: { type: "Polygon", coordinates: [massCoords] },
    properties: { height: 18, num_floors: 6, floor_height: 3.0, mass_shape: "seed" },
  };
  const started = Date.now();
  const variants = await postJson(`${BACKEND}/design/maas/legal-variants/`, {
    pnu: PNU,
    site_polygon: boundary.geometry,
    mass_geojson: massGeojson,
    constraints: constraints.constraints,
    building_type: BUILDING_TYPE,
    max_variants: MAX_VARIANTS,
  });
  return {
    pnu: PNU,
    building_type: BUILDING_TYPE,
    max_variants: MAX_VARIANTS,
    elapsed_ms: Date.now() - started,
    boundary,
    constraints,
    response: variants,
  };
}

function renderCard(feature, siteCoords, globalBounds) {
  const props = feature.properties || {};
  const volumes = (props.mass_volumes || []).length
    ? props.mass_volumes
    : [{ bottom_height: 0, top_height: props.height || 10, geometry: feature.geometry }];
  const project = projectFactory(globalBounds, 310, 190);
  const site = `<path d="${polyPath(siteCoords, project, 0)}" fill="#effaf2" stroke="#58d99b" stroke-width="1.2" stroke-dasharray="4 4"/>`;
  const layers = [];
  [...volumes].sort((a, b) => (a.bottom_height || 0) - (b.bottom_height || 0)).forEach((volume, index) => {
    const coords = geomCoords(volume.geometry);
    const bottom = Number(volume.bottom_height || 0);
    const top = Number(volume.top_height || props.height || 0);
    sidePaths(coords, project, bottom, top).forEach((side, sideIndex) => {
      layers.push(`<path d="${side}" fill="rgba(255,123,24,${sideIndex % 2 ? 0.38 : 0.48})" stroke="rgba(255,115,18,.72)" stroke-width=".8"/>`);
    });
    layers.push(`<path d="${polyPath(coords, project, top)}" fill="rgba(255,207,74,.65)" stroke="#ff7418" stroke-width="1.7"/>`);
  });
  const precheck = props.parking_precheck || {};
  const layout = precheck.layout_candidate || {};
  const required = precheck.required_count || {};
  const parkingStatus = layout.status || "no parking";
  const statusClass = parkingStatus === "pass" ? "good" : parkingStatus === "fail" ? "bad" : "warn";
  const providedSpaces = layout.provided_spaces ?? "-";
  const requiredSpaces = layout.required_spaces ?? required.required_spaces ?? "-";
  return `<section class="card">
    <svg viewBox="0 0 310 190">${site}${layers.join("")}<text x="10" y="20" font-size="13" font-weight="800" fill="#0d1a2d">${escapeHtml(props.variant_id)}</text></svg>
    <div class="meta">
      <div class="shape">${escapeHtml(props.mass_shape)}</div>
      <div class="numbers">FAR ${Number(props.far || 0).toFixed(1)} · BCR ${Number(props.bcr || 0).toFixed(1)} · H ${Number(props.height || 0).toFixed(1)}m</div>
      <div class="${statusClass}">P ${escapeHtml(providedSpaces)}/${escapeHtml(requiredSpaces)} · ${escapeHtml(parkingStatus)}</div>
    </div>
  </section>`;
}

async function render(payload) {
  const features = payload.response.feature_collection.features.slice(0, MAX_VARIANTS);
  const siteCoords = payload.boundary.geometry.coordinates[0];
  const globalBounds = bounds([...siteCoords, ...features.flatMap(allFeatureCoords)]);
  const cards = features.map(feature => renderCard(feature, siteCoords, globalBounds)).join("");
  const html = `<!doctype html><html><head><meta charset="utf-8"><style>
    *{box-sizing:border-box} body{margin:0;width:2200px;height:1400px;overflow:hidden;background:#07111f;color:#edf4ff;font-family:Arial,'Noto Sans KR',sans-serif}
    header{height:92px;padding:24px 32px;border-bottom:1px solid #233852;background:#0d192b}
    h1{margin:0 0 8px;font-size:28px;letter-spacing:0}.sub{font-size:15px;color:#9fb2cc}
    main{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;padding:20px 32px}
    .card{height:282px;border:1px solid #263d5e;border-radius:8px;background:#101d32;overflow:hidden;display:grid;grid-template-rows:190px 1fr}
    svg{background:#f7f9fb}.meta{padding:10px 12px;min-width:0}.shape{font-weight:800;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.numbers{font-size:13px;color:#c2d0e3;margin-top:5px;white-space:nowrap}.good,.warn,.bad{font-size:13px;font-weight:800;margin-top:6px;white-space:nowrap}.good{color:#22d18b}.warn{color:#ffc12c}.bad{color:#ff5573}
    footer{position:absolute;left:32px;right:32px;bottom:14px;border-top:1px solid #233852;padding-top:10px;color:#9fb2cc;font-size:14px}
  </style></head><body>
  <header><h1>MAAS 20 Alternatives · PNU ${escapeHtml(payload.pnu)}</h1><div class="sub">${features.length}/${MAX_VARIANTS} candidates · ${escapeHtml(payload.building_type)} · generated in ${payload.elapsed_ms}ms · green=parking pass, yellow=review, red=parking fail</div></header>
  <main>${cards}</main>
  <footer>Use this as the default mass review evidence. If many cards still share the same footprint, the algorithm is not producing true plan diversity.</footer>
  </body></html>`;
  const htmlPath = path.join(OUT_DIR, "maas-20-alt-latest.html");
  const pngPath = path.join(OUT_DIR, "maas-20-alt-latest.png");
  const jsonPath = path.join(OUT_DIR, "maas-20-alt-latest.json");
  fs.writeFileSync(htmlPath, html, "utf8");
  fs.writeFileSync(jsonPath, JSON.stringify(payload, null, 2), "utf8");

  const browser = await chromium.launch({ headless: true, args: ["--no-sandbox", "--disable-gpu"] });
  const page = await browser.newPage({ viewport: { width: 2200, height: 1400 }, deviceScaleFactor: 1 });
  await page.goto("file://" + htmlPath, { waitUntil: "domcontentloaded" });
  const client = await page.context().newCDPSession(page);
  const shot = await client.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false,
  });
  fs.writeFileSync(pngPath, Buffer.from(shot.data, "base64"));
  await browser.close();
  return { htmlPath, pngPath, jsonPath, count: features.length };
}

(async () => {
  const payload = await buildPayload();
  const rendered = await render(payload);
  console.log(JSON.stringify(rendered, null, 2));
})().catch(error => {
  console.error(error);
  process.exit(1);
});
