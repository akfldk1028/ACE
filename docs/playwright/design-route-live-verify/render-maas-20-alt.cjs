const fs = require("fs");
const path = require("path");
const { execFileSync, spawnSync } = require("child_process");
const { chromium } = require("../../../ARR/frontend/node_modules/playwright");

const OUT_DIR = path.resolve(__dirname);
const BACKEND = process.env.ARR_BACKEND_URL || "http://127.0.0.1:18000";
const PNU = process.env.PNU || "1168011800104170004";
const BUILDING_TYPE = process.env.BUILDING_TYPE || "공동주택";
const MAX_VARIANTS = Number(process.env.MAX_VARIANTS || 20);
const PREFERRED_OPERATOR = process.env.PREFERRED_OPERATOR || "";
const SERVICE_MODE = process.env.MAAS_SERVICE_MODE || "sync";
const SCREENSHOT_TIMEOUT_MS = Number(process.env.SCREENSHOT_TIMEOUT_MS || 15000);
const LLM_LOOP_REQUIRED = process.env.MAAS_LLM_LOOP_REQUIRED !== "0";
const LLM_MODEL = process.env.MAAS_LLM_MODEL || "gpt-5.4-mini";
const LLM_GENERATION_FEEDBACK_JSON = process.env.MAAS_LLM_GENERATION_FEEDBACK_JSON || "";
const FEEDBACK_FAST_LOOP = Boolean(LLM_GENERATION_FEEDBACK_JSON) && process.env.MAAS_LLM_FEEDBACK_FULL_RUN !== "1";
const LLM_TARGET_COUNT = Number(process.env.MAAS_LLM_TARGET_COUNT || (FEEDBACK_FAST_LOOP ? 120 : 120));
const LLM_COMPILE_LIMIT = Number(process.env.MAAS_LLM_COMPILE_LIMIT || (FEEDBACK_FAST_LOOP ? 120 : 90));
const LLM_TIMEOUT_SECONDS = Number(process.env.MAAS_LLM_TIMEOUT || (FEEDBACK_FAST_LOOP ? 120 : 240));
const LLM_BATCH_SIZE = Number(process.env.MAAS_LLM_BATCH_SIZE || (FEEDBACK_FAST_LOOP ? 5 : 30));
const LLM_BATCH_WORKERS = Number(process.env.MAAS_LLM_BATCH_WORKERS || 1);
const LLM_BATCH_CACHE_PATH = process.env.MAAS_LLM_BATCH_CACHE_PATH || "";
const LLM_OVERGENERATE_COUNT = Number(process.env.MAAS_LLM_OVERGENERATE_COUNT || (FEEDBACK_FAST_LOOP ? 8 : 0));
const LLM_BATCH_RETRIES = Number(process.env.MAAS_LLM_BATCH_RETRIES || (FEEDBACK_FAST_LOOP ? 2 : 3));
const LLM_MAX_OPENAI_BATCHES = Number(
  process.env.MAAS_LLM_MAX_OPENAI_BATCHES
  || (FEEDBACK_FAST_LOOP ? Math.ceil((LLM_TARGET_COUNT + LLM_OVERGENERATE_COUNT) / LLM_BATCH_SIZE) : 0),
);
const LLM_MAX_OUTPUT_TOKENS = Number(process.env.MAAS_LLM_MAX_OUTPUT_TOKENS || (FEEDBACK_FAST_LOOP ? 5000 : 12000));
const API_MAX_TIME_SECONDS = Number(process.env.MAAS_RENDER_API_MAX_TIME || (FEEDBACK_FAST_LOOP ? 1200 : 900));
const PREFERENCE_LOOP_ENABLED = process.env.MAAS_PREFERENCE_LOOP_ENABLED === "1";
const PREFERENCE_LOOP_REQUIRE_VLM = process.env.MAAS_PREFERENCE_LOOP_REQUIRE_VLM === "1";
const PREFERENCE_LOOP_TOP_K = Number(process.env.MAAS_PREFERENCE_LOOP_TOP_K || 40);
const PREFERENCE_LOOP_WORKERS = Number(process.env.MAAS_PREFERENCE_LOOP_WORKERS || 4);
const PREFERENCE_LOOP_MIN_FINAL_VLM = Number(process.env.MAAS_PREFERENCE_LOOP_MIN_FINAL_VLM || 16);
const PREFERENCE_VLM_MODEL = process.env.MAAS_PREFERENCE_VLM_MODEL || "gpt-5.4-mini";
const PREFERENCE_REFERENCE_ROOT = process.env.MAAS_PREFERENCE_REFERENCE_ROOT || "docs/ai-session-memory/reference-corpus";
const PREFERENCE_VLM_CACHE_DIR = process.env.MAAS_PREFERENCE_VLM_CACHE_DIR || "docs/ai-session-memory/reference-corpus/vlm-cache";
const PNG_FALLBACK = path.join(__dirname, "render_maas_20_alt_png.py");
const PNG_FALLBACK_PYTHON = process.env.PNG_FALLBACK_PYTHON
  || path.resolve(__dirname, "../../../ARR/backend/.venv/bin/python");

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

