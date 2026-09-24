# 2026-08-03 r341-r343 BASE, capacity, and VLM trace

## Verified improvements

- Measured typed-AST capacity composition is active; replacement requires recompilation, shared-floor hard pass, final capacity hard pass, and strict utilization improvement.
- Focused capacity/lineage/visual-authority regressions pass.
- Competition scheduling now retains an actual pre-BOOK BASE candidate before its descendant.
- BASE VLM is no longer empty: r342/r343 reviewed one real LLM-authored BASE with nonempty render geometry and approved it.
- r342/r343 measured five candidates, with two `capacity_selectable_and_floor_contract_passed` and two capacity hard passes.

## r341

- Result: `0/5`.
- BASE VLM request count advanced from zero to one.
- Main materialization losses moved to authored identity/visual-authority projection.

## r342

- Result: `0/5`, duration about 50 seconds.
- Capacity measured: 5.
- Capacity + shared-floor selectable: 2.
- BASE VLM: input 1, approved 1.
- Descendant release: 0; rejected descendant: 1.
- Final VLM reviewed the BASE itself and rejected `final_book_unresolved_pyramidal_program_relation`.

## r343

- Result: `0/5`, duration about 50 seconds.
- Exact parent geometry binding helper regressions pass, including missing/conflicting fail-closed cases.
- Live result is unchanged: parent shortlist still reports `descendant_candidate_count=0`, release 0, rejected 1.
- This proves the remaining defect is production ordering, not the exact-identity predicate: descendant lineage is attached before the compiler-clean BASE geometry registry is populated.

## Required architectural correction

Split candidate production into two explicit phases for each selected LLM lineage:

1. Materialize, compile, contain, and register the BASE candidate and exact geometry hash.
2. Materialize the descendant and bind `parent_geometry_hash` from that already-certified BASE registry.

Do not relax `exact_parent_fingerprint`, do not use coarse `parent_key` as sufficient VLM identity, and do not bind the descendant's own geometry hash.

## Current PNG

- `D:\\Data\\25_ACE\\docs\\playwright\\design-route-live-verify\\book-program-portfolios-r343-exact-parent-target5\\maas-book-neighborhood-5.png`
- It is a failed 0/5 title-only board, not a valid MASS result.
