import { Hono } from "hono";
import { cors } from "hono/cors";
import { searchRoutes } from "./routes/search";
import { landRoutes } from "./routes/land";
import { lawRoutes } from "./routes/law";
import { healthRoutes } from "./routes/health";
import { designRoutes } from "./routes/design";

export type Env = {
  VWORLD_API_KEY: string;
  LAW_OC: string;          // 법제처 Open API 인증키
  OPENAI_API_KEY: string;  // LLM chat (gpt-4o-mini)
  JINA_API_KEY: string;    // Jina embeddings v3 (1024-dim)
  LAW_VECTORS: VectorizeIndex;
  ARR_BACKEND_URL: string; // Railway-hosted ARR Django backend
};

const app = new Hono<{ Bindings: Env }>();

app.use("*", cors());

app.route("/search", searchRoutes);
app.route("/land", landRoutes);
app.route("/law", lawRoutes);
app.route("/design", designRoutes);
app.route("/", healthRoutes);

export default app;
