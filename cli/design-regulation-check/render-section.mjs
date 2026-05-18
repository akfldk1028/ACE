#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function argValue(name, fallback) {
  const idx = process.argv.indexOf(name);
  return idx >= 0 && process.argv[idx + 1] ? process.argv[idx + 1] : fallback;
}

const baseUrl = argValue('--base', 'http://127.0.0.1:8000').replace(/\/$/, '');
const caseFile = argValue('--cases', path.join(__dirname, 'cases.json'));
const outDir = argValue('--out-dir', path.join(__dirname, 'out', 'sections'));

async function postJson(url, body) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  });
  let json = null;
  try {
    json = await response.json();
  } catch {
    json = { error: 'Invalid JSON response' };
  }
  return { status: response.status, json };
}

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&apos;',
  })[c]);
}

function fmt(value) {
  return typeof value === 'number' && Number.isFinite(value) ? value.toFixed(2) : 'n/a';
}

function slug(value) {
  return String(value).replace(/[^0-9A-Za-z가-힣_-]+/g, '_').replace(/^_+|_+$/g, '');
}

function line(svg, x1, y1, x2, y2, color, width = 2, dash = '') {
  svg.push(`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="${width}"${dash ? ` stroke-dasharray="${dash}"` : ''}/>`);
}

function text(svg, x, y, value, color = '#111827', size = 13, weight = 500, anchor = 'start') {
  svg.push(`<text x="${x}" y="${y}" fill="${color}" font-size="${size}" font-weight="${weight}" text-anchor="${anchor}" font-family="Arial, sans-serif">${esc(value)}</text>`);
}

function rect(svg, x, y, w, h, fill, stroke = 'none', opacity = 1) {
  svg.push(`<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${fill}" stroke="${stroke}" opacity="${opacity}"/>`);
}

function pathEl(svg, d, fill, stroke, opacity = 1, width = 2) {
  svg.push(`<path d="${d}" fill="${fill}" stroke="${stroke}" stroke-width="${width}" opacity="${opacity}"/>`);
}

