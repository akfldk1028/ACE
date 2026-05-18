import { Hono } from "hono";
import type { Env } from "../index";

export const healthRoutes = new Hono<{ Bindings: Env }>();

healthRoutes.get("/health", (c) => {
  return c.json({
    status: true,
    service: "law-light-api",
    version: "0.2.0",
    features: {
      law_search: true,
      land_analysis: true,
      vector_search: !!c.env.JINA_API_KEY,
    },
  });
});
