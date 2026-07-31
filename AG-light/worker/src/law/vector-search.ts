/**
 * Vector Search — semantic search over law articles via Cloudflare Vectorize.
 *
 * Vectors are built by scripts/build-vectors.ts:
 *   법제처 API → 조문 텍스트 → Jina jina-embeddings-v3 (1024-dim) → Vectorize
 *
 * Metadata stored per vector:
 *   { law_name, law_type, article, content (truncated) }
 */

import type { Env } from "../index";

export interface VectorResult {
  id: string;
  score: number;
  law_name: string;
  law_type: string;
  article: string;
  content: string;
}

/**
 * Embed a query string using Jina and search Vectorize.
 */
export async function semanticSearch(
  query: string,
  topK: number,
  env: Env,
): Promise<VectorResult[]> {
  if (!env.JINA_API_KEY || !env.LAW_VECTORS) {
    return [];
  }

  // 1. Embed query
  const vector = await embedQuery(query, env.JINA_API_KEY);
  if (!vector) return [];

  // 2. Query Vectorize
  const matches = await env.LAW_VECTORS.query(vector, {
    topK,
    returnMetadata: "all",
  });

  // 3. Map results
  return (matches.matches ?? []).map((m) => ({
    id: m.id,
    score: m.score ?? 0,
    law_name: String(m.metadata?.law_name ?? ""),
    law_type: String(m.metadata?.law_type ?? ""),
    article: String(m.metadata?.article ?? ""),
    content: String(m.metadata?.content ?? ""),
  }));
}

/**
 * Call Jina Embeddings API (jina-embeddings-v3, 1024-dim).
 */
async function embedQuery(
  text: string,
  apiKey: string,
): Promise<number[] | null> {
  try {
    const resp = await fetch("https://api.jina.ai/v1/embeddings", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "jina-embeddings-v3",
        input: [text],
        dimensions: 1024,
        task: "retrieval.query",
      }),
      signal: AbortSignal.timeout(10_000),
    });

    if (!resp.ok) return null;

    const data = (await resp.json()) as {
      data: Array<{ embedding: number[] }>;
    };
    return data.data[0]?.embedding ?? null;
  } catch {
    return null;
  }
}

/**
 * Simple Reciprocal Rank Fusion for merging two ranked lists.
 * k=60 (standard RRF constant).
 */
export function rrf<T extends { id: string }>(
  listA: T[],
  listB: T[],
  k = 60,
): T[] {
  const scores = new Map<string, { score: number; item: T }>();

  for (let i = 0; i < listA.length; i++) {
    const item = listA[i];
    const prev = scores.get(item.id);
    const s = 1 / (k + i + 1);
    scores.set(item.id, {
      score: (prev?.score ?? 0) + s,
      item: prev?.item ?? item,
    });
  }

  for (let i = 0; i < listB.length; i++) {
    const item = listB[i];
    const prev = scores.get(item.id);
    const s = 1 / (k + i + 1);
    scores.set(item.id, {
      score: (prev?.score ?? 0) + s,
      item: prev?.item ?? item,
    });
  }

  return [...scores.values()]
    .sort((a, b) => b.score - a.score)
    .map((e) => e.item);
}
