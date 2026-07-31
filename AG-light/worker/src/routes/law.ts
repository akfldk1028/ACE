/**
 * /law/* routes — 법제처 API 직접 호출 (korean-law-mcp 원본 코드 흡수)
 *
 * LawApiClient + xml-parser + search-normalizer + article-parser 등
 * korean-law-mcp 원본 lib 파일 그대로 사용.
 */

import { Hono } from "hono";
import type { Env } from "../index";
import { LawApiClient } from "../lib/law-api-client";
import { parseSearchXML, extractTag, stripHtml } from "../lib/xml-parser";
import { lawCache } from "../lib/cache";
import { cleanHtml, formatArticleUnit } from "../lib/article-parser";
import { buildJO } from "../lib/law-parser";

export const lawRoutes = new Hono<{ Bindings: Env }>();

/** POST /law/search — 법령 ���색 (원본 search.ts 로직) */
lawRoutes.post("/search", async (c) => {
  const body = await c.req.json().catch(() => null);
  if (!body || typeof body !== "object") return c.json({ error: "Invalid JSON" }, 400);

  const { query, display = 20 } = body as Record<string, unknown>;
  if (!query || typeof query !== "string") return c.json({ error: "query required" }, 400);

  const client = new LawApiClient({ apiKey: c.env.LAW_OC });
  try {
    const cacheKey = `search:${(query as string).toLowerCase().trim()}:${display}`;
    const cached = lawCache.get<object>(cacheKey);
    if (cached) return c.json(cached);

    const xmlText = await client.searchLaw(query);
    const parsed = parseSearchXML(xmlText, "LawSearch", "law", (content) => ({
      lawName: stripHtml(extractTag(content, "법령명한글")),
      lawId: extractTag(content, "법령ID"),
      mst: extractTag(content, "법령일련번호"),
      promDate: extractTag(content, "공포일자"),
      lawType: extractTag(content, "법령구분명"),
    }));

    const result = { results: parsed.items.slice(0, Number(display) || 20), total: parsed.totalCnt };
    lawCache.set(cacheKey, result, 60 * 60 * 1000);
    return c.json(result);
  } catch (e) {
    return c.json({ error: String(e), results: [] }, 502);
  }
});

/** POST /law/text — 법령 조문 전문 (원본 law-text.ts 로직) */
lawRoutes.post("/text", async (c) => {
  const body = await c.req.json().catch(() => null);
  if (!body || typeof body !== "object") return c.json({ error: "Invalid JSON" }, 400);

  const { mst, lawId, jo } = body as Record<string, unknown>;
  if (!mst && !lawId) return c.json({ error: "mst or lawId required" }, 400);

  // JO 코드 변환: "제38조" → "003800" (원본 law-text.ts 로직)
  let joCode = jo as string | undefined;
  if (joCode && /제\d+조/.test(joCode)) {
    try { joCode = buildJO(joCode); } catch { /* keep original */ }
  }

  const client = new LawApiClient({ apiKey: c.env.LAW_OC });
  try {
    const cacheKey = `lawtext:${mst || lawId}:${joCode || "full"}`;
    const cached = lawCache.get<string>(cacheKey);
    if (cached) return c.json({ text: cached });

    const jsonText = await client.getLawText({
      mst: mst as string | undefined,
      lawId: lawId as string | undefined,
      jo: joCode,
    });

    const json = JSON.parse(jsonText);
    const lawData = json?.법령;
    if (!lawData) return c.json({ error: "법령 데이터를 찾을 수 없습니���." }, 404);

    // 조문 파싱 (원본 article-parser 사용)
    const rawUnits = lawData.조문?.조문단위;
    const articleUnits: unknown[] = Array.isArray(rawUnits) ? rawUnits : rawUnits ? [rawUnits] : [];

    let resultText = "";
    const basicInfo = lawData.기본정보 || lawData;
    const lawName = basicInfo?.법령명_한글 || basicInfo?.법령명한글 || "";
    if (lawName) resultText += `법령명: ${lawName}\n\n`;

    for (const unit of articleUnits) {
      const formatted = formatArticleUnit(unit as Parameters<typeof formatArticleUnit>[0]);
      if (formatted) {
        resultText += `${formatted.header}\n${formatted.body}\n\n`;
      }
    }

    lawCache.set(cacheKey, resultText, 24 * 60 * 60 * 1000);
    return c.json({ text: resultText, lawName, articleCount: articleUnits.length });
  } catch (e) {
    return c.json({ error: String(e) }, 502);
  }
});

