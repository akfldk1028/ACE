/**
 * build-vectors.ts — 법조항 임베딩 빌드 (법제처 API 직접 호출)
 *
 * 외부 의존 0. 법제처 Open API(LAW_OC) + Jina embeddings v3 (1024-dim).
 *
 * Usage:
 *   LAW_OC=hanvit4303 JINA_API_KEY=jina_... npx tsx scripts/build-vectors.ts > vectors.ndjson
 *   cd worker && npx wrangler vectorize insert law-articles --file=../vectors.ndjson
 */

const LAW_API_BASE = "https://www.law.go.kr/DRF";
const JINA_API_KEY = process.env.JINA_API_KEY ?? "";
const LAW_OC = process.env.LAW_OC ?? "";

// 18개 대상 법률 (6법 × 3 types)
const TARGET_LAWS = [
  "국토의 계획 및 이용에 관한 법률",
  "국토의 계획 및 이용에 관한 법률 시행령",
  "국토의 계획 및 이용에 관한 법률 시행규칙",
  "건축법",
  "건축법 시행령",
  "건축법 시행규칙",
  "농지법",
  "농지법 시행령",
  "농지법 시행규칙",
  "산지관리법",
  "산지관리법 시행령",
  "산지관리법 시행규칙",
  "자연공원법",
  "자연공원법 시행령",
  "자연공원법 시행규칙",
  "수도법",
  "수도법 시행령",
  "수도법 시행규칙",
];

// --- 법제처 API 호출 ---

function stripHtml(s: unknown): string {
  if (typeof s !== "string") return String(s ?? "");
  return s.replace(/<[^>]+>/g, "").trim();
}

async function searchLawMst(lawName: string): Promise<string | null> {
  const params = new URLSearchParams({
    OC: LAW_OC,
    type: "XML",
    target: "law",
    query: lawName,
  });

  const resp = await fetch(`${LAW_API_BASE}/lawSearch.do?${params}`, {
    signal: AbortSignal.timeout(15_000),
  });
  if (!resp.ok) throw new Error(`searchLaw ${resp.status}`);

  const xml = await resp.text();

  // Extract MST from first matching law
  // Pattern: <법령일련번호>NUMBER</법령일련번호>
  const mstMatch = xml.match(/<법령일련번호>(\d+)<\/법령일련번호>/);
  return mstMatch ? mstMatch[1] : null;
}

interface ArticleChunk {
  id: string;
  text: string;
  articleNo: string;
  articleTitle: string;
}

async function getLawArticles(mst: string, lawName: string): Promise<ArticleChunk[]> {
  const params = new URLSearchParams({
    OC: LAW_OC,
    type: "JSON",
    target: "eflaw",
    MST: mst,
  });

  const resp = await fetch(`${LAW_API_BASE}/lawService.do?${params}`, {
    signal: AbortSignal.timeout(30_000),
  });
  if (!resp.ok) throw new Error(`getLawText ${resp.status}`);

  const text = await resp.text();
  let data: any;
  try {
    data = JSON.parse(text);
  } catch {
    process.stderr.write(`  ⚠ JSON parse failed for MST=${mst}\n`);
    return [];
  }

  // Navigate JSON structure: 법령 > 조문 > 조문단위
  const lawRoot = data?.법령;
  if (!lawRoot) return [];

  const joList = lawRoot?.조문?.조문단위;
  if (!joList) return [];

  const articles = Array.isArray(joList) ? joList : [joList];
  const chunks: ArticleChunk[] = [];

  let lawType = "법률";
  if (lawName.includes("시행규칙")) lawType = "시행규칙";
  else if (lawName.includes("시행령")) lawType = "시행령";

  for (const jo of articles) {
    const articleNo = stripHtml(jo?.조문번호 ?? "");
    const articleTitle = stripHtml(jo?.조문제목 ?? "");
    const articleContent = stripHtml(jo?.조문내용 ?? "");

    if (!articleNo || !articleContent) continue;

    // Build full text with 항 content
    let fullText = `[${lawName}] 제${articleNo}조`;
    if (articleTitle) fullText += ` (${articleTitle})`;
    fullText += `\n${articleContent}`;

    // Append 항 content
    const hangList = jo?.항;
    if (hangList) {
      const hangs = Array.isArray(hangList) ? hangList : [hangList];
      for (const hang of hangs) {
        const hangNo = hang?.항번호 ?? "";
        const hangContent = stripHtml(hang?.항내용 ?? "");
        if (hangContent) {
          fullText += `\n${hangNo ? `③${hangNo} ` : ""}${hangContent}`;
        }
      }
    }

    // Truncate to ~2000 chars for embedding (keep meaningful)
    const truncated = fullText.length > 2000 ? fullText.slice(0, 2000) + "..." : fullText;

    // Keep ID under 64 bytes (Vectorize limit). Abbreviate long law names.
    const shortLaw = lawName
      .replace("국토의 계획 및 이용에 관한 법률", "국토계획법")
      .replace("산지관리법", "산지법")
      .replace("자연공원법", "공원법")
      .replace(/\s+/g, "_");
    let id = `${shortLaw}_제${articleNo}조`;
    // Final safety: truncate to 64 bytes
    while (Buffer.byteLength(id, "utf8") > 64) {
      id = id.slice(0, id.length - 1);
    }
    chunks.push({
      id,
      text: truncated,
      articleNo,
      articleTitle,
    });
  }

  return chunks;
}

