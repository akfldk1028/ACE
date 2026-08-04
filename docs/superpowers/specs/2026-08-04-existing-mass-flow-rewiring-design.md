# Existing MASS Flow Rewiring Design

## Objective

Restore broad, law-compliant MASS supply by reconnecting existing BASE review, BOOK descendant generation, MAP-Elites retention, final VLM, typed repair, and selector feedback in the intended order. Do not add a second archive, lower statutory gates, or make stair-step massing invalid.

## Confirmed current flow defects

1. Initial generation is two-phase: BASE generation, BASE VLM, reviewed parent registry, then BOOK descendants.
2. Replenishment generates descendants before BASE VLM because it calls the generation pool without the existing review callback.
3. The reviewed BASE registry requires final selection eligibility and discards development-reviewed parents before BOOK operations can improve them.
4. `StreamingMapElitesArchive` retains live candidates only inside one generation invocation. Across replenishment cycles only final-VLM hard passes survive.
5. Selector exclusions are calculated after selection but are not included in the next bounded author-feedback payload.
6. Final VLM accepted-only authority is intentional and remains authoritative. The fix broadens lawful candidate supply before that gate.

## Existing modules and ownership

- `candidate_generation.py`: BASE/descendant phases, reviewed parent authority, generation-local MAP-Elites.
- `portfolio_replenishment.py`: one replenishment cycle, downstream routing, retained candidate pools and cycle evidence.
- `portfolio_benchmark.py`: top-level orchestration, cross-cycle state, selection, feedback and run budgets.
- `quality_diversity_archive.py`: existing live-candidate QD storage and descriptor logic.
- `final_vlm_cycle.py`: initial VLM, typed repair, legal revalidation and second VLM authority.
- `portfolio_selection.py`: final distinct portfolio selection and exclusion diagnostics.

No new archive or agent is introduced.

## Target flow

```text
BASE generation
-> BASE VLM review
-> reviewed or development-eligible certified parent registry
-> BOOK descendants
-> clean/program/statutory/parking gates
-> bounded live QD reserve carried across cycles
-> final VLM + typed repair + statutory revalidation
-> final hard-pass pool
-> portfolio selector
-> selector exclusion feedback
-> next BASE author request
```

## Contracts

### Two-phase replenishment

Replenishment must use the same existing callback boundary as initial generation. Descendant generation must never begin before the current cycle's BASE review evidence and exact parent registry exist.

### Development parent release

A BASE may parent development descendants when it has exact archived identity, valid structural/statutory authority, a real VLM response, no hash conflict, and either final selection eligibility or explicit development-review eligibility. This authority does not make the BASE selectable or publishable.

### Cross-cycle live reserve

Carry only live candidates that already contain materialized source, exact program/geometry identity, legal/program authority and typed lineage. Bound and deduplicate the reserve through existing MAP-Elites/fingerprint functions. Legal archive dictionaries are never rehydrated as candidates.

### Selector feedback

Coordinate-free selector exclusions such as `silhouette_near_duplicate`, operation/scope caps and missing descriptor cells are sanitized through the existing bounded causal-feedback function and added to the next author request. Geometry payloads and coordinates remain excluded.

## Invariants

- Site containment, structure, height, BCR, FAR, statutory law graph and parking remain hard gates.
- Final VLM remains the final visual authority.
- Typed repairs must pass downstream statutory and parking revalidation before second VLM.
- Capacity remains advisory where the current contract marks it diagnostic.
- Stair-step candidates remain valid but must not monopolize descriptor supply.
- Every loop records stage input, output, rejection reasons and carry-forward counts.

## Verification strategy

Each rewiring is tested separately with deterministic fake candidates and callbacks. No paid full run occurs between tasks. After all focused tests pass, run one bounded deterministic multi-cycle funnel and then one live target-5 run. Success requires five rendered candidates, statutory hard-pass evidence, final-VLM authority, and more than one measured phenotype/body/section family.

