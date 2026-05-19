#!/usr/bin/env node

import { spawn } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..', '..');

function argValue(name, fallback) {
  const idx = process.argv.indexOf(name);
  return idx >= 0 && process.argv[idx + 1] ? process.argv[idx + 1] : fallback;
}

function hasFlag(name) {
  return process.argv.includes(name);
}

const baseUrl = argValue('--base', 'http://127.0.0.1:18000').replace(/\/$/, '');
const caseFile = argValue('--cases', path.join(__dirname, 'pnu-9-cases.json'));
const outDir = argValue('--out-dir', path.join(__dirname, 'out', 'pnu-visual-gate'));
const pythonBin = argValue('--python', path.join(repoRoot, 'ARR', 'backend', '.venv', 'bin', 'python'));
const timeout = argValue('--timeout', '300');
const strict = hasFlag('--strict');
const reuseExisting = hasFlag('--reuse-existing');

function runStep(name, command, args) {
  return new Promise((resolve) => {
    const startedAt = Date.now();
    console.log(`\n== ${name}`);
    console.log(`$ ${[command, ...args].join(' ')}`);
    const child = spawn(command, args, {
      cwd: repoRoot,
      stdio: 'inherit',
      env: {
        ...process.env,
        MPLCONFIGDIR: process.env.MPLCONFIGDIR || '/tmp/matplotlib',
      },
    });
    child.on('close', (code) => {
      resolve({
        name,
        code,
        ok: code === 0,
        durationMs: Date.now() - startedAt,
      });
    });
  });
}

async function readJson(file, fallback = null) {
  try {
    return JSON.parse(await fs.readFile(file, 'utf8'));
  } catch {
    return fallback;
  }
}

async function writeJson(file, payload) {
  await fs.mkdir(path.dirname(file), { recursive: true });
  await fs.writeFile(file, `${JSON.stringify(payload, null, 2)}\n`);
}

await fs.mkdir(outDir, { recursive: true });

const apiOut = argValue('--api-out', path.join(outDir, 'design-check.json'));
const demSelectionOut = path.join(outDir, 'dem-selection.json');
const demCasesOut = path.join(outDir, 'dem-cases.json');
const planDir = path.join(outDir, 'plan');
const planPassCasesOut = path.join(outDir, 'plan-pass-cases.json');
const sectionDir = path.join(outDir, 'sections');

const steps = [];
if (reuseExisting && await readJson(apiOut)) {
  steps.push({ name: '9-PNU API/line smoke gate', code: 0, ok: true, durationMs: 0, reused: true });
  console.log(`\n== 9-PNU API/line smoke gate\nReusing ${apiOut}`);
} else {
  steps.push(await runStep('9-PNU API/line smoke gate', 'node', [
    path.join(__dirname, 'check-design.mjs'),
    '--base', baseUrl,
    '--cases', caseFile,
    '--out', apiOut,
  ]));
}

steps.push(await runStep('Select NGII DEM-backed cases', 'node', [
  path.join(__dirname, 'select-dem-cases.mjs'),
  '--input', apiOut,
  '--cases', caseFile,
  '--out', demSelectionOut,
]));

const demSelection = await readJson(demSelectionOut, { selected: [], rejected: [] });
await writeJson(demCasesOut, demSelection.selected || []);

let planSummary = { pass: false, outputs: [] };
let sectionSummary = { pass: false, outputs: [] };
let planPassCases = [];

if ((demSelection.selected || []).length) {
  steps.push(await runStep('Plan datum/line PNG gate for DEM-backed cases', pythonBin, [
    path.join(__dirname, 'render_plan.py'),
    '--base', baseUrl,
    '--cases', demCasesOut,
    '--out-dir', planDir,
    '--timeout', timeout,
  ]));
  planSummary = await readJson(path.join(planDir, 'summary.json'), planSummary);
  const sourceCases = await readJson(demCasesOut, []);
  const byName = new Map(sourceCases.map((item) => [item.name, item]));
  planPassCases = (planSummary.outputs || [])
    .filter((item) => item.pass)
    .map((item) => ({
      ...(byName.get(item.name) || { name: item.name, buildingType: '공동주택' }),
      input: item.pnu,
      expectedDatumSource: 'ngii_local_dem',
      expectRoadDatum: true,
      expectNeighborDatum: true,
    }));
  await writeJson(planPassCasesOut, planPassCases);
}

if (planPassCases.length) {
  steps.push(await runStep('Section datum/envelope PNG gate for plan-passed cases', pythonBin, [
    path.join(__dirname, 'render_section.py'),
    '--base', baseUrl,
    '--cases', planPassCasesOut,
    '--out-dir', sectionDir,
    '--timeout', timeout,
  ]));
  sectionSummary = await readJson(path.join(sectionDir, 'summary.json'), sectionSummary);
}

const summary = {
  baseUrl,
  checkedAt: new Date().toISOString(),
  strict,
  pass: strict
    ? steps.every((step) => step.ok) && (sectionSummary.outputs || []).length === (await readJson(caseFile, [])).length
    : steps[0]?.ok && (sectionSummary.pass || false),
  counts: {
    totalCases: (await readJson(caseFile, [])).length,
    apiStrictPassed: (await readJson(apiOut, { results: [] })).results?.filter((r) => r.pass).length || 0,
    demSelected: (demSelection.selected || []).length,
    demRejected: (demSelection.rejected || []).length,
    planPassed: (planSummary.outputs || []).filter((r) => r.pass).length,
    sectionPassed: (sectionSummary.outputs || []).filter((r) => r.pass).length,
  },
  steps,
  artifacts: {
    apiOut,
    demSelectionOut,
    demCasesOut,
    planDir,
    planPassCasesOut,
    sectionDir,
  },
  demRejected: demSelection.rejected || [],
  planRejected: (planSummary.outputs || []).filter((r) => !r.pass),
};

const summaryFile = path.join(outDir, 'summary.json');
await writeJson(summaryFile, summary);

console.log('\n== PNU Visual Gate Summary');
console.table([summary.counts]);
console.log(`Summary file: ${summaryFile}`);

if (!summary.pass) {
  process.exit(strict ? 1 : 0);
}
