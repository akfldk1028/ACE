/**
 * Law Enricher — 법제처 API 직접 호출로 법조항 검색.
 * 외부 MCP 서버 의존 제거. LawApiClient + XML 파서 사용.
 *
 * 원본: ARR/backend/land/services/law_enricher.py
 */

import type { Env } from "../index";
import { LawApiClient } from "../lib/law-api-client";
import { parseSearchXML, extractTag, stripHtml } from "../lib/xml-parser";

const BASE_QUERIES = [
  "건폐율", "용적률", "건축제한", "높이제한", "일조권",
  "가각전제", "건축물 높이제한 전면도로", "건축선",
  "인접대지", "주차장", "조경", "건축지정선",
];

/**
 * 법령 검색 (단일 쿼리). 법제처 API 직접 호출.
 */
export interface LawSearchResult {
  lawName: string;
  lawId: string;
  mst: string;
  promDate: string;
  lawType: string;
}

export async function searchLawArticles(
  query: string,
  limit: number,
  env: Env,
) {
  if (!env.LAW_OC) {
    return { results: [] as LawSearchResult[], error: "LAW_OC not configured" };
  }

  const client = new LawApiClient({ apiKey: env.LAW_OC });
  try {
    const xml = await client.searchLaw(query);
    const parsed = parseSearchXML(xml, "LawSearch", "law", (content) => ({
      lawName: stripHtml(extractTag(content, "법령명한글")),
      lawId: extractTag(content, "법령ID"),
      mst: extractTag(content, "법령일련번호"),
      promDate: extractTag(content, "공포일자"),
      lawType: extractTag(content, "법령구분명"),
    }));
    return { results: parsed.items.slice(0, limit) };
  } catch (e) {
    return {
      results: [] as LawSearchResult[],
      error: e instanceof Error ? e.message : "Unknown error",
    };
  }
}

/**
 * 용도지역별 법조항 병렬 검색 (fan-out).
 */
export async function searchForZones(zoneNames: string[], env: Env) {
  const queries = [...BASE_QUERIES];
  for (const zone of zoneNames) {
    queries.push(`${zone} 건폐율`);
    queries.push(`${zone} 건축제한`);
  }

  const unique = [...new Set(queries)];
  const BATCH = 5;
  const allArticles: Array<{ query: string; results: LawSearchResult[] }> = [];
  const errors: string[] = [];

  for (let i = 0; i < unique.length; i += BATCH) {
    const batch = unique.slice(i, i + BATCH);
    const results = await Promise.allSettled(
      batch.map(async (q) => {
        const res = await searchLawArticles(q, 5, env);
        return { query: q, results: res.results };
      }),
    );

    for (const r of results) {
      if (r.status === "fulfilled" && r.value.results.length > 0) {
        allArticles.push(r.value);
      } else if (r.status === "rejected") {
        errors.push(String(r.reason));
      }
    }
  }

  return {
    articles: allArticles,
    total_count: allArticles.reduce((s, a) => s + a.results.length, 0),
    errors,
  };
}
