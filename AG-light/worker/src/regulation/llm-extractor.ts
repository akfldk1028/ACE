/**
 * LLM Extractor — 법조문 텍스트에서 규제 수치를 structured JSON으로 추출.
 * Port of: ARR/backend/land/services/law_enricher.py (extract_regulation_values)
 *          ARR/backend/land/data/regulation_prompts.py
 *
 * Flow: zone_names + regulation_type → Worker /law/search → 조문 수집
 *       → OpenAI gpt-4o-mini → JSON 파싱 → regulation_calculator 호환 dict
 *       → 실패 시 null (caller falls back to static JSON)
 */

import type { Env } from "../index";
import type { RegulationResult } from "./calculator";

// ── Prompts ─────────────────────────────────────────────

const SYSTEM_PROMPT =
  "당신은 한국 건축법규 전문가입니다. " +
  "법조문 텍스트에서 규제 수치를 정확히 추출하여 JSON으로 반환합니다. " +
  "추측하지 말고, 조문에 명시된 수치만 추출하세요. " +
  "조문에 없는 정보는 null로 표시하세요.";

const SUNLIGHT_PROMPT = `다음은 건축법 시행령 제86조(일조 등의 확보를 위한 건축물의 높이 제한) 관련 법조문입니다.

<법조문>
{article_text}
</법조문>

용도지역: {zone_name}

위 조문에서 **정북 일조사선 이격거리** 규정을 추출하세요.
반드시 아래 JSON 형식으로만 답하세요 (설명 없이 JSON만):

{
  "sunlight_applies": true/false,
  "sunlight_rules": [
    {"condition": "H <= Xm", "setback_m": Y},
    {"condition": "H > Xm", "formula": "H * Z"}
  ],
  "sunlight_article": "근거 조항 (예: 건축법 시행령 제86조제1항)",
  "applies_to_zones": ["적용되는 용도지역 목록"],
  "exceptions": ["적용 예외 사항"]
}`;

const ADJACENT_SETBACK_PROMPT = `다음은 건축법 제58조(대지 안의 공지) 및 시행령 제80조의2 관련 법조문입니다.

<법조문>
{article_text}
</법조문>

용도지역: {zone_name}

위 조문에서 **인접 대지경계선으로부터의 이격거리** 규정을 추출하세요.
반드시 아래 JSON 형식으로만 답하세요 (설명 없이 JSON만):

{
  "adjacent_setback_m": 최소이격거리(숫자),
  "adjacent_setback_article": "근거 조항",
  "height_dependent_rules": [
    {"condition": "높이 조건", "setback_m": 이격거리}
  ],
  "notes": "조례 위임 여부 등 참고사항"
}`;

const BCR_FAR_PROMPT = `다음은 국토계획법 시행령 제84조(건폐율) 및 제85조(용적률) 관련 법조문입니다.

<법조문>
{article_text}
</법조문>

용도지역: {zone_name}

위 조문에서 해당 용도지역의 **건폐율 상한**과 **용적률 상한**을 추출하세요.
반드시 아래 JSON 형식으로만 답하세요 (설명 없이 JSON만):

{
  "bcr_pct": 건폐율상한(숫자, 퍼센트),
  "bcr_article": "근거 조항",
  "far_pct": 용적률상한(숫자, 퍼센트),
  "far_article": "근거 조항",
  "notes": "조례 위임 범위 등 참고사항"
}`;

const HEIGHT_PROMPT = `다음은 건축법 제60조(건축물의 높이 제한) 관련 법조문입니다.

<법조문>
{article_text}
</법조문>

용도지역: {zone_name}

위 조문에서 해당 용도지역의 **건축물 높이 제한** 규정을 추출하세요.
반드시 아래 JSON 형식으로만 답하세요 (설명 없이 JSON만):

{
  "height_limit_m": 높이제한(숫자, 미터) 또는 null,
  "height_article": "근거 조항",
  "road_width_rule": "도로폭 기반 높이제한 규칙 (예: 도로폭 × 1.5배)",
  "notes": "참고사항"
}`;

const BUILDING_DESIGNATION_PROMPT = `다음은 국토계획법 제49조~제52조(지구단위계획) 및 건축법 제46조~제47조(건축선) 관련 법조문입니다.

<법조문>
{article_text}
</법조문>

용도지역: {zone_name}

위 조문에서 **건축지정선/건축한계선 후퇴거리** 규정을 추출하세요.
건축지정선은 지구단위계획에서 건축물이 반드시 맞닿아야 하는 선이고,
건축한계선은 건축물이 넘을 수 없는 선입니다.
반드시 아래 JSON 형식으로만 답하세요 (설명 없이 JSON만):

{
  "building_designation_setback_m": 후퇴거리(숫자, 미터) 또는 null,
  "building_designation_article": "근거 조항",
  "line_type": "지정선" 또는 "한계선" 또는 null,
  "notes": "참고사항"
}`;

