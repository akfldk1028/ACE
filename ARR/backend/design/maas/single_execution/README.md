# Single MASS Execution

This package is the deployable execution boundary for exactly one explicit
`GeometryProgram`. It does not run the 20-item portfolio search.

## Flow

`GeometryProgram -> validate -> compile -> geometry GATE -> four-view PNG -> execution passport -> causal agent context`

Every run creates one discoverable directory:

```text
<output-root>/<execution-id>/
  program.json
  mass.png                         # only when geometry GATE passes
  mass.png.passport.json           # stage truth + one causal graph
  execution.json                   # status, hashes, artifacts, stage latency
```

`geometry_ready=true` means the deterministic AST/compiler/GATE/render stages
passed. It does not mean law, parking, VLM, or final selection passed. Those
stages remain `not_evaluated` until their owning agents provide real evidence.

## CLI

```powershell
python manage.py execute_maas_single_mass --shape-index 10
python manage.py execute_maas_single_mass --program-json D:\path\program.json
python manage.py execute_maas_single_mass --run-id book-program-portfolios-r196-streaming-qd-one-cycle --mass-index 1
```

## HTTP

```http
POST /design/maas/single-executions/
Content-Type: application/json

{"program": {"schema_version": "arr.maas.geometry_program.v1", "nodes": [], "root_id": "..."}}
```

The response returns preview, passport, and manifest URLs. Paid VLM input and
downstream hard-gate evidence are intentionally not accepted from this public
endpoint; trusted internal agents enrich the same passport.

## Frontend archive integration

Every source-run replay receives a unique UTC execution ID. It is exposed as
`single-execution:<id>` through the existing `/maas/executed-masses/` read model,
so `/design/language` adds it to the same chronological timeline and renders
its one PNG/passport in the same Full Graph. No parallel graph is created.

Before completion, follow
`docs/ai-session-memory/maas-mass-flow/07_FULL_TEST_CONTRACT.md`.