function geomRings(geometry) {
  if (!geometry) return [];
  if (geometry.type === "Polygon") return Array.isArray(geometry.coordinates) ? geometry.coordinates : [];
  if (geometry.type === "MultiPolygon") {
    return Array.isArray(geometry.coordinates?.[0]) ? geometry.coordinates[0] : [];
  }
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
  const stalls = props.parking_precheck?.layout_candidate?.stalls || [];
  return [
    ...coordsOf(feature),
    ...(props.mass_volumes || []).flatMap(volume => geomRings(volume.geometry).flat()),
    ...stalls.flatMap(stall => Array.isArray(stall.polygon_wgs84) ? stall.polygon_wgs84 : []),
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

function geometryPath(geometry, project, z = 0) {
  const rings = geomRings(geometry);
  if (!rings.length) return polyPath(geomCoords(geometry), project, z);
  return rings
    .filter(ring => Array.isArray(ring) && ring.length >= 4)
    .map(ring => polyPath(ring, project, z))
    .join(" ");
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

function centroid(coords) {
  if (!coords.length) return [0, 0];
  const sum = coords.reduce((acc, point) => [acc[0] + point[0], acc[1] + point[1]], [0, 0]);
  return [sum[0] / coords.length, sum[1] / coords.length];
}

function renderSectionProfile(feature, volumes, project) {
  const props = feature.properties || {};
  const profile = props.section_profile || props.maas_model?.section_profile;
  if (!profile || !profile.kind) return "";
  const allCoords = volumes.flatMap(volume => geomCoords(volume.geometry));
  if (allCoords.length < 3) return "";
  const b = bounds(allCoords);
  const maxTop = Math.max(...volumes.map(volume => Number(volume.top_height || props.height || 0)));
  const minTop = Math.min(...volumes.map(volume => Number(volume.top_height || props.height || 0)));
  const kind = String(profile.kind);
  const accent = "#ec4899";
  const label = `<text x="10" y="38" font-size="10" font-weight="800" fill="${accent}">${escapeHtml(kind)}</text>`;
  if (
    props.section_profile_materialized?.status === "materialized_inside_legal_floor_plates"
    && kind !== "sloped_roof"
    && kind !== "sloped_roof_mass"
  ) {
    return label;
  }

  if (kind === "sloped_roof" || kind === "sloped_roof_mass") {
    // Actual materialized source volumes already carry the folded section.
    // A second synthetic roof polygon and ribs obscured that geometry with
    // crossed linework, so the review renderer only labels the real mass.
    return label;
  }

  if (kind === "diagonal_connector" || kind === "diagonal_connect") {
    const ordered = [...volumes].sort((a, b) => Number(a.bottom_height || 0) - Number(b.bottom_height || 0));
    const lower = ordered[0];
    const upper = ordered[ordered.length - 1];
    const lowerCenter = project(centroid(geomCoords(lower.geometry)), Number(lower.top_height || maxTop) + 1.2);
    const upperCenter = project(centroid(geomCoords(upper.geometry)), Number(upper.top_height || maxTop) + 1.2);
    const dx = upperCenter[0] - lowerCenter[0];
    const dy = upperCenter[1] - lowerCenter[1];
    const len = Math.max(1, Math.hypot(dx, dy));
    const nx = -dy / len * 9;
    const ny = dx / len * 9;
    const path = [
      [lowerCenter[0] + nx, lowerCenter[1] + ny],
      [upperCenter[0] + nx, upperCenter[1] + ny],
      [upperCenter[0] - nx, upperCenter[1] - ny],
      [lowerCenter[0] - nx, lowerCenter[1] - ny],
    ].map(([x, y], index) => `${index ? "L" : "M"} ${x.toFixed(1)} ${y.toFixed(1)}`).join(" ") + " Z";
    return `${label}<path d="${path}" fill="rgba(236,72,153,.36)" stroke="#be185d" stroke-width="2"/><line x1="${lowerCenter[0].toFixed(1)}" y1="${lowerCenter[1].toFixed(1)}" x2="${upperCenter[0].toFixed(1)}" y2="${upperCenter[1].toFixed(1)}" stroke="#fdf2f8" stroke-width="1.5" stroke-linecap="round"/>`;
  }

  if (kind === "terrace_ribbon") {
    const lines = [];
    for (let index = 0; index < 4; index += 1) {
      const t = (index + 1) / 5;
      const y = b.maxY - (b.maxY - b.minY) * t * 0.34;
      const z = maxTop * (0.40 + index * 0.13) + 1.2;
      const a = project([b.minX + (b.maxX - b.minX) * 0.06, y], z);
      const c = project([b.maxX - (b.maxX - b.minX) * 0.06, y], z);
      lines.push(`<line x1="${a[0].toFixed(1)}" y1="${a[1].toFixed(1)}" x2="${c[0].toFixed(1)}" y2="${c[1].toFixed(1)}" stroke="#be185d" stroke-width="3" stroke-linecap="round"/>`);
    }
    return `${label}${lines.join("")}`;
  }

  return label;
}

function renderSectionSourceSurfaces(feature, project) {
  const props = feature.properties || {};
  const surfaces = Array.isArray(props.section_source_surfaces)
    ? props.section_source_surfaces
    : Array.isArray(props.maas_model?.section_source_surfaces) ? props.maas_model.section_source_surfaces : [];
  if (!surfaces.length) return "";
  return surfaces.map((surface) => {
    const vertices = Array.isArray(surface.vertices_wgs84_h) ? surface.vertices_wgs84_h : [];
    if (vertices.length < 3) return "";
    const role = String(surface.role || "");
    const kind = String(surface.kind || "");
    const projected = vertices.map(([lng, lat, h]) => project([Number(lng), Number(lat)], Number(h) || 0));
    const path = projected.map(([x, y], index) => `${index ? "L" : "M"} ${x.toFixed(1)} ${y.toFixed(1)}`).join(" ") + " Z";
    const style = kind === "sloped_roof"
      ? { fill: "rgba(255,207,74,.30)", stroke: "#f97316", width: 2.0 }
      : kind === "terrace_ribbon"
        ? { fill: "rgba(255,207,74,.18)", stroke: "#f97316", width: 1.8 }
        : { fill: "rgba(255,207,74,.22)", stroke: "#f97316", width: 1.8 };
    const title = role ? `<title>${escapeHtml(role)}</title>` : "";
    return `<path d="${path}" fill="${style.fill}" stroke="${style.stroke}" stroke-width="${style.width}" opacity=".92">${title}</path>`;
  }).join("");
}

function volumeVisualStyle({ role, designSynthesis }) {
  const isConnectorBridge = role.includes("diagonal_connector_bridge");
  const isSectionSource = role.startsWith("section_source_");
  const isRoof = role.includes("sloped_roof") || role.includes("roof_plane");
  const isOverlap = role.includes("overlap_slab");
  if (isRoof) {
    return {
      sideFillA: "rgba(255,123,24,.28)",
      sideFillB: "rgba(255,123,24,.20)",
      topFill: "rgba(255,220,92,.58)",
      stroke: "#be123c",
      sideStrokeWidth: 0.7,
      topStrokeWidth: 2.4,
    };
  }
  if (isOverlap) {
    return {
      sideFillA: "rgba(255,123,24,.38)",
      sideFillB: "rgba(255,123,24,.28)",
      topFill: "rgba(255,207,74,.54)",
      stroke: "#ea580c",
      sideStrokeWidth: 0.8,
      topStrokeWidth: 2.0,
    };
  }
  if (isConnectorBridge) {
    return {
      sideFillA: "rgba(255,123,24,.34)",
      sideFillB: "rgba(255,123,24,.26)",
      topFill: "rgba(255,207,74,.44)",
      stroke: "#f97316",
      sideStrokeWidth: 0.8,
      topStrokeWidth: 1.2,
    };
  }
  if (designSynthesis && isSectionSource) {
    return {
      sideFillA: "rgba(255,123,24,.34)",
      sideFillB: "rgba(255,123,24,.24)",
      topFill: "rgba(255,207,74,.46)",
      stroke: "#fb923c",
      sideStrokeWidth: 0.7,
      topStrokeWidth: 1.2,
    };
  }
  return {
    sideFillA: "rgba(255,123,24,.48)",
    sideFillB: "rgba(255,123,24,.38)",
    topFill: "rgba(255,207,74,.65)",
    stroke: "#ff7418",
    sideStrokeWidth: 0.8,
    topStrokeWidth: 1.7,
  };
}

function visualFamily(feature) {
  const props = feature.properties || {};
  const signature = props.source_signature || props.maas_model?.source_signature || {};
  return String(signature.family || props.operator_family || "");
}

function profileKind(feature) {
  const props = feature.properties || {};
  return String((props.section_profile || props.maas_model?.section_profile || {}).kind || "");
}

function shouldPreserveLayeredStack(feature) {
  const family = visualFamily(feature);
  const kind = profileKind(feature);
  const shape = String((feature.properties || {}).mass_shape || "");
  return (
    family === "legal_layered"
    || family === "stepback_tower"
    || kind === "stepped_tower"
    || shape.includes("stepback")
    || shape.includes("step_envelope")
  );
}

function volumesForRender(feature, volumes) {
  if (shouldPreserveLayeredStack(feature)) return volumes;
  const byStack = new Map();
  const keep = [];
  volumes.forEach((volume, index) => {
    const role = String(volume.role || "");
    const match = role.match(/^source_geometry_stack_(\d+)_(\d+)/);
    if (!match) {
      keep.push({ volume, index });
      return;
    }
    const key = match[1];
    const level = Number(match[2]);
    const bucket = byStack.get(key) || [];
    bucket.push({ volume, index, level });
    byStack.set(key, bucket);
  });
  byStack.forEach((bucket) => {
    bucket.sort((a, b) => a.level - b.level || a.index - b.index);
    if (bucket.length <= 2) {
      keep.push(...bucket);
    } else {
      keep.push(bucket[0], bucket[bucket.length - 1]);
    }
  });
  return keep
    .sort((a, b) => a.index - b.index)
    .map(item => item.volume);
}

function renderParkingStalls(feature, project) {
  const props = feature.properties || {};
  const layout = props.parking_precheck?.layout_candidate || {};
  const stalls = Array.isArray(layout.stalls) ? layout.stalls : [];
  if (!stalls.length) return "";
  return stalls.map((stall, index) => {
    const coords = Array.isArray(stall.polygon_wgs84) ? stall.polygon_wgs84 : [];
    if (coords.length < 4) return "";
    const path = polyPath(coords, project, 0.35);
    const center = centroid(coords);
    const [x, y] = project(center, 0.65);
    return `<g><path d="${path}" fill="rgba(236,72,153,.16)" stroke="#ec4899" stroke-width="2.2"/><text x="${x.toFixed(1)}" y="${y.toFixed(1)}" text-anchor="middle" font-size="8" font-weight="800" fill="#be185d">P${index + 1}</text></g>`;
  }).join("");
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>]/g, char => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
  }[char]));
}

