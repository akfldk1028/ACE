#!/usr/bin/env node

import { spawn } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function argValue(name, fallback) {
  const idx = process.argv.indexOf(name);
  return idx >= 0 && process.argv[idx + 1] ? process.argv[idx + 1] : fallback;
}

function sanitizeName(name) {
  return name.replace(/[^a-zA-Z0-9가-힣_-]+/g, '_').replace(/^_+|_+$/g, '');
}

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

function runPowerShell(script) {
  return new Promise((resolve) => {
    const child = spawn('powershell.exe', ['-NoProfile', '-Command', script], {
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => { stdout += chunk.toString(); });
    child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
    child.on('close', (code) => resolve({ code, stdout, stderr }));
  });
}

async function readPngSize(file) {
  const handle = await fs.open(file, 'r');
  try {
    const buffer = Buffer.alloc(24);
    await handle.read(buffer, 0, buffer.length, 0);
    const signature = buffer.subarray(0, 8).toString('hex');
    if (signature !== '89504e470d0a1a0a') return null;
    return {
      width: buffer.readUInt32BE(16),
      height: buffer.readUInt32BE(20),
    };
  } finally {
    await handle.close();
  }
}

const backendBase = argValue('--base', 'http://127.0.0.1:18000').replace(/\/$/, '');
const frontendBase = argValue('--frontend', 'http://127.0.0.1:5191').replace(/\/$/, '');
const caseFile = argValue('--cases', path.join(__dirname, 'cases.json'));
const outDir = path.resolve(argValue('--out-dir', path.join(__dirname, 'out', 'vworld')));
const chromePath = argValue('--chrome', 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe');
const width = Number(argValue('--width', '1280'));
const height = Number(argValue('--height', '900'));
const budgetMs = Number(argValue('--budget-ms', '120000'));
const querySuffix = argValue('--query', '');

const cases = JSON.parse(await fs.readFile(caseFile, 'utf8'));
await fs.mkdir(outDir, { recursive: true });

const results = [];
for (const testCase of cases) {
  const site = await postJson(`${backendBase}/design/site-boundary/`, { pnu: testCase.input });
  const pnu = site.json?.pnu || testCase.input;
  const safe = sanitizeName(testCase.name || pnu);
  const png = path.join(outDir, `${safe}.png`);
  const winPng = png.replace(/^\/mnt\/([a-z])\//, (_, drive) => `${drive.toUpperCase()}:\\`).replace(/\//g, '\\');
  const url = `${frontendBase}/design?pnu=${encodeURIComponent(pnu)}${querySuffix ? `&${querySuffix.replace(/^\?/, '')}` : ''}`;

  const ps = [
    `& '${chromePath}'`,
    '--headless=new',
    '--disable-gpu=false',
    '--enable-webgl',
    '--ignore-gpu-blocklist',
    '--run-all-compositor-stages-before-draw',
    '--disable-background-timer-throttling',
    `--window-size=${width},${height}`,
    `--virtual-time-budget=${budgetMs}`,
    `--screenshot='${winPng}'`,
    `'${url}'`,
  ].join(' ');

  console.log(`Capture ${testCase.name}: ${url}`);
  // eslint-disable-next-line no-await-in-loop
  const capture = await runPowerShell(ps);
  let stat = null;
  let imageSize = null;
  try {
    // eslint-disable-next-line no-await-in-loop
    stat = await fs.stat(png);
    // eslint-disable-next-line no-await-in-loop
    imageSize = await readPngSize(png);
  } catch {
    stat = null;
  }
  const dimensionsOk = imageSize?.width === width && imageSize?.height === height;
  results.push({
    name: testCase.name,
    input: testCase.input,
    pnu,
    url,
    png,
    ok: capture.code === 0 && Boolean(stat) && stat.size > 10_000 && dimensionsOk,
    bytes: stat?.size ?? 0,
    width: imageSize?.width ?? null,
    height: imageSize?.height ?? null,
    exitCode: capture.code,
    stderr: capture.stderr.trim().split('\n').slice(-5),
  });
}

const summary = {
  backendBase,
  frontendBase,
  checkedAt: new Date().toISOString(),
  pass: results.every((r) => r.ok),
  results,
};
const summaryFile = path.join(outDir, 'summary.json');
await fs.writeFile(summaryFile, `${JSON.stringify(summary, null, 2)}\n`);

console.table(results.map((r) => ({
  result: r.ok ? 'PASS' : 'FAIL',
  name: r.name,
  pnu: r.pnu,
  bytes: r.bytes,
  size: r.width && r.height ? `${r.width}x${r.height}` : 'missing',
  png: r.png,
})));
console.log(`VWorld capture summary: ${summaryFile}`);

if (!summary.pass) process.exit(1);