// ── Config ──────────────────────────────────────────────

interface ExtractionConfig {
  queries: string[];
  prompt: string;
}

const EXTRACTION_CONFIG: Record<string, ExtractionConfig> = {
  sunlight: {
    queries: [
      "정북 일조사선 이격거리",
      "건축법 시행령 제86조 일조",
      "정북방향 인접 대지경계선 높이",
    ],
    prompt: SUNLIGHT_PROMPT,
  },
  adjacent_setback: {
    queries: [
      "대지 안의 공지 인접대지 이격거리",
      "건축법 시행령 제80조의2",
      "인접 대지경계선 건축물 이격",
    ],
    prompt: ADJACENT_SETBACK_PROMPT,
  },
  bcr_far: {
    queries: [
      "{zone_name} 건폐율 용적률",
      "국토계획법 시행령 제84조 건폐율",
      "국토계획법 시행령 제85조 용적률",
    ],
    prompt: BCR_FAR_PROMPT,
  },
  height: {
    queries: [
      "건축물 높이제한 가로구역별",
      "건축법 제60조 높이 제한",
    ],
    prompt: HEIGHT_PROMPT,
  },
  building_designation: {
    queries: [
      "건축지정선 건축한계선",
      "지구단위계획 건축선 후퇴",
      "국토계획법 제52조 지구단위계획 건축물",
    ],
    prompt: BUILDING_DESIGNATION_PROMPT,
  },
};

// ── Cache ───────────────────────────────────────────────

const extractionCache = new Map<string, Record<string, unknown>>();
const CACHE_MAX_SIZE = 100;

// ── Main ────────────────────────────────────────────────

export type RegulationType = keyof typeof EXTRACTION_CONFIG;

/**
 * 법조문 검색 → LLM structured extraction → 규제 수치 dict.
 * Returns null on failure (caller should fall back to static JSON).
 */
export async function extractRegulationValues(
  zoneNames: string[],
  regulationType: RegulationType,
  env: Env,
): Promise<Record<string, unknown> | null> {
  if (!env.OPENAI_API_KEY) return null;

  const cfg = EXTRACTION_CONFIG[regulationType];
  if (!cfg) return null;

  const zoneKey = [...zoneNames].sort().join(",");
  const cacheKey = `${zoneKey}:${regulationType}`;
  const cached = extractionCache.get(cacheKey);
  if (cached) return cached;

  // Step 1: 관련 법조문 텍스트 수집
  const articleTexts = await fetchArticleTexts(cfg.queries, zoneNames, env);
  if (articleTexts.length === 0) return null;

  // Step 2: LLM extraction
  const zoneName = zoneNames[0] ?? "";
  const combinedText = articleTexts.slice(0, 5).join("\n\n---\n\n");
  const prompt = cfg.prompt
    .replace("{article_text}", combinedText)
    .replace("{zone_name}", zoneName);

  const result = await callLlmExtraction(prompt, env.OPENAI_API_KEY);

  if (result !== null) {
    if (extractionCache.size >= CACHE_MAX_SIZE) extractionCache.clear();
    extractionCache.set(cacheKey, result);
  }

  return result;
}

// ── Internals ───────────────────────────────────────────

async function fetchArticleTexts(
  queries: string[],
  zoneNames: string[],
  env: Env,
): Promise<string[]> {
  const texts: string[] = [];
  const seen = new Set<string>();
  const zoneName = zoneNames[0] ?? "";

  // Prefer Vectorize semantic search (returns actual content in metadata)
  if (env.LAW_VECTORS && env.JINA_API_KEY) {
    const { semanticSearch } = await import("../law/vector-search");
    for (const queryTemplate of queries) {
      const query = queryTemplate.includes("{zone_name}")
        ? queryTemplate.replace("{zone_name}", zoneName)
        : queryTemplate;

      try {
        const results = await semanticSearch(query, 3, env);
        for (const r of results) {
          if (r.content && !seen.has(r.id)) {
            seen.add(r.id);
            const header = r.law_name ? `[${r.law_name} ${r.article}]` : "";
            texts.push(header ? `${header}\n${r.content}` : r.content);
          }
        }
      } catch {
        continue;
      }
    }
    if (texts.length > 0) return texts;
  }

  // Fallback: law search API (returns metadata only — less useful for LLM)
  for (const queryTemplate of queries) {
    const query = queryTemplate.includes("{zone_name}")
      ? queryTemplate.replace("{zone_name}", zoneName)
      : queryTemplate;

    try {
      const { searchLawArticles } = await import("../law/enricher");
      const res = await searchLawArticles(query, 3, env);

      for (const r of res.results) {
        const key = r.lawId + r.mst;
        if (!seen.has(key)) {
          seen.add(key);
          texts.push(`[${r.lawName}] ${r.lawType}`);
        }
      }
    } catch {
      continue;
    }
  }

  return texts;
}

