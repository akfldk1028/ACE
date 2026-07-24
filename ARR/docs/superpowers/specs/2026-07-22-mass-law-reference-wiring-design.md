# MASS Law Evidence and ArchDaily Reference Wiring Design

## Goal

Every single-MASS execution must be a visible multi-agent collaboration. The
existing design orchestrator must hand the exact MASS identity through
`maas_geometry_agent`, `law_graph_agent`, `parking_agent`, and `review_agent`
before it can be accepted. Those agents reuse the existing PNU law calculator,
law MCP, and Neo4j law graph. VLM review must retrieve a bounded but genuinely
diverse set of ArchDaily references using the MASS program identity rather than
falling back to generic references.

## Non-goals

- Do not rebuild or duplicate the existing law Graph DB.
- Do not create a second legal authority or a second geometry graph.
- Do not replace agent collaboration with direct orchestration-layer database
  calls.
- Do not make law or reference retrieval geometry-authoring code.
- Do not increase paid VLM calls per MASS beyond the existing bounded candidate
  review call; reference-image audits remain hash-cached.

## Architecture

### Multi-agent execution authority

The existing `design_orchestrator` owns the run but does not decide specialist
results. It passes an immutable execution identity
`execution_id + program_hash + geometry_hash + PNU` through this sequence:

1. `maas_geometry_agent` confirms compiled geometry and site-bound metrics;
2. `law_graph_agent` invokes the existing law MCP/Neo4j tools and returns typed
   legal provenance plus missing evidence;
3. `parking_agent` consumes the same legal/program context and returns the
   required count and layout feasibility;
4. `review_agent` evaluates the accumulated specialist evidence and returns
   `accepted`, `failed`, or `needs_evidence`;
5. the selector may accept only the `review_agent` decision bound to the exact
   hashes above.

Each handoff is a persisted event with source agent, target agent, input hashes,
output evidence IDs, status, and bounded error category. An agent cannot mark a
stage complete by merely observing another stage's scalar result.

### Law agent evidence boundary

Give `law_graph_agent` one focused law-evidence adapter. The orchestrator calls
the agent contract, never the adapter directly. The adapter reuses existing
services and normalizes their result into a passport-safe contract containing:

- PNU and site-regulation calculator evidence;
- MCP request status and resolved rule IDs;
- Neo4j graph availability and resolved article nodes;
- ordinance/article/appendix/effective-date/source URL evidence when available;
- parking rule and layout evidence;
- explicit missing-evidence reasons.

The adapter records every attempted source. A disconnected MCP or Neo4j service
must never be silently represented as a legal pass.

### Acceptance policy

Geometry compilation and rendering may continue when an external legal service
is unavailable so diagnostic MASS PNGs are not lost. Final selection must be
`needs_evidence`, never `accepted`, until required law and parking provenance is
materialized. Existing PNU numeric checks remain valid preflight evidence, but
they are not substituted for missing graph provenance.

### ArchDaily reference contract

Resolve program identity in this order:

1. explicit review request;
2. top-level `metadata.building_type` or `metadata.program_id`;
3. nested `metadata.program_projection.building_type` or `program_id`;
4. family fallback;
5. `generic` only when all structured program identity is absent.

Retrieve at most three VLM references per MASS:

1. one program-specific whole-building precedent;
2. one formally similar massing precedent;
3. one counterfactual precedent with a missing formal/public-space strategy.

Deduplicate by source identity and exact image hash inside a request. Persist
reference usage in the outcome graph so repeated precedents can be penalized
across later candidates. A program-specific minimum of one is required whenever
the program contract provides a curated collection.

## Unified graph and memory

The existing FULL GRAPH remains the only causal graph. Add agent and handoff
nodes under the selected MASS path for design orchestration, geometry review,
law review, parking review, final review, MCP request, Neo4j resolution, law
articles, parking rule, and each actual VLM reference. Do not create a separate
law, agent, or reference graph UI.

Update `docs/ai-session-memory/maas-mass-flow` with these invariants:

- existing MCP/Graph DB paths must be reused, not reimplemented;
- MASS acceptance is a multi-agent decision and specialist agents cannot be
  bypassed by direct service calls;
- every agent handoff is hash-bound, persisted, and visible in the unified graph;
- external-source attempts and failures are material evidence;
- missing law provenance blocks acceptance but not diagnostic rendering;
- ArchDaily retrieval is program-conditioned and role-diverse;
- every used reference is bound to the MASS passport and unified graph.

## Error handling

- MCP unavailable: record `attempted=true`, `available=false`, and the bounded
  error category; final status becomes `needs_evidence`.
- Neo4j unavailable: preserve PNU preflight results, record graph failure, and
  block acceptance.
- No program-specific ArchDaily image: do not substitute an unrelated iconic
  image as program-specific evidence; record the shortfall and block VLM program
  fit while allowing a diagnostic review.
- Cached reference audit: reuse only when prompt contract, model, and image hash
  all match.

## Verification

Automated tests must prove:

- nested `program_projection.program_id` reaches reference retrieval;
- the three reference roles are distinct and image-deduplicated;
- legal provenance attempts are visible in the passport;
- the orchestrator invokes all required specialist agent contracts in order;
- direct law-adapter use cannot satisfy the multi-agent acceptance contract;
- unavailable graph services cannot produce `accepted`;
- an available existing law source can produce a fully bound accepted passport;
- the frontend unified graph renders the law-source and reference nodes;
- memory documents state the same invariants.

Final live verification will be performed only after the user starts the existing
Neo4j and law MCP services. It must use one MASS, at most three references, and
zero retry loops beyond the existing bounded policy.
