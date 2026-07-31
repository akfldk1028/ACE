/**
 * Design optimization gateway.
 *
 * Worker-side: regulations → constraints conversion (no network).
 * ARR-side:    GA optimization + SSE streaming (proxied).
 *
 * Routes:
 *   POST /design/optimize          — create optimization job on ARR
 *   POST /design/auto-constraints  — proxy to ARR auto-constraints
 *   GET  /design/jobs/:id          — proxy job status
 *   GET  /design/jobs/:id/stream   — SSE relay
 *   GET  /design/jobs/:id/results  — proxy results
 */

import { Hono } from "hono";
import type { Env } from "../index";
import { regulationsToConstraints, buildDefaultJobSpec } from "../regulation/constraint-bridge";

export const designRoutes = new Hono<{ Bindings: Env }>();

// ---------------------------------------------------------------------------
// POST /design/optimize
// Body: { regulations, site_polygon, building_type?, algorithm?, pnu?, address? }
//
// 1. regulations → constraints (Worker internal)
// 2. build job_spec (Worker internal)
// 3. POST to ARR /design/jobs/ to create+start
// 4. Return job info (client then connects to /stream)
// ---------------------------------------------------------------------------
designRoutes.post("/optimize", async (c) => {
  const arrUrl = c.env.ARR_BACKEND_URL;
  if (!arrUrl) {
    return c.json({ error: "ARR_BACKEND_URL not configured" }, 503);
  }

  const body = await c.req.json().catch(() => null);
  if (!body || typeof body !== "object") {
    return c.json({ error: "Invalid JSON body" }, 400);
  }

  const {
    regulations,
    site_polygon,
    building_type = "공동주택",
    algorithm = "additive",
    pnu = "",
    address = "",
    site_area_m2,
  } = body as Record<string, unknown>;

  if (!site_polygon) {
    return c.json({ error: "site_polygon (GeoJSON) is required" }, 400);
  }

  // Convert regulations → GA constraints (Worker internal, no network)
  let constraints: ReturnType<typeof regulationsToConstraints> = [];
  if (regulations && typeof regulations === "object") {
    constraints = regulationsToConstraints(regulations as Record<string, unknown>);
  }

  // Build job_spec if site_area is available
  let jobSpec: ReturnType<typeof buildDefaultJobSpec> | undefined;
  if (typeof site_area_m2 === "number" && site_area_m2 > 0) {
    jobSpec = buildDefaultJobSpec(
      site_area_m2,
      constraints,
      building_type as string,
      algorithm as string,
    );
  }

  // Forward to ARR backend
  const arrBody: Record<string, unknown> = {
    site_polygon,
    constraints,
    pnu,
    address,
  };
  if (jobSpec) {
    arrBody.job_spec = jobSpec;
  }

  const resp = await fetch(`${arrUrl}/design/jobs/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(arrBody),
  });

  const data = await resp.json();
  return c.json(data, resp.status as 200);
});

// ---------------------------------------------------------------------------
// POST /design/auto-constraints — proxy to ARR
// ---------------------------------------------------------------------------
designRoutes.post("/auto-constraints", async (c) => {
  const arrUrl = c.env.ARR_BACKEND_URL;
  if (!arrUrl) {
    return c.json({ error: "ARR_BACKEND_URL not configured" }, 503);
  }

  const body = await c.req.text();
  const resp = await fetch(`${arrUrl}/design/auto-constraints/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });

  const data = await resp.json();
  return c.json(data, resp.status as 200);
});

// ---------------------------------------------------------------------------
// GET /design/jobs/:id — proxy job status
// ---------------------------------------------------------------------------
designRoutes.get("/jobs/:id", async (c) => {
  const arrUrl = c.env.ARR_BACKEND_URL;
  if (!arrUrl) {
    return c.json({ error: "ARR_BACKEND_URL not configured" }, 503);
  }

  const id = c.req.param("id");
  const resp = await fetch(`${arrUrl}/design/jobs/${id}/`);
  const data = await resp.json();
  return c.json(data, resp.status as 200);
});

// ---------------------------------------------------------------------------
// GET /design/jobs/:id/stream — SSE relay
// Reads the SSE stream from ARR and pipes it through to the client.
// ---------------------------------------------------------------------------
designRoutes.get("/jobs/:id/stream", async (c) => {
  const arrUrl = c.env.ARR_BACKEND_URL;
  if (!arrUrl) {
    return c.json({ error: "ARR_BACKEND_URL not configured" }, 503);
  }

  const id = c.req.param("id");
  const resp = await fetch(`${arrUrl}/design/jobs/${id}/stream`);

  if (!resp.ok) {
    const data = await resp.json().catch(() => ({ error: "Upstream error" }));
    return c.json(data, resp.status as 200);
  }

  // Relay the SSE stream
  return new Response(resp.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "X-Accel-Buffering": "no",
    },
  });
});

// ---------------------------------------------------------------------------
// GET /design/jobs/:id/results — proxy results
// ---------------------------------------------------------------------------
designRoutes.get("/jobs/:id/results", async (c) => {
  const arrUrl = c.env.ARR_BACKEND_URL;
  if (!arrUrl) {
    return c.json({ error: "ARR_BACKEND_URL not configured" }, 503);
  }

  const id = c.req.param("id");
  const resp = await fetch(`${arrUrl}/design/jobs/${id}/results/`);
  const data = await resp.json();
  return c.json(data, resp.status as 200);
});