// --- Jina 임베딩 ---

async function embedBatch(texts: string[], retries = 3): Promise<number[][]> {
  for (let attempt = 0; attempt < retries; attempt++) {
    const resp = await fetch("https://api.jina.ai/v1/embeddings", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${JINA_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "jina-embeddings-v3",
        input: texts,
        dimensions: 1024,
        task: "retrieval.passage",
      }),
      signal: AbortSignal.timeout(60_000),
    });

    if (resp.status === 429) {
      const wait = (attempt + 1) * 5000;
      process.stderr.write(`  ⚠ Rate limited, waiting ${wait / 1000}s...\n`);
      await new Promise((r) => setTimeout(r, wait));
      continue;
    }

    if (!resp.ok) {
      const err = await resp.text();
      throw new Error(`Jina embedding failed: ${resp.status} ${err}`);
    }

    const data = (await resp.json()) as { data: Array<{ embedding: number[] }> };
    return data.data.map((d) => d.embedding);
  }
  throw new Error("Jina embedding failed after retries");
}

// --- Main ---

async function main() {
  if (!LAW_OC) {
    console.error("LAW_OC required (법제처 Open API 인증키)");
    process.exit(1);
  }
  if (!JINA_API_KEY) {
    console.error("JINA_API_KEY required");
    process.exit(1);
  }

  let totalChunks = 0;
  let totalVectors = 0;

  for (const lawName of TARGET_LAWS) {
    process.stderr.write(`\n[${lawName}] Searching MST...\n`);

    let mst: string | null;
    try {
      mst = await searchLawMst(lawName);
    } catch (e) {
      process.stderr.write(`  ⚠ Search failed: ${e}, skipping\n`);
      continue;
    }

    if (!mst) {
      process.stderr.write(`  ⚠ MST not found, skipping\n`);
      continue;
    }
    process.stderr.write(`  MST=${mst}\n`);

    // Get articles via 법제처 API
    process.stderr.write(`  Fetching law text (JSON)...\n`);
    let chunks: ArticleChunk[];
    try {
      chunks = await getLawArticles(mst, lawName);
    } catch (e) {
      process.stderr.write(`  ⚠ Fetch failed: ${e}, skipping\n`);
      continue;
    }

    process.stderr.write(`  ${chunks.length} articles found\n`);
    totalChunks += chunks.length;

    if (chunks.length === 0) continue;

    // Detect law type
    let lawType = "법률";
    if (lawName.includes("시행규칙")) lawType = "시행규칙";
    else if (lawName.includes("시행령")) lawType = "시행령";

    // Embed in batches of 20
    const BATCH = 20;
    for (let i = 0; i < chunks.length; i += BATCH) {
      const batch = chunks.slice(i, i + BATCH);
      const texts = batch.map((c) => c.text);

      process.stderr.write(`  Embedding ${i + 1}~${i + batch.length}...\n`);
      const embeddings = await embedBatch(texts);

      for (let j = 0; j < batch.length; j++) {
        const record = {
          id: batch[j].id,
          values: embeddings[j],
          metadata: {
            law_name: lawName,
            law_type: lawType,
            article_no: batch[j].articleNo,
            article_title: batch[j].articleTitle,
            content: batch[j].text.slice(0, 500),
          },
        };
        // Output NDJSON to stdout
        console.log(JSON.stringify(record));
        totalVectors++;
      }

      // Rate limit: 3s between batches (Jina free tier concurrency=2)
      if (i + BATCH < chunks.length) {
        await new Promise((r) => setTimeout(r, 3000));
      }
    }

    // Rate limit between laws: 3s
    await new Promise((r) => setTimeout(r, 3000));
  }

  process.stderr.write(`\n✅ Done: ${totalChunks} chunks, ${totalVectors} vectors\n`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
