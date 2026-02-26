# Multi-Agent Teams

> Last updated: 2026-02-26

## Team 039: Land Swarm Analysis Team (Phase 5)

**File**: `JSON_MODULES/teams/039_Land_Swarm_Analysis_Team.json`

### Architecture

6-agent SelectorGroupChat with phased routing:

```
User Query ("서울시 강남구 역삼동 677 토지 분석")
    │
    ├── Phase 1: land_analyst
    │   └── PNU resolve → zone lookup → regulation calculation
    │
    ├── Phase 2: legal_interpreter
    │   └── Law article search → compliance analysis
    │
    ├── Phase 3: regulatory_monitor
    │   └── Recent regulation changes → pending policy alerts
    │
    ├── Phase 4: spatial_analyzer
    │   └── Adjacent parcel zones → zone transition analysis
    │
    ├── Phase 5: market_analyst
    │   └── Development potential → risk assessment
    │
    └── Phase 6: report_writer
        └── Comprehensive Korean report (7 sections) → TERMINATE
```

### Agent Specifications

| Agent | Role | Tools | Output |
|-------|------|-------|--------|
| `land_analyst` | PNU/zone/regulation lookup | arr_land_analyze, arr_land_resolve | Land data + regulations |
| `legal_interpreter` | Law article interpretation | law_search, law_search_domain | Compliance findings |
| `regulatory_monitor` | Regulation change tracking | law_search (recent amendments) | Change alerts |
| `spatial_analyzer` | Adjacent parcel analysis | arr_land_zones, arr_land_analyze | Spatial context |
| `market_analyst` | Development feasibility | (no tools - synthesis) | Risk/opportunity |
| `report_writer` | Final report generation | get_shared_data, store_decision | 7-section report |

### Report Structure (7 Sections)

1. 토지 기본정보 (Land basics)
2. 용도지역 및 규제 (Zoning & regulations)
3. 법적 근거 분석 (Legal basis)
4. 인접지역 분석 (Adjacent area)
5. 규제 변경/예고 (Regulatory changes)
6. 개발 가능성 (Development potential)
7. 종합 의견 (Summary opinion)

### Configuration

- Pattern: `SelectorGroupChat` (not Swarm — more practical with existing tool definitions)
- Max messages: 25
- Termination: Text "TERMINATE"
- Model: `gpt-4o` for selector, per-agent models configurable
- SharedMemory keys: `land_pnu`, `land_zoning`, `legal_findings`, `spatial_context`, `market_assessment`, `regulatory_alerts`

### How to Use

```bash
# 1. Register team in AutoGen Studio
# POST http://localhost:8081/api/teams/ with 039 JSON body

# 2. Execute via Playground
# Select "039_Land_Swarm_Analysis_Team"
# Input: "서울시 강남구 역삼동 677 토지 건축 규제 분석"

# 3. Or via ACE MCP
# Use execute_team tool with team name and task
```

## Team 038: Land Analysis Team (Legacy)

**File**: `JSON_MODULES/teams/038_Land_Analysis_Team.json`

3-agent SelectorGroupChat (simpler, static lookup only):
- land_analyst, legal_interpreter, report_writer
- No spatial analysis, no market analysis, no regulatory monitoring

## Other Teams

98 team JSON files in `JSON_MODULES/` covering various agent configurations. See `JSON_MODULES/` directory for full list.