async function callLlmExtraction(
  prompt: string,
  openaiApiKey: string,
): Promise<Record<string, unknown> | null> {
  try {
    const resp = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${openaiApiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        messages: [
          { role: "system", content: SYSTEM_PROMPT },
          { role: "user", content: prompt },
        ],
        temperature: 0,
        response_format: { type: "json_object" },
      }),
      signal: AbortSignal.timeout(30_000),
    });

    if (!resp.ok) return null;

    const data = await resp.json() as {
      choices: Array<{ message: { content: string | null } }>;
    };
    const content = data.choices?.[0]?.message?.content;
    if (!content) return null;

    const parsed = JSON.parse(content);
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
      return null;
    }

    // Validate critical field types (LLM may return wrong types)
    if (!validateExtractionResult(parsed)) return null;

    return parsed as Record<string, unknown>;
  } catch {
    return null;
  }
}

function validateExtractionResult(parsed: Record<string, unknown>): boolean {
  // Boolean fields
  for (const key of ["sunlight_applies"]) {
    if (key in parsed && typeof parsed[key] !== "boolean") return false;
  }

  // List fields
  for (const key of ["sunlight_rules", "applies_to_zones", "exceptions", "height_dependent_rules"]) {
    if (key in parsed && !Array.isArray(parsed[key])) return false;
  }

  // Numeric fields (nullable)
  for (const key of ["adjacent_setback_m", "bcr_pct", "far_pct", "height_limit_m", "building_designation_setback_m"]) {
    if (key in parsed && parsed[key] !== null) {
      if (typeof parsed[key] !== "number") return false;
    }
  }

  return true;
}

// ── Public: 3-tier LLM Enhancement ──────────────────────

/**
 * 3-tier override 마지막 단계: LLM 법조문 → regulations 보강.
 *
 * Guards:
 * - sunlight: LLM cannot flip applies False→True (zone applicability = static fact)
 * - adjacent_setback: only override if LLM returns numeric value
 * - building_designation: only attempt if already applies
 */
export async function enhanceWithLlm(
  regulations: RegulationResult,
  zoneNames: string[],
  env: Env,
): Promise<void> {
  const [sunR, adjR, desR] = await Promise.allSettled([
    regulations.sunlight_applies
      ? extractRegulationValues(zoneNames, "sunlight", env)
      : Promise.resolve(null),
    extractRegulationValues(zoneNames, "adjacent_setback", env),
    regulations.building_designation_applies
      ? extractRegulationValues(zoneNames, "building_designation", env)
      : Promise.resolve(null),
  ]);

  if (sunR.status === "fulfilled" && sunR.value) {
    const ex = sunR.value;
    if (Array.isArray(ex.sunlight_rules) && ex.sunlight_rules.length > 0) {
      regulations.sunlight_rules = ex.sunlight_rules as RegulationResult["sunlight_rules"];
    }
    if (typeof ex.sunlight_article === "string" && ex.sunlight_article) {
      regulations.sunlight_article = ex.sunlight_article;
    }
    regulations.sunlight_source = "law_text";
  }

  if (adjR.status === "fulfilled" && adjR.value) {
    const ex = adjR.value;
    if (typeof ex.adjacent_setback_m === "number") {
      regulations.adjacent_setback_m = ex.adjacent_setback_m;
      regulations.adjacent_setback_source = "law_text";
    }
    if (typeof ex.adjacent_setback_article === "string" && ex.adjacent_setback_article) {
      regulations.adjacent_setback_article = ex.adjacent_setback_article;
    }
  }

  if (desR.status === "fulfilled" && desR.value) {
    const ex = desR.value;
    if (typeof ex.building_designation_setback_m === "number") {
      regulations.building_designation_setback_m = ex.building_designation_setback_m;
      regulations.building_designation_source = "law_text";
    }
    if (typeof ex.building_designation_article === "string" && ex.building_designation_article) {
      regulations.building_designation_article = ex.building_designation_article;
    }
  }
}
