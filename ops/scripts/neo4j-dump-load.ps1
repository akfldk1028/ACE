# Move the Desktop Enterprise graph into the compose volume by dump/load (never a raw file copy).
# Precondition: the Desktop DBMS is STOPPED (7687 not listening) - neo4j-admin needs the store offline.
#
# What the 2026-09-26 cutover taught, and this script encodes:
#   * neo4j-admin dump WRITES into the store directory (lock + metadata), so a read-only mount of the Desktop
#     data fails with "You do not have permission to dump the database". The Desktop data is therefore copied
#     to D:\ace-neo4j\desktop-copy first (robocopy, ~90 s for 2.8 GB) and the dump runs on the copy; the original
#     is never opened for writing.
#   * The image entrypoint chowns /data and refuses a directory it cannot write, so neo4j-admin is invoked
#     directly with --entrypoint for the dump. The load goes through compose (named volume, writable).
#   * Under Git Bash, docker arguments starting with / get rewritten to C:\Program Files\Git\...; set
#     MSYS_NO_PATHCONV=1 there. PowerShell needs nothing.
#
#   powershell -File ops/scripts/neo4j-dump-load.ps1 -Step dump    # Desktop data -> copy -> D:\ace-neo4j\dumps\neo4j.dump
#   powershell -File ops/scripts/neo4j-dump-load.ps1 -Step load    # dump -> compose volume (server not running)
#   powershell -File ops/scripts/neo4j-dump-load.ps1 -Step verify  # start the container, compare to the desktop baseline
param([Parameter(Mandatory)][ValidateSet('dump', 'load', 'verify')][string]$Step)
$ErrorActionPreference = 'Stop'
$ops = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$image = 'neo4j:2025.08.0-enterprise'   # exactly the Desktop version; a newer image would upgrade the store on first start
$desktop = Join-Path $env:USERPROFILE '.Neo4jDesktop2\Data\dbmss\dbms-23e9404b-8efc-4706-adc0-90e1c20445ab'
$copy = 'D:\ace-neo4j\desktop-copy\data'
$dumps = 'D:\ace-neo4j\dumps'

function Assert-PortFree([int]$port) {
    $held = netstat -ano | Select-String ":$port\s" | Select-String 'LISTENING'
    if ($held) { throw "port $port is still held:`n$held`nStop the Desktop DBMS (or the container) first." }
}

switch ($Step) {
    'dump' {
        Assert-PortFree 7687
        New-Item -ItemType Directory -Path $dumps, $copy -Force | Out-Null
        robocopy (Join-Path $desktop 'data') $copy /E /NFL /NDL /NJH /R:1 /W:1 | Out-Null
        if ($LASTEXITCODE -ge 8) { throw "robocopy failed ($LASTEXITCODE)" }   # 0-7 are success codes
        docker run --rm --entrypoint /var/lib/neo4j/bin/neo4j-admin -v "${copy}:/data" -v "${dumps}:/dumps" `
            -e NEO4J_ACCEPT_LICENSE_AGREEMENT=yes $image database dump neo4j --to-path=/dumps --overwrite-destination=true
        if ($LASTEXITCODE -ne 0) { throw 'dump failed' }
        Get-ChildItem $dumps | Format-Table Name, @{n = 'MB'; e = { [int]($_.Length / 1MB) } }, LastWriteTime
    }
    'load' {
        Assert-PortFree 7687
        if (-not (Test-Path (Join-Path $dumps 'neo4j.dump'))) { throw "no dump at $dumps\neo4j.dump - run -Step dump first" }
        Push-Location $ops
        try {
            docker compose create neo4j
            if ($LASTEXITCODE -ne 0) { throw 'compose create failed' }
            docker compose run --rm --no-deps -v "${dumps}:/dumps" neo4j `
                neo4j-admin database load neo4j --from-path=/dumps --overwrite-destination=true
            if ($LASTEXITCODE -ne 0) { throw 'load failed' }
        } finally { Pop-Location }
    }
    'verify' {
        Push-Location $ops
        try {
            docker compose up -d --wait neo4j
            if ($LASTEXITCODE -ne 0) { throw 'neo4j did not become healthy' }
        } finally { Pop-Location }
        $py = Join-Path $ops '..\agents\Lawagent\server\law-search\.venv\Scripts\python.exe'
        & $py -X utf8 (Join-Path $ops 'baseline\neo4j_baseline.py') container
        $day = (Get-Date).ToString('yyyy-MM-dd')
        $a = Get-Content (Join-Path $ops "baseline\neo4j-$day-desktop.json") -Raw | ConvertFrom-Json
        $b = Get-Content (Join-Path $ops "baseline\neo4j-$day-container.json") -Raw | ConvertFrom-Json
        $diff = @()
        foreach ($k in $a.counts.PSObject.Properties.Name) {
            if ($a.counts.$k -ne $b.counts.$k) { $diff += "$k desktop=$($a.counts.$k) container=$($b.counts.$k)" }
        }
        $ia = ($a.vector_indexes | ForEach-Object { "$($_.name):$($_.state)" }) -join ','
        $ib = ($b.vector_indexes | ForEach-Object { "$($_.name):$($_.state)" }) -join ','
        if ($ia -ne $ib) { $diff += "vector indexes desktop=[$ia] container=[$ib]" }
        if ($diff) { Write-Host "MISMATCH:`n  $($diff -join "`n  ")"; exit 1 }
        Write-Host "container graph matches the desktop baseline ($($a.counts.nodes) nodes, $($a.counts.relationships) relationships, $($a.vector_indexes.Count) vector indexes)"
    }
}