function sequenceVerbs(props) {
  if (Array.isArray(props.maas_sequence_verbs) && props.maas_sequence_verbs.length) {
    return props.maas_sequence_verbs.map(String);
  }
  const sequence = Array.isArray(props.maas_verb_sequence)
    ? props.maas_verb_sequence
    : Array.isArray(props.maas_model?.verb_sequence) ? props.maas_model.verb_sequence : [];
  return sequence
    .map(call => typeof call === "string" ? call : call && typeof call === "object" ? call.verb : "")
    .filter(Boolean)
    .map(String);
}

function parkingDisplay(layout) {
  const status = layout.status || "no parking";
  const massStage = layout.mass_stage_parking || {};
  if (status === "pass") {
    return { className: "good", label: "permit-precheck pass" };
  }
  if (massStage.status === "pass") {
    return { className: "good", label: `mass-stage count pass / ${status}` };
  }
  if (status === "fail") {
    return { className: "bad", label: status };
  }
  return { className: "warn", label: status };
}

async function postJson(url, body) {
  const result = spawnSync("curl", [
    "-sS",
    "--max-time",
    String(API_MAX_TIME_SECONDS),
    "-H",
    "Content-Type: application/json",
    "-X",
    "POST",
    "--data-binary",
    "@-",
    "-w",
    "\n%{http_code}",
    url,
  ], {
    input: JSON.stringify(body),
    encoding: "utf-8",
    maxBuffer: 1024 * 1024 * 256,
  });
  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    throw new Error(`${url} curl failed: ${result.stderr || result.stdout}`);
  }
  const output = result.stdout || "";
  const marker = output.lastIndexOf("\n");
  const text = marker >= 0 ? output.slice(0, marker) : output;
  const status = marker >= 0 ? Number(output.slice(marker + 1)) : 0;
  if (status < 200 || status >= 300) {
    throw new Error(`${url} failed ${status}: ${text.slice(0, 500)}`);
  }
  return JSON.parse(text);
}

