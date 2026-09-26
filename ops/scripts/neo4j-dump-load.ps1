# Move the Desktop Enterprise graph into the compose volume by dump/load (never a raw file copy).
# Precondition: the Desktop DBMS is STOPPED (7687 not listening) - neo4j-admin needs the store offline.
# The Desktop data directory is mounted read-only, so the original is never touched; the dump is also the first backup.
#
#   powershell -File ops/scripts/neo4j-dump-load.ps1 -Step dump    # Desktop data -> D:\ace-neo4j\dumps\neo4j.dump
#   powershell -File ops/scripts/neo4j-dump-load.ps1 -Step load    # dump -> compose volume (server not running)
#   powershell -File ops/scripts/neo4j-dump-load.ps1 -Step verify  # start the container, compare to the desktop baseline
param([Parameter(Mandatory)][ValidateSet('dump', 'load', 'verify')][string]$Step)
$ErrorActionPreference = 'Stop'
$ops = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$image = 'neo4j:2025.08.0-enterprise'   # exactly the Desktop version; a newer image would upgrade the store on first start
$desktop = Join-Path $env:USERPROFILE '.Neo4jDesktop2\Data\dbmss\dbms-23e9404b-8efc-4706-adc0-90e1c20445ab'
$dumps = 'D:\ace-neo4j\dumps'

function Assert-PortFree([int]$port) {
    $held = netstat -ano | Select-String ":$port\s" | Select-String 'LISTENING'
    if ($held) { throw "port $port is still held:`n$held`nStop the Desktop DBMS (or the container) first." }
}

switch ($Step) {
    'dump' {
        Assert-PortFree 7687
        New-Item -ItemType Directory -Path $dumps -Force | Out-Null
        docker run --rm -v "${desktop}\data:/data:ro" -v "${dumps}:/dumps" -e NEO4J_ACCEPT_LICENSE_AGREEMENT=yes `
            $image neo4j-admin database dump neo4j --to-path=/dumps --overwrite-destination=true
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
