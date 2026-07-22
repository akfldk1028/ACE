# Bounded Single-MASS VLM Flow

Date: 2026-07-22
Status: approved by the user request to make the selected MASS flow succeed
with a paid VLM while explicitly avoiding hundreds of image calls.

## Goal

Execute one selected archived MASS through one auditable flow:

`exact GeometryProgram -> compiler -> geometry GATE -> four-view PNG -> bounded
reference retrieval -> paid/cached VLM -> passport -> same Full Graph`

The result is successful only when deterministic hard gates pass and the VLM
returns an explicit positive massing/program-fit verdict. Merely completing a
VLM request is never acceptance.

## Chosen approach

Use a dedicated single-MASS review orchestrator. Keep the deterministic
`single_execution.pipeline` free of network calls, and let the orchestrator
compose it with the existing geometry VLM adapter. This preserves fast local
execution, keeps paid behavior explicit, and avoids putting portfolio search
or provider code into Django views.

Rejected alternatives:

1. Calling VLM inside `execute_single_mass`: simple, but makes every compiler
   execution potentially paid and couples deterministic tests to the network.
2. Reusing the portfolio audit CLI unchanged: it cannot read single-execution
   bundles and mutates portfolio archives instead of the selected run passport.

## Modules

- `single_execution.pipeline`: deterministic compile/GATE/render/passport only.
- `single_execution.repository`: immutable run ID allocation, bundle lookup,
  and archive indexing. Existing IDs cannot be overwritten.
- `single_execution.replay`: resolve an archived portfolio or single run into
  an exact program plus hash-bound downstream evidence.
- `single_execution.vlm_review`: retrieve at most two references, reuse exact
  reference/candidate caches, make at most one candidate critic request, bind
  response/model/prompt/image/program/geometry hashes and API usage to the same
  passport, and recompute final state.
- Django views: validate HTTP input and call the services; no evidence copying
  or archive dispatch logic.
- Frontend API/hook: explicit `RUN BOUNDED VLM` action for the selected
  single-execution run, then reload the same run/passport/Full Graph.

## Paid-call contract

- Selection unit: exactly one MASS.
- Candidate VLM: at most one live request per action.
- Reference images submitted to the candidate: at most two.
- Reference suitability audits: cache first; cold live audit maximum two.
- Total live HTTP request ceiling for this action: four, including retries.
- No portfolio loop and no automatic audit of sibling MASSes.
- Record request count, cache-hit count, model, response IDs, image hashes,
  prompt contract, input/output/total tokens and errors.
- Reference suitability audit uses low image detail; candidate four-view review
  uses high detail.
- If the budget is exhausted, the passport remains `not_evaluated` or failed;
  it never becomes accepted.

## Acceptance semantics

- `full_flow_complete`: every required stage was evaluated, including VLM.
- `final_hard_pass`: deterministic hard stages passed AND VLM status is a
  successful cached/live evaluation AND VLM `hard_pass=true` AND
  `program_fit_hard_pass=true`.
- API/provider errors, missing hash binding, explicit VLM failure, or stale
  evidence produce `final_hard_pass=false`.

## Immutable evidence

- HTTP execution IDs are server-generated and unique.
- A client label or idempotency key cannot select a filesystem directory.
- Existing execution directories are never replaced.
- VLM evidence is reusable only when program hash, geometry hash, candidate
  PNG SHA, model, prompt contract and submitted reference hashes match.
- Internal absolute paths remain in the persisted manifest but are not exposed
  by the public HTTP response.

## Frontend behavior

- `EXECUTE SELECTED MASS` creates the immutable deterministic run.
- The right sidebar then offers `RUN BOUNDED VLM` with the visible limits.
- During review it shows live/cache request counts and never says PASS early.
- Completion reloads the same single run; no second graph is created.
- On run change, stale passport/outcome/VLM state is cleared immediately and
  prior requests are aborted.

## Tests

1. VLM `program_fit_hard_pass=false` cannot produce accepted state.
2. VLM provider error cannot produce accepted state.
3. hash-matched cached positive VLM can produce accepted state when every
   deterministic stage passes.
4. duplicate requested execution IDs cannot overwrite a bundle.
5. `reference_limit=1` retrieves/audits/submits no more than one reference.
6. cache root is repository-absolute independent of process CWD.
7. single-run VLM endpoint rejects portfolio-wide or multi-MASS requests.
8. mocked live review records exact call/usage/hash evidence and enriches the
   same passport.
9. frontend displays limits and reloads the same run after VLM review.
10. browser E2E verifies one graph, one selected MASS, evaluated VLM evidence,
    actual submitted reference nodes only, and zero browser errors.

One real paid run is performed only after deterministic and mocked tests pass.
The live run targets the latest verified single MASS and uses the four-request
ceiling above.
