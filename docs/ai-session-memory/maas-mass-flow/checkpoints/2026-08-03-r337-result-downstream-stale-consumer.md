# r337 result: downstream stale consumer

Date: 2026-08-03 KST

## Result

r337 completed in 154.4 seconds but selected 0/3.

- LLM directed geometry materialized: 5
- Authored legal projection materialized: 5
- Scope distribution: 1/1 = 2, 3/8 = 1, 1/4 = 2
- Base VLM calls: 2
- Final selected: 0
- PNG contained only the title strip because no candidate passed the downstream hard gate.

This is a material improvement over r336: Task8A/8B/8C allowed real authored masses to materialize and reach VLM. The remaining failure was not another geometric materialization collapse.

## Root cause

The bridge producer and projection certificate use canonical `post_book_authored_program_hash` and `post_book_authored_geometry_hash`. Task7C intentionally removed obsolete `upstream_authored_*` aliases. The downstream hard gate still read the removed aliases, so its diagnostic showed `bridge_input_program_hash=''` even while certificate and final program hashes matched.

Task8A did not erase the hash. Its repaired legal authority transport allowed exact artifacts to progress far enough to expose this stale consumer.

## Repair

- Downstream projection-chain checks now read only canonical `post_book_authored_program_hash` and `post_book_authored_geometry_hash`.
- Program and geometry equality remain strict.
- No obsolete alias or fallback was restored.
- Regression proves the downstream chain passes while obsolete aliases remain absent.

Focused Task7C result: 8/8 passed. Independent review: PASS.

Next action: run one r338 target3 full MASS portfolio and inspect the final PNG. Do not loop if another typed terminal reason appears.
