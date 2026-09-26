# Seed the hf-cache volume with the bge-m3 snapshot the host already has (4.3 GB), symlinks resolved.
# Only the live snapshot (refs/main -> 5617a9f...) is copied; the orphan partial download 9a0624b... is left behind.
# Idempotent: re-running overwrites the same files.
$ErrorActionPreference = 'Stop'
$volume = 'ace_hf-cache'
$src = Join-Path $env:USERPROFILE '.cache\huggingface\hub\models--BAAI--bge-m3'
$snapshot = (Get-Content (Join-Path $src 'refs\main') -Raw).Trim()
if (-not (Test-Path (Join-Path $src "snapshots\$snapshot"))) { throw "snapshot $snapshot missing under $src" }
docker volume create $volume | Out-Null
# cp -rL resolves the blob symlinks; on some Windows mounts they appear as plain files already, which cp also accepts.
docker run --rm -v "${volume}:/hf" -v "${src}:/src:ro" alpine:3.20 sh -c @"
set -e
M=/hf/hub/models--BAAI--bge-m3
mkdir -p `$M/snapshots `$M/refs
cp /src/refs/main `$M/refs/main
cp -rL /src/snapshots/$snapshot `$M/snapshots/
chown -R 1000:1000 /hf
du -sh `$M
ls -la `$M/snapshots/$snapshot
"@
if ($LASTEXITCODE -ne 0) { throw "seed failed" }
Write-Host "seeded $volume with snapshot $snapshot"
