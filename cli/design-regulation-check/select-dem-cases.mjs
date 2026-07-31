#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';

function argValue(name, fallback) {
  const idx = process.argv.indexOf(name);
  return idx >= 0 && process.argv[idx + 1] ? process.argv[idx + 1] : fallback;
}

const inputFile = argValue('--input', 'cli/design-regulation-check/out/pnu-9-design-check.json');
const sourceCasesFile = argValue('--cases', 'cli/design-regulation-check/pnu-9-cases.json');
const outFile = argValue('--out', 'cli/design-regulation-check/out/pnu-9-dem-cases.json');
const requiredSource = argValue('--source', 'ngii_local_dem');

const [summary, sourceCases] = await Promise.all([
  fs.readFile(inputFile, 'utf8').then(JSON.parse),
  fs.readFile(sourceCasesFile, 'utf8').then(JSON.parse),
]);

const byInput = new Map(sourceCases.map((c) => [c.input, c]));
const selected = [];
const rejected = [];

for (const result of summary.results || []) {
  const source = result.datum?.elevation_source || null;
  const candidate = byInput.get(result.input) || byInput.get(result.pnu);
  const row = {
    name: result.name,
    input: result.input,
    pnu: result.pnu,
    source,
    datum: result.datum?.elevation_m ?? null,
    roadDatum: result.datum?.road_datum_m ?? null,
    neighborDatum: result.datum?.neighbor_datum_m ?? null,
    keys: result.keys || [],
  };
  if (source === requiredSource && candidate) {
    selected.push({ ...candidate, input: result.pnu || candidate.input });
  } else {
    rejected.push(row);
  }
}

const payload = {
  inputFile,
  requiredSource,
  selectedCount: selected.length,
  rejectedCount: rejected.length,
  selected,
  rejected,
};

await fs.mkdir(path.dirname(outFile), { recursive: true });
await fs.writeFile(outFile, `${JSON.stringify(payload, null, 2)}\n`);
console.table([
  ...selected.map((c) => ({ result: 'SELECT', name: c.name, input: c.input })),
  ...rejected.map((r) => ({ result: 'SKIP', name: r.name, input: r.pnu || r.input, source: r.source })),
]);
console.log(`Wrote ${outFile}`);

if (selected.length === 0) {
  process.exit(1);
}