function buildSvg(testCase, site, auto) {
  const sg = auto.setback_geometries || {};
  const datum = sg.datum_result || {};
  const regs = auto.regulations || {};
  const sunlight = sg.sunlight_envelope || null;
  const daylight = sg.daylight_diagonal_envelope || null;

  const parcel = datum.parcel_datum_m ?? datum.elevation_m;
  const road = datum.road_datum_m;
  const neighbor = datum.neighbor_datum_m;
  const avg = datum.neighbor_avg_datum_m;
  const sunlightBase = sunlight?.datum_elevation_m;
  const daylightMult = regs.daylight_diagonal_multiplier ?? daylight?.slope ?? 2;

  const heights = [parcel, road, neighbor, avg, sunlightBase].filter((v) => typeof v === 'number');
  const minH = Math.floor(Math.min(...heights, 0) - 2);
  const maxH = Math.ceil(Math.max(...heights, 50) + 8);
  const width = 980;
  const height = 620;
  const left = 82;
  const right = 40;
  const top = 64;
  const bottom = 82;
  const plotW = width - left - right;
  const plotH = height - top - bottom;
  const xMax = 30;

  const x = (m) => left + (m / xMax) * plotW;
  const y = (m) => top + ((maxH - m) / (maxH - minH)) * plotH;

  const svg = [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`,
    '<rect width="100%" height="100%" fill="#f8fafc"/>',
  ];

  text(svg, left, 34, `${testCase.name} / ${site.pnu || testCase.input}`, '#0f172a', 20, 700);
  text(svg, left, 56, `source=${datum.elevation_source || 'n/a'}  case=${datum.case || 'n/a'}  zones=${(auto.zones || []).join(', ')}`, '#475569', 12);

  rect(svg, left, top, plotW, plotH, '#ffffff', '#cbd5e1');

  for (let h = Math.ceil(minH / 5) * 5; h <= maxH; h += 5) {
    line(svg, left, y(h), left + plotW, y(h), '#e2e8f0', 1);
    text(svg, 12, y(h) + 4, `${h}m`, '#64748b', 11);
  }
  for (let d = 0; d <= xMax; d += 5) {
    line(svg, x(d), top, x(d), top + plotH, '#f1f5f9', 1);
    text(svg, x(d), top + plotH + 24, `${d}m`, '#64748b', 11, 500, 'middle');
  }
  text(svg, left + plotW / 2, height - 18, 'distance inward from adjacent/north boundary (schematic)', '#475569', 12, 500, 'middle');

  const datumLines = [
    ['대지 §119 H0', parcel, '#eab308'],
    ['전면도로 기준', road, '#f97316'],
    ['인접대지 기준', neighbor, '#2563eb'],
    ['§86 평균수평면', avg, '#16a34a'],
  ];
  for (const [label, value, color] of datumLines) {
    if (typeof value !== 'number') continue;
    line(svg, left, y(value), left + plotW, y(value), color, 2, '7 5');
    text(svg, left + plotW + 8, y(value) + 4, `${label} ${fmt(value)}m`, color, 12, 700);
  }

  rect(svg, x(6), y((parcel ?? 0) + 26), x(10) - x(6), y(parcel ?? 0) - y((parcel ?? 0) + 26), '#94a3b8', '#475569', 0.75);
  text(svg, x(8), y((parcel ?? 0) + 13), 'test mass', '#1e293b', 12, 700, 'middle');

  if (sunlight) {
    const base = typeof sunlightBase === 'number' ? sunlightBase : 0;
    const baseSetback = sunlight.base_setback_m ?? 1.5;
    const baseHeight = sunlight.base_height_m ?? 10;
    const slope = sunlight.slope ?? 2;
    const capDepth = sunlight.max_depth_m ?? 25;
    const plateauEnd = sunlight.plateau_end_m ?? 5;
    const y0 = y(base);
    const y10 = y(base + baseHeight);
    const yCap = y(base + capDepth * slope);
    line(svg, x(baseSetback), y0, x(baseSetback), y10, '#dc2626', 4);
    line(svg, x(baseSetback), y10, x(plateauEnd), y10, '#f472b6', 4);
    line(svg, x(plateauEnd), y10, x(capDepth), yCap, '#ec4899', 4);
    pathEl(svg, `M ${x(baseSetback)} ${y0} L ${x(baseSetback)} ${y10} L ${x(plateauEnd)} ${y10} L ${x(capDepth)} ${yCap} L ${x(capDepth)} ${y0} Z`, '#f9a8d4', '#ec4899', 0.16, 2);
    text(svg, x(13), y(base + 24), `정북일조: H0=${fmt(base)}m (${sunlight.datum_case || 'datum'})`, '#be185d', 13, 700);
  } else {
    text(svg, x(13), y(maxH - 7), '정북일조 미적용 또는 envelope 없음', '#64748b', 13, 700);
  }

  if (daylight) {
    const base = typeof parcel === 'number' ? parcel : 0;
    const d0 = 0;
    const d1 = Math.min(18, xMax);
    const h1 = base + d1 * daylightMult;
    line(svg, x(d0), y(base), x(d1), y(h1), '#7e22ce', 4);
    pathEl(svg, `M ${x(d0)} ${y(base)} L ${x(d1)} ${y(h1)} L ${x(d1)} ${y(base)} Z`, '#c084fc', '#7e22ce', 0.18, 2);
    text(svg, x(13), y(base + 7), `채광사선: parcel H0=${fmt(base)}m, multiplier=${daylightMult}`, '#6b21a8', 13, 700);
  }

  const checks = [];
  if (typeof avg === 'number' && sunlight && Math.abs((sunlightBase ?? NaN) - avg) > 0.01) {
    checks.push(`FAIL sunlightDatum(${fmt(sunlightBase)}) != neighborAvg(${fmt(avg)})`);
  }
  if (typeof avg === 'number' && sunlight && sunlight.datum_case !== 'neighbor_avg_86') {
    checks.push(`FAIL sunlight datum_case=${sunlight.datum_case || 'missing'}; expected neighbor_avg_86`);
  }
  if (testCase.expectSunlight && !sunlight) {
    checks.push('FAIL expected sunlight envelope is missing');
  }
  if (testCase.expectSunlight === false && sunlight) {
    checks.push('FAIL sunlight envelope exists but should be absent for this case');
  }
  if (testCase.expectDaylight !== false && !daylight) {
    checks.push('FAIL expected daylight diagonal envelope is missing');
  }
  if (testCase.expectDaylight === false && daylight) {
    checks.push('FAIL daylight diagonal envelope exists but should be absent for this case');
  }
  if (daylight && typeof parcel !== 'number') {
    checks.push('FAIL daylight has no parcel datum base');
  }
  if (daylight && !daylight.walls?.length) {
    checks.push('FAIL daylight diagonal envelope has no walls');
  }
  if (datum.elevation_source !== 'ngii_local_dem') {
    checks.push(`FAIL source=${datum.elevation_source || 'missing'}; expected ngii_local_dem`);
  }
  if (Array.isArray(datum.split_bands) && datum.split_bands.length) {
    checks.push(`INFO split_bands=${datum.split_bands.length} (profile metadata, not area polygons)`);
  }
  if (!checks.length) checks.push('PASS datum/envelope basis checks');

  let cy = height - 58;
  for (const check of checks) {
    const isFail = check.startsWith('FAIL');
    const isWarn = check.startsWith('WARN');
    text(svg, left, cy, check, isFail ? '#dc2626' : isWarn ? '#d97706' : '#166534', 13, 700);
    cy += 18;
  }

  svg.push('</svg>');
  return {
    svg: svg.join('\n'),
    checks,
    pass: checks.every((c) => !c.startsWith('FAIL')),
    summary: {
      pnu: site.pnu || testCase.input,
      parcelDatum: parcel ?? null,
      roadDatum: road ?? null,
      neighborDatum: neighbor ?? null,
      neighborAvgDatum: avg ?? null,
      sunlightDatum: sunlightBase ?? null,
      sunlightCase: sunlight?.datum_case ?? null,
      daylightWalls: daylight?.walls?.length ?? 0,
      source: datum.elevation_source ?? null,
    },
  };
}

const cases = JSON.parse(await fs.readFile(caseFile, 'utf8'));
await fs.mkdir(outDir, { recursive: true });

const outputs = [];
for (const testCase of cases) {
  const siteRes = await postJson(`${baseUrl}/design/site-boundary/`, { pnu: testCase.input });
  if (siteRes.status !== 200 || !siteRes.json?.geometry) {
    outputs.push({ name: testCase.name, pass: false, error: siteRes.json?.error || `site status ${siteRes.status}` });
    continue;
  }
  const autoRes = await postJson(`${baseUrl}/design/auto-constraints/`, {
    pnu: siteRes.json.pnu || testCase.input,
    site_polygon: siteRes.json.geometry,
    building_type: testCase.buildingType || '공동주택',
  });
  if (autoRes.status !== 200 || autoRes.json?.error) {
    outputs.push({ name: testCase.name, pass: false, error: autoRes.json?.error || `auto status ${autoRes.status}` });
    continue;
  }
  const rendered = buildSvg(testCase, siteRes.json, autoRes.json);
  const file = path.join(outDir, `${slug(testCase.name)}.svg`);
  await fs.writeFile(file, `${rendered.svg}\n`);
  outputs.push({ name: testCase.name, file, pass: rendered.pass, checks: rendered.checks, ...rendered.summary });
}

const summary = {
  baseUrl,
  renderedAt: new Date().toISOString(),
  pass: outputs.every((o) => o.pass),
  outputs,
};
const summaryFile = path.join(outDir, 'summary.json');
await fs.writeFile(summaryFile, `${JSON.stringify(summary, null, 2)}\n`);

console.table(outputs.map((o) => ({
  result: o.pass ? 'PASS' : 'FAIL',
  name: o.name,
  parcel: fmt(o.parcelDatum),
  road: fmt(o.roadDatum),
  neighbor: fmt(o.neighborDatum),
  avg86: fmt(o.neighborAvgDatum),
  sunlight: fmt(o.sunlightDatum),
  daylightWalls: o.daylightWalls ?? 'n/a',
  file: o.file ? path.relative(process.cwd(), o.file) : o.error,
})));

console.log(`Section render summary: ${summaryFile}`);
if (!summary.pass) process.exit(1);