async function buildPayload() {
  const cachedJsonPath = path.join(OUT_DIR, "maas-20-alt-latest.json");
  if (process.env.REUSE_JSON === "1" && fs.existsSync(cachedJsonPath)) {
    console.error(`[maas-render] reusing ${cachedJsonPath}`);
    return JSON.parse(fs.readFileSync(cachedJsonPath, "utf8"));
  }
  console.error(`[maas-render] loading boundary for PNU ${PNU}`);
  const boundary = await postJson(`${BACKEND}/design/site-boundary/`, { pnu: PNU });
  const coords = boundary.geometry.coordinates[0];
  console.error("[maas-render] resolving legal constraints");
  const constraints = await postJson(`${BACKEND}/design/auto-constraints/`, {
    pnu: PNU,
    building_type: BUILDING_TYPE,
    site_polygon: boundary.geometry,
  });
  const cx = coords.slice(0, -1).reduce((sum, point) => sum + point[0], 0) / (coords.length - 1);
  const cy = coords.slice(0, -1).reduce((sum, point) => sum + point[1], 0) / (coords.length - 1);
  const massCoords = coords.map(([x, y]) => [cx + (x - cx) * 0.72, cy + (y - cy) * 0.72]);
  const massGeojson = {
    type: "Feature",
    geometry: { type: "Polygon", coordinates: [massCoords] },
    properties: { height: 18, num_floors: 6, floor_height: 3.0, mass_shape: "seed" },
  };
  const started = Date.now();
  console.error(`[maas-render] requesting ${MAX_VARIANTS} legal variants; llm=${LLM_LOOP_REQUIRED ? "on" : "off"} model=${LLM_MODEL || "server-default"} target=${LLM_TARGET_COUNT} feedback=${LLM_GENERATION_FEEDBACK_JSON ? "on" : "off"} fast=${FEEDBACK_FAST_LOOP ? "on" : "off"} preference=${PREFERENCE_LOOP_ENABLED || PREFERENCE_LOOP_REQUIRE_VLM ? "on" : "off"}`);
  const variants = await postJson(`${BACKEND}/design/maas/legal-variants/`, {
    service_mode: SERVICE_MODE,
    pnu: PNU,
    site_polygon: boundary.geometry,
    mass_geojson: massGeojson,
    constraints: constraints.constraints,
    sunlight_envelope: constraints.setback_geometries?.sunlight_envelope || null,
    setback_geometries: constraints.setback_geometries || null,
    building_type: BUILDING_TYPE,
    max_variants: MAX_VARIANTS,
    parking_options: {
      maas_llm_loop: {
        enabled: LLM_LOOP_REQUIRED,
        required: LLM_LOOP_REQUIRED,
        target_count: LLM_TARGET_COUNT,
        compile_limit: LLM_COMPILE_LIMIT,
        timeout: LLM_TIMEOUT_SECONDS,
        batch_size: LLM_BATCH_SIZE,
        batch_workers: LLM_BATCH_WORKERS,
        ...(LLM_BATCH_CACHE_PATH ? { batch_cache_path: path.resolve(LLM_BATCH_CACHE_PATH) } : {}),
        overgenerate_count: LLM_OVERGENERATE_COUNT,
        batch_retries: LLM_BATCH_RETRIES,
        ...(LLM_MAX_OPENAI_BATCHES > 0 ? { max_openai_batches: LLM_MAX_OPENAI_BATCHES } : {}),
        max_output_tokens: LLM_MAX_OUTPUT_TOKENS,
        ...(LLM_MODEL ? { model: LLM_MODEL } : {}),
        ...(LLM_GENERATION_FEEDBACK_JSON ? { generation_feedback_path: path.resolve(LLM_GENERATION_FEEDBACK_JSON) } : {}),
      },
      maas_preference_loop: {
        enabled: PREFERENCE_LOOP_ENABLED || PREFERENCE_LOOP_REQUIRE_VLM,
        require_vlm: PREFERENCE_LOOP_REQUIRE_VLM,
        top_k: PREFERENCE_LOOP_TOP_K,
        parallel_workers: PREFERENCE_LOOP_WORKERS,
        min_final_vlm_scored: PREFERENCE_LOOP_MIN_FINAL_VLM,
        ...(PREFERENCE_VLM_MODEL ? { model: PREFERENCE_VLM_MODEL } : {}),
        reference_root: PREFERENCE_REFERENCE_ROOT,
        cache_dir: PREFERENCE_VLM_CACHE_DIR,
      },
    },
    ...(PREFERRED_OPERATOR ? { preferred_operator: PREFERRED_OPERATOR } : {}),
  });
  console.error(`[maas-render] legal variants returned in ${Date.now() - started}ms`);
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
  const renderVolumes = volumesForRender(feature, volumes);
  const designSynthesis = Boolean(props.section_profile_materialized?.design_synthesis);
  const project = projectFactory(globalBounds, 310, 190);
  const site = `<path d="${polyPath(siteCoords, project, 0)}" fill="#effaf2" stroke="#58d99b" stroke-width="1.2" stroke-dasharray="4 4"/>`;
  const layers = [];
  [...renderVolumes].sort((a, b) => (a.bottom_height || 0) - (b.bottom_height || 0)).forEach((volume, index) => {
    const coords = geomCoords(volume.geometry);
    const bottom = Number(volume.bottom_height || 0);
    const top = Number(volume.top_height || props.height || 0);
    const role = String(volume.role || "");
    const visual = volumeVisualStyle({ role, designSynthesis });
    sidePaths(coords, project, bottom, top).forEach((side, sideIndex) => {
      layers.push(`<path d="${side}" fill="${sideIndex % 2 ? visual.sideFillB : visual.sideFillA}" stroke="${visual.stroke}" stroke-width="${visual.sideStrokeWidth}"/>`);
    });
    layers.push(`<path d="${geometryPath(volume.geometry, project, top)}" fill="${visual.topFill}" stroke="${visual.stroke}" stroke-width="${visual.topStrokeWidth}" fill-rule="evenodd"/>`);
  });
  if (designSynthesis) {
    layers.push(renderSectionSourceSurfaces(feature, project));
  }
  layers.push(renderSectionProfile(feature, renderVolumes, project));
  layers.push(renderParkingStalls(feature, project));
  const precheck = props.parking_precheck || {};
  const layout = precheck.layout_candidate || {};
  const required = precheck.required_count || {};
  const parking = parkingDisplay(layout);
  const providedSpaces = layout.provided_spaces ?? "-";
  const requiredSpaces = layout.required_spaces ?? required.required_spaces ?? "-";
  const concept = props.maas_concept || props.operator_family || "";
  const family = props.typology_family || props.operator_family || "";
  const verbs = sequenceVerbs(props).slice(0, 4).join(">");
  const synthesis = props.section_profile_materialized?.design_synthesis
    ? `synthesis:${props.section_profile_materialized.kind || "section"}`
    : "";
  return `<section class="card">
    <svg viewBox="0 0 310 190">${site}${layers.join("")}<text x="10" y="20" font-size="13" font-weight="800" fill="#0d1a2d">${escapeHtml(props.variant_id)}</text></svg>
    <div class="meta">
      <div class="shape">${escapeHtml(props.mass_shape)}</div>
      <div class="section">${escapeHtml(concept)}${family ? ` · typology:${escapeHtml(family)}` : ""}</div>
      ${synthesis ? `<div class="synthesis">${escapeHtml(synthesis)}</div>` : ""}
      <div class="verbs">${escapeHtml(verbs || "base")}</div>
      <div class="numbers">FAR ${Number(props.far || 0).toFixed(1)} · BCR ${Number(props.bcr || 0).toFixed(1)} · H ${Number(props.height || 0).toFixed(1)}m</div>
      <div class="${parking.className}">P ${escapeHtml(providedSpaces)}/${escapeHtml(requiredSpaces)} · ${escapeHtml(parking.label)}</div>
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
    .card{height:282px;position:relative;border:1px solid #263d5e;border-radius:8px;background:#101d32;overflow:hidden;display:grid;grid-template-rows:190px 1fr}
    svg{background:#f7f9fb}.meta{padding:8px 12px 22px;min-width:0}.shape{font-weight:800;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.section{font-size:12px;color:#f9a8d4;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.synthesis{font-size:11px;color:#fbbf24;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.verbs{font-size:11px;color:#93c5fd;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.numbers{font-size:12px;color:#c2d0e3;margin-top:3px;white-space:nowrap}.good,.warn,.bad{position:absolute;left:12px;right:12px;bottom:4px;font-size:12px;font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.good{color:#22d18b}.warn{color:#ffc12c}.bad{color:#ff5573}
    footer{position:absolute;left:32px;right:32px;bottom:14px;border-top:1px solid #233852;padding-top:10px;color:#9fb2cc;font-size:14px}
  </style></head><body>
  <header><h1>MAAS 20 Alternatives · PNU ${escapeHtml(payload.pnu)}</h1><div class="sub">${features.length}/${MAX_VARIANTS} candidates · ${escapeHtml(payload.building_type)} · generated in ${payload.elapsed_ms}ms · green=mass-stage count satisfied, yellow=permit review, red=count/layout fail</div></header>
  <main>${cards}</main>
  <footer>Use this as the default mass review evidence. If many cards still share the same footprint, the algorithm is not producing true plan diversity.</footer>
  </body></html>`;
  const htmlPath = path.join(OUT_DIR, "maas-20-alt-latest.html");
  const pngPath = path.join(OUT_DIR, "maas-20-alt-latest.png");
  const jsonPath = path.join(OUT_DIR, "maas-20-alt-latest.json");
  fs.writeFileSync(htmlPath, html, "utf8");
  fs.writeFileSync(jsonPath, JSON.stringify(payload, null, 2), "utf8");

  let screenshotStatus = "not_attempted";
  let screenshotError = null;
  let browser = null;
  try {
    browser = await chromium.launch({ headless: true, args: ["--no-sandbox", "--disable-gpu"] });
    const page = await browser.newPage({ viewport: { width: 2200, height: 1400 }, deviceScaleFactor: 1 });
    page.setDefaultTimeout(SCREENSHOT_TIMEOUT_MS);
    await page.goto("file://" + htmlPath, { waitUntil: "domcontentloaded", timeout: SCREENSHOT_TIMEOUT_MS });
    const client = await page.context().newCDPSession(page);
    const shot = await Promise.race([
      client.send("Page.captureScreenshot", {
        format: "png",
        fromSurface: true,
        captureBeyondViewport: false,
      }),
      new Promise((_, reject) => setTimeout(() => reject(new Error(`screenshot timeout after ${SCREENSHOT_TIMEOUT_MS}ms`)), SCREENSHOT_TIMEOUT_MS)),
    ]);
    fs.writeFileSync(pngPath, Buffer.from(shot.data, "base64"));
    screenshotStatus = "updated";
  } catch (error) {
    screenshotStatus = "failed";
    screenshotError = String(error && error.message ? error.message : error);
  } finally {
    if (browser) {
      await browser.close().catch(() => {});
    }
  }
  let fallback = null;
  if (screenshotStatus === "failed" && process.env.NO_PNG_FALLBACK !== "1") {
    try {
      const python = fs.existsSync(PNG_FALLBACK_PYTHON) ? PNG_FALLBACK_PYTHON : "python3";
      const output = execFileSync(python, [PNG_FALLBACK], {
        cwd: OUT_DIR,
        encoding: "utf8",
        stdio: ["ignore", "pipe", "pipe"],
      });
      fallback = JSON.parse(output);
      screenshotStatus = "fallback_updated";
    } catch (fallbackError) {
      fallback = {
        status: "failed",
        error: String(fallbackError && fallbackError.message ? fallbackError.message : fallbackError),
      };
    }
  }
  return { htmlPath, pngPath, jsonPath, count: features.length, screenshotStatus, screenshotError, fallback };
}

(async () => {
  const payload = await buildPayload();
  const rendered = await render(payload);
  console.log(JSON.stringify(rendered, null, 2));
  if (rendered.screenshotStatus === "failed") {
    process.exit(1);
  }
})().catch(error => {
  console.error(error);
  process.exit(1);
});
