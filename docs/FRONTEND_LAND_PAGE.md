1168010600109000058


# AG-frontend Land Page (Phase 4)

> Last updated: 2026-02-26

## Overview

The Land Regulation Analysis page (`/land`) is a React page in AG-frontend that lets users input an address or PNU code and receive a comprehensive regulation analysis report.

## File Structure

```
AG-frontend/src/features/land/
├── LandPage.tsx                    # Main page component
├── useLand.ts                      # TanStack Query hooks
└── components/
    ├── LandSearchForm.tsx          # Address/PNU input + zone dropdown
    ├── LandInfoCard.tsx            # PNU + address + zone + area + price
    ├── RegulationSummary.tsx       # 10 core regulations (2-column grid)
    ├── ExtendedRegulations.tsx     # 31 extended regs (3 groups, collapsible)
    ├── LawArticleList.tsx          # Related law articles (collapsible)
    ├── RestrictionsList.tsx        # Restriction badges
    └── LandStatsPanel.tsx          # Query statistics dashboard
```

## Routing

```tsx
// AG-frontend/src/app/router.tsx
const LandPage = lazy(() => import('@/features/land/LandPage').then(m => ({ default: m.LandPage })))
// children array:
{ path: 'land', element: <SuspenseWrapper><LandPage /></SuspenseWrapper> }
```

## Navigation

```tsx
// AG-frontend/src/shared/ui/Sidebar.tsx
import { MapPin } from 'lucide-react'
{ path: '/land', icon: MapPin, labelKey: 'nav.land' }
```

## API Client

All types and API methods in `src/shared/api/arrClient.ts`:

```typescript
// Key types
interface LandAnalyzeResponse {
  pnu: PnuInfo
  regulations: RegulationsResponse | null
  zone_info: ZoneInfo | null
  land_info: LandInfoResponse | null
  law_articles: LawArticlesResponse | null
  restrictions: string[]
  errors?: string[]
  warning?: string
}

// API methods
landAPI.analyze(params)  // POST /arr/land/analyze/
landAPI.resolve(params)  // POST /arr/land/resolve/
landAPI.zones()          // GET  /arr/land/zones/
landAPI.stats()          // GET  /arr/land/stats/
```

**Vite proxy**: `/arr/*` → `localhost:8000/*` (strips `/arr` prefix)

## TanStack Query Hooks (useLand.ts)

```typescript
useLandAnalyze()   // useMutation for POST /land/analyze/
useLandZones()     // useQuery, staleTime: 5min
useLandStats()     // useQuery, staleTime: 30s
```

## i18n Keys

38 keys per locale in `land.*` namespace:
- `land.title`, `land.desc`, `land.analyze`, `land.analyzing`
- `land.bcr`, `land.far`, `land.height`, `land.sunlight`, etc.
- `land.coreRegulations`, `land.extendedRegulations`, `land.lawArticles`
- `land.stats`, `land.totalQueries`, `land.avgResponse`, `land.errorCount`

Files: `src/shared/i18n/locales/en-US.json`, `src/shared/i18n/locales/ko-KR.json`

## UI Layout

```
┌─ Header: "토지 규제 분석" ──────────────────────────────────┐
│                                                             │
│ ┌─ LandSearchForm ───────────────────────────────────────┐  │
│ │ [주소 | PNU] [____input____] [분석 버튼]                │  │
│ │ Zone override: [▼ dropdown (auto-detect + 21 zones)]   │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ LandInfoCard ─────────────────────────────────────────┐  │
│ │ PNU: 11680-101-00-1-0077-0000                          │  │
│ │ Address | Zone: 일반상업지역 | Area: 497.2m²            │  │
│ │ Official Price: ₩28,620,000/m² | Land Use: 대           │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ RegulationSummary (2×5 grid) ─────────────────────────┐  │
│ │ BCR 80% | FAR 1300% | Height - | Sunlight - | Corner ✓ │  │
│ │ Road 1.5x | Line 0m | Adjacent 0.5m | Park ✓ | Land 5% │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ▶ Extended Regulations (31 items)  [collapsible]            │
│ ▶ Related Law Articles (N articles) [collapsible]           │
│                                                             │
│ ┌─ RestrictionsList ─────────────────────────────────────┐  │
│ │ [badge] [badge] [badge]                                 │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ LandStatsPanel ───────────────────────────────────────┐  │
│ │ Total: 42 | Avg: 385ms | Errors: 2 | Top: address      │  │
│ └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## E2E Tests

```bash
cd AG-frontend && npx playwright test e2e/land.spec.ts
```

16 tests across 6 describe blocks, all API-mocked (no backend needed):
- **Basic layout** (5): title, description, search form, zone dropdown, zone population
- **Stats panel** (1): renders with mock data
- **Analyze flow** (4): button enable, land info card, regulation values, law articles collapsible
- **Input type toggle** (2): PNU button switch, 19-digit auto-detect
- **Zone selection** (1): zone included in POST request body
- **Error handling** (1): API 500 error message display
- **Navigation** (1): routing from / to /land

## Conventions

- `React.memo()` on all card/list components
- `useCallback`/`useMemo` for handlers and derived state
- Semantic tokens: `text-(--color-text-secondary)`, `bg-(--color-surface-card)`
- Badge: wrapped in `<span>` (no className prop on Badge component)
- All text through i18n `useTranslation()` with `t('land.key')` pattern
- Lucide icons: MapPin, Building2, Scale, Gavel, Search, ChevronDown
