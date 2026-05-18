import { Hono } from "hono";
import type { Env } from "../index";
import { searchLawArticles } from "../law";
import { semanticSearch, rrf, type VectorResult } from "../law";

export const searchRoutes = new Hono<{ Bindings: Env }>();

/**
 * POST /search
 * Body: { query: string, limit?: number, mode?: "hybrid"|"keyword"|"semantic" }
 *
 * hybrid (default): Vectorize semantic + 법제처 keyword → RRF merge
 * keyword: 법제처 API keyword only
 * semantic: Vectorize only
 */
searchRoutes.post("/", async (c) => {
  const body = await c.req.json().catch(() => null);
  if (!body || typeof body !== "object") {
    return c.json({ error: "Invalid JSON body" }, 400);
  }

  const { query, limit = 10, mode = "hybrid" } = body as Record<string, unknown>;

  if (!query || typeof query !== "string") {
    return c.json({ error: "query is required" }, 400);
  }

  const n = Math.min(Math.max(typeof limit === "number" ? limit : 10, 1), 50);
  const searchMode = typeof mode === "string" ? mode : "hybrid";

  // Semantic search (Vectorize)
  let vectorResults: VectorResult[] = [];
  if (searchMode !== "keyword") {
    vectorResults = await semanticSearch(query, n * 2, c.env);
  }

  // Keyword search (korean-law-mcp)
  let keywordResults: Array<{ id: string; lawName: string; lawId: string; mst: string; lawType: string }> = [];
  if (searchMode !== "semantic") {
    const mcpRes = await searchLawArticles(query, n, c.env);
    keywordResults = mcpRes.results.map((r) => ({
      id: `mcp_${r.mst}_${r.lawId}`,
      ...r,
    }));
  }

  // Merge
  if (searchMode === "hybrid" && vectorResults.length > 0 && keywordResults.length > 0) {
    const merged = rrf(
      vectorResults.map((v) => ({ ...v })),
      keywordResults.map((k) => ({
        id: k.id,
        score: 0,
        law_name: k.lawName,
        law_type: k.lawType,
        article: "",
        content: "",
      })),
    );
    return c.json({
      results: merged.slice(0, n),
      mode: "hybrid",
      stats: {
        vector_count: vectorResults.length,
        keyword_count: keywordResults.length,
        merged_count: merged.length,
      },
    });
  }

  // Single mode
  if (vectorResults.length > 0) {
    return c.json({
      results: vectorResults.slice(0, n),
      mode: "semantic",
      stats: { vector_count: vectorResults.length },
    });
  }

  return c.json({
    results: keywordResults.slice(0, n),
    mode: "keyword",
    stats: { keyword_count: keywordResults.length },
  });
});
