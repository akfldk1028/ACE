# Program-site infeasible early-stop independent review

Date: 2026-07-29  
Mode: read-only code review and fresh focused verification

## Decision

**APPROVE**

The reviewed `portfolio_benchmark.py` change is correctly scoped to a raw
program dimensional result whose `status` is `infeasible`.

## Requirement review

- **No gate, span, or acceptance lowering:** pass. The implementation does not
  change `_program_dimensional_context`, the 6 m gym minimum span, legal CSG,
  parking, capacity, or selection thresholds.
- **Raw infeasible evidence preserved:** pass. Existing dimensional fields,
  including `status`, subtype, failure reasons, host dimensions, and zero
  effective height/floors, are retained. Added catalog, advisory, plan-hash,
  and floor-authority fields are supplemental.
- **No MASS generation:** pass. The infeasible branch appends its result and
  executes `continue` before capacity-contract construction and
  `_program_pool`.
- **Compatible path unchanged at the boundary:** pass. A feasible dimensional
  result continues to the existing capacity-contract and `_program_pool`
  path. The dedicated regression test proves `_program_pool` is reached.
- **Diagnostic and downstream remain failed:** pass. The early result records
  `generation_status=program_site_infeasible`, zero selected/evaluated counts,
  downstream `status=fail`, completion `hard_pass=False`, and explicit
  failure reasons. Diagnostic policy may rewrite display `status` to
  `diagnostic_only`, but does not convert any failure or completion field to
  pass.
- **PNG, state, and summary schema:** pass within focused evidence. The
  regression executes the empty-board renderer, writes and reparses the
  summary JSON, and checks persisted early-stop evidence. The run-state writer
  is called with the explicit `program_site_infeasible` phase and zero counts.
  The normal combined-board path receives the generated empty board.
- **No unintended `plan_infeasible` expansion:** pass. The new early stop
  predicate is only `dimensional_context["status"] == "infeasible"`.
  `plan_infeasible` remains on its existing downstream fallback path and is
  only reported in advisory evidence.

## Fresh verification

Command:

```text
python manage.py test \
  design.test_maas_book_language.MaasBookLanguageRegistryTest.test_program_site_infeasible_stops_before_mass_generation_and_persists_evidence \
  design.test_maas_book_language.MaasBookLanguageRegistryTest.test_program_site_compatible_still_reaches_mass_generation \
  design.test_maas_geometry_language.MaasGeometryLanguageTest.test_gym_dimensional_context_adapts_height_or_reports_infeasible \
  design.test_maas_mass_product_evidence.MaasMassProductEvidenceTest.test_diagnostic_target_is_strictly_bounded_and_never_completes_portfolio \
  --verbosity 2
```

Result:

- 4 tests discovered
- 4 passed
- 0 failed
- Django system check: 0 issues
- exit code 0

## Non-blocking observation

The internal materializer still reports only the outer
`directed_geometry_materialization_failed` reason for other failures. That
observability limitation is outside this early-stop patch and does not block
approval.