/** POST /law/article — 조문 상세 (원본 article-detail.ts 로직) */
lawRoutes.post("/article", async (c) => {
  const body = await c.req.json().catch(() => null);
  if (!body || typeof body !== "object") return c.json({ error: "Invalid JSON" }, 400);

  const { mst, lawId, jo, hang, ho, mok } = body as Record<string, unknown>;
  if (!jo) return c.json({ error: "jo required" }, 400);
  if (!mst && !lawId) return c.json({ error: "mst or lawId required" }, 400);

  // JO 코드 변환 (원본 article-detail.ts 로직)
  let joCode = jo as string;
  if (/제\d+조/.test(joCode)) {
    try { joCode = buildJO(joCode); } catch { /* keep original */ }
  }

  const client = new LawApiClient({ apiKey: c.env.LAW_OC });
  try {
    // fetchApi with extraParams — hang/ho/mok 전달 (원본 article-detail.ts 로직)
    const extraParams: Record<string, string> = {};
    if (mst) extraParams.MST = String(mst);
    if (lawId) extraParams.ID = String(lawId);
    extraParams.JO = joCode;
    if (hang) extraParams.HANG = String(hang);
    if (ho) extraParams.HO = String(ho);
    if (mok) extraParams.MOK = String(mok);

    const jsonText = await client.fetchApi({
      endpoint: "lawService.do",
      target: "eflaw",
      type: "JSON",
      extraParams,
    });

    const json = JSON.parse(jsonText);
    const lawData = json?.법령;
    if (!lawData) return c.json({ error: "법령 데이터를 찾을 수 없습니다." }, 404);

    const basicInfo = lawData.기본정보 || lawData;
    const lawName = basicInfo?.법령명_한글 || basicInfo?.법령명한글 || "";

    const rawUnits = lawData.조문?.조문단위;
    const articleUnits: unknown[] = Array.isArray(rawUnits) ? rawUnits : rawUnits ? [rawUnits] : [];

    let resultText = `법령명: ${lawName}\n\n`;
    for (const unit of articleUnits) {
      const formatted = formatArticleUnit(unit as Parameters<typeof formatArticleUnit>[0]);
      if (formatted) {
        resultText += `${formatted.header}\n${formatted.body}\n\n`;
      }
    }

    return c.json({ text: resultText, lawName });
  } catch (e) {
    return c.json({ error: String(e) }, 502);
  }
});

/** POST /law/ordinance — 자치법규 검색 (원본 ordinance-search.ts 로직) */
lawRoutes.post("/ordinance", async (c) => {
  const body = await c.req.json().catch(() => null);
  if (!body || typeof body !== "object") return c.json({ error: "Invalid JSON" }, 400);

  const { query, display = 20 } = body as Record<string, unknown>;
  if (!query || typeof query !== "string") return c.json({ error: "query required" }, 400);

  const client = new LawApiClient({ apiKey: c.env.LAW_OC });
  try {
    const xmlText = await client.searchOrdinance({
      query: query as string,
      display: Number(display) || 20,
    });

    const parsed = parseSearchXML(xmlText, "OrdinSearch", "law", (content) => ({
      ordinSeq: extractTag(content, "자치법규일련번호"),
      name: stripHtml(extractTag(content, "자치법규명")),
      organ: extractTag(content, "지자체기관명"),
      promDate: extractTag(content, "공포일자"),
      effectDate: extractTag(content, "시행일자"),
    }));

    return c.json({ results: parsed.items, total: parsed.totalCnt });
  } catch (e) {
    return c.json({ error: String(e), results: [] }, 502);
  }
});
