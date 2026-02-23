// ============================================================
// ARR Backend API Client - Land Regulation Analysis
// Proxied via Vite: /arr/* -> localhost:8000/*
// ============================================================

const ARR_BASE = '/arr'

// --------------- Types ---------------

export interface PnuInfo {
  pnu: string
  sido: string
  sigungu: string
  eupmyeondong: string
  ri: string
  land_type: string
  main_number: string
  sub_number: string
}

export interface ZoneRegulation {
  zone: string
  bcr_limit: number
  far_limit: number
  category: string
}

export interface RegulationResult {
  bcr_limit: number
  far_limit: number
  zones: ZoneRegulation[]
  matched: number
  unmatched: string[]
}

export interface LawArticle {
  hang_id: string
  content: string
  law_name: string
  article: string
  similarity?: number
}

export interface LandAnalyzeResponse {
  pnu: PnuInfo
  regulation: RegulationResult
  land_info: Record<string, unknown>
  law_articles: {
    articles: LawArticle[]
    total_count: number
    errors: string[]
  }
  restrictions: string[]
}

export interface LandAnalyzeRequest {
  input: string
  input_type: 'pnu' | 'address'
  zones?: string[]
  include_law?: boolean
}

export interface LandResolveRequest {
  input: string
  input_type: 'pnu' | 'address'
}

export interface LandResolveResponse {
  valid?: boolean
  parsed?: Record<string, string>
  pnu?: string
  error?: string
}

export interface LandZone {
  zone_name: string
  bcr_default: number
  far_default: number
  category: string
}

export interface LandStats {
  total_queries: number
  avg_response_time_ms: number
  by_input_type: Array<{ input_type: string; count: number }>
  error_count: number
}

export interface LandZonesResponse {
  zones: LandZone[]
  count: number
}

// --------------- Fetch Helper ---------------

async function arrFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${ARR_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers as Record<string, string>),
    },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.error ?? `${res.status} ${res.statusText}`)
  }
  return res.json()
}

// --------------- Land API ---------------

export const landAPI = {
  analyze: (req: LandAnalyzeRequest) =>
    arrFetch<LandAnalyzeResponse>('/land/analyze/', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  resolve: (req: LandResolveRequest) =>
    arrFetch<LandResolveResponse>('/land/resolve/', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  zones: () => arrFetch<LandZonesResponse>('/land/zones/'),

  stats: () => arrFetch<LandStats>('/land/stats/'),
}
