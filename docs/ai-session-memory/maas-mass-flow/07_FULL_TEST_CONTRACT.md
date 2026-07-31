# MAAS Full-Test Completion Contract

No session may call MAAS work complete after a unit test, one PNG, a backend
response, or a frontend screenshot alone. Completion has two distinct gates.

## Engineering full test

Run all of the following after the final source edit:

1. Backend: `python manage.py test design --verbosity 1` and
   `python manage.py check`.
2. Frontend: `npm test` (including its Vite pretest build) and
   `npm run type-check`.
3. Live HTTP through the same Vite proxy used by people, not a test client only.
4. Browser E2E on `/design/language`:
   - exactly one Full Graph;
   - actual MASS archive PNGs load;
   - click one MASS and observe real active causal edges;
   - click `EXECUTE SELECTED MASS`;
   - a new chronological `single-execution:<id>` run appears;
   - the UI switches to one actual generated PNG and the same passport graph;
   - no BOOK raster, console error, page error, or hidden 4xx/5xx request.
5. Directly inspect the generated four-view PNG and record component count,
   triangle count, geometry hash, and visible quality limits.
6. Validate every updated machine-readable memory JSON.

Any skipped or failed item keeps engineering status incomplete.

## Full MAAS acceptance

Engineering green is not architectural acceptance. One MASS is accepted only
when its passport records real evaluated evidence for site, capacity, law,
parking, program fit, compiler, geometry GATE, render, VLM, and selector.

- `not_evaluated` is never a pass.
- A fresh paid VLM call is required when the requested outcome includes a new
  visual/program-fit judgement and no exact image/prompt/model/program-hash
  cache exists. Bound calls after deterministic GATE; never spray hundreds.
- A cached VLM result is valid only when its input hashes and model/prompt
  identity match and the passport says `cache_hit`.
- Legal/parking preflight is not approval-grade law verification.
- If VLM or an authority stage is pending, report `engineering_full_test=pass`
  and `full_maas_acceptance=incomplete`; never shorten that to "all passed".

## Memory and git handoff

After a full test, update `02_CURRENT_STATE.md`, `current-checkpoint.json`, and
`CHANGELOG.md` with commands, counts, browser evidence, paid VLM request count,
truthful pending stages, commit, and push target. Preserve historical runs and
commit only the current task's files from a mixed worktree.
