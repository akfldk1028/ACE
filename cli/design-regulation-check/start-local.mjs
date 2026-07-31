#!/usr/bin/env node

import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..', '..');
const backendDir = path.join(repoRoot, 'ARR', 'backend');
const frontendDir = path.join(repoRoot, 'ARR', 'frontend');
const pythonBin = path.join(backendDir, '.venv', 'bin', 'python');

function argValue(name, fallback) {
  const idx = process.argv.indexOf(name);
  return idx >= 0 && process.argv[idx + 1] ? process.argv[idx + 1] : fallback;
}

function hasFlag(name) {
  return process.argv.includes(name);
}

const host = argValue('--host', '127.0.0.1');
const backendPort = argValue('--backend-port', '18000');
const frontendPort = argValue('--frontend-port', '5174');
const backendUrl = `http://${host}:${backendPort}`;
const frontendOrigin = `http://${host}:${frontendPort}`;
const frontendUrl = `${frontendOrigin}/design`;
const noVerify = hasFlag('--no-verify');

const children = new Set();

function start(name, command, args, options = {}) {
  console.log(`\n== ${name}`);
  console.log(`$ ${[command, ...args].join(' ')}`);
  const child = spawn(command, args, {
    cwd: options.cwd || repoRoot,
    stdio: ['ignore', 'pipe', 'pipe'],
    env: {
      ...process.env,
      ...(options.env || {}),
    },
  });

  children.add(child);
  child.stdout.on('data', (chunk) => process.stdout.write(`[${name}] ${chunk}`));
  child.stderr.on('data', (chunk) => process.stderr.write(`[${name}] ${chunk}`));
  child.on('exit', (code, signal) => {
    children.delete(child);
    if (signal) {
      console.log(`[${name}] stopped by ${signal}`);
    } else if (code !== 0 && code !== null) {
      console.error(`[${name}] exited with code ${code}`);
    }
  });
  return child;
}

async function waitForUrl(url, { timeoutMs = 60000, label = url } = {}) {
  const started = Date.now();
  let lastError = '';
  while (Date.now() - started < timeoutMs) {
    try {
      const response = await fetch(url);
      if (response.status < 500) return response;
      lastError = `${response.status} ${response.statusText}`;
    } catch (error) {
      lastError = error.message;
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  throw new Error(`Timed out waiting for ${label}: ${lastError}`);
}

async function isUrlUp(url) {
  try {
    await waitForUrl(url, { timeoutMs: 1500 });
    return true;
  } catch {
    return false;
  }
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`${url} returned ${response.status}`);
  }
  return response.json();
}

async function verifyFrontendProxy() {
  const site = await postJson(`${frontendOrigin}/design/site-boundary/`, {
    pnu: '강남구 도곡동 467-3',
  });
  const auto = await postJson(`${frontendOrigin}/design/auto-constraints/`, {
    pnu: site.pnu,
    site_polygon: site.geometry,
    building_type: '공동주택',
  });
  const geometries = auto.setback_geometries || {};
  const datum = geometries.datum_result || {};
  const sunlight = geometries.sunlight_envelope || {};
  if (datum.elevation_source !== 'ngii_local_dem') {
    throw new Error(`frontend proxy datum source is ${datum.elevation_source || 'missing'}, expected ngii_local_dem`);
  }
  const neighborAvg = Number(datum.neighbor_avg_datum_m);
  const sunlightDatum = Number(sunlight.datum_elevation_m);
  if (Number.isFinite(neighborAvg) && Number.isFinite(sunlightDatum) && Math.abs(neighborAvg - sunlightDatum) > 0.001) {
    throw new Error(`frontend proxy sunlight datum ${sunlightDatum} does not match §86 average ${neighborAvg}`);
  }
  console.log(`Frontend proxy OK: ${site.pnu}, datum=${datum.parcel_datum_m}m/${datum.elevation_source}`);
}

function runOnce(name, command, args, options = {}) {
  return new Promise((resolve, reject) => {
    console.log(`\n== ${name}`);
    console.log(`$ ${[command, ...args].join(' ')}`);
    const child = spawn(command, args, {
      cwd: options.cwd || repoRoot,
      stdio: 'inherit',
      env: {
        ...process.env,
        MPLCONFIGDIR: process.env.MPLCONFIGDIR || '/tmp/matplotlib',
        ...(options.env || {}),
      },
    });
    child.on('close', (code) => {
      if (code === 0) resolve();
      else reject(new Error(`${name} failed with exit code ${code}`));
    });
  });
}

function stopChildren() {
  for (const child of children) {
    if (!child.killed) child.kill('SIGTERM');
  }
}

process.on('SIGINT', () => {
  stopChildren();
  process.exit(130);
});
process.on('SIGTERM', () => {
  stopChildren();
  process.exit(143);
});

try {
  if (await isUrlUp(`${backendUrl}/design/`)) {
    console.log(`Backend already running: ${backendUrl}`);
  } else {
    start('backend', pythonBin, ['manage.py', 'runserver', `${host}:${backendPort}`], {
      cwd: backendDir,
    });
  }

  await waitForUrl(`${backendUrl}/design/`, {
    label: 'ARR backend /design/',
  });

  if (await isUrlUp(frontendUrl)) {
    console.log(`Frontend already running: ${frontendUrl}`);
  } else {
    start('frontend', 'npm', ['run', 'dev', '--', '--host', host, '--port', frontendPort, '--strictPort'], {
      cwd: frontendDir,
      env: {
        VITE_ARR_BACKEND_URL: backendUrl,
      },
    });
  }

  await waitForUrl(frontendUrl, {
    label: 'ARR frontend /design',
  });
  await verifyFrontendProxy();

  if (!noVerify) {
    await runOnce('design regulation full gate', 'node', [
      path.join(__dirname, 'run-all.mjs'),
      '--base',
      backendUrl,
    ]);
  }

  console.log('\n== Local ARR design is running');
  console.log(`Open: ${frontendUrl}`);
  console.log(`Backend: ${backendUrl}`);
  console.log('Press Ctrl+C in this terminal to stop both servers.');

  await new Promise(() => {});
} catch (error) {
  console.error(`\nstart-local failed: ${error.message}`);
  stopChildren();
  process.exit(1);
}
