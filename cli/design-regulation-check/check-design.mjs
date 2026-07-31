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
const outFile = argValue('--out', path.join(__dirname, 'out', 'latest.json'));

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

function hasKey(data, key) {
  return Boolean(data?.setback_geometries?.[key]);
}

function matchesExpected(actual, expected) {
  if (expected === true) return actual === true;
  if (expected === false) return actual === false;
  return true;
}

function almostEqual(a, b, epsilon = 0.01) {
  return typeof a === 'number' && typeof b === 'number' && Math.abs(a - b) <= epsilon;
}

function validSplitBands(bands) {
  return Array.isArray(bands)
    && bands.length > 0
    && bands.every((band) => (
      typeof band.datum_m === 'number'
      && typeof band.length_m === 'number'
      && band.length_m > 0
      && typeof band.sample_count === 'number'
      && band.sample_count > 0
    ));
}

function validDaylightEnvelope(envelope) {
  const walls = envelope?.walls;
  return Array.isArray(walls)
    && walls.length > 0
    && walls.every((wall) => (
      Array.isArray(wall.positions)
      && wall.positions.length >= 2
      && Array.isArray(wall.min_heights)
      && Array.isArray(wall.max_heights)
      && wall.min_heights.length === wall.max_heights.length
      && wall.min_heights.every((h) => typeof h === 'number')
      && wall.max_heights.every((h, idx) => typeof h === 'number' && h >= wall.min_heights[idx])
    ));
}

function evaluate(testCase, site, auto) {
  const setbacks = auto.json?.setback_geometries || {};
  const datum = setbacks.datum_result || null;
  const sunlight = setbacks.sunlight_envelope || null;
  const daylight = setbacks.daylight_diagonal_envelope || null;
  const actual = {
    buildableArea: hasKey(auto.json, 'buildable_area'),
    adjacent: hasKey(auto.json, 'adjacent_setback'),
    road: hasKey(auto.json, 'road_setback'),
    cornerCutoff: hasKey(auto.json, 'corner_cutoff'),
    daylight: hasKey(auto.json, 'daylight_diagonal_envelope'),
    sunlight: hasKey(auto.json, 'sunlight_envelope'),
  };
  const checks = {
    siteBoundary: site.status === 200 && Boolean(site.json?.geometry),
    autoConstraints: auto.status === 200 && !auto.json?.error,
    datum: Boolean(datum?.elevation_m),
    datumSource: !testCase.expectedDatumSource || datum?.elevation_source === testCase.expectedDatumSource,
    roadDatum: !testCase.expectRoadDatum || typeof datum?.road_datum_m === 'number',
    neighborDatum: !testCase.expectNeighborDatum || typeof datum?.neighbor_datum_m === 'number',
    splitBands: !testCase.expectSplitBands || validSplitBands(datum?.split_bands),
    adjacent: matchesExpected(actual.adjacent, testCase.expectAdjacent),
    road: matchesExpected(actual.road, testCase.expectRoad),
    daylight: matchesExpected(actual.daylight, testCase.expectDaylight),
    sunlight: matchesExpected(actual.sunlight, testCase.expectSunlight),
    sunlightDatumBasis: !actual.sunlight || typeof datum?.neighbor_avg_datum_m !== 'number'
      || (
        almostEqual(sunlight?.datum_elevation_m, datum.neighbor_avg_datum_m)
        && sunlight?.datum_case === 'neighbor_avg_86'
      ),
    daylightShape: !actual.daylight || validDaylightEnvelope(daylight),
  };
  const pass = Object.values(checks).every(Boolean);
  return {
    name: testCase.name,
    input: testCase.input,
    buildingType: testCase.buildingType,
    pass,
    checks,
    pnu: site.json?.pnu || testCase.input,
    area_m2: site.json?.area_m2 ?? null,
    zones: auto.json?.zones || [],
    keys: Object.keys(setbacks),
    actual,
    datum,
    regulations: auto.json?.regulations || null,
    errors: [site.json?.error, auto.json?.error].filter(Boolean),
  };
}

function printTable(results) {
  const rows = results.map((r) => ({
    result: r.pass ? 'PASS' : 'FAIL',
    name: r.name,
    pnu: r.pnu,
    datum: r.datum ? `${r.datum.elevation_m}m/${r.datum.elevation_source}` : 'missing',
    datumCase: r.datum?.case || 'missing',
    roadDatum: typeof r.datum?.road_datum_m === 'number' ? `${r.datum.road_datum_m}m` : 'missing',
    neighborDatum: typeof r.datum?.neighbor_datum_m === 'number' ? `${r.datum.neighbor_datum_m}m` : 'missing',
    splitBands: Array.isArray(r.datum?.split_bands) ? r.datum.split_bands.length : 0,
    road: r.actual.road ? 'yes' : 'no',
    adjacent: r.actual.adjacent ? 'yes' : 'no',
    daylight: r.actual.daylight ? 'yes' : 'no',
    sunlight: r.actual.sunlight ? 'yes' : 'no',
    keys: r.keys.join(','),
  }));
  console.table(rows);
}

const cases = JSON.parse(await fs.readFile(caseFile, 'utf8'));
const results = [];

for (const testCase of cases) {
  const site = await postJson(`${baseUrl}/design/site-boundary/`, { pnu: testCase.input });
  const sitePolygon = site.json?.geometry;
  const pnu = site.json?.pnu || testCase.input;
  const auto = sitePolygon
    ? await postJson(`${baseUrl}/design/auto-constraints/`, {
        pnu,
        site_polygon: sitePolygon,
        building_type: testCase.buildingType || '공동주택',
      })
    : { status: 0, json: { error: 'site-boundary failed; auto-constraints skipped' } };
  results.push(evaluate(testCase, site, auto));
}

printTable(results);

const summary = {
  baseUrl,
  checkedAt: new Date().toISOString(),
  pass: results.every((r) => r.pass),
  results,
};

await fs.mkdir(path.dirname(outFile), { recursive: true });
await fs.writeFile(outFile, `${JSON.stringify(summary, null, 2)}\n`);

if (!summary.pass) {
  console.error(`Design regulation check failed. Detail: ${outFile}`);
  process.exit(1);
}

console.log(`Design regulation check passed. Detail: ${outFile}`);
