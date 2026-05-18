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

const baseUrl = argValue('--base', 'http://127.0.0.1:8000');
const outDir = argValue('--out-dir', path.join(__dirname, 'out'));
const pythonBin = argValue('--python', path.join(repoRoot, 'ARR', 'backend', '.venv', 'bin', 'python'));
const skipBackendTests = hasFlag('--skip-backend-tests');
const withVworldCaptures = hasFlag('--with-vworld-captures');
const frontendUrl = argValue('--frontend', 'http://127.0.0.1:5191');
const requestTimeout = argValue('--request-timeout', '240');

function runStep(name, command, args, options = {}) {
  return new Promise((resolve) => {
    const startedAt = Date.now();
    console.log(`\n== ${name}`);
    console.log(`$ ${[command, ...args].join(' ')}`);
    const child = spawn(command, args, {
      cwd: options.cwd || repoRoot,
      stdio: 'inherit',
      env: {
        ...process.env,
        MPLCONFIGDIR: process.env.MPLCONFIGDIR || '/tmp/matplotlib',
      },
    });
    child.on('close', (code) => {
      resolve({
        name,
        command: [command, ...args],
        cwd: options.cwd || repoRoot,
        code,
        ok: code === 0,
        durationMs: Date.now() - startedAt,
      });
    });
  });
}

const steps = [
  {
    name: 'API regulation gate',
    command: 'node',
    args: [
      path.join(__dirname, 'check-design.mjs'),
      '--base',
      baseUrl,
      '--out',
      path.join(outDir, 'latest.json'),
    ],
  },
  {
    name: 'SVG section render gate',
    command: 'node',
    args: [
      path.join(__dirname, 'render-section.mjs'),
      '--base',
      baseUrl,
      '--out-dir',
      path.join(outDir, 'sections'),
    ],
  },
  {
    name: 'Python matplotlib section gate',
    command: pythonBin,
    args: [
      path.join(__dirname, 'render_section.py'),
      '--base',
      baseUrl,
      '--out-dir',
      path.join(outDir, 'pysections'),
      '--timeout',
      requestTimeout,
    ],
  },
  {
    name: 'Python matplotlib plan gate',
    command: pythonBin,
    args: [
      path.join(__dirname, 'render_plan.py'),
      '--base',
      baseUrl,
      '--out-dir',
      path.join(outDir, 'plan'),
      '--timeout',
      requestTimeout,
    ],
  },
  {
    name: 'Python PNG pixel verification gate',
    command: pythonBin,
    args: [
      path.join(__dirname, 'verify_images.py'),
      '--summary',
      path.join(outDir, 'pysections', 'summary.json'),
      '--out',
      path.join(outDir, 'pysections', 'image-check.json'),
    ],
  },
  {
    name: 'Python plan datum image verification gate',
    command: pythonBin,
    args: [
      path.join(__dirname, 'verify_plan_images.py'),
      '--summary',
      path.join(outDir, 'plan', 'summary.json'),
      '--out',
      path.join(outDir, 'plan', 'image-check.json'),
    ],
  },
  {
    name: 'Python NGII DEM coverage report',
    command: pythonBin,
    args: [
      path.join(__dirname, 'check_dem_coverage.py'),
      '--base',
      baseUrl,
      '--out',
      path.join(outDir, 'dem-coverage.json'),
      '--timeout',
      requestTimeout,
    ],
  },
];

if (!skipBackendTests) {
  steps.push({
    name: 'Backend datum/setback unit tests',
    command: pythonBin,
    args: ['manage.py', 'test', 'land.tests.SetbackGeometryDatumTest', 'land.tests.DatumCasesTest'],
    cwd: path.join(repoRoot, 'ARR', 'backend'),
  });
}

if (withVworldCaptures) {
  steps.push({
    name: 'Windows Chrome VWorld capture gate',
    command: 'node',
    args: [
      path.join(__dirname, 'capture-vworld.mjs'),
      '--base',
      baseUrl,
      '--frontend',
      frontendUrl,
      '--out-dir',
      path.join(outDir, 'vworld'),
    ],
  });
}

const results = [];
for (const step of steps) {
  // eslint-disable-next-line no-await-in-loop
  results.push(await runStep(step.name, step.command, step.args, { cwd: step.cwd }));
}

const summary = {
  baseUrl,
  checkedAt: new Date().toISOString(),
  pass: results.every((r) => r.ok),
  results,
  artifacts: {
    api: path.join(outDir, 'latest.json'),
    svgSections: path.join(outDir, 'sections'),
    pythonSections: path.join(outDir, 'pysections'),
    imageCheck: path.join(outDir, 'pysections', 'image-check.json'),
    demCoverage: path.join(outDir, 'dem-coverage.json'),
    vworldCaptures: path.join(outDir, 'vworld'),
  },
};

await fs.mkdir(outDir, { recursive: true });
const summaryFile = path.join(outDir, 'run-all-summary.json');
await fs.writeFile(summaryFile, `${JSON.stringify(summary, null, 2)}\n`);

console.log('\n== Summary');
console.table(results.map((r) => ({
  result: r.ok ? 'PASS' : 'FAIL',
  step: r.name,
  seconds: (r.durationMs / 1000).toFixed(1),
})));
console.log(`Summary file: ${summaryFile}`);

if (!summary.pass) process.exit(1);
